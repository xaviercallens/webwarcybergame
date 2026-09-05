/**
 * Neo-Hack: Gridlock v3.2 — Help Overlay
 * Tabbed help screen: Controls, CLI Commands, UI Guide, Icons Legend. Searchable.
 */

import { events, Events } from '../game-events.js';
import { getCommandsForRole } from '../cli/command-parser.js';

const TABS = ['controls', 'cli', 'ui', 'icons'];

export class HelpOverlay {
  constructor(hotkeyManager) {
    this._hotkeyManager = hotkeyManager;
    this.el = document.createElement('div');
    this.el.id = 'help-overlay';
    this.el.className = 'help-overlay';
    this.el.setAttribute('role', 'dialog');
    this.el.setAttribute('aria-label', 'Help & Reference');
    this.el.style.display = 'none';
    document.body.appendChild(this.el);

    this._activeTab = 'controls';
    this._searchQuery = '';
    this._role = 'attacker';
    this._isOpen = false;

    events.on(Events.GAME_START, ({ role }) => { this._role = role; });
  }

  get isOpen() { return this._isOpen; }

  show() {
    this._isOpen = true;
    this._render();
    this.el.style.display = 'flex';
  }

  hide() {
    this._isOpen = false;
    this.el.style.display = 'none';
  }

  toggle() {
    if (this._isOpen) this.hide(); else this.show();
  }

