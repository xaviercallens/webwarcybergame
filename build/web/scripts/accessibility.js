/**
 * Neo-Hack: Gridlock v3.2 — Accessibility Manager
 * ARIA roles, focus management, screen reader announcements, colorblind modes, reduced motion.
 */

import { events, Events } from './game-events.js';

export class AccessibilityManager {
  constructor() {
    // Live region for screen reader announcements
    this._liveRegion = document.createElement('div');
    this._liveRegion.id = 'a11y-live';
    this._liveRegion.setAttribute('role', 'status');
    this._liveRegion.setAttribute('aria-live', 'polite');
    this._liveRegion.setAttribute('aria-atomic', 'true');
    this._liveRegion.className = 'sr-only';
    document.body.appendChild(this._liveRegion);

    // Assertive region for urgent announcements
    this._alertRegion = document.createElement('div');
    this._alertRegion.id = 'a11y-alert';
    this._alertRegion.setAttribute('role', 'alert');
    this._alertRegion.setAttribute('aria-live', 'assertive');
    this._alertRegion.setAttribute('aria-atomic', 'true');
    this._alertRegion.className = 'sr-only';
    document.body.appendChild(this._alertRegion);

    this._focusTrapStack = [];
    this._uiScale = parseFloat(localStorage.getItem('nh_ui_scale') || '1');

    this._init();
    this._bindEvents();
  }

  _init() {
    // Set ARIA roles on main containers
    const app = document.getElementById('app');
    if (app) app.setAttribute('role', 'application');

    // Apply saved preferences
    this.applyUIScale(this._uiScale);
    this._applyReducedMotion();
    this._applyHighContrast();
  }

  _bindEvents() {
    events.on(Events.ACTION_RESULT, ({ actionName, success, detected, message }) => {
      const text = message || `${(actionName || '').replace(/_/g, ' ')} ${success ? 'succeeded' : 'failed'}`;
      this.announce(text);
      if (detected) {
        this.announceUrgent('Alert: suspicious activity detected by defender!');
      }
    });

    events.on(Events.TURN_SWITCH, ({ player, isMyTurn }) => {
      const msg = isMyTurn ? `Your turn. You are the ${player}.` : `Waiting for ${player}'s move.`;
      this.announce(msg);
    });

    events.on(Events.ALERT_CHANGE, ({ level }) => {
      if (level >= 70) {
        this.announceUrgent(`Alert level critical: ${level}%`);
      }
    });

    events.on(Events.GAME_OVER, ({ isWin, winner }) => {
      const msg = isWin ? 'Mission accomplished. You win!' : `Mission failed. ${winner} wins.`;
      this.announceUrgent(msg);
    });

    // Detect prefers-reduced-motion changes
    const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
    mql.addEventListener('change', () => this._applyReducedMotion());
  }

  /**
   * Announce text to screen readers (polite).
   */
  announce(text) {
    this._liveRegion.textContent = '';
    // Force re-announcement
    requestAnimationFrame(() => {
      this._liveRegion.textContent = text;
    });
  }

  /**
   * Announce urgent text to screen readers (assertive).
   */
  announceUrgent(text) {
    this._alertRegion.textContent = '';
    requestAnimationFrame(() => {
      this._alertRegion.textContent = text;
    });
  }

  /**
   * Trap focus within a container (for modals/dialogs).
   * @param {HTMLElement} container
   */
  trapFocus(container) {
    if (!container) return;

    const focusable = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    const handler = (e) => {
      if (e.key !== 'Tab') return;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };

    container.addEventListener('keydown', handler);
    this._focusTrapStack.push({ container, handler });

    // Focus first element
    first?.focus();
  }

  /**
   * Release focus trap on the most recent container.
   */
  releaseFocus() {
    const trap = this._focusTrapStack.pop();
    if (trap) {
      trap.container.removeEventListener('keydown', trap.handler);
    }
  }

  /**
   * Set and apply UI scale.
   * @param {number} scale - 0.8 to 1.5
   */
  applyUIScale(scale) {
    this._uiScale = Math.max(0.8, Math.min(1.5, scale));
    document.documentElement.style.setProperty('--ui-scale', this._uiScale);
    const gameUI = document.querySelector('.game-ui');
    if (gameUI) {
      gameUI.style.transform = `scale(${this._uiScale})`;
      gameUI.style.transformOrigin = 'top left';
    }
    localStorage.setItem('nh_ui_scale', String(this._uiScale));
  }

  get uiScale() { return this._uiScale; }

  _applyReducedMotion() {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.documentElement.setAttribute('data-reduced-motion', reduced ? 'true' : 'false');
  }

  _applyHighContrast() {
    const hc = localStorage.getItem('nh_high_contrast') === 'true';
    document.documentElement.setAttribute('data-high-contrast', hc ? 'true' : 'false');
  }

  setHighContrast(enabled) {
    localStorage.setItem('nh_high_contrast', enabled ? 'true' : 'false');
    this._applyHighContrast();
  }

  destroy() {
    this._liveRegion.remove();
    this._alertRegion.remove();
    while (this._focusTrapStack.length) this.releaseFocus();
  }
}
