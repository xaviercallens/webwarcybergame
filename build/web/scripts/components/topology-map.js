/**
 * Neo-Hack: Gridlock v4.1 — Mesh Topology Global Map Component
 */
export class TopologyMap {
  constructor() {
    this.nodes = [
      { name: 'PHANTOM_NODE_01', lat: 55, lng: -30, type: 'phantom', alert: 'MALICIOUS_DETECTION' },
      { name: 'STABLE_RELAY_B', lat: 30, lng: 10, type: 'stable' },
      { name: 'STABLE_RELAY_F', lat: -10, lng: -20, type: 'stable' },
      { name: 'GHOST_ENTRY_RED', lat: 25, lng: 55, type: 'ghost' },
      { name: 'COMMAND_ALPHA', lat: 40, lng: -74, type: 'command' }
    ];
  }

  init() {
    this.renderNodeList();
    const btnRefresh = document.getElementById('btn-topo-refresh');
    if (btnRefresh) btnRefresh.addEventListener('click', () => this.refreshData());
  }

  renderNodeList() {
    const container = document.getElementById('topo-node-overlay');
    if (!container) return;
    // Render as labeled dots on the map area
    container.innerHTML = this.nodes.map(n => {
      const color = n.type === 'ghost' ? 'var(--color-scarlet)' : 
                    n.type === 'phantom' ? 'var(--color-accent)' : 
                    n.type === 'command' ? 'var(--color-stable)' : 'var(--color-accent)';
      const top = 50 - (n.lat / 90 * 40);
      const left = 50 + (n.lng / 180 * 45);
      return `<div class="topo-node" style="top:${top}%;left:${left}%;color:${color};">
        <span class="topo-node__dot" style="background:${color};"></span>
        <span class="topo-node__label">${n.name}</span>
      </div>`;
    }).join('');
  }

  refreshData() {
    const heatmapPanel = document.getElementById('topo-heatmap-density');
    if (heatmapPanel) heatmapPanel.textContent = 'REFRESHING...';
    setTimeout(() => {
      if (heatmapPanel) heatmapPanel.textContent = 'HIGH_VOL_DETECTED';
    }, 1000);
  }
}
