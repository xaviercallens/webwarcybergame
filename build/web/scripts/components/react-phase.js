/**
 * Neo-Hack: Gridlock v4.1 — React Phase Interrupt
 * 15-second QTE combat phase with WASD counter-pattern input
 */

export class ReactPhase {
  constructor() {
    this.isActive = false;
    this.timer = 15;
    this.interval = null;
    this.pattern = [];
    this.inputSequence = [];
    this.attackerSuccess = 84;
    this.systemStability = 14;
    this.onComplete = null;
  }

  start(onComplete) {
    this.isActive = true;
    this.timer = 15;
    this.attackerSuccess = 84;
    this.systemStability = 14;
    this.inputSequence = [];
    this.onComplete = onComplete;

    // Generate random target pattern
    const keys = ['w', 'a', 's', 'd'];
    this.pattern = Array.from({ length: 8 }, () => keys[Math.floor(Math.random() * 4)]);

    const el = document.getElementById('view-react-phase');
    if (el) {
      el.classList.add('active');
      el.style.display = 'flex';
    }

    this._updateDisplay();
    this._bindKeys();

    this.interval = setInterval(() => {
      this.timer--;
      this._updateDisplay();
      // Increase attacker success over time
      this.attackerSuccess = Math.min(99, this.attackerSuccess + 1);
      this.systemStability = Math.max(0, this.systemStability - 1);

      if (this.timer <= 0) {
        this.resolve(false);
      }
    }, 1000);
  }

  _bindKeys() {
    this._keyHandler = (e) => {
      if (!this.isActive) return;
      const key = e.key.toLowerCase();
      if (!['w', 'a', 's', 'd'].includes(key)) return;

      this.inputSequence.push(key);

      // Visual feedback
      const keyEls = document.querySelectorAll('.react-phase__qte-key');
      keyEls.forEach(el => {
        if (el.dataset.key === key) {
          el.classList.add('pressed');
          setTimeout(() => el.classList.remove('pressed'), 200);
        }
      });

      // Each correct input reduces attacker success
      const idx = this.inputSequence.length - 1;
      if (idx < this.pattern.length && this.pattern[idx] === key) {
        this.attackerSuccess = Math.max(0, this.attackerSuccess - 12);
        this.systemStability = Math.min(100, this.systemStability + 8);
        this._addLog(`> COUNTER_SEQUENCE_${idx + 1}: MATCHED`, 'info');
      } else {
        this.attackerSuccess = Math.min(99, this.attackerSuccess + 5);
        this._addLog(`> PATTERN_MISMATCH_AT_${idx + 1}`, 'warn');
        // Mark key as missed
        keyEls.forEach(el => {
          if (el.dataset.key === key) {
            el.classList.add('missed');
            setTimeout(() => el.classList.remove('missed'), 300);
          }
        });
      }

      this._updateDisplay();

      // Check if pattern complete
      if (this.inputSequence.length >= this.pattern.length) {
        setTimeout(() => this.resolve(this.attackerSuccess < 50), 500);
      }
    };
    window.addEventListener('keydown', this._keyHandler);
  }

  _addLog(text, type = '') {
    const logs = document.getElementById('rp-logs');
    if (!logs) return;
    const entry = document.createElement('div');
    entry.className = `entry ${type}`;
    entry.textContent = text;
    logs.appendChild(entry);
    logs.scrollTop = logs.scrollHeight;
  }

  _updateDisplay() {
    const timerEl = document.getElementById('rp-timer');
    const stabilityEl = document.getElementById('rp-stability');
    const atkPctEl = document.getElementById('rp-atk-pct');
    const atkBarEl = document.getElementById('rp-atk-bar');

    if (timerEl) timerEl.textContent = this.timer;
    if (stabilityEl) stabilityEl.textContent = `${this.systemStability}%`;
    if (atkPctEl) atkPctEl.textContent = `${this.attackerSuccess}%`;
    if (atkBarEl) atkBarEl.style.width = `${this.attackerSuccess}%`;
  }

  resolve(defenderWins) {
    this.isActive = false;
    clearInterval(this.interval);
    window.removeEventListener('keydown', this._keyHandler);

    const el = document.getElementById('view-react-phase');
    if (el) {
      setTimeout(() => {
        el.classList.remove('active');
        el.style.display = 'none';
      }, 1000);
    }

    if (this.onComplete) {
      this.onComplete({
        defenderWins,
        attackerSuccess: this.attackerSuccess,
        systemStability: this.systemStability,
        timeRemaining: this.timer,
      });
    }
  }
}
