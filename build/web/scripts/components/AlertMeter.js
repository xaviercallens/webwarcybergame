/**
 * AlertMeter component for Neo-Hack v3.1.
 * Standalone alert level visualization for defender HUD.
 * Blueprint Alignment: Day 4, Section 2 (User Experience)
 */

export class AlertMeter {
  constructor(container) {
    this.container = container;
    this.el = document.createElement('div');
    this.el.id = 'alert-meter';
    this.el.className = 'alert-meter-widget';
    this.container.appendChild(this.el);
    this._level = 0;
    this._threshold = 70;
  }

  setLevel(level) {
    this._level = Math.max(0, Math.min(100, level));
    this._update();
  }

  setThreshold(threshold) {
    this._threshold = threshold;
    this._update();
  }

  _update() {
    const color = this._getColor();
    const overThreshold = this._level >= this._threshold;

    this.el.innerHTML = `
      <div class="alert-meter-widget__label">
        ALERT LEVEL
        ${overThreshold ? '<span class="alert-meter-widget__warning">CRITICAL</span>' : ''}
      </div>
      <div class="alert-meter-widget__bar">
        <div class="alert-meter-widget__fill ${overThreshold ? 'alert-meter-widget__fill--critical' : ''}" 
             style="width: ${this._level}%; background: ${color};"></div>
        <div class="alert-meter-widget__threshold" style="left: ${this._threshold}%;"></div>
      </div>
      <div class="alert-meter-widget__value">${this._level} / 100</div>
    `;
  }

  _getColor() {
    if (this._level < 30) return '#00ffdd';
    if (this._level < 70) return '#ffcc00';
    return '#ff0055';
  }

  destroy() {
    this.el.remove();
  }
}
