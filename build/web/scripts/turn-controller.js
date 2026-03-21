/**
 * Neo-Hack: Gridlock v3.2 — Turn-Based Game Controller
 * Replaces the real-time game loop with a turn-based flow.
 * Communicates with the backend for each action and manages turn switching.
 */

import { events, Events } from './game-events.js';
import { api } from './api-client.js';

export class TurnController {
  constructor() {
    this.sessionId = null;
    this.role = null;           // 'attacker' | 'defender'
    this.difficulty = 'normal'; // 'novice' | 'normal' | 'expert'
    this.scenario = 'default';

    // Game state received from backend
    this.gameState = {
      currentTurn: 0,
      maxTurns: 20,
      currentPlayer: 'attacker',
      actionPointsRemaining: 1,
      alertLevel: 0,
      stealthLevel: 100,
      nodes: [],
      connections: [],
      discoveredNodes: [],
      compromisedNodes: [],
      detectedNodes: [],
      resources: {},
      objectives: { attacker: [], defender: [] },
      gameOver: false,
      winner: null,
    };

    this._pollTimer = null;
    this._isProcessing = false;

    this._bindEvents();
  }

  _bindEvents() {
    events.on(Events.ACTION_EXECUTE, (payload) => this.onPlayerAction(payload));
  }

  /**
   * Emit game state update event for UI/renderer to listen to
   */
  _emitStateUpdate() {
    events.emit(Events.GAME_STATE_UPDATE, {
      gameState: this.gameState,
      sessionId: this.sessionId,
      role: this.role,
    });
  }

  /**
   * Is it currently the local player's turn?
   */
  get isMyTurn() {
    return this.gameState.currentPlayer === this.role;
  }

  /**
   * Start a new game session.
   * @param {object} opts - { role, difficulty, scenario }
   */
  async startGame({ role, difficulty, scenario }) {
    this.role = role;
    this.difficulty = difficulty || 'normal';
    this.scenario = scenario || 'default';
    this._isProcessing = true;

    try {
      const res = await api.createGameSession({
        role: this.role,
        difficulty: this.difficulty,
        scenario: this.scenario,
      });

      this.sessionId = res.session_id;
      this._applyState(res.game_state);

      // Emit initial state update for renderer
      this._emitStateUpdate();

      events.emit(Events.GAME_START, {
        sessionId: this.sessionId,
        role: this.role,
        gameState: this.gameState,
      });

      events.emit(Events.TURN_START, {
        turn: this.gameState.currentTurn,
        player: this.gameState.currentPlayer,
        isMyTurn: this.isMyTurn,
      });

      // If AI goes first, poll for its action
      if (!this.isMyTurn) {
        this._startOpponentPoll();
      }
    } catch (err) {
      console.error('[TurnController] Failed to create game session:', err);
      events.emit(Events.TOAST_SHOW, {
        message: 'Failed to start game. Is the server online?',
        type: 'error',
      });
    } finally {
      this._isProcessing = false;
    }
  }

  /**
   * Execute a player action.
   * @param {object} payload - { actionId, actionName, targetNode }
   */
  async onPlayerAction({ actionId, actionName, targetNode }) {
    if (!this.sessionId) return;
    if (!this.isMyTurn) {
      events.emit(Events.TOAST_SHOW, { message: 'Not your turn!', type: 'warning' });
      return;
    }
    if (this._isProcessing) return;
    this._isProcessing = true;

    try {
      const res = await api.submitTurnAction({
        session_id: this.sessionId,
        player_role: this.role,
        action_type: actionName,
        action_id: actionId,
        target_node: targetNode,
      });

      // Emit action result
      events.emit(Events.ACTION_RESULT, {
        actionName,
        targetNode,
        success: res.success,
        detected: res.detected,
        message: res.message,
        details: res.details || {},
      });

      // Apply updated game state
      if (res.game_state) {
        this._applyState(res.game_state);
      }

      // Log the event
      events.emit(Events.LOG_ADD, {
        message: res.message || `${actionName} on node ${targetNode}`,
        severity: res.success ? 'info' : 'warning',
        source: 'action',
        nodeRef: targetNode,
        turn: this.gameState.currentTurn,
      });

      // Check game over
      if (this.gameState.gameOver) {
        this._handleGameOver();
        return;
      }

      // Check if turn switched
      if (this.gameState.currentPlayer !== this.role) {
        events.emit(Events.TURN_SWITCH, {
          turn: this.gameState.currentTurn,
          player: this.gameState.currentPlayer,
          isMyTurn: false,
        });
        this._startOpponentPoll();
      } else {
        // Same player's turn continues (multi-AP scenario)
        events.emit(Events.TURN_START, {
          turn: this.gameState.currentTurn,
          player: this.gameState.currentPlayer,
          isMyTurn: true,
        });
      }
    } catch (err) {
      console.error('[TurnController] Action failed:', err);
      events.emit(Events.TOAST_SHOW, {
        message: `Action failed: ${err.message}`,
        type: 'error',
      });
    } finally {
      this._isProcessing = false;
    }
  }

