/**
 * Unit tests for StateMachine
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { StateMachine, ViewState } from '../scripts/state-machine.js';
import { events, Events } from '../scripts/game-events.js';

describe('StateMachine', () => {
  let sm;

  beforeEach(() => {
    events.clear();
    sm = new StateMachine();
  });

  it('should start in LOGIN state', () => {
    expect(sm.current).toBe(ViewState.LOGIN);
    expect(sm.previous).toBeNull();
  });

  it('should transition LOGIN → MENU', () => {
    const result = sm.transitionTo(ViewState.MENU);
    expect(result).toBe(true);
    expect(sm.current).toBe(ViewState.MENU);
    expect(sm.previous).toBe(ViewState.LOGIN);
  });

  it('should reject invalid transitions', () => {
    const result = sm.transitionTo(ViewState.GAME);
    expect(result).toBe(false);
    expect(sm.current).toBe(ViewState.LOGIN);
  });

  it('should emit VIEW_CHANGE on valid transition', () => {
    const handler = vi.fn();
    events.on(Events.VIEW_CHANGE, handler);
    sm.transitionTo(ViewState.MENU);
    expect(handler).toHaveBeenCalledWith({
      from: ViewState.LOGIN,
      to: ViewState.MENU,
      data: {},
    });
  });

  it('should not emit VIEW_CHANGE on invalid transition', () => {
    const handler = vi.fn();
    events.on(Events.VIEW_CHANGE, handler);
    sm.transitionTo(ViewState.GAME);
    expect(handler).not.toHaveBeenCalled();
  });

  it('should pass data with transitions', () => {
    const handler = vi.fn();
    events.on(Events.VIEW_CHANGE, handler);
    sm.transitionTo(ViewState.MENU, { test: true });
    expect(handler).toHaveBeenCalledWith({
      from: ViewState.LOGIN,
      to: ViewState.MENU,
      data: { test: true },
    });
  });

  it('should follow full game flow: LOGIN → MENU → ROLE_SELECT → BRIEFING → GAME', () => {
    expect(sm.transitionTo(ViewState.MENU)).toBe(true);
    expect(sm.transitionTo(ViewState.ROLE_SELECT)).toBe(true);
    expect(sm.transitionTo(ViewState.BRIEFING)).toBe(true);
    expect(sm.transitionTo(ViewState.GAME)).toBe(true);
    expect(sm.current).toBe(ViewState.GAME);
  });

  it('should allow GAME → PAUSE → GAME', () => {
    sm.forceState(ViewState.GAME);
    expect(sm.transitionTo(ViewState.PAUSE)).toBe(true);
    expect(sm.transitionTo(ViewState.GAME)).toBe(true);
    expect(sm.current).toBe(ViewState.GAME);
  });

  it('should allow GAME → DEBRIEF → MENU', () => {
    sm.forceState(ViewState.GAME);
    expect(sm.transitionTo(ViewState.DEBRIEF)).toBe(true);
    expect(sm.transitionTo(ViewState.MENU)).toBe(true);
    expect(sm.current).toBe(ViewState.MENU);
  });

  it('should track full history', () => {
    sm.transitionTo(ViewState.MENU);
    sm.transitionTo(ViewState.ROLE_SELECT);
    sm.transitionTo(ViewState.BRIEFING);
    expect(sm.history).toEqual([
      ViewState.LOGIN,
      ViewState.MENU,
      ViewState.ROLE_SELECT,
      ViewState.BRIEFING,
    ]);
  });

  it('back() should return to previous state', () => {
    sm.transitionTo(ViewState.MENU);
    sm.transitionTo(ViewState.LEADERBOARD);
    const result = sm.back();
    expect(result).toBe(true);
    expect(sm.current).toBe(ViewState.MENU);
  });

  it('back() should fail if no valid reverse transition', () => {
    sm.transitionTo(ViewState.MENU);
    sm.transitionTo(ViewState.ROLE_SELECT);
    sm.transitionTo(ViewState.BRIEFING);
    // Briefing → RoleSelect is not in TRANSITIONS
    const result = sm.back();
    expect(result).toBe(false);
  });

  it('canTransitionTo() should check validity', () => {
    expect(sm.canTransitionTo(ViewState.MENU)).toBe(true);
    expect(sm.canTransitionTo(ViewState.GAME)).toBe(false);
  });

  it('forceState() should bypass validation', () => {
    sm.forceState(ViewState.GAME);
    expect(sm.current).toBe(ViewState.GAME);
    expect(sm.previous).toBe(ViewState.LOGIN);
  });
});
