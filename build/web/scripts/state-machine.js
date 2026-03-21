/**
 * Neo-Hack: Gridlock v3.2 — View State Machine
 * Controls navigation between game screens with validated transitions.
 *
 * States: LOGIN → MENU → ROLE_SELECT → BRIEFING → GAME ↔ PAUSE → DEBRIEF → MENU
 */

import { events, Events } from './game-events.js';

export const ViewState = {
  LOGIN:       'login',
  MENU:        'menu',
  ROLE_SELECT: 'role_select',
  BRIEFING:    'briefing',
  GAME:        'game',
  PAUSE:       'pause',
  DEBRIEF:     'debrief',
  LEADERBOARD: 'leaderboard',
  SETTINGS:    'settings',
};

// Allowed transitions: { fromState: [toState, ...] }
const TRANSITIONS = {
  [ViewState.LOGIN]:       [ViewState.MENU],
  [ViewState.MENU]:        [ViewState.ROLE_SELECT, ViewState.LEADERBOARD, ViewState.SETTINGS, ViewState.LOGIN],
  [ViewState.ROLE_SELECT]: [ViewState.BRIEFING, ViewState.MENU],
  [ViewState.BRIEFING]:    [ViewState.GAME, ViewState.MENU],
  [ViewState.GAME]:        [ViewState.PAUSE, ViewState.DEBRIEF, ViewState.MENU],
  [ViewState.PAUSE]:       [ViewState.GAME, ViewState.MENU],
  [ViewState.DEBRIEF]:     [ViewState.MENU, ViewState.ROLE_SELECT],
  [ViewState.LEADERBOARD]: [ViewState.MENU],
  [ViewState.SETTINGS]:    [ViewState.MENU],
};

export class StateMachine {
  constructor() {
    this._current = ViewState.LOGIN;
    this._previous = null;
    this._history = [ViewState.LOGIN];
  }

  /** Current view state. */
  get current() {
    return this._current;
  }

  /** Previous view state (or null). */
  get previous() {
    return this._previous;
  }

  /**
   * Transition to a new state. Validates the transition is allowed.
   * @param {string} newState - Target ViewState
   * @param {object} [data] - Optional payload for the transition
   * @returns {boolean} True if transition succeeded
   */
  transitionTo(newState, data = {}) {
    const allowed = TRANSITIONS[this._current];
    if (!allowed || !allowed.includes(newState)) {
      console.warn(`[StateMachine] Invalid transition: ${this._current} → ${newState}`);
      return false;
    }

    this._previous = this._current;
    this._current = newState;
    this._history.push(newState);

    events.emit(Events.VIEW_CHANGE, {
      from: this._previous,
      to: this._current,
      data,
    });

    return true;
  }

  /**
   * Go back to the previous state (if the reverse transition is valid).
   * @returns {boolean}
   */
  back() {
    if (!this._previous) return false;
    return this.transitionTo(this._previous);
  }

  /**
   * Check if a given transition is valid from the current state.
   * @param {string} newState
   * @returns {boolean}
   */
  canTransitionTo(newState) {
    const allowed = TRANSITIONS[this._current];
    return !!(allowed && allowed.includes(newState));
  }

  /**
   * Force-set state without validation (for initialization / recovery).
   * @param {string} state
   */
  forceState(state) {
    this._previous = this._current;
    this._current = state;
    this._history.push(state);
  }

  /** Full history of state transitions. */
  get history() {
    return [...this._history];
  }
}
