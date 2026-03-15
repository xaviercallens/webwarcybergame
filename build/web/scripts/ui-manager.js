/**
 * Neo-Hack: Gridlock — UI Manager
 * Handles HUD injections and Game UI logic
 */

import { audio } from './audio-manager.js';

export function initUI() {
  const hudLayer = document.getElementById('hud-layer');
  if (!hudLayer) return;

  // Initial HUD template
  hudLayer.innerHTML = `
    <!-- Top Left HUD: Faction Stats & Control Progress -->
    <div id="hud-stats-panel" class="panel" style="position: absolute; top: 1rem; left: 1rem; width: 400px; pointer-events: auto;">
      <div style="font-family: var(--font-hud); color: var(--color-text-muted); margin-bottom: 0.5rem; text-transform: uppercase;">
        [SYS] <span style="color:var(--color-player)">Player: <span id="hud-count-player">0</span></span> | 
        <span style="color:var(--color-enemy)">Enemy: <span id="hud-count-enemy">0</span></span> | 
        <span style="color:var(--color-ally)">Ally: <span id="hud-count-ally">0</span></span> | 
        <span style="color:var(--color-neutral)">Neutral: <span id="hud-count-neutral">0</span></span>
      </div>
      <div style="display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 0.8rem; margin-bottom: 0.25rem;">
        <span>// Global Override: <span id="hud-control-pct">0</span>%</span>
        <span style="color:var(--color-accent)">Target: 75%</span>
      </div>
      <div class="progress-track" style="margin-bottom: 0;">
        <div id="hud-progress-fill" class="progress-fill player" style="width: 0%; transition: width 0.3s ease;"></div>
      </div>
      <div style="margin-top: 1rem; padding-top: 0.5rem; border-top: 1px dashed var(--color-accent); font-family: var(--font-mono); font-size: 0.8rem; display: flex; justify-content: space-between;">
        <span id="hud-epoch">EPOCH: --</span>
        <span id="hud-phase" style="color:var(--color-warning)">PHASE: --</span>
        <span id="hud-timer">00:00</span>
      </div>
    </div>
    
    <!-- Top Center: Toast Notifications -->
    <div id="toast-container" style="position: absolute; top: 1rem; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; gap: 0.5rem; pointer-events: none; z-index: 100;">
    </div>
    
    <!-- Right Panel: Node Info (Hidden by default) -->
    <div id="info-panel" class="panel" style="position: absolute; top: 1rem; right: 8rem; width: 300px; display: none; pointer-events: auto;">
      <div class="panel-header">
        <span id="info-name">SYS-00</span>
        <span id="info-owner" style="font-size: 0.8rem;">NEUTRAL</span>
      </div>
      <div style="margin-top:1rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
          <span>Firewall</span>
          <span id="info-firewall-text">100/100</span>
        </div>
        <div class="progress-track">
          <div id="info-firewall-fill" class="progress-fill neutral" style="width: 100%;"></div>
        </div>
        <div style="margin-top: 1rem;">
          <span>Compute Output: <span id="info-power">8</span> TB/s</span>
        </div>
        
        <div id="action-panel" style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--color-accent); display: none;">
          <div style="margin-bottom: 0.5rem; font-size: 0.8rem; color: var(--color-accent);">[ AVAILABLE ACTIONS ]</div>
          <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <button id="btn-action-breach" class="btn btn-primary" style="flex:1; padding: 0.25rem;">BREACH</button>
            <button id="btn-action-scan" class="btn" style="flex:1; padding: 0.25rem;">SCAN</button>
          </div>
          <div style="margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem; font-size:0.8rem;">
            <span>Commit CU:</span>
            <input type="range" id="input-cu" min="1" max="100" value="10" style="flex:1;">
            <span id="text-cu">10</span>
          </div>
        </div>
      </div>
    </div>
  `;

  // Bind Game State Events
  window.addEventListener('gameStateUpdate', (e) => {
    const nodes = e.detail.nodes;
    const epoch = e.detail.epoch;
    updateHUD(nodes, epoch);
  });
  
  window.addEventListener('nodeSelected', (e) => {
    const node = e.detail.node;
    if (node) {
      showInfoPanel(node);
    } else {
      hideInfoPanel();
    }
  });

  window.addEventListener('toast', (e) => {
    showToast(e.detail.message, e.detail.type);
  });
  
  // HUD Update loop for the timer
  setInterval(updateTimer, 1000);
  
  // Bind Action Panel Buttons
  document.getElementById('input-cu').addEventListener('input', (e) => {
      document.getElementById('text-cu').textContent = e.target.value;
  });
  
  document.getElementById('btn-action-breach').addEventListener('click', () => {
      const cu = document.getElementById('input-cu').value;
      if (window.GameInstance) window.GameInstance.submitPlayerAction('BREACH', cu);
  });
  
  document.getElementById('btn-action-scan').addEventListener('click', () => {
      const cu = document.getElementById('input-cu').value;
      if (window.GameInstance) window.GameInstance.submitPlayerAction('SCAN', cu);
  });
}

