/**
 * Unit tests for GameEventBus
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { events, Events } from '../scripts/game-events.js';

describe('GameEventBus', () => {
  beforeEach(() => {
    events.clear();
  });

  it('should emit and receive events', () => {
    const handler = vi.fn();
    events.on('test:event', handler);
    events.emit('test:event', { data: 42 });
    expect(handler).toHaveBeenCalledWith({ data: 42 });
  });

  it('should support multiple listeners', () => {
    const h1 = vi.fn();
    const h2 = vi.fn();
    events.on('test:multi', h1);
    events.on('test:multi', h2);
    events.emit('test:multi', 'payload');
    expect(h1).toHaveBeenCalledWith('payload');
    expect(h2).toHaveBeenCalledWith('payload');
  });

  it('should unsubscribe with returned function', () => {
    const handler = vi.fn();
    const unsub = events.on('test:unsub', handler);
    unsub();
    events.emit('test:unsub', 'ignored');
    expect(handler).not.toHaveBeenCalled();
  });

  it('should unsubscribe with off()', () => {
    const handler = vi.fn();
    events.on('test:off', handler);
    events.off('test:off', handler);
    events.emit('test:off', 'ignored');
    expect(handler).not.toHaveBeenCalled();
  });

  it('should support once()', () => {
    const handler = vi.fn();
    events.once('test:once', handler);
    events.emit('test:once', 'first');
    events.emit('test:once', 'second');
    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler).toHaveBeenCalledWith('first');
  });

  it('should clear all listeners for a specific event', () => {
    const h1 = vi.fn();
    const h2 = vi.fn();
    events.on('test:clear', h1);
    events.on('test:other', h2);
    events.clear('test:clear');
    events.emit('test:clear', 'ignored');
    events.emit('test:other', 'received');
    expect(h1).not.toHaveBeenCalled();
    expect(h2).toHaveBeenCalledWith('received');
  });

  it('should clear all listeners when no event specified', () => {
    const h1 = vi.fn();
    const h2 = vi.fn();
    events.on('a', h1);
    events.on('b', h2);
    events.clear();
    events.emit('a');
    events.emit('b');
    expect(h1).not.toHaveBeenCalled();
    expect(h2).not.toHaveBeenCalled();
  });

  it('should not crash when emitting with no listeners', () => {
    expect(() => events.emit('nonexistent', 'data')).not.toThrow();
  });

  it('should catch errors in handlers without breaking other handlers', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const badHandler = () => { throw new Error('boom'); };
    const goodHandler = vi.fn();
    events.on('test:error', badHandler);
    events.on('test:error', goodHandler);
    events.emit('test:error', 'payload');
    expect(goodHandler).toHaveBeenCalledWith('payload');
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it('should export all expected event constants', () => {
    expect(Events.NODE_SELECT).toBe('node:select');
    expect(Events.ACTION_EXECUTE).toBe('action:execute');
    expect(Events.TURN_SWITCH).toBe('turn:switch');
    expect(Events.GAME_START).toBe('game:start');
    expect(Events.GAME_OVER).toBe('game:over');
    expect(Events.GAME_STATE).toBe('game:state');
    expect(Events.LOG_ADD).toBe('log:add');
    expect(Events.TOAST_SHOW).toBe('toast:show');
    expect(Events.VIEW_CHANGE).toBe('view:change');
    expect(Events.HOTKEY).toBe('hotkey:press');
  });

  it('debug() should return listener counts', () => {
    events.on('a', () => {});
    events.on('a', () => {});
    events.on('b', () => {});
    const info = events.debug();
    expect(info.a).toBe(2);
    expect(info.b).toBe(1);
  });
});
