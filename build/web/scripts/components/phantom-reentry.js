/**
 * Neo-Hack: Gridlock v4.1 — Phantom Re-Entry Component
 */
export class PhantomReEntry {
  constructor() {
    this.phantoms = [
      { name: 'NODE-04', status: 'ACTIVE_PHANTOM', turns: 2, color: 'var(--color-accent)' },
      { name: 'NODE-12', status: 'COMPROMISED', turns: 1, color: 'var(--color-scarlet)' },
      { name: 'NODE-08', status: 'ACTIVE_PHANTOM', turns: 4, color: 'var(--color-accent)' },
      { name: 'GATEWAY-B', status: 'SIGNAL_WEAK', turns: 3, color: 'var(--color-amber)' }
    ];
  }

  init() {
    this.renderDormancyTracker();
    const btnRecomp = document.getElementById('btn-recompromise-all');
    if (btnRecomp) btnRecomp.addEventListener('click', () => this.recompromiseAll());
    const btnRapid = document.getElementById('btn-rapid-execute');
    if (btnRapid) btnRapid.addEventListener('click', () => this.addFeedEntry('[RAPID] EXECUTING_ALL_ACTIVE_PHANTOMS...'));
    const btnStealth = document.getElementById('btn-stealth-veil');
    if (btnStealth) btnStealth.addEventListener('click', () => this.addFeedEntry('[STEALTH] VEIL_PROTOCOL_ENGAGED'));
  }

  renderDormancyTracker() {
    const container = document.getElementById('dormancy-tracker-list');
    if (!container) return;
    container.innerHTML = this.phantoms.map(p => `
      <div class="phantom-reentry__node" style="border-left-color:${p.color}">
        <div>
          <div class="phantom-reentry__node-name" style="color:${p.status === 'COMPROMISED' ? 'var(--color-scarlet)' : 'var(--color-text-primary)'}">${p.name}</div>
          <div class="phantom-reentry__node-turns">${p.turns} TURN${p.turns > 1 ? 'S' : ''} REMAINING</div>
        </div>
        <div style="display:flex;align-items:center;gap:0.5rem;">
          <span class="phantom-reentry__node-badge" style="border-color:${p.color};color:${p.color}">${p.status}</span>
          <div style="display:flex;gap:2px;">${'■'.repeat(p.turns).split('').map(() => `<span style="color:${p.color};font-size:0.5rem;">■</span>`).join('')}</div>
        </div>
      </div>
    `).join('');
  }

  recompromiseAll() {
    this.addFeedEntry('[SYS] RE_COMPROMISE_ALL — INITIATING SHADOW HANDSHAKE...');
    this.phantoms.forEach(p => {
      if (p.status !== 'COMPROMISED') {
        this.addFeedEntry(`[TARGET] ${p.name} — BYPASSING_KERNEL_PATCH...`);
      }
    });
    this.addFeedEntry('[SUCCESS] ALL_PHANTOMS_REACTIVATED');
  }

  addFeedEntry(text) {
    const feed = document.getElementById('reentry-feed');
    if (!feed) return;
    const div = document.createElement('div');
    div.style.cssText = 'color:var(--color-accent);font-size:var(--text-xs);';
    div.textContent = `> ${text}`;
    feed.appendChild(div);
    feed.scrollTop = feed.scrollHeight;
  }
}
