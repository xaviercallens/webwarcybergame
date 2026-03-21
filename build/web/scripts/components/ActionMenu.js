/**
 * ActionMenu component for Neo-Hack v3.2.
 * Contextual action selection with success rates, hotkey badges, CLI preview.
 * Wired into event bus for live game state integration.
 */

import { events, Events } from '../game-events.js';

const ATTACKER_ACTIONS = [
  { id: 0, name: 'SCAN_NETWORK', icon: '\u{1F50D}', description: 'Discover network topology and identify hosts', successRate: 95, cost: 1, cli: 'scan' },
  { id: 1, name: 'EXPLOIT_VULNERABILITY', icon: '\u{1F4A5}', description: 'Compromise a host using known vulnerability', successRate: 70, cost: 2, cli: 'exploit' },
  { id: 2, name: 'PHISHING', icon: '\u{1F3A3}', description: 'Social engineering attack to gain credentials', successRate: 60, cost: 1, cli: 'phish' },
  { id: 3, name: 'INSTALL_MALWARE', icon: '\u{1F41B}', description: 'Install persistent malware on compromised host', successRate: 75, cost: 2, cli: 'malware' },
  { id: 4, name: 'ELEVATE_PRIVILEGES', icon: '\u{2B06}', description: 'Escalate privileges to admin access', successRate: 65, cost: 2, cli: 'elevate' },
  { id: 5, name: 'LATERAL_MOVEMENT', icon: '\u{27A1}', description: 'Move to adjacent network segment', successRate: 80, cost: 1, cli: 'move' },
  { id: 6, name: 'EXFILTRATE_DATA', icon: '\u{1F4E4}', description: 'Steal sensitive data from compromised hosts', successRate: 70, cost: 3, cli: 'exfiltrate' },
  { id: 7, name: 'CLEAR_LOGS', icon: '\u{1F9F9}', description: 'Remove evidence of attack from logs', successRate: 85, cost: 1, cli: 'clearlogs' },
];

const DEFENDER_ACTIONS = [
  { id: 0, name: 'MONITOR_LOGS', icon: '\u{1F4CB}', description: 'Check system logs for suspicious activity', successRate: null, cost: 1, cli: 'monitor' },
  { id: 1, name: 'SCAN_FOR_MALWARE', icon: '\u{1F6E1}', description: 'Scan hosts for malware infections', successRate: null, cost: 1, cli: 'scanmal' },
  { id: 2, name: 'APPLY_PATCH', icon: '\u{1FA79}', description: 'Apply security patches to fix vulnerabilities', successRate: null, cost: 2, cli: 'patch' },
  { id: 3, name: 'ISOLATE_HOST', icon: '\u{1F6AB}', description: 'Quarantine a host from network', successRate: null, cost: 1, cli: 'isolate' },
  { id: 4, name: 'RESTORE_BACKUP', icon: '\u{1F504}', description: 'Restore system from clean backup', successRate: null, cost: 3, cli: 'restore' },
  { id: 5, name: 'FIREWALL_RULE', icon: '\u{1F525}', description: 'Add firewall rule to block connections', successRate: null, cost: 1, cli: 'firewall' },
  { id: 6, name: 'INCIDENT_RESPONSE', icon: '\u{26A1}', description: 'Active countermeasure against ongoing attack', successRate: null, cost: 2, cli: 'respond' },
];

export class ActionMenu {
  constructor(container, onActionSelect) {
    this.container = container;
    this.onActionSelect = onActionSelect;
    this.el = document.createElement('div');
    this.el.id = 'action-menu';
    this.el.className = 'action-menu';
    this.el.setAttribute('role', 'toolbar');
    this.el.setAttribute('aria-label', 'Action panel');
    this.container.appendChild(this.el);
    this._selectedNode = null;
    this._role = 'attacker';
    this._enabled = true;
    this._apRemaining = 1;
    this._gameState = null;

    this._bindEvents();
  }

