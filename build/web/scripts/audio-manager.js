/**
 * Neo-Hack: Gridlock — Procedural Audio Manager
 * Generates synthetic UI sounds using the Web Audio API.
 */

class AudioManager {
  constructor() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
        this.masterGain = this.ctx.createGain();
        this.masterGain.gain.value = 0.5; // Default volume
        this.masterGain.connect(this.ctx.destination);
        
        // Bind global interactions to resume audio context (browser autoplay policy)
        const unlock = () => {
          if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
          }
          document.removeEventListener('click', unlock);
        };
        document.addEventListener('click', unlock);
      } else {
        this.ctx = null;
        console.warn('AudioContext not supported');
      }
    } catch(e) {
      this.ctx = null;
      console.error('Failed to initialize AudioContext:', e);
    }
  }

  /**
   * Set the master volume for all synthesized sounds.
   * @param {number} val - Volume level between 0 and 1.
   */
  setVolume(val) {
    this.masterGain.gain.value = Math.max(0, Math.min(1, val));
  }

  /**
   * Play a subtle sine wave sound for UI hover events.
   */
  playHover() {
    this._playOscillator('sine', 440, 0.05, 0.1);
  }

  /**
   * Play a distinct square wave sound for button click events.
   */
  playClick() {
    this._playOscillator('square', 880, 0.1, 0.15);
  }

  /**
   * Play a dual-tone sawtooth sound for node selection.
   */
  playSelect() {
    this._playOscillator('sawtooth', 220, 0.15, 0.2);
    setTimeout(() => this._playOscillator('sawtooth', 440, 0.1, 0.2), 50);
  }

  /**
   * Play a low, aggressive dual-tone sound indicating an attack initiation.
   */
  playAttack() {
    this._playOscillator('square', 110, 0.3, 0.4);
    setTimeout(() => this._playOscillator('triangle', 55, 0.2, 0.3), 100);
  }

  /**
   * Play an ascending three-tone chime for a successful node capture.
   */
  playCapture() {
    this._playOscillator('sine', 880, 0.3, 0.1);
    setTimeout(() => this._playOscillator('sine', 1100, 0.3, 0.1), 100);
    setTimeout(() => this._playOscillator('sine', 1320, 0.4, 0.3), 200);
  }

  /**
   * Play a bright notification chime for toast messages.
   */
  playToast() {
    this._playOscillator('triangle', 660, 0.2, 0.1);
    setTimeout(() => this._playOscillator('triangle', 880, 0.2, 0.2), 100);
  }
  
  /**
   * Play a harsh sawtooth buzz for error states or failed actions.
   */
  playError() {
    this._playOscillator('sawtooth', 150, 0.3, 0.3);
  }

  /**
   * Internal generator for playing an oscillator tone with a quick fade-out.
   * @private
   * @param {string} type - Oscillator type (sine, square, sawtooth, triangle).
   * @param {number} freq - Frequency in Hz.
   * @param {number} vol - Peak volume level.
   * @param {number} duration - Duration in seconds.
   */
  _playOscillator(type, freq, vol, duration) {
    if (this.ctx.state === 'suspended') return;
    
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    
    osc.type = type;
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
    
    gain.gain.setValueAtTime(0, this.ctx.currentTime);
    gain.gain.linearRampToValueAtTime(vol, this.ctx.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
    
    osc.connect(gain);
    gain.connect(this.masterGain);
    
    osc.start();
    osc.stop(this.ctx.currentTime + duration + 0.1);
  }
}

export const audio = new AudioManager();
