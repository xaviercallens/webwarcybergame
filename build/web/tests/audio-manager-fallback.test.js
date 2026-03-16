import { describe, it, expect, vi } from 'vitest';

describe('AudioManager Fallbacks', () => {
  it('should handle missing AudioContext gracefully', async () => {
    // Force AudioContext to be falsy
    window.AudioContext = undefined;
    window.webkitAudioContext = undefined;
    
    vi.resetModules();
    const mod = await import('../scripts/audio-manager.js');
    const fallbackAudio = mod.audio;

    expect(fallbackAudio.ctx).toBeNull();
  });

  it('should handle AudioContext initialization error gracefully', async () => {
    // Force AudioContext to throw
    window.AudioContext = vi.fn(() => { throw new Error('Simulated error'); });
    
    vi.resetModules();
    const mod = await import('../scripts/audio-manager.js');
    const erroredAudio = mod.audio;

    expect(erroredAudio.ctx).toBeNull();
  });
});
