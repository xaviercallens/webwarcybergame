/**
 * Neo-Hack: Gridlock v3.2 — Gamepad Manager
 * Full controller support using the Gamepad API.
 * Maps D-pad/analog to node navigation, face buttons to actions, triggers to zoom.
 */

import { events, Events } from './game-events.js';

// Standard Gamepad button indices (Xbox layout)
const BTN = {
  A: 0, B: 1, X: 2, Y: 3,
  LB: 4, RB: 5, LT: 6, RT: 7,
  SELECT: 8, START: 9,
  L_STICK: 10, R_STICK: 11,
  DPAD_UP: 12, DPAD_DOWN: 13, DPAD_LEFT: 14, DPAD_RIGHT: 15,
};

const AXIS = { LEFT_X: 0, LEFT_Y: 1, RIGHT_X: 2, RIGHT_Y: 3 };

const DEAD_ZONE = 0.25;
const REPEAT_DELAY = 250; // ms between repeated nav from held stick

export class GamepadManager {
  constructor() {
    this._active = false;
    this._gamepadIndex = null;
    this._prevButtons = new Array(16).fill(false);
    this._lastNavTime = 0;
    this._rafId = null;
    this._connected = false;

    this._onConnect = this._onConnect.bind(this);
    this._onDisconnect = this._onDisconnect.bind(this);
    this._poll = this._poll.bind(this);

    window.addEventListener('gamepadconnected', this._onConnect);
    window.addEventListener('gamepaddisconnected', this._onDisconnect);
  }

  get isConnected() { return this._connected; }

  enable() {
    this._active = true;
    if (this._connected && !this._rafId) {
      this._rafId = requestAnimationFrame(this._poll);
    }
  }

  disable() {
    this._active = false;
    if (this._rafId) {
      cancelAnimationFrame(this._rafId);
      this._rafId = null;
    }
  }

  _onConnect(e) {
    this._gamepadIndex = e.gamepad.index;
    this._connected = true;
    console.log(`[Gamepad] Connected: ${e.gamepad.id}`);
    events.emit(Events.TOAST_SHOW, { message: `Controller connected: ${e.gamepad.id}`, type: 'info' });

    if (this._active && !this._rafId) {
      this._rafId = requestAnimationFrame(this._poll);
    }
  }

  _onDisconnect(e) {
    if (e.gamepad.index === this._gamepadIndex) {
      this._connected = false;
      this._gamepadIndex = null;
      console.log('[Gamepad] Disconnected');
      events.emit(Events.TOAST_SHOW, { message: 'Controller disconnected', type: 'warning' });
    }
  }

  _poll() {
    if (!this._active || !this._connected) {
      this._rafId = null;
      return;
    }

    const gp = navigator.getGamepads()[this._gamepadIndex];
    if (!gp) {
      this._rafId = requestAnimationFrame(this._poll);
      return;
    }

    const now = performance.now();

    // --- Button presses (edge detection) ---
    for (let i = 0; i < gp.buttons.length && i < 16; i++) {
      const pressed = gp.buttons[i].pressed;
      const wasPressed = this._prevButtons[i];

      if (pressed && !wasPressed) {
        this._handleButtonPress(i);
      }
      this._prevButtons[i] = pressed;
    }

    // --- Analog stick navigation (with repeat delay) ---
    const lx = gp.axes[AXIS.LEFT_X] || 0;
    const ly = gp.axes[AXIS.LEFT_Y] || 0;

    if (now - this._lastNavTime > REPEAT_DELAY) {
      if (Math.abs(lx) > DEAD_ZONE || Math.abs(ly) > DEAD_ZONE) {
        this._handleStickNav(lx, ly);
        this._lastNavTime = now;
      }
    }

    // --- Triggers for zoom ---
    const lt = gp.buttons[BTN.LT]?.value || 0;
    const rt = gp.buttons[BTN.RT]?.value || 0;
    if (lt > 0.3) {
      events.emit(Events.HOTKEY, { key: '-', action: 'zoom_out' });
    }
    if (rt > 0.3) {
      events.emit(Events.HOTKEY, { key: '+', action: 'zoom_in' });
    }

    this._rafId = requestAnimationFrame(this._poll);
  }

  _handleButtonPress(index) {
    switch (index) {
      case BTN.A:
        events.emit(Events.HOTKEY, { key: 'Enter', action: 'confirm' });
        break;
      case BTN.B:
        events.emit(Events.HOTKEY, { key: 'Escape', action: 'cancel' });
        break;
      case BTN.X:
        events.emit(Events.HOTKEY, { key: 'x', action: 'open_actions' });
        break;
      case BTN.Y:
        events.emit(Events.HOTKEY, { key: 'l', action: 'toggle_log' });
        break;
      case BTN.LB:
        events.emit(Events.HOTKEY, { key: 'lb', action: 'prev_action' });
        break;
      case BTN.RB:
        events.emit(Events.HOTKEY, { key: 'rb', action: 'next_action' });
        break;
      case BTN.START:
        events.emit(Events.HOTKEY, { key: 'Escape', action: 'cancel' });
        break;
      case BTN.SELECT:
        events.emit(Events.HOTKEY, { key: '`', action: 'toggle_console' });
        break;
      case BTN.DPAD_UP:
        events.emit(Events.HOTKEY, { key: 'ArrowUp', action: 'nav_up' });
        break;
      case BTN.DPAD_DOWN:
        events.emit(Events.HOTKEY, { key: 'ArrowDown', action: 'nav_down' });
        break;
      case BTN.DPAD_LEFT:
        events.emit(Events.HOTKEY, { key: 'ArrowLeft', action: 'nav_left' });
        break;
      case BTN.DPAD_RIGHT:
        events.emit(Events.HOTKEY, { key: 'ArrowRight', action: 'nav_right' });
        break;
    }
  }

  _handleStickNav(lx, ly) {
    // Determine dominant direction
    if (Math.abs(lx) > Math.abs(ly)) {
      if (lx > DEAD_ZONE) {
        events.emit(Events.HOTKEY, { key: 'ArrowRight', action: 'nav_right' });
      } else if (lx < -DEAD_ZONE) {
        events.emit(Events.HOTKEY, { key: 'ArrowLeft', action: 'nav_left' });
      }
    } else {
      if (ly > DEAD_ZONE) {
        events.emit(Events.HOTKEY, { key: 'ArrowDown', action: 'nav_down' });
      } else if (ly < -DEAD_ZONE) {
        events.emit(Events.HOTKEY, { key: 'ArrowUp', action: 'nav_up' });
      }
    }
  }

  destroy() {
    this.disable();
    window.removeEventListener('gamepadconnected', this._onConnect);
    window.removeEventListener('gamepaddisconnected', this._onDisconnect);
  }
}
