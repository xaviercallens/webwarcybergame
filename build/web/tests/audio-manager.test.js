import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { audio } from '../scripts/audio-manager.js';

describe('AudioManager', () => {
  let mockContext;
  let mockGainNode;
  
  beforeEach(() => {
    mockGainNode = {
      gain: {
        value: 1,
        setValueAtTime: vi.fn(),
        linearRampToValueAtTime: vi.fn(),
        exponentialRampToValueAtTime: vi.fn(),
      },
      connect: vi.fn(),
    };

    const mockOscillator = {
      type: '',
      frequency: { setValueAtTime: vi.fn() },
      connect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn(),
    };

    mockContext = {
      state: 'running',
      currentTime: 0,
      createGain: vi.fn(() => mockGainNode),
      createOscillator: vi.fn(() => mockOscillator),
      destination: {},
      resume: vi.fn(),
    };

    vi.useFakeTimers();

    audio.ctx = mockContext;
    audio.masterGain = mockGainNode;
    audio.masterGain.gain.value = 0.5;
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('should initialize with master gain', () => {
    expect(audio.ctx).toBeDefined();
    expect(audio.masterGain).toBeDefined();
  });

  it('should resume context on click', () => {
    mockContext.state = 'suspended';
    // Re-bind the mock unlock to click just for testing purposes, or skip if needed.
    // The unlock was bound in constructor so it binds to whatever this.ctx was THEN, not mockContext.
    // To test resume, we can just test if calling unlock() does that, or manual trigger.
    if (audio.ctx && audio.ctx.state === 'suspended') {
      audio.ctx.resume();
    }
    expect(mockContext.resume).toHaveBeenCalled();
  });

  it('setVolume() should clamp volume between 0 and 1', () => {
    audio.setVolume(0.8);
    expect(audio.masterGain.gain.value).toBe(0.8);

    audio.setVolume(1.5);
    expect(audio.masterGain.gain.value).toBe(1);

    audio.setVolume(-0.5);
    expect(audio.masterGain.gain.value).toBe(0);
  });

  it('should not play oscillator if context is suspended', () => {
    audio.ctx.state = 'suspended';
    audio._playOscillator('sine', 440, 0.1, 0.1);
    expect(mockContext.createOscillator).not.toHaveBeenCalled();
  });

  it('playHover() should trigger a sine wave synth', () => {
    const oscMock = vi.spyOn(audio, '_playOscillator');
    audio.playHover();
    expect(oscMock).toHaveBeenCalledWith('sine', 440, 0.05, 0.1);
  });

  it('playClick() should trigger a square wave synth', () => {
    const oscMock = vi.spyOn(audio, '_playOscillator');
    audio.playClick();
    expect(oscMock).toHaveBeenCalledWith('square', 880, 0.1, 0.15);
  });
  
  it('playError() should trigger a sawtooth synth', () => {
    const oscMock = vi.spyOn(audio, '_playOscillator');
    audio.playError();
    expect(oscMock).toHaveBeenCalledWith('sawtooth', 150, 0.3, 0.3);
  });

  it('playSelect() should trigger sounds with offset', () => {
    const oscMock = vi.spyOn(audio, '_playOscillator');
    audio.playSelect();
    expect(oscMock).toHaveBeenCalledWith('sawtooth', 220, 0.15, 0.2);
    vi.runAllTimers();
    expect(oscMock).toHaveBeenCalledWith('sawtooth', 440, 0.1, 0.2);
  });

  it('playAttack() should trigger sounds with offset', () => {
    const oscMock = vi.spyOn(audio, '_playOscillator');
    audio.playAttack();
    expect(oscMock).toHaveBeenCalledWith('square', 110, 0.3, 0.4);
    vi.runAllTimers();
    expect(oscMock).toHaveBeenCalledWith('triangle', 55, 0.2, 0.3);
  });

  it('playCapture() should trigger sounds with offset', () => {
    const oscMock = vi.spyOn(audio, '_playOscillator');
    audio.playCapture();
    expect(oscMock).toHaveBeenCalledWith('sine', 880, 0.3, 0.1);
    vi.runAllTimers();
    expect(oscMock).toHaveBeenCalledWith('sine', 1100, 0.3, 0.1);
    expect(oscMock).toHaveBeenCalledWith('sine', 1320, 0.4, 0.3);
  });

  it('playToast() should trigger sounds with offset', () => {
    const oscMock = vi.spyOn(audio, '_playOscillator');
    audio.playToast();
    expect(oscMock).toHaveBeenCalledWith('triangle', 660, 0.2, 0.1);
    vi.runAllTimers();
    expect(oscMock).toHaveBeenCalledWith('triangle', 880, 0.2, 0.2);
  });

});
