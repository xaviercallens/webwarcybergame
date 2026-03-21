/**
 * Neo-Hack: Gridlock v3.2 — Centralized Hotkey Manager
 * Remappable keyboard shortcuts. Suppressed when typing in inputs.
 */

import { events, Events } from './game-events.js';

const DEFAULT_BINDINGS = {
  'Tab':       { action: 'cycle_focus',     description: 'Cycle focus: map → action panel → log' },
  'Space':     { action: 'confirm',         description: 'Confirm action / End turn' },
  'Escape':    { action: 'cancel',          description: 'Cancel / Close panel / Pause menu' },
  'h':         { action: 'toggle_hints',    description: 'Toggle hint highlights' },
  'F1':        { action: 'help',            description: 'Open help overlay' },
  '`':         { action: 'toggle_console',  description: 'Toggle CLI console' },
  '/':         { action: 'toggle_console',  description: 'Toggle CLI console' },
  'l':         { action: 'toggle_log',      description: 'Toggle log panel' },
  'm':         { action: 'toggle_mission',  description: 'Toggle mission panel' },
  '1':         { action: 'action_1',        description: 'Action slot 1' },
  '2':         { action: 'action_2',        description: 'Action slot 2' },
  '3':         { action: 'action_3',        description: 'Action slot 3' },
  '4':         { action: 'action_4',        description: 'Action slot 4' },
  '5':         { action: 'action_5',        description: 'Action slot 5' },
  '6':         { action: 'action_6',        description: 'Action slot 6' },
  '7':         { action: 'action_7',        description: 'Action slot 7' },
  'ArrowUp':   { action: 'nav_up',          description: 'Navigate node up' },
  'ArrowDown': { action: 'nav_down',        description: 'Navigate node down' },
  'ArrowLeft': { action: 'nav_left',        description: 'Navigate node left' },
  'ArrowRight':{ action: 'nav_right',       description: 'Navigate node right' },
  'w':         { action: 'nav_up',          description: 'Navigate node up (WASD)' },
  's':         { action: 'nav_down',        description: 'Navigate node down (WASD)' },
  'a':         { action: 'nav_left',        description: 'Navigate node left (WASD)' },
  'd':         { action: 'nav_right',       description: 'Navigate node right (WASD)' },
  '+':         { action: 'zoom_in',         description: 'Zoom in' },
  '-':         { action: 'zoom_out',        description: 'Zoom out' },
  '=':         { action: 'zoom_in',         description: 'Zoom in' },
};

export class HotkeyManager {
  constructor() {
    this._bindings = { ...DEFAULT_BINDINGS };
    this._enabled = true;
    this._activeView = 'menu';

    this._onKeyDown = this._onKeyDown.bind(this);
    document.addEventListener('keydown', this._onKeyDown);

    events.on(Events.VIEW_CHANGE, ({ to }) => { this._activeView = to; });
  }

  /** Enable or disable all hotkeys. */
  setEnabled(enabled) {
    this._enabled = enabled;
  }

  /**
   * Rebind a key to a different action.
   * @param {string} key - The key string (e.g. 'Tab', 'h')
   * @param {string} action - Action name
   */
  rebind(key, action) {
    const desc = this._bindings[key]?.description || action;
    this._bindings[key] = { action, description: desc };
  }

  /** Get current binding map (for settings UI / help display). */
  getBindings() {
    return { ...this._bindings };
  }

  /** Reset to defaults. */
  resetBindings() {
    this._bindings = { ...DEFAULT_BINDINGS };
  }

  /**
   * Save bindings to localStorage.
   */
  save() {
    try {
      const data = {};
      for (const [key, val] of Object.entries(this._bindings)) {
        data[key] = val.action;
      }
      localStorage.setItem('nh_hotkeys', JSON.stringify(data));
    } catch (e) { /* ignore */ }
  }

  /**
   * Load bindings from localStorage.
   */
  load() {
    try {
      const raw = localStorage.getItem('nh_hotkeys');
      if (!raw) return;
      const data = JSON.parse(raw);
      for (const [key, action] of Object.entries(data)) {
        if (this._bindings[key]) {
          this._bindings[key].action = action;
        } else {
          this._bindings[key] = { action, description: action };
        }
      }
    } catch (e) { /* ignore */ }
  }

  _onKeyDown(e) {
    if (!this._enabled) return;

    // Suppress when typing in input/textarea
    const tag = document.activeElement?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
      // Allow Escape even in inputs
      if (e.key !== 'Escape') return;
    }

    // Only process game hotkeys when in game view (or certain global ones)
    const globalActions = ['cancel', 'help', 'toggle_console'];
    const binding = this._bindings[e.key];
    if (!binding) return;

    const isGameView = this._activeView === 'game' || this._activeView === 'pause';
    const isGlobal = globalActions.includes(binding.action);

    if (!isGameView && !isGlobal) return;

    // Prevent browser defaults for game keys
    if (['Tab', 'Space', 'F1', '/', 'Escape'].includes(e.key)) {
      e.preventDefault();
    }

    events.emit(Events.HOTKEY, {
      key: e.key,
      action: binding.action,
      originalEvent: e,
    });
  }

  destroy() {
    document.removeEventListener('keydown', this._onKeyDown);
  }
}
