/**
 * Neo-Hack: Gridlock — UI Manager
 * Handles HUD injections and Game UI logic
 */

import { api } from './api-client.js';
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
          
          <div style="margin-top: 0.5rem; display: flex;">
            <button id="btn-action-diplomacy" class="btn" style="flex: 1; padding: 0.35rem; border-color: var(--color-enemy); color: var(--color-enemy);">CONTACT AMBASSADOR</button>
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
  
  // Real-time WebSocket handlers
  window.addEventListener('wsMessage', (e) => {
      const msg = e.detail;
      
      if (msg.type === 'EPOCH_PHASE_CHANGE') {
          const el = document.getElementById('hud-phase');
          if (el) {
              el.textContent = `PHASE: ${msg.phase}`;
              if(msg.phase === 'PLANNING') el.style.color = "var(--color-player)";
              else if(msg.phase === 'SIM') el.style.color = "var(--color-primary)";
              else el.style.color = "var(--color-warning)";
          }
          // Refresh world state entirely on phase change
          if (window.GameInstance) window.GameInstance.fetchWorldState();
      }
      
      if (msg.type === 'NODE_CAPTURED') {
          showToast(`[INTEL] ${msg.message}`, 'warning');
          if (window.GameInstance) window.GameInstance.fetchWorldState();
      }
      
      if (msg.type === 'TREATY_BROKEN') {
          showToast(`[INTEL] A Diplomatic Accord has been BROKEN!`, 'error');
          audio.playAlarm();
      }
      
      if (msg.type === 'NOTIFICATION') {
          showToast(msg.message, msg.severity || 'info');
      }
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
  
  // Diplomacy action binding
  const dipBtn = document.getElementById('btn-action-diplomacy');
  if(dipBtn) {
    dipBtn.addEventListener('click', () => {
      // Find currently selected node in GameInstance
      if (window.GameInstance && window.GameInstance.selectedNodeId) {
        const node = window.GameInstance.nodes.find(n => n.id === window.GameInstance.selectedNodeId);
        if(node && node.faction_id && node.faction_id !== 1) {
          openDiplomacyPanel(node.faction_id);
        }
      }
    });
  }
  
  // Sentinel Lab action binding
  const labBtn = document.getElementById('btn-lab');
  if (labBtn) {
    labBtn.addEventListener('click', openSentinelLab);
  }
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
      
      const dipBtn = document.getElementById('btn-action-diplomacy');
      if (dipBtn) {
        // Only allow diplomacy with major AI factions (2,3,4,5), not neutrals (0)
        if (node.faction_id > 1) {
           dipBtn.style.display = 'block';
        } else {
           dipBtn.style.display = 'none';
        }
      }
      
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

// --- SPRINT 3.5: DIPLOMACY UI & EMOTION PARSER ---

let currentDiplomacyTarget = null;
let isDiplomacyLoading = false;

export function initDiplomacyEvents() {
  const modal = document.getElementById('modal-diplomacy');
  const closeBtn = document.getElementById('btn-close-diplomacy');
  const chatInput = document.getElementById('dip-chat-input');
  const sendBtn = document.getElementById('btn-dip-send');
  const proposeBtn = document.getElementById('btn-dip-propose');
  const breakBtn = document.getElementById('btn-dip-break');
  
  if (!modal) return;

  closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
    modal.classList.remove('active');
    audio.playClick();
  });

  // Contact Selection Binding
  document.querySelectorAll('.btn-dip-contact').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const fid = parseInt(e.currentTarget.getAttribute('data-fid'));
      openDiplomacyPanel(fid);
    });
  });

  // Chat Submission
  const submitChat = async () => {
    if (isDiplomacyLoading || !currentDiplomacyTarget || !chatInput.value.trim()) return;
    
    const msg = chatInput.value.trim();
    chatInput.value = '';
    appendChatMessage('OPERATIVE', msg, 'var(--color-player)');
    
    isDiplomacyLoading = true;
    chatInput.disabled = true;
    sendBtn.disabled = true;
    
    try {
      const response = await api.sendDiplomacyChat(currentDiplomacyTarget, msg);
      // Parse Emotion Tags for Advanced Accessibility
      parseAndAppendAIResponse(response.reply);
      audio.playToast();
    } catch (e) {
      appendChatMessage('SYS', 'Connection severed.', 'var(--color-enemy)');
    } finally {
      isDiplomacyLoading = false;
      chatInput.disabled = false;
      sendBtn.disabled = false;
      chatInput.focus();
    }
  };

  sendBtn.addEventListener('click', submitChat);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') submitChat();
  });

  // Treaties
  proposeBtn.addEventListener('click', async () => {
    if (isDiplomacyLoading || !currentDiplomacyTarget) return;
    const type = document.getElementById('dip-treaty-type').value;
    const proposalText = "I propose a formal " + type + " treaty to ensure mutual benefits.";
    
    appendChatMessage('OPERATIVE', '[PROPOSAL SENT: ' + type + ']', 'var(--color-warning)');
    
    isDiplomacyLoading = true;
    try {
      const response = await api.proposeTreaty(currentDiplomacyTarget, type, proposalText);
      if (response && response.status === 'accepted') {
          appendChatMessage('AMBASSADOR', '[PROPOSAL ACCEPTED]', 'var(--color-player)');
          document.getElementById('dip-status-badge').textContent = type + ' (ACTIVE)';
          document.getElementById('dip-status-badge').style.color = 'var(--color-player)';
          document.getElementById('dip-status-badge').style.borderColor = 'var(--color-player)';
          audio.playCapture();
      } else {
          appendChatMessage('AMBASSADOR', '[PROPOSAL REJECTED]', 'var(--color-enemy)');
          audio.playError();
      }
    } catch (e) {
      appendChatMessage('SYS', 'Neural handshake failed.', 'var(--color-enemy)');
    } finally {
      isDiplomacyLoading = false;
    }
  });
}