let currentEpochEnd = null;

function updateTimer() {
  if (!currentEpochEnd) return;
  const now = new Date().getTime();
  const end = new Date(currentEpochEnd + "Z").getTime(); // Ensure UTC
  let diff = Math.floor((end - now) / 1000);
  
  if (diff < 0) diff = 0;
  
  const m = Math.floor(diff / 60);
  const s = diff % 60;
  
  const timerEl = document.getElementById('hud-timer');
  if (timerEl) {
    timerEl.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    if (diff <= 10) timerEl.style.color = 'var(--color-enemy)';
    else timerEl.style.color = '#fff';
  }
}

function updateHUD(nodes, epoch) {
  let counts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  
  nodes.forEach(n => {
    if (counts[n.faction_id] !== undefined) counts[n.faction_id]++;
  });

  document.getElementById('hud-count-player').textContent = counts[1];
  document.getElementById('hud-count-enemy').textContent = counts[2] + counts[3]; // Approx enemies
  document.getElementById('hud-count-ally').textContent = counts[4];
  document.getElementById('hud-count-neutral').textContent = counts[5];

  const total = nodes.length;
  const pct = total === 0 ? 0 : Math.round((counts[1] || 0) / total * 100); // Faction 1 = Player for testing
  
  document.getElementById('hud-control-pct').textContent = pct;
  document.getElementById('hud-progress-fill').style.width = `${pct}%`;
  
  if (epoch) {
      document.getElementById('hud-epoch').textContent = `EPOCH: ${epoch.number}`;
      document.getElementById('hud-phase').textContent = `PHASE: ${epoch.phase}`;
      
      const phaseEl = document.getElementById('hud-phase');
      if (epoch.phase === 'PLANNING') phaseEl.style.color = 'var(--color-player)';
      else if (epoch.phase === 'SIMULATION') phaseEl.style.color = 'var(--color-warning)';
      else phaseEl.style.color = 'var(--color-enemy)';
      
      currentEpochEnd = epoch.ended_at;
  }
}

function showInfoPanel(node) {
  const panel = document.getElementById('info-panel');
  panel.style.display = 'block';
  
  document.getElementById('info-name').textContent = node.name;
  
  let ownerStr = "NEUTRAL";
  if (node.faction_id === 1) ownerStr = "SILICON VALLEY BLOC";
  else if (node.faction_id === 2) ownerStr = "IRON GRID";
  else if (node.faction_id === 3) ownerStr = "SILK ROAD COALITION";
  else if (node.faction_id === 4) ownerStr = "EURO NEXUS";
  else if (node.faction_id === 5) ownerStr = "PACIFIC VANGUARD";
  
  document.getElementById('info-owner').textContent = ownerStr;
  document.getElementById('info-power').textContent = node.power;
  
  const fwPct = (node.firewall / node.maxFirewall) * 100;
  document.getElementById('info-firewall-text').textContent = `${Math.round(node.firewall)}/${node.maxFirewall}`;
  
  const fill = document.getElementById('info-firewall-fill');
  fill.style.width = `${Math.max(0, fwPct)}%`;
  
  // Update color class
  fill.className = 'progress-fill';
  
  // TODO: Use true player faction check
  if (node.faction_id === 1) fill.classList.add('player');
  else if (node.faction_id === 2) fill.classList.add('enemy');
  else if (node.faction_id === 3) fill.classList.add('enemy');
  else if (node.faction_id === 4) fill.classList.add('ally');
  else fill.classList.add('neutral');
  
  const actionPanel = document.getElementById('action-panel');
  if (node.faction_id !== 1 && window.GameInstance?.currentEpoch?.phase === 'PLANNING') {
      actionPanel.style.display = 'block';
  } else {
      actionPanel.style.display = 'none';
  }
}

function hideInfoPanel() {
  document.getElementById('info-panel').style.display = 'none';
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'panel toast';
  
  let borderColor = 'var(--color-accent)';
  if (type === 'capture') borderColor = 'var(--color-player)';
  if (type === 'lost') borderColor = 'var(--color-enemy)';
  
  toast.style.borderLeft = `4px solid ${borderColor}`;
  toast.style.padding = '0.5rem 1rem';
  toast.style.animation = 'glitch-anim-1 0.2s linear';
  toast.style.background = 'rgba(10, 14, 23, 0.9)';
  toast.style.backdropFilter = 'blur(4px)';
  toast.innerText = message;

  container.appendChild(toast);
  
  audio.playToast();

  // Auto remove
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
  
  // Enforce max 4 toasts
  while (container.children.length > 4) {
    container.removeChild(container.firstChild);
  }
}