  _render() {
    this.el.innerHTML = `
      <div class="help-overlay__backdrop"></div>
      <div class="help-overlay__panel">
        <div class="help-overlay__header">
          <h2>OPERATOR MANUAL</h2>
          <div class="help-overlay__search">
            <input type="text" id="help-search" placeholder="Search..." 
                   value="${this._searchQuery}" autocomplete="off" />
          </div>
          <button class="help-overlay__close" id="btn-help-close" aria-label="Close help overlay">×</button>
        </div>
        <div class="help-overlay__tabs">
          ${TABS.map(t => `
            <button class="help-overlay__tab ${this._activeTab === t ? 'help-overlay__tab--active' : ''}"
                    data-tab="${t}">${t.toUpperCase()}</button>
          `).join('')}
        </div>
        <div class="help-overlay__body">
          ${this._renderTabContent()}
        </div>
      </div>
    `;

    // Bind events
    this.el.querySelector('#btn-help-close').addEventListener('click', () => this.hide());
    this.el.querySelectorAll('.help-overlay__tab').forEach(btn => {
      btn.addEventListener('click', () => {
        this._activeTab = btn.dataset.tab;
        this._render();
      });
    });
    const searchInput = this.el.querySelector('#help-search');
    searchInput.addEventListener('input', (e) => {
      this._searchQuery = e.target.value.toLowerCase();
      this._render();
      // Restore focus to search
      this.el.querySelector('#help-search')?.focus();
    });

    // Escape to close
    this.el.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { e.preventDefault(); this.hide(); }
    });
  }

  _renderTabContent() {
    switch (this._activeTab) {
      case 'controls': return this._renderControls();
      case 'cli':      return this._renderCLI();
      case 'ui':       return this._renderUI();
      case 'icons':    return this._renderIcons();
      default:         return '';
    }
  }

  _renderControls() {
    const bindings = this._hotkeyManager ? this._hotkeyManager.getBindings() : {};
    const rows = Object.entries(bindings)
      .filter(([key, val]) => {
        if (!this._searchQuery) return true;
        return key.toLowerCase().includes(this._searchQuery) ||
               val.action.toLowerCase().includes(this._searchQuery) ||
               val.description.toLowerCase().includes(this._searchQuery);
      })
      .map(([key, val]) => `
        <tr>
          <td class="help-key"><kbd>${this._displayKey(key)}</kbd></td>
          <td>${val.description}</td>
        </tr>
      `).join('');

    return `
      <h3>KEYBOARD SHORTCUTS</h3>
      <table class="help-table">
        <tr><th>Key</th><th>Action</th></tr>
        ${rows}
      </table>
      <h3 style="margin-top:1rem">MOUSE</h3>
      <table class="help-table">
        <tr><td>Left Click</td><td>Select node</td></tr>
        <tr><td>Right Click</td><td>Context menu on node</td></tr>
        <tr><td>Scroll Wheel</td><td>Zoom map</td></tr>
        <tr><td>Click + Drag</td><td>Pan map</td></tr>
      </table>
      <h3 style="margin-top:1rem">GAMEPAD</h3>
      <table class="help-table">
        <tr><td>Left Stick / D-Pad</td><td>Navigate nodes</td></tr>
        <tr><td>A / ×</td><td>Select / Confirm</td></tr>
        <tr><td>B / ○</td><td>Cancel / Back</td></tr>
        <tr><td>X / □</td><td>Open action menu</td></tr>
        <tr><td>Y / △</td><td>Toggle log panel</td></tr>
        <tr><td>LB / RB</td><td>Cycle actions</td></tr>
        <tr><td>LT / RT</td><td>Zoom in / out</td></tr>
        <tr><td>Start</td><td>Pause menu</td></tr>
        <tr><td>Select</td><td>Toggle CLI</td></tr>
      </table>
    `;
  }

  _renderCLI() {
    const cmds = getCommandsForRole(this._role);
    const filtered = cmds.filter(c => {
      if (!this._searchQuery) return true;
      return c.name.includes(this._searchQuery) ||
             c.description.toLowerCase().includes(this._searchQuery) ||
             (c.action || '').toLowerCase().includes(this._searchQuery);
    });

    const rows = filtered.map(c => {
      const aliases = c.aliases ? c.aliases.join(', ') : '—';
      const target = c.requiresTarget ? '&lt;target&gt;' : '';
      const flags = c.flags ? c.flags.join(' ') : '';
      return `
        <tr>
          <td class="help-cmd">${c.name} ${target} ${flags}</td>
          <td>${aliases}</td>
          <td>${c.description}</td>
        </tr>
      `;
    }).join('');

    return `
      <h3>CLI COMMANDS (${this._role.toUpperCase()})</h3>
      <p style="color:var(--color-text-muted);margin-bottom:1rem">
        Open console with <kbd>\`</kbd> or <kbd>/</kbd>. Tab to auto-complete. ↑↓ for history.
      </p>
      <table class="help-table">
        <tr><th>Command</th><th>Aliases</th><th>Description</th></tr>
        ${rows}
      </table>
    `;
  }

  _renderUI() {
    return `
      <h3>USER INTERFACE GUIDE</h3>
      <div class="help-section">
        <h4>HUD (Heads-Up Display)</h4>
        <p>Top of screen: Turn counter, current player, action points remaining, resource meters.</p>
      </div>
      <div class="help-section">
        <h4>Network Map</h4>
        <p>Central area showing all network nodes. Click to select. Right-click for context menu. 
        Use WASD/arrows to navigate between nodes via keyboard.</p>
      </div>
      <div class="help-section">
        <h4>Action Panel</h4>
        <p>Right side: shows available actions for the selected node. Each action has a hotkey [1-7], 
        cost in AP, and success probability (attacker only).</p>
      </div>
      <div class="help-section">
        <h4>Intel Feed / Log Panel</h4>
        <p>Bottom: shows recent game events. Press L to expand. Filter by type. Click node references 
        to focus the map.</p>
      </div>
      <div class="help-section">
        <h4>Mission Panel</h4>
        <p>Press M to view objectives for both roles. Completed objectives are checked.</p>
      </div>
    `;
  }

  _renderIcons() {
    const icons = [
      ['🔴', 'Compromised node (attacker owns)'],
      ['🔒', 'Secured / Patched node'],
      ['⚠️', 'Suspicious activity detected'],
      ['🔍', 'Discovered (scanned) node'],
      ['░░', 'Undiscovered (fog of war)'],
      ['⛔', 'Compromised & detected by defender'],
      ['🔴', 'Attacker role / attacker turn'],
      ['🔵', 'Defender role / defender turn'],
      ['✓', 'Action succeeded'],
      ['✗', 'Action failed'],
      ['⚠', 'Alert / detection warning'],
      ['📋', 'Intel feed / log panel'],
    ];

    const filtered = icons.filter(([icon, desc]) => {
      if (!this._searchQuery) return true;
      return desc.toLowerCase().includes(this._searchQuery);
    });

    return `
      <h3>ICON LEGEND</h3>
      <table class="help-table">
        <tr><th>Icon</th><th>Meaning</th></tr>
        ${filtered.map(([icon, desc]) => `<tr><td style="font-size:1.5rem;text-align:center">${icon}</td><td>${desc}</td></tr>`).join('')}
      </table>
    `;
  }

  _displayKey(key) {
    const map = {
      ' ': 'Space', 'ArrowUp': '↑', 'ArrowDown': '↓',
      'ArrowLeft': '←', 'ArrowRight': '→', 'Escape': 'Esc',
    };
    return map[key] || key;
  }

  destroy() {
    this.el.remove();
  }
}
