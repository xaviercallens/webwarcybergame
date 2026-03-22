/**
 * Neo-Hack: Gridlock v4.1 — Data Siphon Operations Component
 */
export class DataSiphon {
  constructor() {
    this.siphonPercent = 0;
    this.isActive = false;
    this.intervalId = null;
  }

  init() {
    const gauge = document.getElementById('siphon-gauge-value');
    const statusLabel = document.getElementById('siphon-status-label');
    const btnExecute = document.getElementById('btn-execute-siphon');
    const btnDecoy = document.getElementById('btn-decoy-signal');

    if (btnExecute) {
      btnExecute.addEventListener('click', () => this.startSiphon());
    }
    if (btnDecoy) {
      btnDecoy.addEventListener('click', () => this.activateDecoy());
    }
  }

  startSiphon() {
    if (this.isActive) return;
    this.isActive = true;
    this.siphonPercent = 0;

    const gauge = document.getElementById('siphon-gauge-value');
    const statusLabel = document.getElementById('siphon-status-label');
    const ring = document.getElementById('siphon-ring');

    if (statusLabel) statusLabel.textContent = 'ACTIVE_DRAIN';
    this.addLog('[SYS] SIPHON_INITIATED — STREAM_OPEN');

    this.intervalId = setInterval(() => {
      this.siphonPercent += Math.random() * 3 + 1;
      if (this.siphonPercent >= 100) {
        this.siphonPercent = 100;
        clearInterval(this.intervalId);
        this.completeSiphon();
      }
      if (gauge) gauge.textContent = `${Math.floor(this.siphonPercent)}%`;
      if (ring) {
        const circumference = 2 * Math.PI * 120;
        const offset = circumference - (this.siphonPercent / 100) * circumference;
        ring.style.strokeDashoffset = offset;
      }
    }, 500);
  }

  completeSiphon() {
    this.isActive = false;
    const statusLabel = document.getElementById('siphon-status-label');
    if (statusLabel) statusLabel.textContent = 'SECURED_SUCCESS';
    this.addLog('[SUCCESS] DATA_BREACHED — SIPHON_COMPLETE');
    this.addLog('[CLEANUP] SCRUBBING_FOOTPRINTS...');
  }

  activateDecoy() {
    this.addLog('[DECOY] SIGNAL_DEPLOYED — MASKING_PRIMARY_STREAM');
    const btnDecoy = document.getElementById('btn-decoy-signal');
    if (btnDecoy) {
      btnDecoy.textContent = 'DECOY_ACTIVE ✓';
      btnDecoy.style.borderColor = 'var(--color-stable)';
      btnDecoy.style.color = 'var(--color-stable)';
    }
  }

  addLog(text) {
    const log = document.getElementById('siphon-log-entries');
    if (!log) return;
    const entry = document.createElement('div');
    entry.className = 'siphon-log__entry';
    const now = new Date();
    const ts = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
    entry.innerHTML = `<span class="ts">${ts}</span> ${text}`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
  }

  destroy() {
    if (this.intervalId) clearInterval(this.intervalId);
  }
}
