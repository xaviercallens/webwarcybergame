/**
 * Neo-Hack: Gridlock v3.2 — Toast Notification Component
 * Brief floating messages for action results; auto-dismiss, stacks up to 3.
 */

import { events, Events } from '../game-events.js';

const TOAST_TYPES = {
  success: { icon: '✓', class: 'toast--success' },
  error:   { icon: '✗', class: 'toast--error' },
  warning: { icon: '⚠', class: 'toast--warning' },
  info:    { icon: 'ℹ', class: 'toast--info' },
  capture: { icon: '⚡', class: 'toast--capture' },
};

const MAX_VISIBLE = 3;
const DISMISS_MS = 3000;

export class ToastManager {
  constructor() {
    this.container = document.createElement('div');
    this.container.id = 'toast-manager';
    this.container.className = 'toast-manager';
    this.container.setAttribute('aria-live', 'polite');
    this.container.setAttribute('aria-atomic', 'false');
    document.body.appendChild(this.container);

    this._toasts = [];

    events.on(Events.TOAST_SHOW, (data) => this.show(data));
    events.on(Events.ACTION_RESULT, (data) => this._onActionResult(data));
  }

  /**
   * Show a toast notification.
   * @param {object} opts - { message, type }
   */
  show({ message, type = 'info' }) {
    const cfg = TOAST_TYPES[type] || TOAST_TYPES.info;

    const el = document.createElement('div');
    el.className = `toast ${cfg.class}`;
    el.setAttribute('role', 'status');
    el.innerHTML = `
      <span class="toast__icon">${cfg.icon}</span>
      <span class="toast__message">${message}</span>
    `;

    this.container.appendChild(el);
    this._toasts.push(el);

    // Force reflow for animation
    void el.offsetHeight;
    el.classList.add('toast--visible');

    // Remove excess
    while (this._toasts.length > MAX_VISIBLE) {
      this._remove(this._toasts[0]);
    }

    // Auto-dismiss
    setTimeout(() => this._remove(el), DISMISS_MS);
  }

  _remove(el) {
    if (!el || !el.parentNode) return;
    el.classList.remove('toast--visible');
    el.classList.add('toast--exiting');
    setTimeout(() => {
      if (el.parentNode) el.parentNode.removeChild(el);
      const idx = this._toasts.indexOf(el);
      if (idx !== -1) this._toasts.splice(idx, 1);
    }, 300);
  }

  _onActionResult({ actionName, success, detected, message }) {
    const displayName = (actionName || '').replace(/_/g, ' ');
    if (success) {
      this.show({ message: message || `${displayName} succeeded`, type: 'success' });
    } else {
      this.show({ message: message || `${displayName} failed`, type: 'error' });
    }

    if (detected) {
      this.show({ message: '⚠ ALERT: Activity detected!', type: 'warning' });
    }
  }

  destroy() {
    this.container.remove();
  }
}
