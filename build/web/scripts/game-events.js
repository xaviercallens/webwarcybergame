/**
 * Neo-Hack: Gridlock v3.2 — Lightweight Event Bus
 * Decouples UI components via named events with typed payloads.
 */

class GameEventBus {
  constructor() {
    this._listeners = new Map();
  }

  /**
   * Subscribe to an event.
   * @param {string} event - Event name (e.g. 'node:select', 'turn:switch')
   * @param {Function} callback - Handler receiving the event payload
   * @returns {Function} Unsubscribe function
   */
  on(event, callback) {
    if (!this._listeners.has(event)) {
      this._listeners.set(event, new Set());
    }
    this._listeners.get(event).add(callback);
    return () => this.off(event, callback);
  }

  /**
   * Subscribe to an event once.
   * @param {string} event
   * @param {Function} callback
   */
  once(event, callback) {
    const wrapper = (payload) => {
      this.off(event, wrapper);
      callback(payload);
    };
    this.on(event, wrapper);
  }

  /**
   * Unsubscribe from an event.
   * @param {string} event
   * @param {Function} callback
   */
  off(event, callback) {
    const set = this._listeners.get(event);
    if (set) {
      set.delete(callback);
      if (set.size === 0) this._listeners.delete(event);
    }
  }

  /**
   * Emit an event to all subscribers.
   * @param {string} event
   * @param {*} payload
   */
  emit(event, payload) {
    const set = this._listeners.get(event);
    if (set) {
      for (const cb of set) {
        try {
          cb(payload);
        } catch (err) {
          console.error(`[EventBus] Error in handler for '${event}':`, err);
        }
      }
    }
  }

  /**
   * Remove all listeners for a given event, or all listeners entirely.
   * @param {string} [event]
   */
  clear(event) {
    if (event) {
      this._listeners.delete(event);
    } else {
      this._listeners.clear();
    }
  }

  /** Debug: list all registered events and their listener counts. */
  debug() {
    const info = {};
    for (const [event, set] of this._listeners) {
      info[event] = set.size;
    }
    return info;
  }
}

// Event name constants
export const Events = {
  // Node events
  NODE_SELECT:    'node:select',
  NODE_DESELECT:  'node:deselect',
  NODE_HOVER:     'node:hover',
  NODE_HOVER_END: 'node:hover_end',

  // Action events
  ACTION_EXECUTE:  'action:execute',
  ACTION_RESULT:   'action:result',
  ACTION_PREVIEW:  'action:preview',

  // Turn events
  TURN_SWITCH:     'turn:switch',
  TURN_START:      'turn:start',
  TURN_END:        'turn:end',

  // Game lifecycle
  GAME_CREATE:     'game:create',
  GAME_START:      'game:start',
  GAME_OVER:       'game:over',
  GAME_STATE:      'game:state',
  GAME_STATE_UPDATE: 'game:state:update',

  // Alert / stealth
  ALERT_CHANGE:    'alert:change',
  STEALTH_CHANGE:  'stealth:change',

  // Log / notifications
  LOG_ADD:         'log:add',
  TOAST_SHOW:      'toast:show',

  // UI / view
  VIEW_CHANGE:     'view:change',
  CONSOLE_TOGGLE:  'console:toggle',
  PANEL_TOGGLE:    'panel:toggle',

  // Input
  HOTKEY:          'hotkey:press',
};

// Singleton
export const events = new GameEventBus();
