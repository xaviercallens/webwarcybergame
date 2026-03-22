/**
 * Neo-Hack: Gridlock v4.1 — Factions Overview Component
 */
export class FactionsOverview {
  constructor() {
    this.factions = [
      { id: 1, name: 'SILICON VALLEY', leader: 'THE ARCHITECT', affiliation: 'GRID_CORE', status: 'NO ACCORD', statusColor: 'var(--color-accent)', agg: 78, stl: 92, per: 65, eff: 88, affinity: 42,
        dossier: "The Silicon Valley collective, led by the enigmatic 'Architect', seeks total digital hegemony through the implementation of a decentralized neural lattice." },
      { id: 2, name: 'IRON GRID', leader: 'GENERAL VOLKOV', affiliation: 'MILITARY_OPS', status: 'HOSTILE', statusColor: 'var(--color-scarlet)', agg: 95, stl: 30, per: 88, eff: 72, affinity: 12,
        dossier: "A militarized cyber-state governed by General Volkov. They favor brute-force intrusion and maintain the largest standing botnet in the digital theatre." },
      { id: 3, name: 'SILK ROAD COALITION', leader: 'CHAIRMAN WEI', affiliation: 'TRADE_NET', status: 'ACTIVE', statusColor: 'var(--color-amber)', agg: 45, stl: 80, per: 70, eff: 90, affinity: 65,
        dossier: "A decentralized trade consortium that prefers subtle manipulation of market protocols and high-frequency trading disruptions over direct confrontation." },
      { id: 4, name: 'EURO NEXUS', leader: 'DIRECTOR VANCE', affiliation: 'INFRA_CORE', status: 'NEUTRAL', statusColor: 'var(--color-text-muted)', agg: 55, stl: 70, per: 80, eff: 85, affinity: 50,
        dossier: "A consortium of European cyber-defense agencies focused on infrastructure protection. They maintain strict neutrality but can be swayed by strategic alliances." }
    ];
    this.selectedFaction = null;
  }

  init() {
    this.selectedFaction = this.factions[0];
    this.renderFactionList();
    this.renderFactionDetail(this.selectedFaction);

    document.querySelectorAll('.factions__card').forEach(card => {
      card.addEventListener('click', () => {
        const fid = parseInt(card.dataset.fid);
        const f = this.factions.find(f => f.id === fid);
        if (f) {
          this.selectedFaction = f;
          this.renderFactionDetail(f);
          document.querySelectorAll('.factions__card').forEach(c => c.classList.remove('active'));
          card.classList.add('active');
        }
      });
    });
  }

  renderFactionList() {
    const list = document.getElementById('faction-list');
    if (!list) return;
    list.innerHTML = this.factions.map(f => `
      <div class="factions__card ${f.id === 1 ? 'active' : ''}" data-fid="${f.id}" style="border-left-color: ${f.statusColor}">
        <div class="factions__card-portrait">👤</div>
        <div>
          <div class="factions__card-name">${f.name}</div>
          <div class="factions__card-leader">${f.leader}</div>
          <div class="factions__card-status" style="color:${f.statusColor}">● STATUS: ${f.status}</div>
        </div>
      </div>
    `).join('');
  }

  renderFactionDetail(f) {
    const el = document.getElementById('faction-detail');
    if (!el || !f) return;
    el.innerHTML = `
      <div class="factions__detail-header">
        <h1 style="font-family:var(--font-title);font-size:var(--text-3xl);margin:0;">${f.name}</h1>
        <div style="text-align:right;">
          <div style="font-size:var(--text-xs);color:var(--color-text-muted);">CURRENT_STATUS</div>
          <div style="color:${f.statusColor};font-family:var(--font-title);font-size:var(--text-xl);">${f.status}</div>
        </div>
      </div>
      <div style="margin-bottom:0.5rem;">
        <span style="background:var(--color-accent);color:var(--bg-color);padding:0.2rem 0.5rem;font-size:var(--text-xs);font-weight:bold;">LEADER: ${f.leader}</span>
        <span style="color:var(--color-accent);margin-left:1rem;font-size:var(--text-sm);">AFFILIATION: ${f.affiliation}</span>
      </div>
      <div style="display:flex;gap:2rem;margin-top:1.5rem;">
        <div style="flex:1;">
          <h3 style="color:var(--color-accent);font-size:var(--text-sm);letter-spacing:2px;">🔒 STRATEGIC_DOSSIER</h3>
          <p style="color:var(--color-text-primary);font-family:var(--font-body);line-height:1.6;margin-top:0.5rem;">${f.dossier}</p>
          <div style="margin-top:1.5rem;">
            <div style="display:flex;justify-content:space-between;margin-bottom:0.25rem;">
              <span style="color:var(--color-accent);font-size:var(--text-xs);">AFFINITY_MATRIX</span>
              <span style="color:var(--color-text-primary);">${f.affinity}%</span>
            </div>
            <div class="progress-track"><div class="progress-fill" style="width:${f.affinity}%"></div></div>
          </div>
        </div>
        <div style="flex:1;">
          <h3 style="color:var(--color-accent);font-size:var(--text-sm);letter-spacing:2px;">📊 COMBAT_CAPABILITY</h3>
          <div style="display:flex;gap:1.5rem;margin-top:1rem;justify-content:center;">
            <div style="text-align:center;"><div style="font-size:var(--text-xs);color:var(--color-text-muted);">AGG</div><div style="font-size:var(--text-xl);color:var(--color-accent);">${f.agg}</div></div>
            <div style="text-align:center;"><div style="font-size:var(--text-xs);color:var(--color-text-muted);">STL</div><div style="font-size:var(--text-xl);color:var(--color-accent);">${f.stl}</div></div>
            <div style="text-align:center;"><div style="font-size:var(--text-xs);color:var(--color-text-muted);">PER</div><div style="font-size:var(--text-xl);color:var(--color-accent);">${f.per}</div></div>
            <div style="text-align:center;"><div style="font-size:var(--text-xs);color:var(--color-text-muted);">EFF</div><div style="font-size:var(--text-xl);color:var(--color-accent);">${f.eff}</div></div>
          </div>
        </div>
      </div>
      <div style="border-top:1px solid rgba(0,255,221,0.15);margin-top:2rem;padding-top:1.5rem;">
        <h3 style="font-family:var(--font-heading);color:var(--color-text-primary);letter-spacing:2px;margin-bottom:1rem;">DIPLOMACY_TERMINAL_V.01</h3>
        <div style="display:flex;gap:1rem;justify-content:flex-end;">
          <button class="btn" style="border-color:var(--color-accent);">◈ PROPOSE CEASEFIRE</button>
          <button class="btn" style="border-color:var(--color-accent);">₿ OFFER TRADE</button>
          <button class="btn btn-danger">▲ THREATEN</button>
        </div>
      </div>
    `;
  }
}
