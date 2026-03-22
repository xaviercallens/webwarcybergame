/**
 * Neo-Hack: Gridlock v4.1 — Mesh Gateway Capture Component
 */
export class GatewayCapture {
  constructor() {
    this.capturePercent = 0;
    this.isActive = false;
    this.intervalId = null;
  }

  init() {
    const btn = document.getElementById('btn-initiate-override');
    if (btn) btn.addEventListener('click', () => this.startCapture());
  }

  startCapture() {
    if (this.isActive) return;
    this.isActive = true;
    this.capturePercent = 0;

    const gauge = document.getElementById('capture-gauge-value');
    const ring = document.getElementById('capture-ring');

    this.intervalId = setInterval(() => {
      this.capturePercent += Math.random() * 4 + 1;
      if (this.capturePercent >= 100) {
        this.capturePercent = 100;
        clearInterval(this.intervalId);
        this.isActive = false;
      }
      if (gauge) gauge.textContent = `${Math.floor(this.capturePercent)}%`;
      if (ring) {
        const circumference = 2 * Math.PI * 120;
        const offset = circumference - (this.capturePercent / 100) * circumference;
        ring.style.strokeDashoffset = offset;
      }
    }, 400);
  }

  destroy() {
    if (this.intervalId) clearInterval(this.intervalId);
  }
}