  /**
   * End the current turn manually (skip remaining AP).
   */
  async endTurn() {
    if (!this.isMyTurn || this._isProcessing) return;
    this._isProcessing = true;

    try {
      const res = await api.endTurn({
        session_id: this.sessionId,
        player_role: this.role,
      });

      if (res.game_state) {
        this._applyState(res.game_state);
      }

      if (this.gameState.gameOver) {
        this._handleGameOver();
        return;
      }

      events.emit(Events.TURN_SWITCH, {
        turn: this.gameState.currentTurn,
        player: this.gameState.currentPlayer,
        isMyTurn: this.isMyTurn,
      });

      if (!this.isMyTurn) {
        this._startOpponentPoll();
      }
    } catch (err) {
      console.error('[TurnController] End turn failed:', err);
      events.emit(Events.TOAST_SHOW, {
        message: `End turn failed: ${err.message}`,
        type: 'error',
      });
    } finally {
      this._isProcessing = false;
    }
  }

  /**
   * Poll the backend waiting for the opponent (AI or human) to finish their turn.
   */
  _startOpponentPoll() {
    this._stopOpponentPoll();

    events.emit(Events.LOG_ADD, {
      message: `Waiting for ${this.gameState.currentPlayer}'s move...`,
      severity: 'info',
      source: 'system',
    });

    this._pollTimer = setInterval(async () => {
      try {
        const res = await api.getGameState(this.sessionId);
        if (!res || !res.game_state) return;

        const prevPlayer = this.gameState.currentPlayer;
        this._applyState(res.game_state);

        if (this.gameState.gameOver) {
          this._stopOpponentPoll();
          this._handleGameOver();
          return;
        }

        // If turn flipped back to us, stop polling
        if (this.isMyTurn && prevPlayer !== this.role) {
          this._stopOpponentPoll();

          events.emit(Events.TURN_SWITCH, {
            turn: this.gameState.currentTurn,
            player: this.gameState.currentPlayer,
            isMyTurn: true,
          });
          events.emit(Events.TURN_START, {
            turn: this.gameState.currentTurn,
            player: this.gameState.currentPlayer,
            isMyTurn: true,
          });
        }
      } catch (err) {
        console.error('[TurnController] Poll failed:', err);
      }
    }, 1500);
  }

  _stopOpponentPoll() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  }

  /**
   * Apply a backend game state snapshot to our local state.
   */
  _applyState(state) {
    if (!state) return;

    const prevAlert = this.gameState.alertLevel;

    Object.assign(this.gameState, {
      currentTurn:           state.current_turn ?? this.gameState.currentTurn,
      maxTurns:              state.max_turns ?? this.gameState.maxTurns,
      currentPlayer:         state.current_player ?? this.gameState.currentPlayer,
      actionPointsRemaining: state.action_points_remaining ?? this.gameState.actionPointsRemaining,
      alertLevel:            state.alert_level ?? this.gameState.alertLevel,
      stealthLevel:          state.stealth_level ?? this.gameState.stealthLevel,
      nodes:                 state.nodes ?? this.gameState.nodes,
      connections:           state.connections ?? this.gameState.connections,
      discoveredNodes:       state.discovered_nodes ?? this.gameState.discoveredNodes,
      compromisedNodes:      state.compromised_nodes ?? this.gameState.compromisedNodes,
      detectedNodes:         state.detected_nodes ?? this.gameState.detectedNodes,
      resources:             state.resources ?? this.gameState.resources,
      objectives:            state.objectives ?? this.gameState.objectives,
      gameOver:              state.game_over ?? false,
      winner:                state.winner ?? null,
    });

    // Emit state update
    events.emit(Events.GAME_STATE, { ...this.gameState, role: this.role });
    this._emitStateUpdate();

    // Emit alert change if it changed
    if (this.gameState.alertLevel !== prevAlert) {
      events.emit(Events.ALERT_CHANGE, {
        level: this.gameState.alertLevel,
        previous: prevAlert,
      });
    }
  }

  _handleGameOver() {
    this._stopOpponentPoll();
    events.emit(Events.GAME_OVER, {
      winner: this.gameState.winner,
      role: this.role,
      isWin: this.gameState.winner === this.role,
      gameState: this.gameState,
    });
  }

  /**
   * Clean up for a fresh game.
   */
  destroy() {
    this._stopOpponentPoll();
    this.sessionId = null;
    this.gameState.gameOver = false;
  }
}
