/**
 * Neo-Hack: Gridlock — Main Entry Point & Router
 */

import { GameEngine } from './game-engine.js';
import { DemoManager } from './demo-manager.js';
import { PromoManager } from './promo-manager.js';
import { api } from './api-client.js';
import { audio } from './audio-manager.js';
import { initUI } from './ui-manager.js';

// --- State ---
const AppState = {
  currentView: 'login',
  isAuthenticated: false,
  player: {
    username: 'GHOST_4X1',
    rank: 'SCRIPT_KIDDIE',
    xp: 245,
    maxXp: 500
  }
};

// --- View Templates ---
const views = {
  login: `
    <div id="view-login" class="view screen-menu active">
      <div class="menu-title-container">
        <h1>NEO-HACK</h1>
        <h1 style="color: #fff">GRIDLOCK</h1>
        <div class="menu-subtitle">v2.0.0 // AUTHENTICATION REQUIRED</div>
      </div>

      <div class="login-container" style="width: 380px; margin-top: 2rem;">
        <div class="panel" style="pointer-events: auto; padding: 2rem;">
          <div class="panel-header" style="justify-content: center; margin-bottom: 1.5rem;">
            <span id="auth-mode-label" style="letter-spacing: 3px;">[ AUTHENTICATE ]</span>
          </div>

          <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div>
              <label style="font-family: var(--font-hud); color: var(--color-accent); font-size: 0.8rem; letter-spacing: 2px;">OPERATIVE_ID</label>
              <input type="text" id="login-username" maxlength="20" autocomplete="username"
                style="width: 100%; padding: 0.75rem; background: rgba(0,20,30,0.8); border: 1px solid var(--color-accent); color: var(--color-player); font-family: var(--font-mono); font-size: 1rem; outline: none; margin-top: 0.25rem; box-sizing: border-box;"
                placeholder="Enter callsign..." />
            </div>

            <div>
              <label style="font-family: var(--font-hud); color: var(--color-accent); font-size: 0.8rem; letter-spacing: 2px;">PASSPHRASE</label>
              <input type="password" id="login-password" maxlength="64" autocomplete="current-password"
                style="width: 100%; padding: 0.75rem; background: rgba(0,20,30,0.8); border: 1px solid var(--color-accent); color: var(--color-player); font-family: var(--font-mono); font-size: 1rem; outline: none; margin-top: 0.25rem; box-sizing: border-box;"
                placeholder="••••••••" />
            </div>

            <div id="login-error" style="color: var(--color-enemy); font-family: var(--font-mono); font-size: 0.8rem; min-height: 1.2rem; text-shadow: 0 0 8px var(--color-enemy);"></div>

            <div style="display: flex; gap: 0.75rem; margin-top: 0.5rem;">
              <button id="btn-login" class="btn btn-primary" style="flex: 1;">▶ LOGIN</button>
              <button id="btn-register" class="btn" style="flex: 1;">⊕ REGISTER</button>
            </div>
          </div>

          <div style="text-align: center; margin-top: 1.5rem; border-top: 1px solid rgba(0,255,221,0.15); padding-top: 1rem;">
            <div style="color: var(--color-text-muted); font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 1px;">STATUS: <span id="login-status" style="color: var(--color-warning);">AWAITING CREDENTIALS</span></div>
          </div>
        </div>
      </div>
    </div>
  `,
  menu: `
    <div id="view-menu" class="view screen-menu active">
      <div class="menu-title-container">
        <h1>NEO-HACK</h1>
        <h1 style="color: #fff">GRIDLOCK</h1>
        <div class="menu-subtitle">v2.0.0 // SYSTEM ONLINE</div>
      </div>
      
      <div class="menu-buttons">
        <div class="difficulty-selector" style="margin-bottom: 2rem; border-bottom: 1px solid var(--color-accent); padding-bottom: 1rem;">
          <label style="color: var(--color-accent); font-family: var(--font-mono); margin-right: 1rem;">[ DIFFICULTY_SYS ]</label>
          <select id="sel-difficulty" style="background: var(--color-bg); color: #fff; border: 1px solid var(--color-primary); padding: 0.5rem; font-family: var(--font-display); cursor: pointer; outline: none;">
            <option value="BEGINNER">🟢 BEGINNER</option>
            <option value="INTERMEDIATE" selected>🟡 INTERMEDIATE</option>
            <option value="ADVANCED">🔴 ADVANCED</option>
          </select>
          <div id="diff-tooltip" style="color: var(--color-text-muted); font-family: var(--font-mono); font-size: 0.8rem; margin-top: 0.5rem;">Standard warfare. Balanced AI heuristics.</div>
        </div>
        
        <button id="btn-play" class="btn btn-primary">▶ PLAY</button>
        <button id="btn-demo" class="btn">⊡ DEMO MODE</button>
        <button id="btn-promo" class="btn" style="color: #ff0055; border-color: #ff0055;">🎦 RECORD PROMO</button>
        <button id="btn-settings" class="btn">⚙ SETTINGS</button>
      </div>
      
      <div class="player-card">
        <span>Player: <input type="text" id="input-username" class="glitch-text" value="${AppState.player.username}" maxlength="16" style="background:transparent; border:none; border-bottom:1px solid var(--color-accent); color:var(--color-player); font-family:var(--font-mono); font-size:1rem; outline:none; text-shadow:0 0 5px var(--color-player); width:auto;"></span>
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
        
        <!-- Intel Feed (Aria-Live Region) -->
        <div id="intel-feed" aria-live="polite" aria-atomic="false" style="position:absolute; bottom: 1rem; right: 1rem; width: 300px; height: 250px; background: rgba(0,0,0,0.7); border: 1px solid var(--color-accent); border-radius: 4px; padding: 1rem; overflow-y: hidden; display: flex; flex-direction: column; justify-content: flex-end; font-family: var(--font-mono); font-size: 0.8rem; pointer-events: none; z-index: 50;">
          <div style="color: var(--color-accent); margin-bottom: 0.5rem; text-transform: uppercase; border-bottom: 1px dashed var(--color-accent); padding-bottom: 0.25rem;">[ INTEL FEED ]</div>
          <div id="intel-log-container" style="display: flex; flex-direction: column; gap: 0.25rem;">
            <!-- Logs injected here -->
          </div>
        </div>
        
        <!-- Tutorial Overlay -->
        <div id="tutorial-panel" class="panel" style="display:none; position: absolute; bottom: 2rem; left: 50%; transform: translateX(-50%); width: 500px; text-align: center; border-color: var(--color-accent); box-shadow: 0 0 30px rgba(0,255,221,0.15); z-index: 100;">
          <h3 id="tut-title" style="color: var(--color-accent); margin-top: 0; font-family: var(--font-display); letter-spacing: 2px;">[ TUTORIAL : STEP 1 ]</h3>
          <p id="tut-text" style="font-family: var(--font-mono); color: #fff; line-height: 1.5; margin: 1.5rem 0;"></p>
          <div>
              <button id="btn-tut-next" class="btn btn-primary">NEXT >></button>
          </div>
        </div>

        <!-- Hotkeys Overlay -->
        <div id="hotkeys-panel" style="position: absolute; bottom: 1rem; left: 1rem; padding: 1rem; background: rgba(0,0,0,0.6); border: 1px solid var(--color-accent); border-radius: 4px; pointer-events: none; font-family: var(--font-mono); font-size: 0.85rem; color: #fff; z-index: 50;">
          <div style="color: var(--color-accent); margin-bottom: 0.5rem; text-transform: uppercase;">[ HOTKEYS ]</div>
          <div>Hold <span style="color: var(--color-player); font-weight: bold;">[A]</span> : Highlight Playable Nodes</div>
          <div>Hold <span style="color: var(--color-enemy); font-weight: bold;">[E]</span> : Highlight Enemy Targets</div>
          <div>Tap <span style="color: var(--color-accent); font-weight: bold;">[SPACE]</span> : Auto-Strike Target</div>
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
  
  // Inject HTML — login view is the first screen
  appElement.innerHTML = views.login + views.menu + views.game + views.leaderboard + views.gameover + views.settingsModal;

  // --- Login / Auth Flow ---
  const loginUsername = document.getElementById('login-username');
  const loginPassword = document.getElementById('login-password');
  const loginError = document.getElementById('login-error');
  const loginStatus = document.getElementById('login-status');
  const btnLogin = document.getElementById('btn-login');
  const btnRegister = document.getElementById('btn-register');

  async function handleAuth(isRegister) {
    const username = loginUsername.value.trim();
    const password = loginPassword.value;
    loginError.textContent = '';

    if (!username || !password) {
      loginError.textContent = '⚠ ALL FIELDS REQUIRED';
      return;
    }
    if (password.length < 6) {
      loginError.textContent = '⚠ PASSPHRASE MIN 6 CHARS';
      return;
    }

    loginStatus.textContent = isRegister ? 'CREATING OPERATIVE...' : 'AUTHENTICATING...';
    loginStatus.style.color = 'var(--color-accent)';

    try {
      const data = isRegister
        ? await api.register(username, password)
        : await api.login(username, password);

      AppState.isAuthenticated = true;
      AppState.player.username = data.player.username;
      AppState.player.rank = data.player.rank;
      AppState.player.xp = data.player.xp;

      loginStatus.textContent = 'ACCESS GRANTED';
      loginStatus.style.color = 'var(--color-player)';

      // Update menu player card
      const usernameInput = document.getElementById('input-username');
      if (usernameInput) usernameInput.value = AppState.player.username;

      setTimeout(() => navigateTo('menu'), 400);
    } catch (e) {
      loginError.textContent = isRegister
        ? '⚠ REGISTRATION FAILED — CALLSIGN MAY BE TAKEN'
        : '⚠ AUTH FAILED — INVALID CREDENTIALS';
      loginStatus.textContent = 'ACCESS DENIED';
      loginStatus.style.color = 'var(--color-enemy)';
    }
  }

  btnLogin.addEventListener('click', () => handleAuth(false));
  btnRegister.addEventListener('click', () => handleAuth(true));

  // Allow Enter key to submit
  loginPassword.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleAuth(false);
  });
  loginUsername.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') loginPassword.focus();
  });

  // --- Auto-login if token exists ---
  if (api.token) {
    loginStatus.textContent = 'RESTORING SESSION...';
    loginStatus.style.color = 'var(--color-accent)';
    const profile = await api.getProfile();
    if (profile) {
      AppState.isAuthenticated = true;
      AppState.player.username = profile.username;
      AppState.player.rank = profile.rank;
      AppState.player.xp = profile.xp;
      loginStatus.textContent = 'SESSION RESTORED';
      loginStatus.style.color = 'var(--color-player)';
      navigateTo('menu');
    } else {
      // Token expired/invalid
      api.token = null;
      localStorage.removeItem('nh_token');
      loginStatus.textContent = 'SESSION EXPIRED — RE-AUTHENTICATE';
      loginStatus.style.color = 'var(--color-warning)';
    }
  }

  // Check Backend Status
  const subtitle = document.querySelector('.menu-subtitle');
  subtitle.innerHTML = 'v2.0.0 // CONTACTING SERVER...';

  const health = await api.health();
  if (health.status === 'healthy') {
    subtitle.innerHTML = 'v2.0.0 // SYSTEM <span style="color:var(--color-player)">ONLINE</span>';
  } else {
    subtitle.innerHTML = 'v2.0.0 // SYSTEM <span style="color:var(--color-enemy)">OFFLINE</span> (GUEST MODE)';
  }
  
  const btnPlay = document.getElementById('btn-play');
  const selDiff = document.getElementById('sel-difficulty');
  const diffTooltip = document.getElementById('diff-tooltip');

  if (selDiff) {
    selDiff.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val === 'BEGINNER') {
            diffTooltip.innerText = 'Highly recommended for new operatives. Slower AI response.';
            diffTooltip.style.color = 'var(--color-player)';
        } else if (val === 'INTERMEDIATE') {
            diffTooltip.innerText = 'Standard warfare. Balanced AI heuristics.';
            diffTooltip.style.color = 'var(--color-text-muted)';
        } else {
            diffTooltip.innerText = 'Lethal threat level. Aggressive AI and fortified targets.';
            diffTooltip.style.color = 'var(--color-enemy)';
        }
        audio.playSelect();
    });
  }

  btnPlay.addEventListener('click', () => {
    navigateTo('game');
    const selectedDifficulty = selDiff ? selDiff.value : 'INTERMEDIATE';
    if (window.GameInstance) {
      if (window.DemoInstance) window.DemoInstance.stop();
      if (window.PromoInstance) window.PromoInstance.stop();
      window.GameInstance.init(selectedDifficulty); // Reset game on play with difficulty
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
    if (window.PromoInstance) {
      const started = window.PromoInstance.start();
      if (started !== false) {
          if (window.DemoInstance) window.DemoInstance.stop();
          navigateTo('game');
      }
    }
  });
  
  // Add Leaderboard button to menu dynamically
  const menuButtons = document.querySelector('.menu-buttons');
  const lbBtn = document.createElement('button');
  lbBtn.className = 'btn';
  lbBtn.innerText = 'LEADERBOARD';
  lbBtn.id = 'btn-leaderboard';
  menuButtons.appendChild(lbBtn);

  // Add Logout button
  const logoutBtn = document.createElement('button');
  logoutBtn.className = 'btn';
  logoutBtn.id = 'btn-logout';
  logoutBtn.innerText = '⏻ DISCONNECT';
  logoutBtn.style.cssText = 'color: var(--color-enemy); border-color: var(--color-enemy); margin-top: 1rem;';
  menuButtons.appendChild(logoutBtn);

  document.getElementById('btn-logout').addEventListener('click', () => {
    api.token = null;
    localStorage.removeItem('nh_token');
    AppState.isAuthenticated = false;
    navigateTo('login');
  });
  
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

  // Handle Custom Name
  const inputUsername = document.getElementById('input-username');
  if (inputUsername) {
      inputUsername.addEventListener('input', (e) => {
          AppState.player.username = e.target.value.toUpperCase() || 'ANONYMOUS';
      });
  }

  // --- Intel Feed (Aria-Live) ---
  const intelContainer = document.getElementById('intel-log-container');
  const addIntelLog = (msg, isPositive = true) => {
      if (!intelContainer) return;
      const el = document.createElement('div');
      el.innerText = msg;
      el.style.color = isPositive ? 'var(--color-player)' : 'var(--color-enemy)';
      intelContainer.appendChild(el);
      // Auto-scroll
      if (intelContainer.children.length > 10) {
          intelContainer.removeChild(intelContainer.firstChild);
      }
  };

  window.addEventListener('attackLaunched', () => addIntelLog('> UPLINK ESTABLISHED. INJECTING PAYLOAD.', true));
  window.addEventListener('toast', (e) => {
      addIntelLog(e.detail.message, e.detail.type === 'capture');
  });

  // --- Global Keyboard Shortcuts ---
  window.addEventListener('keydown', (e) => {
      // Don't trigger if user is typing in the name input field
      if (document.activeElement === inputUsername) return;
      
      const key = e.key.toLowerCase();
      // Menu Shortcuts
      if (AppState.currentView === 'menu') {
          if (key === 'p') document.getElementById('btn-play').click();
          if (key === 'd') document.getElementById('btn-demo').click();
      }
      // Game Shortcuts
      if (AppState.currentView === 'game') {
          if (key === 'q') document.getElementById('btn-quit').click();
      }
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
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
