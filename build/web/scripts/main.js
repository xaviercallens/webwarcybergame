/**
 * Neo-Hack: Gridlock — Main Entry Point & Router
 */

import { GameEngine } from './game-engine.js';
import { DemoManager } from './demo-manager.js';
import { PromoManager } from './promo-manager.js';
import { api } from './api-client.js';
import { audio } from './audio-manager.js';

// --- State ---
const AppState = {
  currentView: 'menu',
  player: {
    username: 'GHOST_4X1',
    rank: 'SCRIPT_KIDDIE',
    xp: 245,
    maxXp: 500
  }
};

// --- View Templates ---
const views = {
  menu: `
    <div id="view-menu" class="view screen-menu active">
      <div class="menu-title-container">
        <h1>NEO-HACK</h1>
        <h1 style="color: #fff">GRIDLOCK</h1>
        <div class="menu-subtitle">v1.0.0 // SYSTEM ONLINE</div>
      </div>
      
      <div class="menu-buttons">
        <button id="btn-play" class="btn btn-primary">▶ PLAY</button>
        <button id="btn-demo" class="btn">⊡ DEMO MODE</button>
        <button id="btn-promo" class="btn" style="color: #ff0055; border-color: #ff0055;">🎦 RECORD PROMO</button>
        <button id="btn-settings" class="btn">⚙ SETTINGS</button>
      </div>
      
      <div class="player-card">
        <span>Player: <span class="glitch-text">${AppState.player.username}</span></span>
        <span>Rank: ${AppState.player.rank}</span>
        <span>XP: ${AppState.player.xp} / ${AppState.player.maxXp}</span>
      </div>
    </div>
  `,
  game: `
    <div id="view-game" class="view screen-game">
      <div id="canvas-container"></div>
      
      <div class="game-ui">
        <!-- HUD will be injected here by ui-manager -->
        <div id="hud-layer"></div>
        <button id="btn-quit" class="btn btn-danger" style="position:absolute; top: 1rem; right: 1rem; min-width: 100px;">QUIT</button>
        
        <!-- Tutorial Overlay -->
        <div id="tutorial-panel" class="panel" style="display:none; position: absolute; bottom: 2rem; left: 50%; transform: translateX(-50%); width: 500px; text-align: center; border-color: var(--color-accent); box-shadow: 0 0 30px rgba(0,255,221,0.15); z-index: 100;">
          <h3 id="tut-title" style="color: var(--color-accent); margin-top: 0; font-family: var(--font-display); letter-spacing: 2px;">[ TUTORIAL : STEP 1 ]</h3>
          <p id="tut-text" style="font-family: var(--font-mono); color: #fff; line-height: 1.5; margin: 1.5rem 0;"></p>
          <div>
              <button id="btn-tut-next" class="btn btn-primary">NEXT >></button>
          </div>
        </div>
      </div>
    </div>
  `,
  settingsModal: `
    <div id="modal-settings" class="modal-overlay">
      <div class="panel settings-panel">
        <div class="panel-header">
          <span>⚙ SYSTEM.CFG</span>
          <button id="btn-close-settings" style="background:none; border:none; color:var(--color-accent); cursor:pointer; font-size:1.5rem;">×</button>
        </div>
        
        <div class="setting-row">
          <label>Master Volume</label>
          <input type="range" min="0" max="100" value="80" />
        </div>
        <div class="setting-row">
          <label>Colorblind Mode</label>
          <input type="checkbox" id="toggle-colorblind" />
        </div>
        <div class="setting-row">
          <label>CRT FX</label>
          <input type="checkbox" checked />
        </div>
        
        <div style="margin-top: var(--spacing-6); text-align: right;">
          <button id="btn-save-settings" class="btn">APPLY</button>
        </div>
      </div>
    </div>
  `,
  leaderboard: `
    <div id="view-leaderboard" class="view screen-leaderboard">
      <div class="panel" style="width: 600px; margin: 4rem auto; pointer-events: auto;">
        <div class="panel-header" style="justify-content: center; font-size: 1.5rem; text-shadow: 0 0 10px var(--color-player);">
          [ GLOBAL RANKINGS ]
        </div>
        <table style="width: 100%; margin-top: 2rem; color: #fff; text-align: left; font-family: var(--font-mono);">
          <tr style="color: var(--color-accent); border-bottom: 1px solid var(--color-accent);">
            <th>RANK</th><th>OPERATIVE</th><th>TIER</th><th>XP</th>
          </tr>
          <tr><td>#1</td><td style="color:var(--color-player);">N30_LUNAR</td><td>ARCHITECT</td><td>9,450</td></tr>
          <tr><td>#2</td><td>ZERO_SUM</td><td>ELITE</td><td>8,120</td></tr>
          <tr><td>#3</td><td>${AppState.player.username}</td><td>${AppState.player.rank}</td><td>${AppState.player.xp}</td></tr>
          <tr><td>#4</td><td>GL1TCH</td><td>HACKER</td><td>145</td></tr>
        </table>
        <div style="text-align: center; margin-top: 2rem;">
          <button id="btn-lb-back" class="btn">RETURN</button>
        </div>
      </div>
    </div>
  `,
  gameover: `
    <div id="view-gameover" class="view screen-gameover" style="display:none; justify-content: center; align-items: center; background: rgba(0,0,0,0.8); z-index: 1000; position: absolute; inset: 0;">
      <div class="panel" style="text-align: center; max-width: 400px; animation: glitch-anim-1 0.3s linear; pointer-events: auto;">
        <h1 id="gameover-title" style="font-family: var(--font-display); font-size: 3rem; margin-bottom: 1rem; color: var(--color-player); text-shadow: 0 0 15px var(--color-player);">TOTAL DOMINANCE</h1>
        <p style="color: var(--color-text-muted); font-family: var(--font-mono);">
          Time: <span id="gameover-time" style="color:#fff">00:00</span><br/>
          Nodes Captured: <span id="gameover-nodes" style="color:#fff">0</span><br/>
          XP Gained: <span id="gameover-xp" style="color:var(--color-accent)">+150</span>
        </p>
        <div style="margin-top: 2rem; display: flex; gap: 1rem; justify-content: center;">
          <button id="btn-retry" class="btn btn-primary">REDEPLOY</button>
          <button id="btn-main-menu" class="btn">DISCONNECT</button>
        </div>
      </div>
    </div>
  `
};

