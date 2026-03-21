/**
 * Neo-Hack: Gridlock v3.2 — Node Tooltip Component
 * Shows node details on hover/focus. Auto-positions near cursor, flips at viewport edges.
 */

import { events, Events } from '../game-events.js';

export class NodeTooltip {
  constructor() {
    this.el = document.createElement('div');
    this.el.id = 'node-tooltip';
    this.el.className = 'node-tooltip';
    this.el.setAttribute('role', 'tooltip');
    this.el.style.display = 'none';
    document.body.appendChild(this.el);

    this._visible = false;
    this._currentNode = null;

    events.on(Events.NODE_HOVER, (data) => this.show(data.node, data.x, data.y));
    events.on(Events.NODE_HOVER_END, () => this.hide());
    events.on(Events.NODE_SELECT, () => this.hide());
  }

  show(node, x, y) {
    if (!node) return;
    this._currentNode = node;
    this._visible = true;

    const statusLabel = this._getStatusLabel(node.statusOverlay);
    const statusClass = `node-tooltip__status--${node.statusOverlay || 'unknown'}`;

    this.el.innerHTML = `
      <div class="node-tooltip__header">
        <span class="node-tooltip__name">${node.name || 'Unknown'}</span>
        <span class="node-tooltip__id">#${node.id}</span>
      </div>
      <div class="node-tooltip__status ${statusClass}">${statusLabel}</div>
      ${node.node_class ? `<div class="node-tooltip__row"><span>Class:</span> <span>${node.node_class}</span></div>` : ''}
      ${node.firewall != null ? `<div class="node-tooltip__row"><span>Firewall:</span> <span>${node.firewall}</span></div>` : ''}
      ${node.power != null ? `<div class="node-tooltip__row"><span>Compute:</span> <span>${node.power} TB/s</span></div>` : ''}
      ${node.vulnerabilities ? `<div class="node-tooltip__row"><span>Vulns:</span> <span>${node.vulnerabilities.length}</span></div>` : ''}
    `;

    this._position(x, y);
    this.el.style.display = 'block';
  }

  hide() {
    this._visible = false;
    this._currentNode = null;
    this.el.style.display = 'none';
  }

  _position(x, y) {
    const pad = 12;
    const rect = this.el.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let left = x + pad;
    let top = y + pad;

    // Flip horizontally if near right edge
    if (left + 220 > vw) {
      left = x - 220 - pad;
    }
    // Flip vertically if near bottom edge
    if (top + 160 > vh) {
      top = y - 160 - pad;
    }

    this.el.style.left = `${Math.max(0, left)}px`;
    this.el.style.top = `${Math.max(0, top)}px`;
  }

  _getStatusLabel(overlay) {
    const labels = {
      compromised: '⛔ COMPROMISED',
      compromised_detected: '⛔ COMPROMISED (DETECTED)',
      compromised_hidden: '🔒 SECURE',
      discovered: '🔍 DISCOVERED',
      suspicious: '⚠️ SUSPICIOUS',
      secure: '🔒 SECURE',
      hidden: '░░ UNKNOWN',
    };
    return labels[overlay] || '—';
  }

  destroy() {
    this.el.remove();
  }
}