  _bindEvents() {
    events.on(Events.NODE_SELECT, (data) => {
      this._selectedNode = data.nodeId || data.node?.id || null;
      this._rerender();
    });

    events.on(Events.NODE_DESELECT, () => {
      this._selectedNode = null;
      this._rerender();
    });

    events.on(Events.GAME_STATE, (state) => {
      this._gameState = state;
      this._role = state.role || this._role;
      this._apRemaining = state.actionPointsRemaining ?? 1;
      this._enabled = state.currentPlayer === this._role;
      this._rerender();
    });

    events.on(Events.GAME_START, ({ role }) => {
      this._role = role;
      this._rerender();
    });

    // Hotkey action slots [1]-[7]
    events.on(Events.HOTKEY, ({ action }) => {
      const match = action.match(/^action_(\d+)$/);
      if (!match) return;
      const idx = parseInt(match[1], 10) - 1;
      const actions = this._role === 'attacker' ? ATTACKER_ACTIONS : DEFENDER_ACTIONS;
      if (idx >= 0 && idx < actions.length && this._enabled && this._selectedNode != null) {
        const a = actions[idx];
        if (a.cost <= this._apRemaining) {
          events.emit(Events.ACTION_EXECUTE, {
            actionId: a.id,
            actionName: a.name,
            targetNode: this._selectedNode,
          });
        }
      }
    });
  }

  setSelectedNode(nodeId) {
    this._selectedNode = nodeId;
  }

  _rerender() {
    this.render(this._role, this._enabled);
  }

  render(role, enabled = true) {
    const actions = role === 'attacker' ? ATTACKER_ACTIONS : DEFENDER_ACTIONS;
    const roleClass = role === 'attacker' ? 'action-menu--attacker' : 'action-menu--defender';

    this.el.className = `action-menu ${roleClass}`;
    this.el.innerHTML = `
      <div class="action-menu__header">
        <span class="action-menu__title">AVAILABLE ACTIONS</span>
        ${this._selectedNode !== null ? `<span class="action-menu__target">TARGET: NODE ${this._selectedNode}</span>` : '<span class="action-menu__target">NO TARGET</span>'}
      </div>
      <div class="action-menu__list">
        ${actions.map((a, i) => this._renderActionButton(a, enabled, i)).join('')}
      </div>
      ${!enabled ? '<div style="text-align:center;padding:0.5rem;color:rgba(255,255,255,0.3);font-size:0.7rem;">WAITING FOR OPPONENT</div>' : ''}
    `;

    if (enabled) {
      this.el.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const actionId = parseInt(btn.dataset.actionId, 10);
          const action = actions.find(a => a.id === actionId);
          if (action) {
            if (this.onActionSelect) {
              this.onActionSelect(action, this._selectedNode);
            }
            events.emit(Events.ACTION_EXECUTE, {
              actionId: action.id,
              actionName: action.name,
              targetNode: this._selectedNode,
            });
          }
        });

        // CLI preview on hover
        btn.addEventListener('mouseenter', () => {
          const actionId = parseInt(btn.dataset.actionId, 10);
          const action = actions.find(a => a.id === actionId);
          if (action) {
            events.emit(Events.ACTION_PREVIEW, {
              cliCommand: `${action.cli} ${this._selectedNode || '<target>'}`,
            });
          }
        });
      });
    }
  }

  _renderActionButton(action, enabled, index) {
    const tooExpensive = action.cost > this._apRemaining;
    const noTarget = this._selectedNode == null && action.name !== 'CLEAR_LOGS' && action.name !== 'MONITOR_LOGS';
    const isDisabled = !enabled || tooExpensive || noTarget;
    const disabledAttr = isDisabled ? 'disabled' : '';

    const successRateHtml = action.successRate !== null
      ? `<span class="action-btn__rate">${action.successRate}%</span>`
      : '';

    return `
      <button class="action-btn action-btn--${action.name.toLowerCase()}" 
              data-action-id="${action.id}" 
              title="${action.description}${tooExpensive ? ' (Insufficient AP)' : ''}${noTarget ? ' (Select a target)' : ''}\nCLI: ${action.cli}"
              aria-label="${action.name.replace(/_/g, ' ')} - ${action.description}"
              ${disabledAttr}>
        <span class="action-btn__hotkey">${index + 1}</span>
        <span class="action-btn__icon">${action.icon}</span>
        <span class="action-btn__name">${action.name.replace(/_/g, ' ')}</span>
        ${successRateHtml}
        <span class="action-btn__cost">AP: ${action.cost}</span>
      </button>
    `;
  }

  hide() {
    this.el.style.display = 'none';
  }

  show() {
    this.el.style.display = '';
  }

  destroy() {
    this.el.remove();
  }
}

export { ATTACKER_ACTIONS, DEFENDER_ACTIONS };
