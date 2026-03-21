/**
 * Unit tests for HotkeyManager
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { HotkeyManager } from '../scripts/hotkey-manager.js';
import { events, Events } from '../scripts/game-events.js';

describe('HotkeyManager', () => {
  let hm;

  beforeEach(() => {
    events.clear();
    hm = new HotkeyManager();
    // Set active view directly since events.emit before construction won't work
    hm._activeView = 'game';
  });

  afterEach(() => {
    hm.destroy();
  });

  function pressKey(key, opts = {}) {
    const event = new KeyboardEvent('keydown', { key, bubbles: true, ...opts });
    document.dispatchEvent(event);
  }

  it('should emit HOTKEY on valid game key press', () => {
    const handler = vi.fn();
    events.on(Events.HOTKEY, handler);

    pressKey('h');

    expect(handler).toHaveBeenCalledWith(expect.objectContaining({
      key: 'h',
      action: 'toggle_hints',
    }));
  });

  it('should emit action slot hotkeys', () => {
    const handler = vi.fn();
    events.on(Events.HOTKEY, handler);

    pressKey('1');
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ action: 'action_1' }));

    pressKey('3');
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ action: 'action_3' }));
  });

  it('should emit navigation hotkeys', () => {
    const handler = vi.fn();
    events.on(Events.HOTKEY, handler);

    pressKey('ArrowUp');
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ action: 'nav_up' }));

    pressKey('w');
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ action: 'nav_up' }));
  });

  it('should not emit when disabled', () => {
    const handler = vi.fn();
    events.on(Events.HOTKEY, handler);

    hm.setEnabled(false);
    pressKey('h');
    expect(handler).not.toHaveBeenCalled();
  });

  it('should not emit for unbound keys', () => {
    const handler = vi.fn();
    events.on(Events.HOTKEY, handler);

    pressKey('z');
    expect(handler).not.toHaveBeenCalled();
  });

  it('should suppress hotkeys when focused on input (except Escape)', () => {
    const handler = vi.fn();
    events.on(Events.HOTKEY, handler);

    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    pressKey('h');
    expect(handler).not.toHaveBeenCalled();

    pressKey('Escape');
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ action: 'cancel' }));

    document.body.removeChild(input);
  });

  it('should rebind a key', () => {
    hm.rebind('h', 'custom_action');

    const handler = vi.fn();
    events.on(Events.HOTKEY, handler);

    pressKey('h');
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ action: 'custom_action' }));
  });

  it('should return bindings map', () => {
    const bindings = hm.getBindings();
    expect(bindings['Tab']).toBeDefined();
    expect(bindings['Tab'].action).toBe('cycle_focus');
    expect(bindings['Escape'].action).toBe('cancel');
  });

  it('should reset bindings to defaults', () => {
    hm.rebind('h', 'custom');
    hm.resetBindings();
    const bindings = hm.getBindings();
    expect(bindings['h'].action).toBe('toggle_hints');
  });

  it('should save and load bindings from localStorage', () => {
    hm.rebind('h', 'saved_action');
    hm.save();

    const hm2 = new HotkeyManager();
    hm2.load();
    const bindings = hm2.getBindings();
    expect(bindings['h'].action).toBe('saved_action');
    hm2.destroy();

    // Clean up
    localStorage.removeItem('nh_hotkeys');
  });

  it('should only emit global actions outside game view', () => {
    hm._activeView = 'menu';

    const handler = vi.fn();
    events.on(Events.HOTKEY, handler);

    // Non-global action should not fire in menu
    pressKey('h');
    expect(handler).not.toHaveBeenCalled();

    // Global action (Escape/cancel) should fire
    pressKey('Escape');
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ action: 'cancel' }));
  });
});
