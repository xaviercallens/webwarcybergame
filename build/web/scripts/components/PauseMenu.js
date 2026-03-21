/**
 * Neo-Hack: Gridlock v3.2 — Pause Menu
 * Overlay with Resume / Settings / Help / Quit. Keyboard & controller navigable.
 */

import { events, Events } from '../game-events.js';

export class PauseMenu {
  constructor() {
    this.el = document.createElement('div');
    this.el.id = 'pause-menu';
    this.el.className = 'pause-menu';
    this.el.setAttribute('role', 'dialog');
    this.el.setAttribute('aria-label', 'Pause Menu');
    this.el.style.display = 'none';
    document.body.appendChild(this.el);

    this._isOpen = false;
    this._focusIndex = 0;
    this._buttons = [];
    this._onAction = null;

    this._render();
  }

  get isOpen() { return this._isOpen; }

  /**
   * Show pause menu.
   * @returns {Promise<string>} Resolves with action: 'resume', 'settings', 'help', 'quit'
   */
  show() {
    this._isOpen = true;
    this.el.style.display = 'flex';
    this._focusIndex = 0;
    this._updateFocus();

    return new Promise((resolve) => {
      this._onAction = (action) => {
        this._isOpen = false;
        this.el.style.display = 'none';
        resolve(action);
      };
    });
  }

  hide() {
    this._isOpen = false;
    this.el.style.display = 'none';
    if (this._onAction) {
      this._onAction('resume');
      this._onAction = null;
    }
  }

  _render() {
    this.el.innerHTML = `
      <div class="pause-menu__backdrop"></div>
      <div class="pause-menu__panel">
        <h2 class="pause-menu__title">// SYSTEM PAUSED //</h2>
        <div class="pause-menu__buttons">
          <button class="btn btn-primary pause-menu__btn" data-action="resume">▶ RESUME</button>
          <button class="btn pause-menu__btn" data-action="settings">⚙ SETTINGS</button>
          <button class="btn pause-menu__btn" data-action="help">? HELP</button>
          <button class="btn btn-danger pause-menu__btn" data-action="quit">⏻ QUIT TO MENU</button>
        </div>
      </div>
    `;

    this._buttons = Array.from(this.el.querySelectorAll('.pause-menu__btn'));

    this._buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        if (this._onAction) this._onAction(btn.dataset.action);
      });
    });

    // Keyboard navigation within pause menu
    this.el.addEventListener('keydown', (e) => {
      if (!this._isOpen) return;

      if (e.key === 'ArrowDown' || e.key === 's') {
        e.preventDefault();
        this._focusIndex = Math.min(this._focusIndex + 1, this._buttons.length - 1);
        this._updateFocus();
      } else if (e.key === 'ArrowUp' || e.key === 'w') {
        e.preventDefault();
        this._focusIndex = Math.max(this._focusIndex - 1, 0);
        this._updateFocus();
      } else if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this._buttons[this._focusIndex]?.click();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        if (this._onAction) this._onAction('resume');
      }
    });
  }

  _updateFocus() {
    this._buttons.forEach((btn, i) => {
      btn.classList.toggle('pause-menu__btn--focused', i === this._focusIndex);
      if (i === this._focusIndex) btn.focus();
    });
  }

  destroy() {
    this.el.remove();
  }
}
