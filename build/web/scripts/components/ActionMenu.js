/**
 * ActionMenu component for Neo-Hack v3.1.
 * Contextual action selection with success rates and descriptions.
 * Blueprint Alignment: Day 4, Section 2 (User Experience)
 */

const ATTACKER_ACTIONS = [
  { id: 0, name: 'SCAN_NETWORK', icon: '\u{1F50D}', description: 'Discover network topology and identify hosts', successRate: 95, cost: 1 },
  { id: 1, name: 'EXPLOIT_VULNERABILITY', icon: '\u{1F4A5}', description: 'Compromise a host using known vulnerability', successRate: 70, cost: 2 },
  { id: 2, name: 'PHISHING', icon: '\u{1F3A3}', description: 'Social engineering attack to gain credentials', successRate: 60, cost: 1 },
  { id: 3, name: 'INSTALL_MALWARE', icon: '\u{1F41B}', description: 'Install persistent malware on compromised host', successRate: 75, cost: 2 },
  { id: 4, name: 'ELEVATE_PRIVILEGES', icon: '\u{2B06}', description: 'Escalate privileges to admin access', successRate: 65, cost: 2 },
  { id: 5, name: 'LATERAL_MOVEMENT', icon: '\u{27A1}', description: 'Move to adjacent network segment', successRate: 80, cost: 1 },
  { id: 6, name: 'EXFILTRATE_DATA', icon: '\u{1F4E4}', description: 'Steal sensitive data from compromised hosts', successRate: 70, cost: 3 },
  { id: 7, name: 'CLEAR_LOGS', icon: '\u{1F9F9}', description: 'Remove evidence of attack from logs', successRate: 85, cost: 1 },
];

const DEFENDER_ACTIONS = [
  { id: 0, name: 'MONITOR_LOGS', icon: '\u{1F4CB}', description: 'Check system logs for suspicious activity', successRate: null, cost: 1 },
  { id: 1, name: 'SCAN_FOR_MALWARE', icon: '\u{1F6E1}', description: 'Scan hosts for malware infections', successRate: null, cost: 1 },
  { id: 2, name: 'APPLY_PATCH', icon: '\u{1FA79}', description: 'Apply security patches to fix vulnerabilities', successRate: null, cost: 2 },
  { id: 3, name: 'ISOLATE_HOST', icon: '\u{1F6AB}', description: 'Quarantine a host from network', successRate: null, cost: 1 },
  { id: 4, name: 'RESTORE_BACKUP', icon: '\u{1F504}', description: 'Restore system from clean backup', successRate: null, cost: 3 },
  { id: 5, name: 'FIREWALL_RULE', icon: '\u{1F525}', description: 'Add firewall rule to block connections', successRate: null, cost: 1 },
  { id: 6, name: 'INCIDENT_RESPONSE', icon: '\u{26A1}', description: 'Active countermeasure against ongoing attack', successRate: null, cost: 2 },
];

export class ActionMenu {
  constructor(container, onActionSelect) {
    this.container = container;
    this.onActionSelect = onActionSelect;
    this.el = document.createElement('div');
    this.el.id = 'action-menu';
    this.el.className = 'action-menu';
    this.container.appendChild(this.el);
    this._selectedNode = null;
  }

  setSelectedNode(nodeId) {
    this._selectedNode = nodeId;
  }

  render(role, enabled = true) {
    const actions = role === 'attacker' ? ATTACKER_ACTIONS : DEFENDER_ACTIONS;
    const roleClass = role === 'attacker' ? 'action-menu--attacker' : 'action-menu--defender';

    this.el.className = `action-menu ${roleClass}`;
    this.el.innerHTML = `
      <div class="action-menu__header">
        <span class="action-menu__title">AVAILABLE ACTIONS</span>
        ${this._selectedNode !== null ? `<span class="action-menu__target">TARGET: NODE ${this._selectedNode}</span>` : ''}
      </div>
      <div class="action-menu__list">
        ${actions.map(a => this._renderActionButton(a, enabled)).join('')}
      </div>
    `;

    if (enabled) {
      this.el.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const actionId = parseInt(btn.dataset.actionId, 10);
          const action = actions.find(a => a.id === actionId);
          if (action && this.onActionSelect) {
            this.onActionSelect(action, this._selectedNode);
          }
        });
      });
    }
  }

  _renderActionButton(action, enabled) {
    const disabledAttr = enabled ? '' : 'disabled';
    const successRateHtml = action.successRate !== null
      ? `<span class="action-btn__rate">${action.successRate}%</span>`
      : '';

    return `
      <button class="action-btn action-btn--${action.name.toLowerCase()}" 
              data-action-id="${action.id}" 
              title="${action.description}"
              ${disabledAttr}>
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
