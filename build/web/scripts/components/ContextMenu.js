/**
 * Neo-Hack: Gridlock v3.2 — Right-Click Context Menu
 * Shows available actions at cursor position when right-clicking a node.
 */

import { events, Events } from '../game-events.js';
import { ATTACKER_ACTIONS, DEFENDER_ACTIONS } from './ActionMenu.js';

export class ContextMenu {
  constructor() {
    this.el = document.createElement('div');
    this.el.id = 'context-menu';
    this.el.className = 'context-menu';
    this.el.setAttribute('role', 'menu');
    this.el.style.display = 'none';
    document.body.appendChild(this.el);

    this._role = null;
    this._targetNode = null;

    events.on(Events.GAME_START, ({ role }) => { this._role = role; });

    // Close on click outside or Escape
    document.addEventListener('click', (e) => {
      if (!this.el.contains(e.target)) this.hide();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.hide();
    });
  }

  /**
   * Show context menu at coordinates for a given node.
   * @param {object} node
   * @param {number} x - clientX
   * @param {number} y - clientY
   * @param {object} gameState - current game state for filtering
   */
  show(node, x, y, gameState) {
    if (!node || !this._role) return;
    this._targetNode = node;

    const actions = this._role === 'attacker' ? ATTACKER_ACTIONS : DEFENDER_ACTIONS;
    const isMyTurn = gameState && gameState.currentPlayer === this._role;

    this.el.innerHTML = `
      <div class="context-menu__header">${node.name || 'Node ' + node.id}</div>
      <div class="context-menu__list">
        ${actions.map((a, i) => `
          <button class="context-menu__item" data-action-id="${a.id}"
                  role="menuitem" ${!isMyTurn ? 'disabled' : ''}>
            <span class="context-menu__icon">${a.icon}</span>
            <span class="context-menu__name">${a.name.replace(/_/g, ' ')}</span>
            <span class="context-menu__hotkey">[${i + 1}]</span>
          </button>
        `).join('')}
      </div>
    `;

    this._position(x, y);
    this.el.style.display = 'block';

    // Bind clicks
    this.el.querySelectorAll('.context-menu__item').forEach(btn => {
      btn.addEventListener('click', () => {
        const actionId = parseInt(btn.dataset.actionId, 10);
        const action = actions.find(a => a.id === actionId);
        if (action) {
          events.emit(Events.ACTION_EXECUTE, {
            actionId: action.id,
            actionName: action.name,
            targetNode: this._targetNode.id,
          });
        }
        this.hide();
      });
    });
  }

  hide() {
    this.el.style.display = 'none';
    this._targetNode = null;
  }

  _position(x, y) {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const menuW = 240;
    const menuH = 350;

    let left = x;
    let top = y;

    if (left + menuW > vw) left = vw - menuW - 8;
    if (top + menuH > vh) top = vh - menuH - 8;

    this.el.style.left = `${Math.max(0, left)}px`;
    this.el.style.top = `${Math.max(0, top)}px`;
  }

  destroy() {
    this.el.remove();
  }
}
