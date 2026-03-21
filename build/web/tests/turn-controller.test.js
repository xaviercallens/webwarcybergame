/**
 * Unit tests for TurnController
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { TurnController } from '../scripts/turn-controller.js';
import { events, Events } from '../scripts/game-events.js';
import { api } from '../scripts/api-client.js';

// Mock the API client
vi.mock('../scripts/api-client.js', () => ({
  api: {
    createGameSession: vi.fn(),
    submitTurnAction: vi.fn(),
    endTurn: vi.fn(),
    getGameState: vi.fn(),
  }
}));

const MOCK_GAME_STATE = {
  current_turn: 1,
  max_turns: 20,
  current_player: 'attacker',
  action_points_remaining: 2,
  alert_level: 10,
  stealth_level: 90,
  nodes: [{ id: 1, name: 'gateway' }, { id: 2, name: 'db' }],
  connections: [{ source: 1, target: 2 }],
  discovered_nodes: [1],
  compromised_nodes: [],
  detected_nodes: [],
  resources: { exploitKits: 3 },
  objectives: { attacker: [], defender: [] },
  game_over: false,
  winner: null,
};

describe('TurnController', () => {
  let tc;

  beforeEach(() => {
    events.clear();
    vi.clearAllMocks();
    vi.useFakeTimers();
    tc = new TurnController();
  });

  afterEach(() => {
    tc.destroy();
    vi.useRealTimers();
  });

  describe('startGame', () => {
    it('should create session and emit GAME_START', async () => {
      api.createGameSession.mockResolvedValue({
        session_id: 'test-session-1',
        game_state: MOCK_GAME_STATE,
      });

      const gameStartHandler = vi.fn();
      const turnStartHandler = vi.fn();
      events.on(Events.GAME_START, gameStartHandler);
      events.on(Events.TURN_START, turnStartHandler);

      await tc.startGame({ role: 'attacker', difficulty: 'normal', scenario: 'default' });

      expect(api.createGameSession).toHaveBeenCalledWith({
        role: 'attacker',
        difficulty: 'normal',
        scenario: 'default',
      });
      expect(tc.sessionId).toBe('test-session-1');
      expect(tc.role).toBe('attacker');
      expect(gameStartHandler).toHaveBeenCalled();
      expect(turnStartHandler).toHaveBeenCalled();
    });

    it('should emit toast on failure', async () => {
      api.createGameSession.mockRejectedValue(new Error('Connection refused'));

      const toastHandler = vi.fn();
      events.on(Events.TOAST_SHOW, toastHandler);

      await tc.startGame({ role: 'attacker' });

      expect(toastHandler).toHaveBeenCalledWith(expect.objectContaining({ type: 'error' }));
    });

    it('should start polling if AI goes first', async () => {
      const defenderFirst = { ...MOCK_GAME_STATE, current_player: 'defender' };
      api.createGameSession.mockResolvedValue({
        session_id: 'sess-2',
        game_state: defenderFirst,
      });

      await tc.startGame({ role: 'attacker' });

      expect(tc._pollTimer).not.toBeNull();
    });
  });

  describe('onPlayerAction', () => {
    beforeEach(async () => {
      api.createGameSession.mockResolvedValue({
        session_id: 'sess-action',
        game_state: MOCK_GAME_STATE,
      });
      await tc.startGame({ role: 'attacker' });
    });

    it('should submit action and emit ACTION_RESULT', async () => {
      api.submitTurnAction.mockResolvedValue({
        success: true,
        detected: false,
        message: 'Scan complete',
        game_state: { ...MOCK_GAME_STATE, discovered_nodes: [1, 2] },
      });

      const resultHandler = vi.fn();
      events.on(Events.ACTION_RESULT, resultHandler);

      await tc.onPlayerAction({
        actionId: 0,
        actionName: 'SCAN_NETWORK',
        targetNode: 1,
      });

      expect(api.submitTurnAction).toHaveBeenCalledWith(expect.objectContaining({
        session_id: 'sess-action',
        player_role: 'attacker',
        action_type: 'SCAN_NETWORK',
        target_node: 1,
      }));
      expect(resultHandler).toHaveBeenCalledWith(expect.objectContaining({
        success: true,
        actionName: 'SCAN_NETWORK',
      }));
    });

    it('should reject action when not my turn', async () => {
      // Force opponent turn
      tc.gameState.currentPlayer = 'defender';

      const toastHandler = vi.fn();
      events.on(Events.TOAST_SHOW, toastHandler);

      await tc.onPlayerAction({ actionId: 0, actionName: 'SCAN', targetNode: 1 });

      expect(toastHandler).toHaveBeenCalledWith(expect.objectContaining({
        message: 'Not your turn!',
      }));
      expect(api.submitTurnAction).not.toHaveBeenCalled();
    });

    it('should handle game over after action', async () => {
      api.submitTurnAction.mockResolvedValue({
        success: true,
        detected: false,
        message: 'Victory!',
        game_state: { ...MOCK_GAME_STATE, game_over: true, winner: 'attacker' },
      });

      const gameOverHandler = vi.fn();
      events.on(Events.GAME_OVER, gameOverHandler);

      await tc.onPlayerAction({ actionId: 0, actionName: 'SCAN', targetNode: 1 });

      expect(gameOverHandler).toHaveBeenCalledWith(expect.objectContaining({
        winner: 'attacker',
        isWin: true,
      }));
    });

    it('should emit TURN_SWITCH when player changes', async () => {
      api.submitTurnAction.mockResolvedValue({
        success: true,
        detected: false,
        message: 'Done',
        game_state: { ...MOCK_GAME_STATE, current_player: 'defender' },
      });

      const switchHandler = vi.fn();
      events.on(Events.TURN_SWITCH, switchHandler);

      await tc.onPlayerAction({ actionId: 0, actionName: 'SCAN', targetNode: 1 });

      expect(switchHandler).toHaveBeenCalledWith(expect.objectContaining({
        isMyTurn: false,
      }));
    });
  });

  describe('endTurn', () => {
    beforeEach(async () => {
      api.createGameSession.mockResolvedValue({
        session_id: 'sess-end',
        game_state: MOCK_GAME_STATE,
      });
      await tc.startGame({ role: 'attacker' });
    });

    it('should call api.endTurn and emit TURN_SWITCH', async () => {
      api.endTurn.mockResolvedValue({
        game_state: { ...MOCK_GAME_STATE, current_player: 'defender', current_turn: 2 },
      });

      const switchHandler = vi.fn();
      events.on(Events.TURN_SWITCH, switchHandler);

      await tc.endTurn();

      expect(api.endTurn).toHaveBeenCalledWith({
        session_id: 'sess-end',
        player_role: 'attacker',
      });
      expect(switchHandler).toHaveBeenCalled();
    });

    it('should not end turn when not my turn', async () => {
      tc.gameState.currentPlayer = 'defender';
      await tc.endTurn();
      expect(api.endTurn).not.toHaveBeenCalled();
    });
  });

  describe('isMyTurn', () => {
    it('should return true when currentPlayer matches role', () => {
      tc.role = 'attacker';
      tc.gameState.currentPlayer = 'attacker';
      expect(tc.isMyTurn).toBe(true);
    });

    it('should return false when currentPlayer differs', () => {
      tc.role = 'attacker';
      tc.gameState.currentPlayer = 'defender';
      expect(tc.isMyTurn).toBe(false);
    });
  });

  describe('_applyState', () => {
    it('should emit ALERT_CHANGE when alert level changes', () => {
      tc.gameState.alertLevel = 10;
      const alertHandler = vi.fn();
      events.on(Events.ALERT_CHANGE, alertHandler);

      tc._applyState({ alert_level: 50 });

      expect(alertHandler).toHaveBeenCalledWith({ level: 50, previous: 10 });
    });

    it('should not emit ALERT_CHANGE when level unchanged', () => {
      tc.gameState.alertLevel = 10;
      const alertHandler = vi.fn();
      events.on(Events.ALERT_CHANGE, alertHandler);

      tc._applyState({ alert_level: 10 });

      expect(alertHandler).not.toHaveBeenCalled();
    });

    it('should emit GAME_STATE on every apply', () => {
      const stateHandler = vi.fn();
      events.on(Events.GAME_STATE, stateHandler);

      tc._applyState({ current_turn: 5 });

      expect(stateHandler).toHaveBeenCalled();
    });
  });

  describe('destroy', () => {
    it('should clear poll timer and session', async () => {
      api.createGameSession.mockResolvedValue({
        session_id: 'sess-destroy',
        game_state: { ...MOCK_GAME_STATE, current_player: 'defender' },
      });
      await tc.startGame({ role: 'attacker' });
      expect(tc._pollTimer).not.toBeNull();

      tc.destroy();
      expect(tc._pollTimer).toBeNull();
      expect(tc.sessionId).toBeNull();
    });
  });
});