function parseAndAppendAIResponse(rawText) {
    // Look for tags like [Greedy] or [Impatient]
    const emotionMatch = rawText.match(/^\[(.*?)\]\s*(.*)/);
    
    const box = document.getElementById('dip-chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.style.marginBottom = '0.75rem';
    msgDiv.style.fontFamily = 'var(--font-mono)';
    msgDiv.style.fontSize = '0.9rem';
    msgDiv.style.lineHeight = '1.4';
    msgDiv.style.color = '#fff';

    const senderSpan = document.createElement('span');
    senderSpan.style.color = 'var(--color-accent)';
    senderSpan.style.fontWeight = 'bold';
    senderSpan.style.marginRight = '0.5rem';
    senderSpan.textContent = 'AMBASSADOR:';
    
    msgDiv.appendChild(senderSpan);

    if (emotionMatch) {
       const emotion = emotionMatch[1].toUpperCase();
       const text = emotionMatch[2];
       
       const emotionSpan = document.createElement('span');
       emotionSpan.textContent = '<' + emotion + '> ';
       emotionSpan.style.color = '#FFCC00'; // distinct highlight for emotion
       emotionSpan.style.fontStyle = 'italic';
       emotionSpan.style.marginRight = '0.5rem';
       
       const textSpan = document.createElement('span');
       textSpan.textContent = text;
       
       msgDiv.appendChild(emotionSpan);
       msgDiv.appendChild(textSpan);
    } else {
       const textSpan = document.createElement('span');
       textSpan.textContent = rawText;
       msgDiv.appendChild(textSpan);
    }
    
    box.appendChild(msgDiv);
    box.scrollTop = box.scrollHeight;
}

function appendChatMessage(sender, text, color) {
  const box = document.getElementById('dip-chat-box');
  if (!box) return;
  
  const msgDiv = document.createElement('div');
  msgDiv.style.marginBottom = '0.5rem';
  msgDiv.innerHTML = `<span style="color: ${color}; font-weight: bold;">${sender}:</span> <span style="color:#fff">${text}</span>`;
  
  box.appendChild(msgDiv);
  box.scrollTop = box.scrollHeight;
}

export function openDiplomacyPanel(factionId) {
  currentDiplomacyTarget = factionId;
  const modal = document.getElementById('modal-diplomacy');
  
  // Set UI Details
  const nameEl = document.getElementById('dip-target-name');
  const leaderEl = document.getElementById('dip-target-leader');
  
  const map = {
     2: { name: 'Iron Grid', leader: 'General Volkov', color: '#FF4444' },
     3: { name: 'Silk Road Coalition', leader: 'Chairman Wei', color: '#FFCC00' },
     4: { name: 'Euro Nexus', leader: 'Director Vance', color: '#4488FF' },
     5: { name: 'Pacific Vanguard', leader: 'Commandant Sato', color: '#AA44FF' },
     6: { name: 'Cyber Mercenaries', leader: 'Proxy (CNSA)', color: '#AAAAAA' },
     7: { name: 'Sentinel Vanguard', leader: 'Oracle (CNSA)', color: '#FFFFFF' },
     8: { name: 'Shadow Cartels', leader: 'Cipher (CNSA)', color: '#880088' }
  };
  
  const info = map[factionId];
  if (info) {
     nameEl.textContent = info.name;
     nameEl.style.color = info.color;
     leaderEl.textContent = "CONTACT: " + info.leader;
  }
  
  // Reset chat
  const box = document.getElementById('dip-chat-box');
  box.innerHTML = '';
  appendChatMessage('SYS', 'Establishing secure handshake... connected.', 'var(--color-accent)');
  
  // Reset buttons
  document.getElementById('dip-chat-input').disabled = false;
  document.getElementById('btn-dip-send').disabled = false;
  document.getElementById('btn-dip-propose').disabled = false;
  document.getElementById('dip-treaty-type').disabled = false;
  
  // Reset status
  document.getElementById('dip-status-badge').textContent = 'NO ACCORD';
  document.getElementById('dip-status-badge').style.color = 'var(--color-text-muted)';
  document.getElementById('dip-status-badge').style.borderColor = 'var(--color-text-muted)';
  
  modal.style.display = 'flex';
  modal.classList.add('active');
  audio.playClick();
}

// --- SPRINT 4: SENTINEL LAB UI ---

let sentinelChart = null;
let currentSentinelId = null;

export async function openSentinelLab() {
  const modal = document.getElementById('modal-sentinel');
  if(!modal) return;
  modal.style.display = 'flex';
  audio.playClick();
  
  // Bind close
  document.getElementById('btn-close-sentinel').onclick = () => {
     modal.style.display = 'none';
     audio.playClick();
  };
  
  await refreshSentinelLab();
}

async function refreshSentinelLab() {
  const data = await api.getSentinels();
  const sntName = document.getElementById('snt-name');
  const sntStatus = document.getElementById('snt-status');
  const btnCreate = document.getElementById('btn-snt-create');
  const controls = document.getElementById('snt-controls');
  
  if (!data.sentinels || data.sentinels.length === 0) {
    sntName.textContent = "NO SENTINEL FOUND";
    sntStatus.textContent = "NOT INITIALIZED";
    sntStatus.style.color = "var(--color-warning)";
    btnCreate.style.display = 'block';
    controls.style.display = 'none';
    
    btnCreate.onclick = async () => {
      audio.playClick();
      btnCreate.disabled = true;
      btnCreate.textContent = "INITIALIZING...";
      await api.createSentinel("Alpha-1");
      await refreshSentinelLab();
    };
    initRadarChart([0,0,0,0]); // Empty chart
    return;
  }
  
  btnCreate.style.display = 'none';
  controls.style.display = 'flex';
  
  const sentinelInfo = data.sentinels[0];
  const sentinel = sentinelInfo.sentinel;
  const policy = sentinelInfo.policy;
  
  currentSentinelId = sentinel.id;
  
  sntName.textContent = sentinel.name;
  sntStatus.textContent = sentinel.status;
  if (sentinel.status === 'DEPLOYED') {
      sntStatus.style.color = "var(--color-player)";
  } else {
      sntStatus.style.color = "var(--color-warning)";
  }
  
  // Render Chart
  initRadarChart([
      policy.persistence_weight,
      policy.stealth_weight,
      policy.efficiency_weight,
      policy.aggression_weight
  ]);
  
  // Bind Sliders
  const slPers = document.getElementById('slider-persistence');
  const slStlh = document.getElementById('slider-stealth');
  const slEff = document.getElementById('slider-efficiency');
  const slAggr = document.getElementById('slider-aggression');
  
  slPers.value = policy.persistence_weight * 100;
  slStlh.value = policy.stealth_weight * 100;
  slEff.value = policy.efficiency_weight * 100;
  slAggr.value = policy.aggression_weight * 100;
  
  const updateVals = () => {
      document.getElementById('val-persistence').textContent = (slPers.value / 100).toFixed(2);
      document.getElementById('val-stealth').textContent = (slStlh.value / 100).toFixed(2);
      document.getElementById('val-efficiency').textContent = (slEff.value / 100).toFixed(2);
      document.getElementById('val-aggression').textContent = (slAggr.value / 100).toFixed(2);
      
      // Live update chart
      if (sentinelChart) {
          sentinelChart.data.datasets[0].data = [
              slPers.value / 100, slStlh.value / 100, slEff.value / 100, slAggr.value / 100
          ];
          sentinelChart.update();
      }
  };
  
  updateVals();
  [slPers, slStlh, slEff, slAggr].forEach(s => s.oninput = updateVals);
  
  // Bind Actions
  const btnSave = document.getElementById('btn-snt-save');
  btnSave.onclick = async () => {
      audio.playClick();
      btnSave.textContent = "SAVING...";
      await api.updateSentinelPolicy(currentSentinelId, {
          persistence_weight: slPers.value / 100,
          stealth_weight: slStlh.value / 100,
          efficiency_weight: slEff.value / 100,
          aggression_weight: slAggr.value / 100
      });
      btnSave.textContent = "SAVE POLICY";
  };
  
  const btnToggle = document.getElementById('btn-snt-toggle');
  btnToggle.textContent = sentinel.status === 'DEPLOYED' ? 'RECALL' : 'DEPLOY';
  if (sentinel.status === 'DEPLOYED') {
      btnToggle.style.color = "var(--color-enemy)";
      btnToggle.style.borderColor = "var(--color-enemy)";
  } else {
      btnToggle.style.color = "var(--color-warning)";
      btnToggle.style.borderColor = "var(--color-warning)";
  }
  
  btnToggle.onclick = async () => {
      audio.playClick();
      btnToggle.disabled = true;
      await api.toggleSentinel(currentSentinelId);
      await refreshSentinelLab();
  };
  
  // Load Logs
  const logContainer = document.getElementById('snt-logs');
  logContainer.innerHTML = '<div style="color: var(--color-text-muted); font-style: italic;">[ OPERATIONAL LOGS ]</div>';
  const logsRes = await api.getSentinelLogs(currentSentinelId);
  const logs = logsRes.logs || [];
  
  logs.forEach(log => {
      const el = document.createElement('div');
      el.innerHTML = `<span style="color: var(--color-accent)">[EP ${log.epoch_id}]</span> ${log.description}`;
      logContainer.appendChild(el);
  });
}

function initRadarChart(weightsArr) {
    const ctx = document.getElementById('snt-radar-chart');
    if (!ctx) return;
    
    if (sentinelChart) {
        sentinelChart.destroy();
    }
    
    sentinelChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['PERSISTENCE', 'STEALTH', 'EFFICIENCY', 'AGGRESSION'],
            datasets: [{
                label: 'Weights',
                data: weightsArr,
                backgroundColor: 'rgba(0, 255, 221, 0.2)',
                borderColor: 'rgba(0, 255, 221, 1)',
                pointBackgroundColor: 'rgba(0, 255, 221, 1)',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        font: { family: '"Fira Code", monospace', size: 10 }
                    },
                    ticks: {
                        display: false,
                        min: 0,
                        max: 1
                    }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}


