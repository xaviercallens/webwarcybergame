/**
 * Neo-Hack: Gridlock v3.2 — Notification & Log Panel
 * Collapsible panel showing game events with filtering, severity icons, and clickable node refs.
 */

import { events, Events } from '../game-events.js';

const SEVERITY_CONFIG = {
  critical: { icon: '🔴', class: 'log-entry--critical' },
  warning:  { icon: '🟡', class: 'log-entry--warning' },
  info:     { icon: '🟢', class: 'log-entry--info' },
  system:   { icon: '⚙️', class: 'log-entry--system' },
};

const FILTERS = ['all', 'alert', 'system', 'action', 'narrative'];

export class LogPanel {
  constructor(container) {
    this.container = container;
    this.el = document.createElement('div');
    this.el.id = 'log-panel';
    this.el.className = 'log-panel';
    this.el.setAttribute('role', 'log');
    this.el.setAttribute('aria-label', 'Game event log');
    this.container.appendChild(this.el);

    this._entries = [];
    this._expanded = false;
    this._activeFilter = 'all';
    this._maxEntries = 200;
    this._tickerMax = 3;
    this._unreadCount = 0;

    this._render();
    this._bindEvents();
  }

  _bindEvents() {
    events.on(Events.LOG_ADD, (entry) => this.addEntry(entry));

    // Keyboard shortcut L to toggle
    events.on(Events.HOTKEY, ({ key }) => {
      if (key === 'l') this.toggle();
    });
  }

  addEntry({ message, severity = 'info', source = 'system', nodeRef = null, turn = null }) {
    const entry = {
      id: Date.now() + Math.random(),
      message,
      severity,
      source,
      nodeRef,
      turn,
      timestamp: new Date(),
      read: this._expanded,
    };

    this._entries.push(entry);
    if (this._entries.length > this._maxEntries) {
      this._entries.shift();
    }

    if (!this._expanded) {
      this._unreadCount++;
    }

    this._renderEntries();
  }

  toggle() {
    this._expanded = !this._expanded;
    if (this._expanded) {
      this._unreadCount = 0;
      this._entries.forEach(e => e.read = true);
    }
    this._render();
  }

  show() { this._expanded = true; this._unreadCount = 0; this._render(); }
  hide() { this._expanded = false; this._render(); }

  setFilter(filter) {
    this._activeFilter = filter;
    this._renderEntries();
  }

  _render() {
    this.el.innerHTML = `
      <div class="log-panel__header">
        <button class="log-panel__toggle" aria-label="Toggle log panel">
          <span class="log-panel__icon">📋</span>
          <span class="log-panel__title">INTEL FEED</span>
          ${this._unreadCount > 0 ? `<span class="log-panel__badge">${this._unreadCount}</span>` : ''}
        </button>
        ${this._expanded ? `
          <div class="log-panel__filters">
            ${FILTERS.map(f => `
              <button class="log-panel__filter-btn ${this._activeFilter === f ? 'log-panel__filter-btn--active' : ''}"
                      data-filter="${f}">${f.toUpperCase()}</button>
            `).join('')}
          </div>
        ` : ''}
      </div>
      <div class="log-panel__body ${this._expanded ? 'log-panel__body--expanded' : ''}">
        <div class="log-panel__entries" id="log-entries-container">
        </div>
      </div>
    `;

    // Bind toggle
    const toggleBtn = this.el.querySelector('.log-panel__toggle');
    if (toggleBtn) toggleBtn.addEventListener('click', () => this.toggle());

    // Bind filters
    this.el.querySelectorAll('.log-panel__filter-btn').forEach(btn => {
      btn.addEventListener('click', () => this.setFilter(btn.dataset.filter));
    });

    this._renderEntries();
  }

  _renderEntries() {
    const container = this.el.querySelector('#log-entries-container');
    if (!container) return;

    const filtered = this._activeFilter === 'all'
      ? this._entries
      : this._entries.filter(e => e.source === this._activeFilter || e.severity === this._activeFilter);

    const toShow = this._expanded ? filtered : filtered.slice(-this._tickerMax);

    container.innerHTML = toShow.map(entry => {
      const sev = SEVERITY_CONFIG[entry.severity] || SEVERITY_CONFIG.info;
      const timeStr = entry.timestamp.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const nodeRefHtml = entry.nodeRef != null
        ? ` <span class="log-entry__node-ref" data-node-id="${entry.nodeRef}">[Node ${entry.nodeRef}]</span>`
        : '';
      const turnHtml = entry.turn != null ? `<span class="log-entry__turn">T${entry.turn}</span>` : '';

      return `
        <div class="log-entry ${sev.class} ${entry.read ? '' : 'log-entry--unread'}" data-entry-id="${entry.id}">
          <span class="log-entry__severity">${sev.icon}</span>
          ${turnHtml}
          <span class="log-entry__time">${timeStr}</span>
          <span class="log-entry__message">${entry.message}${nodeRefHtml}</span>
        </div>
      `;
    }).join('');

    // Bind clickable node references
    container.querySelectorAll('.log-entry__node-ref').forEach(ref => {
      ref.addEventListener('click', () => {
        const nodeId = parseInt(ref.dataset.nodeId, 10);
        if (!isNaN(nodeId)) {
          events.emit(Events.NODE_SELECT, { nodeId, source: 'log' });
        }
      });
    });

    // Auto-scroll to bottom
    if (this._expanded) {
      container.scrollTop = container.scrollHeight;
    }
  }

  destroy() {
    this.el.remove();
  }
}
