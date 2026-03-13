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
          <span>Power Level: <span id="info-power">8</span> TB/s</span>
        </div>
      </div>
    </div>
  `;

  bindGameStateEvents();
}

function bindGameStateEvents() {
  window.addEventListener('gameStateUpdate', (e) => {
    const nodes = e.detail.nodes;
    updateHUD(nodes);
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
}

function updateHUD(nodes) {
  let counts = { PLAYER: 0, ENEMY: 0, ALLY: 0, NEUTRAL: 0 };
  
  nodes.forEach(n => {
    if (counts[n.owner] !== undefined) counts[n.owner]++;
  });

  document.getElementById('hud-count-player').textContent = counts.PLAYER;
  document.getElementById('hud-count-enemy').textContent = counts.ENEMY;
  document.getElementById('hud-count-ally').textContent = counts.ALLY;
  document.getElementById('hud-count-neutral').textContent = counts.NEUTRAL;

  const total = nodes.length;
  const pct = total === 0 ? 0 : Math.round((counts.PLAYER / total) * 100);
  
  document.getElementById('hud-control-pct').textContent = pct;
  document.getElementById('hud-progress-fill').style.width = `${pct}%`;
}

function showInfoPanel(node) {
  const panel = document.getElementById('info-panel');
  panel.style.display = 'block';
  
  document.getElementById('info-name').textContent = node.name;
  document.getElementById('info-owner').textContent = node.owner;
  document.getElementById('info-power').textContent = node.power;
  
  const fwPct = (node.firewall / node.maxFirewall) * 100;
  document.getElementById('info-firewall-text').textContent = `${Math.round(node.firewall)}/${node.maxFirewall}`;
  
  const fill = document.getElementById('info-firewall-fill');
  fill.style.width = `${Math.max(0, fwPct)}%`;
  
  // Update color class
  fill.className = 'progress-fill';
  if (node.owner === 'PLAYER') fill.classList.add('player');
  else if (node.owner === 'ENEMY') fill.classList.add('enemy');
  else if (node.owner === 'ALLY') fill.classList.add('ally');
  else fill.classList.add('neutral');
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
