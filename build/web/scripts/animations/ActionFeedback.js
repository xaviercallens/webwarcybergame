/**
 * ActionFeedback animations for Neo-Hack v3.1.
 * Visual and audio feedback for action results.
 * Blueprint Alignment: Day 4, Section 2.1 (Real-Time Feedback)
 */

export class ActionFeedback {
  constructor() {
    this._overlay = null;
    this._init();
  }

  _init() {
    this._overlay = document.createElement('div');
    this._overlay.id = 'action-feedback-overlay';
    this._overlay.className = 'action-feedback-overlay';
    document.body.appendChild(this._overlay);
  }

  /**
   * Show action result feedback.
   * @param {object} action - { name, target }
   * @param {object} result - { success, detected }
   */
  showActionResult(action, result) {
    if (result.success) {
      this._showFloatingText(action.target, '\u2713 SUCCESS', 'success');
      this._pulseNode(action.target, 'success');
    } else {
      this._showFloatingText(action.target, '\u2717 FAILED', 'failure');
      this._pulseNode(action.target, 'failure');
    }

    if (result.detected) {
      this._showAlertPopup('\u26A0 ALERT: Suspicious activity detected!');
      this._pulseNode(action.target, 'alert');
    }
  }

  _showFloatingText(targetId, text, type) {
    const el = document.createElement('div');
    el.className = `floating-text floating-text--${type}`;
    el.textContent = text;

    // Position near center-top (could be positioned near node in a real 3D scene)
    el.style.cssText = `
      position: fixed;
      top: 30%;
      left: 50%;
      transform: translateX(-50%);
      z-index: 9000;
      pointer-events: none;
    `;

    this._overlay.appendChild(el);

    // Animate upward and fade
    requestAnimationFrame(() => {
      el.style.transition = 'all 1.5s ease-out';
      el.style.top = '20%';
      el.style.opacity = '0';
    });

    setTimeout(() => el.remove(), 1600);
  }

  _pulseNode(targetId, type) {
    // Emit a custom event that the renderer/game-engine can listen for
    const event = new CustomEvent('actionFeedback', {
      detail: { targetId, type }
    });
    window.dispatchEvent(event);
  }

  _showAlertPopup(message) {
    const el = document.createElement('div');
    el.className = 'alert-popup';
    el.innerHTML = `
      <div class="alert-popup__icon">\u26A0</div>
      <div class="alert-popup__message">${message}</div>
    `;

    el.style.cssText = `
      position: fixed;
      top: 10%;
      left: 50%;
      transform: translateX(-50%);
      z-index: 9001;
      pointer-events: none;
    `;

    this._overlay.appendChild(el);

    // Fade out
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s ease-out';
      el.style.opacity = '0';
    }, 2000);

    setTimeout(() => el.remove(), 2600);
  }

  destroy() {
    if (this._overlay) {
      this._overlay.remove();
    }
  }
}
