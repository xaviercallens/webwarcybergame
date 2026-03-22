/**
 * Neo-Hack: Gridlock v4.1 — Ghost Node Deployment Component
 * Manages decoy ghost node placement and monitoring
 */

export class GhostDeploy {
  constructor() {
    this.deceptionBudget = 7;
    this.maxBudget = 10;
    this.ghostNodes = [];
    this.deployLog = [];
  }

  deployGhost(nodeId, position) {
    if (this.deceptionBudget <= 0) {
      this._addLog('DEPLOY_FAILED: BUDGET_EXHAUSTED', 'red');
      return false;
    }

    const ghost = {
      id: `GHOST_${Date.now().toString(36).toUpperCase()}`,
      targetNode: nodeId,
      position,
      deployedAt: Date.now(),
      status: 'active',
      trapsTriggered: 0,
    };

    this.ghostNodes.push(ghost);
    this.deceptionBudget--;

    this._addLog(`GHOST_DEPLOYED: ${ghost.id} → ${nodeId}`, 'green');
    this._addLog(`BUDGET_REMAINING: ${this.deceptionBudget}/${this.maxBudget}`, 'cyan');
    this._updateBudgetDisplay();

    window.dispatchEvent(new CustomEvent('ghostDeployed', { detail: ghost }));
    return true;
  }

  triggerTrap(ghostId) {
    const ghost = this.ghostNodes.find(g => g.id === ghostId);
    if (!ghost) return;

    ghost.trapsTriggered++;
    ghost.status = 'triggered';

    this._addLog(`TRAP_TRIGGERED: ${ghostId} — TARGET_ENGAGED`, 'red');
    window.dispatchEvent(new CustomEvent('ghostTriggered', { detail: ghost }));
  }

  _addLog(text, dotColor = 'cyan') {
    this.deployLog.push({ text, dotColor, time: new Date().toISOString().slice(11, 19) });
    this._renderLog();
  }

  _renderLog() {
    const container = document.querySelector('.ghost-deploy__log');
    if (!container) return;

    const entries = this.deployLog.slice(-10).map(entry =>
      `<div class="ghost-deploy__log-entry">
        <span class="dot ${entry.dotColor}"></span>
        <span class="time">[${entry.time}]</span>
        <span class="text">${entry.text}</span>
      </div>`
    ).join('');

    const logBody = container.querySelector('.ghost-deploy__log-entries') || container;
    logBody.innerHTML = entries;
  }

  _updateBudgetDisplay() {
    const budgetVal = document.querySelector('.ghost-deploy__budget .value');
    if (budgetVal) budgetVal.textContent = `${this.deceptionBudget}/${this.maxBudget}`;

    const bars = document.querySelectorAll('.ghost-deploy__budget .bar-segment');
    bars.forEach((bar, i) => {
      bar.classList.toggle('empty', i >= this.deceptionBudget);
    });
  }

  getActiveGhosts() {
    return this.ghostNodes.filter(g => g.status === 'active');
  }

  destroy() {
    this.ghostNodes = [];
    this.deployLog = [];
  }
}