// --- Core App Logic ---
async function initApp() {
  const appElement = document.getElementById('app');
  
  // Inject HTML
  appElement.innerHTML = views.menu + views.game + views.leaderboard + views.gameover + views.settingsModal;
  
  // Check Backend Status
  const subtitle = document.querySelector('.menu-subtitle');
  subtitle.innerHTML = 'v1.0.0 // CONTACTING SERVER...';
  
  const health = await api.health();
  if (health.status === 'healthy') {
    subtitle.innerHTML = 'v1.0.0 // SYSTEM <span style="color:var(--color-player)">ONLINE</span>';
  } else {
    subtitle.innerHTML = 'v1.0.0 // SYSTEM <span style="color:var(--color-enemy)">OFFLINE</span> (GUEST MODE)';
  }
  
  document.getElementById('btn-play').addEventListener('click', () => {
    navigateTo('game');
    if (window.GameInstance) {
      if (window.DemoInstance) window.DemoInstance.stop();
      if (window.PromoInstance) window.PromoInstance.stop();
      window.GameInstance.init(); // Reset game on play
    }
  });

  document.getElementById('btn-demo').addEventListener('click', () => {
    navigateTo('game');
    if (window.PromoInstance) window.PromoInstance.stop();
    if (window.DemoInstance) {
      window.DemoInstance.start();
    }
  });

  document.getElementById('btn-promo').addEventListener('click', () => {
    if (window.DemoInstance) window.DemoInstance.stop();
    if (window.PromoInstance) {
      window.PromoInstance.start();
    }
  });
  
  // Add Leaderboard button to menu dynamically since we didn't include it in original menu HTML
  const menuButtons = document.querySelector('.menu-buttons');
  const lbBtn = document.createElement('button');
  lbBtn.className = 'btn';
  lbBtn.innerText = 'LEADERBOARD';
  lbBtn.id = 'btn-leaderboard';
  menuButtons.appendChild(lbBtn);
  
  document.getElementById('btn-leaderboard').addEventListener('click', () => navigateTo('leaderboard'));
  document.getElementById('btn-lb-back').addEventListener('click', () => navigateTo('menu'));
  
  document.getElementById('btn-quit').addEventListener('click', () => navigateTo('menu'));
  
  document.getElementById('btn-retry').addEventListener('click', () => {
    document.getElementById('view-gameover').style.display = 'none';
    if (window.GameInstance) window.GameInstance.init();
  });
  
  document.getElementById('btn-main-menu').addEventListener('click', () => {
    document.getElementById('view-gameover').style.display = 'none';
    navigateTo('menu');
  });

  // Listen for game over event
  window.addEventListener('gameOver', async (e) => {
    const isWin = e.detail.isWin;
    const stats = e.detail.stats;
    const title = document.getElementById('gameover-title');
    title.innerText = isWin ? 'TOTAL DOMINANCE' : 'SYSTEM FAILURE';
    title.style.color = isWin ? 'var(--color-player)' : 'var(--color-enemy)';
    title.style.textShadow = `0 0 15px ${isWin ? 'var(--color-player)' : 'var(--color-enemy)'}`;
    
    // Update local UI with bare minimum assuming offline
    document.getElementById('gameover-time').innerText = `${Math.floor(stats.time_seconds / 60)}:${(stats.time_seconds % 60).toString().padStart(2, '0')}`;
    document.getElementById('gameover-nodes').innerText = stats.nodes_captured;
    document.getElementById('gameover-xp').innerText = isWin ? '+???' : '+???';
    
    // Call backend
    if (api.token) {
        const res = await api.postGameOverStats(stats);
        if (res) {
            // Update the player stats in memory
            AppState.player.xp = res.xp;
            AppState.player.rank = res.rank;
            // The exact XP gained isn't returned, but we know the final XP.
            // We just show a dummy +XP calculation matching the backend for visual flair
            const base_xp = isWin ? 100 : 50;
            const capture_bonus = stats.nodes_captured * 8;
            const speed_bonus = Math.max(0, Math.floor((480 - stats.time_seconds) / 4));
            // we don't have streak here easily without refetching profile, but let's approximate
            const total = base_xp + capture_bonus + speed_bonus; 
            document.getElementById('gameover-xp').innerText = `+${total}`;
        }
    }
    
    if (isWin) audio.playCapture();
    else audio.playError();
    
    document.getElementById('view-gameover').style.display = 'flex';
  });
  
  // Bind settings modal
  document.getElementById('btn-settings').addEventListener('click', () => {
    document.getElementById('modal-settings').classList.add('active');
  });
  
  const closeSettings = () => document.getElementById('modal-settings').classList.remove('active');
  document.getElementById('btn-close-settings').addEventListener('click', closeSettings);
  document.getElementById('btn-save-settings').addEventListener('click', closeSettings);
  
  // Colorblind toggle logic
  document.getElementById('toggle-colorblind').addEventListener('change', (e) => {
    document.documentElement.setAttribute('data-colorblind', e.target.checked);
  });
  
  // Audio master volume
  document.querySelector('input[type="range"]').addEventListener('input', (e) => {
    audio.setVolume(e.target.value / 100);
  });
  
  // Attach sound effects to all buttons
  document.addEventListener('mouseover', (e) => {
    if (e.target.tagName === 'BUTTON' || e.target.classList.contains('btn')) {
      audio.playSelect();
    }
  });
  document.addEventListener('click', (e) => {
    if (e.target.tagName === 'BUTTON' || e.target.classList.contains('btn')) {
      audio.playClick();
    }
  });
  
  // Initialize UI features (HUD, Canvas, etc)
  initUI();
  
  // Init Game Engine and Demo
  window.GameInstance = new GameEngine();
  window.DemoInstance = new DemoManager(window.GameInstance);
  window.PromoInstance = new PromoManager(window.GameInstance);
}

// Simple Router
function navigateTo(viewName) {
  // Hide all views
  document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
  
  // Show target view
  const target = document.getElementById(`view-${viewName}`);
  if (target) {
    target.classList.add('active');
    AppState.currentView = viewName;
    console.log(`[SYS] Navigated to ${viewName}`);
    
    // Trigger custom event for other systems to react (e.g., Pixi canvas)
    window.dispatchEvent(new CustomEvent('viewChanged', { detail: { view: viewName } }));
  }
}

// Bootstrap
document.addEventListener('DOMContentLoaded', initApp);
