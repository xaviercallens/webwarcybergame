/**
 * TurnHUD component for Neo-Hack v3.2.
 * Displays turn counter, current player, AP, resources, alert/stealth, end turn button.
 * Wired into event bus for live game state.
 */

import { events, Events } from '../game-events.js';

export class TurnHUD {
  constructor(container) {
    this.container = container;
    this.el = document.createElement('div');
    this.el.id = 'turn-hud';
    this.el.className = 'turn-hud';
    this.el.setAttribute('role', 'status');
    this.el.setAttribute('aria-label', 'Game status');
    this.container.appendChild(this.el);

    this._gameState = null;
    this._role = null;

    this._bindEvents();
  }

  _bindEvents() {
    events.on(Events.GAME_STATE, (state) => {
      this._gameState = state;
      this._role = state.role || this._role;
      this.render(state);
    });

    events.on(Events.GAME_START, ({ role, gameState }) => {
      this._role = role;
      if (gameState) {
        this._gameState = gameState;
        this.render(gameState);
      }
    });

    // End turn via Space hotkey
    events.on(Events.HOTKEY, ({ action }) => {
      if (action === 'confirm' && this._gameState && this._gameState.currentPlayer === this._role) {
        events.emit(Events.TURN_END, { role: this._role });
      }
    });
  }

  render(gameState) {
    if (!gameState) return;
    const gs = { ...gameState, role: this._role || gameState.role };

    const isAttacker = gs.currentPlayer === 'attacker';
    const playerClass = isAttacker ? 'attacker' : 'defender';
    const playerIcon = isAttacker ? '\u{1F534}' : '\u{1F535}';
    const playerLabel = isAttacker ? 'ATTACKER TURN' : 'DEFENDER TURN';
    const isMyTurn = gs.currentPlayer === gs.role;
    const turnsLeft = (gs.maxTurns || 20) - (gs.currentTurn || 0);
    const urgentClass = turnsLeft <= 3 ? 'turn-hud__value--urgent' : '';

    const resources = gs.resources || {};

    this.el.innerHTML = `
      <div class="turn-hud__row">
        <div class="turn-hud__turn-counter">
          <span class="turn-hud__label">TURN</span>
          <span class="turn-hud__value ${urgentClass}">${gs.currentTurn || 0} / ${gs.maxTurns || 20}</span>
        </div>

        <div class="turn-hud__player-indicator ${playerClass}">
          <span class="turn-hud__player-icon">${playerIcon}</span>
          <span class="turn-hud__player-name">${playerLabel}</span>
        </div>

        <div class="turn-hud__action-points">
          <span class="turn-hud__label">AP</span>
          <span class="turn-hud__value">${gs.actionPointsRemaining ?? 1}</span>
        </div>

        ${gs.role === 'attacker' && gs.stealthLevel != null ? `
        <div class="turn-hud__stealth">
          <span class="turn-hud__label">STEALTH</span>
          <span class="turn-hud__value" style="color: ${this._stealthColor(gs.stealthLevel)}">${gs.stealthLevel}%</span>
        </div>
        ` : ''}

        ${resources.exploitKits != null ? `
        <div class="turn-hud__resource">
          <span class="turn-hud__label">EXPLOITS</span>
          <span class="turn-hud__value">${resources.exploitKits}</span>
        </div>
        ` : ''}

        ${resources.irBudget != null ? `
        <div class="turn-hud__resource">
          <span class="turn-hud__label">IR BUDGET</span>
          <span class="turn-hud__value">${resources.irBudget}</span>
        </div>
        ` : ''}

        ${isMyTurn ? `
        <button class="btn btn-primary turn-hud__end-turn" id="btn-end-turn" style="pointer-events:auto;padding:0.3rem 1rem;font-size:0.75rem;">
          END TURN [Space]
        </button>
        ` : ''}
      </div>

      ${gs.role === 'defender' ? `
      <div class="turn-hud__alert-bar">
        <span class="turn-hud__label">ALERT</span>
        <div class="alert-meter">
          <div class="alert-meter__fill" style="width: ${gs.alertLevel || 0}%; background: ${this._alertColor(gs.alertLevel || 0)};"></div>
        </div>
        <span class="alert-meter__value">${gs.alertLevel || 0}%</span>
      </div>
      ` : ''}
    `;

    // Bind end turn button
    const endTurnBtn = this.el.querySelector('#btn-end-turn');
    if (endTurnBtn) {
      endTurnBtn.addEventListener('click', () => {
        events.emit(Events.TURN_END, { role: this._role });
      });
    }
  }

  _alertColor(level) {
    if (level < 30) return 'var(--color-player, #00ffdd)';
    if (level < 70) return 'var(--color-warning, #ffcc00)';
    return 'var(--color-enemy, #ff0055)';
  }

  _stealthColor(level) {
    if (level > 70) return '#00ffdd';
    if (level > 30) return '#ffcc00';
    return '#ff0055';
  }

  destroy() {
    this.el.remove();
  }
}
