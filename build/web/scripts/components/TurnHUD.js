/**
 * TurnHUD component for Neo-Hack v3.1.
 * Displays turn counter, current player indicator, action points, and alert meter.
 * Blueprint Alignment: Day 4, Section 2 (User Experience)
 */

export class TurnHUD {
  constructor(container) {
    this.container = container;
    this.el = document.createElement('div');
    this.el.id = 'turn-hud';
    this.el.className = 'turn-hud';
    this.container.appendChild(this.el);
  }

  render(gameState) {
    const isAttacker = gameState.currentPlayer === 'attacker';
    const playerClass = isAttacker ? 'attacker' : 'defender';
    const playerIcon = isAttacker ? '\u{1F534}' : '\u{1F535}';
    const playerLabel = isAttacker ? 'ATTACKER TURN' : 'DEFENDER TURN';

    this.el.innerHTML = `
      <div class="turn-hud__row">
        <div class="turn-hud__turn-counter">
          <span class="turn-hud__label">TURN</span>
          <span class="turn-hud__value">${gameState.currentTurn} / ${gameState.maxTurns}</span>
        </div>

        <div class="turn-hud__player-indicator ${playerClass}">
          <span class="turn-hud__player-icon">${playerIcon}</span>
          <span class="turn-hud__player-name">${playerLabel}</span>
        </div>

        <div class="turn-hud__action-points">
          <span class="turn-hud__label">AP</span>
          <span class="turn-hud__value">${gameState.actionPointsRemaining || 1}</span>
        </div>
      </div>

      ${gameState.role === 'defender' ? `
      <div class="turn-hud__alert-bar">
        <span class="turn-hud__label">ALERT</span>
        <div class="alert-meter">
          <div class="alert-meter__fill" style="width: ${gameState.alertLevel}%; background: ${this._alertColor(gameState.alertLevel)};"></div>
        </div>
        <span class="alert-meter__value">${gameState.alertLevel}%</span>
      </div>
      ` : ''}
    `;
  }

  _alertColor(level) {
    if (level < 30) return 'var(--color-player, #00ffdd)';
    if (level < 70) return 'var(--color-warning, #ffcc00)';
    return 'var(--color-enemy, #ff0055)';
  }

  destroy() {
    this.el.remove();
  }
}
