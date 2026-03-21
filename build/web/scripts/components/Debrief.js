/**
 * Neo-Hack: Gridlock v3.2 — Mission Debrief Overlay
 * Styled as "Incident Report" showing results, XP, and key moments.
 */

import { events, Events } from '../game-events.js';

export class Debrief {
  constructor() {
    this.el = document.createElement('div');
    this.el.id = 'debrief-overlay';
    this.el.className = 'debrief-overlay';
    this.el.style.display = 'none';
    document.body.appendChild(this.el);
  }

  /**
   * Show debrief overlay.
   * @param {object} data - { winner, role, isWin, gameState }
   * @returns {Promise<string>} Resolves with 'menu' or 'replay'
   */
  show({ winner, role, isWin, gameState }) {
    const title = isWin ? 'MISSION ACCOMPLISHED' : 'MISSION FAILED';
    const titleClass = isWin ? 'debrief--win' : 'debrief--loss';
    const roleLabel = role === 'attacker' ? '🔴 ATTACKER' : '🔵 DEFENDER';
    const winnerLabel = winner === 'attacker' ? '🔴 ATTACKER' : '🔵 DEFENDER';

    const turns = gameState.currentTurn || 0;
    const maxTurns = gameState.maxTurns || 20;
    const compromised = (gameState.compromisedNodes || []).length;
    const totalNodes = (gameState.nodes || []).length;
    const alertLevel = gameState.alertLevel || 0;

    // Calculate XP
    const baseXp = isWin ? 150 : 50;
    const turnBonus = isWin ? Math.max(0, (maxTurns - turns) * 5) : 0;
    const nodeBonus = role === 'attacker' ? compromised * 10 : (totalNodes - compromised) * 8;
    const stealthBonus = role === 'attacker' && alertLevel < 30 ? 50 : 0;
    const totalXp = baseXp + turnBonus + nodeBonus + stealthBonus;

    // Objectives completion
    const objectives = gameState.objectives || { attacker: [], defender: [] };
    const myObjectives = objectives[role] || [];
    const completed = myObjectives.filter(o => o.completed).length;

    this.el.innerHTML = `
      <div class="debrief-overlay__content ${titleClass}">
        <div class="debrief-overlay__header">
          <div class="debrief-overlay__report-id">INCIDENT REPORT #${Date.now().toString(36).toUpperCase()}</div>
          <h1 class="debrief-overlay__title">${title}</h1>
          <div class="debrief-overlay__subtitle">Winner: ${winnerLabel}</div>
        </div>

        <div class="debrief-overlay__body">
          <div class="debrief-overlay__stats">
            <div class="debrief-stat">
              <span class="debrief-stat__label">YOUR ROLE</span>
              <span class="debrief-stat__value">${roleLabel}</span>
            </div>
            <div class="debrief-stat">
              <span class="debrief-stat__label">TURNS PLAYED</span>
              <span class="debrief-stat__value">${turns} / ${maxTurns}</span>
            </div>
            <div class="debrief-stat">
              <span class="debrief-stat__label">NODES COMPROMISED</span>
              <span class="debrief-stat__value">${compromised} / ${totalNodes}</span>
            </div>
            <div class="debrief-stat">
              <span class="debrief-stat__label">FINAL ALERT LEVEL</span>
              <span class="debrief-stat__value">${alertLevel}%</span>
            </div>
            <div class="debrief-stat">
              <span class="debrief-stat__label">OBJECTIVES</span>
              <span class="debrief-stat__value">${completed} / ${myObjectives.length}</span>
            </div>
          </div>

          <div class="debrief-overlay__xp">
            <h3>EXPERIENCE GAINED</h3>
            <div class="debrief-xp__breakdown">
              <div>Base: <span>+${baseXp}</span></div>
              ${turnBonus > 0 ? `<div>Speed Bonus: <span>+${turnBonus}</span></div>` : ''}
              <div>Node Bonus: <span>+${nodeBonus}</span></div>
              ${stealthBonus > 0 ? `<div>Stealth Bonus: <span>+${stealthBonus}</span></div>` : ''}
              <div class="debrief-xp__total">TOTAL: <span>+${totalXp} XP</span></div>
            </div>
          </div>
        </div>

        <div class="debrief-overlay__footer">
          <button class="btn btn-primary" id="btn-debrief-replay">PLAY AGAIN</button>
          <button class="btn" id="btn-debrief-menu">RETURN TO BASE</button>
        </div>
      </div>
    `;

    this.el.style.display = 'flex';

    return new Promise((resolve) => {
      this.el.querySelector('#btn-debrief-replay').addEventListener('click', () => {
        this.hide();
        resolve('replay');
      });
      this.el.querySelector('#btn-debrief-menu').addEventListener('click', () => {
        this.hide();
        resolve('menu');
      });
    });
  }

  hide() {
    this.el.style.display = 'none';
  }

  destroy() {
    this.el.remove();
  }
}
