import { GameEngine } from './game-engine.js';
import { DemoManager } from './demo-manager.js';
import { PromoManager } from './promo-manager.js';
import { api } from './api-client.js';
import { audio } from './audio-manager.js';
import { initUI, initDiplomacyEvents } from './ui-manager.js';
import { TerminalManager } from './terminal-manager.js';

// v4.1 Phantom Mesh Components
import { MeshHub } from './components/mesh-hub.js';
import { ReactPhase } from './components/react-phase.js';
import { LeaderboardHub } from './components/leaderboard.js';
import { GhostDeploy } from './components/ghost-deploy.js';
import { Campaign } from './components/campaign.js';

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
window.AppState = AppState;

// --- View Templates ---
const views = {
  login: `
    <div id="view-login" class="view screen-menu active">
      <div class="menu-title-container">
        <h1>NEO-HACK</h1>
        <h1 style="color: #fff">GRIDLOCK</h1>
        <div class="menu-subtitle">v4.1.0 // AUTHENTICATION REQUIRED</div>
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
    <div id="view-menu" class="view screen-menu">
      <div class="menu-title-container">
        <h1>NEO-HACK</h1>
        <h1 style="color: #fff">GRIDLOCK</h1>
        <div class="menu-subtitle">v4.1.0 // SYSTEM ONLINE</div>
      </div>
      
      <div class="menu-buttons">
        <div class="difficulty-selector" style="margin-bottom: 1rem; border-bottom: 1px solid var(--color-accent); padding-bottom: 1rem;">
          <label style="color: var(--color-accent); font-family: var(--font-mono); margin-right: 1rem;">[ DIFFICULTY_SYS ]</label>
          <select id="sel-difficulty" style="background: var(--color-bg); color: #fff; border: 1px solid var(--color-primary); padding: 0.5rem; font-family: var(--font-display); cursor: pointer; outline: none;">
            <option value="BEGINNER">🟢 BEGINNER</option>
            <option value="INTERMEDIATE" selected>🟡 INTERMEDIATE</option>
            <option value="ADVANCED">🔴 ADVANCED</option>
          </select>
          <div id="diff-tooltip" style="color: var(--color-text-muted); font-family: var(--font-mono); font-size: 0.8rem; margin-top: 0.5rem;">Standard warfare. Balanced AI heuristics.</div>
        </div>

        <div class="difficulty-selector" style="margin-bottom: 2rem; border-bottom: 1px solid var(--color-accent); padding-bottom: 1rem;">
          <label style="color: var(--color-accent); font-family: var(--font-mono); margin-right: 1rem;">[ DEMO_SCENARIO ]</label>
          <select id="sel-scenario" style="background: var(--color-bg); color: #fff; border: 1px solid #ff9900; padding: 0.5rem; font-family: var(--font-display); cursor: pointer; outline: none;">
            <option value="tutorial">01 : CORE SYSTEMS TUTORIAL</option>
            <option value="bank_run">02 : THE BERYLIA BANK RUN</option>
            <option value="heist">03 : SILICON SILK ROAD HEIST</option>
            <option value="blackout">04 : OPERATION BLACKOUT</option>
          </select>
          <div id="scenario-tooltip" style="color: #ff9900; font-family: var(--font-mono); font-size: 0.8rem; margin-top: 0.5rem;">Select a guided scenario to learn advanced mechanics.</div>
        </div>
        
        <button id="btn-play" class="btn btn-primary">▶ PLAY SANDBOX</button>
        <button id="btn-demo" class="btn" style="color: #ff9900; border-color: #ff9900;">⊡ PLAY SCENARIO</button>
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
        <button id="btn-lab" class="btn btn-primary" style="position:absolute; top: 1rem; right: 8rem; min-width: 130px; box-shadow: 0 0 10px rgba(0, 255, 221, 0.4);">SENTINEL LAB</button>
        
        <!-- Intel Feed (Aria-Live Region) -->
        <div id="intel-feed" aria-live="polite" aria-atomic="false" style="position:absolute; bottom: 1rem; right: 1rem; width: 300px; height: 250px; background: rgba(0,0,0,0.7); border: 1px solid var(--color-accent); border-radius: 4px; padding: 1rem; overflow-y: hidden; display: flex; flex-direction: column; justify-content: flex-end; font-family: var(--font-mono); font-size: 0.8rem; pointer-events: none; z-index: 50;">
          <div style="color: var(--color-accent); margin-bottom: 0.5rem; text-transform: uppercase; border-bottom: 1px dashed var(--color-accent); padding-bottom: 0.25rem;">[ INTEL FEED ]</div>
          <div id="intel-log-container" style="display: flex; flex-direction: column; gap: 0.25rem;">
            <!-- Logs injected here -->
          </div>
        </div>
        
        <!-- Operative Induction Tutorial Overlay -->
        <div id="tutorial-overlay" class="tutorial-overlay hidden">
          <div class="tutorial-bottom-bar">
            <div class="tutorial-progress">
              <span class="tutorial-progress-text" id="tut-progress-text">STEP 1 / 5</span>
              <div class="tutorial-progress-bars" id="tut-progress-bars">
                 <div class="tut-bar active"></div>
                 <div class="tut-bar"></div>
                 <div class="tut-bar"></div>
                 <div class="tut-bar"></div>
                 <div class="tut-bar"></div>
              </div>
            </div>
            <button id="btn-tut-skip" class="btn btn-danger" style="min-width: 150px;">SKIP TUTORIAL</button>
          </div>
          <div class="coach-container">
            <div class="coach-bubble" id="tut-bubble">
              <div class="coach-bubble-name">COACH <span>AI ADVISOR</span></div>
              <h3 id="tut-title" style="color: var(--color-accent); margin: 0.5rem 0; font-family: var(--font-display); letter-spacing: 2px; font-size: var(--text-base);">[ TUTORIAL : STEP 1 ]</h3>
              <div class="coach-bubble-text" id="tut-text">Operative, we've detected an intrusion. Select NODE-04 on the map to begin analysis.</div>
              <div style="margin-top: 1rem; text-align: right;">
                <button id="btn-tut-next" class="btn btn-primary" style="min-width:120px; font-size:var(--text-xs); padding: 0.5rem 1rem;">ACKNOWLEDGE >></button>
              </div>
            </div>
            <div class="coach-drone-img">❖</div>
          </div>
        </div>

        <!-- Hotkeys Overlay -->
        <div id="hotkeys-panel" style="position: absolute; bottom: 1rem; left: 1rem; padding: 1rem; background: rgba(0,0,0,0.6); border: 1px solid var(--color-accent); border-radius: 4px; pointer-events: none; font-family: var(--font-mono); font-size: 0.85rem; color: #fff; z-index: 50;">
          <div style="color: var(--color-accent); margin-bottom: 0.5rem; text-transform: uppercase;">[ HOTKEYS ]</div>
          <div>Hold <span style="color: var(--color-player); font-weight: bold;">[A]</span> : Highlight Playable Nodes</div>
          <div>Hold <span style="color: var(--color-enemy); font-weight: bold;">[E]</span> : Highlight Enemy Targets</div>
          <div>Tap <span style="color: var(--color-player); font-weight: bold;">[\`]</span> : Toggle Terminal CLI</div>
        </div>

        <!-- Terminal Overlay -->
        <div id="terminal-panel" style="display:none; position: absolute; inset: 0; background: rgba(0,20,30,0.95); z-index: 200; font-family: var(--font-mono); color: var(--color-player); padding: 2rem; flex-direction: column;">
          <div style="flex: 1; overflow-y: auto; margin-bottom: 1rem; padding-right: 1rem;" id="terminal-output">
            <div style="color: var(--color-accent); margin-bottom: 1rem;">Neo-Hack OS v4.1.0 - Terminal Access Granted. Type /help for commands.</div>
          </div>
          <div style="display: flex; gap: 0.5rem; border-top: 1px solid var(--color-accent); padding-top: 1rem;">
            <span style="color: var(--color-accent);">root@gridlock:~$</span>
            <input type="text" id="terminal-input" style="flex: 1; background: transparent; border: none; color: #fff; font-family: var(--font-mono); font-size: 1rem; outline: none;" autocomplete="off" spellcheck="false" />
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
  `,
  diplomacyModal: `
    <div id="modal-diplomacy" class="modal-overlay" style="display:none; position: fixed; inset: 0; background: rgba(0,20,30,0.95); z-index: 1000; justify-content: center; align-items: center; font-family: var(--font-mono);">
      <div class="panel" style="width: 800px; max-height: 80vh; display: flex; flex-direction: column; background: rgba(10,14,23,0.9); border: 2px solid var(--color-accent); pointer-events: auto;">
        
        <div class="panel-header" style="justify-content: space-between; border-bottom: 1px solid var(--color-accent); padding-bottom: 0.5rem;">
          <span style="color: var(--color-accent); text-shadow: 0 0 5px var(--color-accent); font-size: 1.2rem;">[ SECURE DIPLOMATIC CHANNEL ]</span>
          <button id="btn-close-diplomacy" style="background: none; border: none; color: var(--color-accent); font-size: 1.5rem; cursor: pointer;">×</button>
        </div>

        <div style="display: flex; flex: 1; overflow: hidden; margin-top: 1rem;">
          
          <!-- Contacts Sidebar -->
          <div style="flex: 1; border-right: 1px solid rgba(0,255,221,0.2); display: flex; flex-direction: column;">
            <div style="color: var(--color-text-muted); font-size: 0.8rem; margin-bottom: 0.5rem; letter-spacing: 1px;">STATE ACTORS</div>
            <button class="btn btn-dip-contact" data-fid="2" style="text-align: left; margin-bottom: 0.5rem; border-color: #FF4444;"><span style="color:#FF4444">■</span> Iron Grid</button>
            <button class="btn btn-dip-contact" data-fid="3" style="text-align: left; margin-bottom: 0.5rem; border-color: #FFCC00;"><span style="color:#FFCC00">▲</span> Silk Road</button>
            <button class="btn btn-dip-contact" data-fid="4" style="text-align: left; margin-bottom: 0.5rem; border-color: #4488FF;"><span style="color:#4488FF">●</span> Euro Nexus</button>
            <button class="btn btn-dip-contact" data-fid="5" style="text-align: left; margin-bottom: 1rem; border-color: #AA44FF;"><span style="color:#AA44FF">◆</span> Pacific Vanguard</button>

            <div style="color: var(--color-text-muted); font-size: 0.8rem; margin-bottom: 0.5rem; letter-spacing: 1px;">NON-STATE ACTORS (CNSA)</div>
            <button class="btn btn-dip-contact" data-fid="6" style="text-align: left; margin-bottom: 0.5rem; border-color: #AAAAAA;" title="Hire Mercenaries: +20% Offense, -100 CU/Epoch"><span style="color:#AAAAAA">★</span> Cyber Mercenaries</button>
            <button class="btn btn-dip-contact" data-fid="7" style="text-align: left; margin-bottom: 0.5rem; border-color: #FFFFFF;" title="Form Alliance: +20% Global Defense"><span style="color:#FFFFFF">✚</span> Sentinel Vanguard</button>
            <button class="btn btn-dip-contact" data-fid="8" style="text-align: left; margin-bottom: 0.5rem; border-color: #880088;" title="Chaos Ops: -20% Offense penalty to anyone attacking you"><span style="color:#880088">☠</span> Shadow Cartels</button>
          </div>

          <!-- Active Diplomatic Session -->
          <div style="flex: 2; padding-left: 1rem; display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
              <div>
                <h3 id="dip-target-name" style="margin: 0; color: #fff; font-family: var(--font-display);">SELECT CONTACT</h3>
                <div id="dip-target-leader" style="color: var(--color-accent); font-size: 0.9rem;">--</div>
              </div>
              <div id="dip-status-badge" style="padding: 0.25rem 0.5rem; border: 1px solid var(--color-text-muted); color: var(--color-text-muted); font-size: 0.8rem;">NO ACCORD</div>
            </div>

            <!-- Chat Area -->
            <div id="dip-chat-box" style="flex: 1; background: rgba(0,0,0,0.5); border: 1px inset rgba(0,255,221,0.2); padding: 1rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem;">
              <div style="color: var(--color-text-muted); text-align: center; font-style: italic;">[ Channel Open ]</div>
            </div>

            <!-- Chat Input -->
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
              <input type="text" id="dip-chat-input" disabled style="flex: 1; padding: 0.5rem; background: transparent; border: 1px solid var(--color-accent); color: #fff; font-family: var(--font-mono); outline: none;" placeholder="Message Ambassador..." />
              <button id="btn-dip-send" class="btn btn-primary" disabled>SEND</button>
            </div>

            <!-- Treaty Proposal -->
            <div style="border-top: 1px dashed var(--color-accent); padding-top: 1rem; display: flex; gap: 0.5rem;">
              <select id="dip-treaty-type" disabled style="background: var(--color-bg); color: #fff; border: 1px solid var(--color-accent); padding: 0.5rem; font-family: var(--font-mono); outline: none; cursor: pointer;">
                <option value="CEASEFIRE">Ceasefire</option>
                <option value="TRADE">Trade Agreement</option>
                <option value="ALLIANCE">Grand Alliance</option>
              </select>
              <button id="btn-dip-propose" class="btn btn-primary" disabled style="flex: 1;">PROPOSE ACCORD</button>
              <button id="btn-dip-break" class="btn btn-danger" style="display: none;">REVOKE ACCORD</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  sentinelModal: `
    <div id="modal-sentinel" class="modal-overlay" style="display:none; position: fixed; inset: 0; background: rgba(0,20,30,0.95); z-index: var(--z-modal, 1200); justify-content: center; align-items: center; font-family: var(--font-mono);">
      <div class="panel" style="width: 800px; max-height: 80vh; display: flex; flex-direction: column; background: rgba(10,14,23,0.9); border: 2px solid var(--color-accent); pointer-events: auto;">
        
        <div class="panel-header" style="justify-content: space-between; border-bottom: 1px solid var(--color-accent); padding-bottom: 0.5rem;">
          <span style="color: var(--color-accent); text-shadow: 0 0 5px var(--color-accent); font-size: 1.2rem;">[ SENTINEL LAB ]</span>
          <button id="btn-close-sentinel" style="background: none; border: none; color: var(--color-accent); font-size: 1.5rem; cursor: pointer;">×</button>
        </div>

        <div style="display: flex; flex: 1; overflow: hidden; margin-top: 1rem; padding: 1rem; gap: 2rem;">
          
          <div style="flex: 1; display: flex; flex-direction: column; gap: 1rem;">
            <div style="color: #fff; font-family: var(--font-display); font-size: 1.2rem;">
               <span id="snt-name">NO SENTINEL FOUND</span>
            </div>
            <div style="font-size: 0.9rem; color: var(--color-text-muted);">SYS_STATUS: <span id="snt-status" style="color: var(--color-warning);">NOT INITIALIZED</span></div>
            
            <button id="btn-snt-create" class="btn btn-primary" style="display:none;">INITIALIZE SENTINEL</button>

            <div id="snt-controls" style="display: none; flex-direction: column; gap: 1rem;">
                <div>
                   <div style="display:flex; justify-content:space-between; color:var(--color-accent); font-size:0.8rem;">
                       <span>PERSISTENCE</span> <span id="val-persistence">0.50</span>
                   </div>
                   <input type="range" id="slider-persistence" min="0" max="100" value="50" style="width:100%; cursor: pointer;">
                </div>
                <div>
                   <div style="display:flex; justify-content:space-between; color:var(--color-accent); font-size:0.8rem;">
                       <span>STEALTH</span> <span id="val-stealth">0.50</span>
                   </div>
                   <input type="range" id="slider-stealth" min="0" max="100" value="50" style="width:100%; cursor: pointer;">
                </div>
                <div>
                   <div style="display:flex; justify-content:space-between; color:var(--color-accent); font-size:0.8rem;">
                       <span>EFFICIENCY</span> <span id="val-efficiency">0.50</span>
                   </div>
                   <input type="range" id="slider-efficiency" min="0" max="100" value="50" style="width:100%; cursor: pointer;">
                </div>
                <div>
                   <div style="display:flex; justify-content:space-between; color:var(--color-accent); font-size:0.8rem;">
                       <span>AGGRESSION</span> <span id="val-aggression">0.50</span>
                   </div>
                   <input type="range" id="slider-aggression" min="0" max="100" value="50" style="width:100%; cursor: pointer;">
                </div>

                <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                   <button id="btn-snt-save" class="btn btn-primary" style="flex: 1;">SAVE POLICY</button>
                   <button id="btn-snt-toggle" class="btn" style="flex: 1; color: var(--color-warning); border-color: var(--color-warning);">DEPLOY</button>
                </div>
            </div>
            
            <div style="margin-top: 1rem; flex: 1; border: 1px solid var(--color-accent); background: rgba(0,0,0,0.5); padding: 0.5rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.7rem;" id="snt-logs">
                <div style="color: var(--color-text-muted); font-style: italic;">[ OPERATIONAL LOGS ]</div>
            </div>
          </div>
          
          <div style="flex: 1; display: flex; justify-content: center; align-items: center; position: relative;">
            <canvas id="snt-radar-chart"></canvas>
          </div>

        </div>
      </div>
    </div>
  `,
  // ===== V4.1 PHANTOM MESH VIEWS =====
  leaderboard: `
    <div id="view-leaderboard" class="view v41-screen">
      <div class="v41-topbar">
        <span class="v41-topbar__brand">GRIDLOCK_V4.1</span>
        <div class="v41-topbar__actions">
          <button title="Settings">⚙</button>
        </div>
      </div>
      <div style="flex:1; overflow-y:auto; display:flex; flex-direction:column;">
        <div class="leaderboard-hub">
          <h1 class="leaderboard-hub__title">GLOBAL OPERATIVE LEADERBOARD HUB</h1>
          <div class="leaderboard-hub__controls">
            <div class="leaderboard-hub__tabs">
              <button class="leaderboard-hub__tab active" id="tab-rankings">GLOBAL RANKINGS</button>
              <button class="leaderboard-hub__tab" id="tab-hof">HALL OF FAME</button>
            </div>
            <div class="leaderboard-hub__search">
              <input type="text" id="lb-search" placeholder="SEARCH OPERATIVE" />
              <span class="icon">🔍</span>
            </div>
          </div>
          <table class="leaderboard-hub__table">
            <thead>
              <tr><th>RANK</th><th>OPERATIVE_ID</th><th>MISSION_XP</th><th>TIER</th><th>ACCORD_RATING</th><th></th></tr>
            </thead>
            <tbody id="lb-tbody"></tbody>
          </table>
          <div class="leaderboard-hub__footer">
            <button id="btn-lb-refresh" class="btn-v41">↻ REFRESH DATA</button>
            <button id="btn-lb-back" class="btn-v41">← RETURN TO COMMAND</button>
          </div>
        </div>
      </div>
    </div>
  `,
  meshHub: `
    <div id="view-mesh-hub" class="view v41-screen">
      <div class="v41-topbar">
        <span class="v41-topbar__brand">GRIDLOCK_V4.1</span>
        <div class="v41-topbar__nav">
          <span class="active">MISSION_LOGS</span>
          <span>MESH_NODES</span>
          <span>PHANTOM_SIG</span>
        </div>
        <div style="display:flex; align-items:center; gap:1rem;">
          <div class="v41-react-timer">
            <span class="v41-react-timer__label">REACT_PHASE</span>
            <span class="v41-react-timer__value" id="mesh-react-timer">00:15</span>
          </div>
          <div class="v41-topbar__actions">
            <button title="Globe">🌐</button>
            <button title="Map">🗺</button>
            <button title="Settings">⚙</button>
          </div>
        </div>
      </div>
      <div class="mesh-hub">
        <div class="v41-sidebar">
          <div class="v41-sidebar__profile">
            <div style="display:flex;gap:0.75rem;align-items:center;margin-bottom:0.5rem;">
              <div style="width:36px;height:36px;background:var(--panel-bg);border:1px solid var(--color-text-muted);display:flex;align-items:center;justify-content:center;">👤</div>
              <div>
                <div class="v41-sidebar__profile-name">PHANTOM_STRIKE</div>
                <div class="v41-sidebar__profile-rank">LEVEL_9_BREACHER</div>
              </div>
            </div>
          </div>
          <div class="v41-sidebar__nav">
            <button class="v41-sidebar__item active">⊕ ATTACK_VECTOR</button>
            <button class="v41-sidebar__item">🛡 DEFENSE_GRID</button>
            <button class="v41-sidebar__item">📡 VOID_SCAN</button>
            <button class="v41-sidebar__item">🔐 NULL_ROOT</button>
            <button class="v41-sidebar__item" style="margin-top:auto;">⏻ EXIT_NODE</button>
          </div>
          <div class="v41-sidebar__bottom">
            <button class="btn-init-ghost" id="btn-init-ghost">INITIALIZE_GHOST</button>
            <div style="display:flex;gap:1rem;font-size:var(--text-xs);color:var(--color-text-muted);">
              <span>⊕ SYS_OK</span>
              <span>🔒 ENC_ON</span>
            </div>
          </div>
        </div>
        <div class="mesh-hub__main">
          <div class="mesh-hub__status-bar">
            <div class="mesh-hub__mesh-status">
              <h2>MESH_STATUS: <span class="stable" id="mesh-status-val">STABLE</span></h2>
              <div class="mesh-hub__metrics">
                <div><span>PACKET EFFICIENCY</span><span class="value" id="mesh-pkt-eff">99.2%</span></div>
                <div><span>GHOST NODES</span><span class="value" id="mesh-ghost-count" style="color:var(--color-amber)">04</span></div>
                <div><span>BANDWIDTH CONSUMPTION</span><span class="value" id="mesh-bw">2.4 TB/S</span></div>
              </div>
            </div>
            <div class="mesh-hub__latency-box">
              <div class="metric"><div class="label">LATENCY</div><div class="value" id="mesh-latency">14MS</div></div>
              <div class="metric"><div class="label">THREATS</div><div class="value" id="mesh-threats" style="color:var(--color-stable)">LOW</div></div>
            </div>
          </div>
          <div class="mesh-hub__canvas"><canvas id="mesh-topology-canvas"></canvas></div>
          <div class="mesh-hub__terminal">
            <div class="mesh-hub__terminal-header">
              <span>TER NODE_SEC_A</span>
              <span class="close-indicator"></span>
            </div>
            <div class="mesh-hub__terminal-log" id="mesh-term-log">
              <div class="log-sys">>> INITIALIZING_SEQUENCE_V4.1...</div>
              <div class="log-info">[INFO] SCANNING_SUBNET_NODES... OK</div>
              <div class="log-info">[INFO] DECRYPTION_KEYS_LOADED</div>
              <div class="log-warn">[WARN] PHANTOM_SIG_DETECTED_0x88X</div>
              <div class="log-auth">[AUTH] PENDING_HANDSHAKE_NODE_C</div>
              <div class="log-sys">>> _</div>
            </div>
            <div class="mesh-hub__terminal-input">
              <span>>_</span>
              <input type="text" placeholder="ENTER_COMMAND..." id="mesh-term-input" />
            </div>
          </div>
          <div class="mesh-hub__footer">
            <span>LOC: [40.7128, -74.0060]</span>
            <span>TZ: UTC-5_PHANTOM</span>
            <span class="phantom-mode">GHOST_MODE_ENABLED: YES</span>
          </div>
        </div>
      </div>
    </div>
  `,
  campaign: `
    <div id="view-campaign" class="view v41-screen">
      <div class="v41-topbar">
        <span class="v41-topbar__brand">GRIDLOCK_V4.1</span>
        <div class="v41-topbar__actions"><button>⚙</button></div>
      </div>
      <div class="campaign__player-bar">
        <div class="campaign__player-stat">PLAYER RANK: <span class="value">SENIOR OPERATIVE</span></div>
        <div class="campaign__player-stat" style="border-color:var(--color-stable);">CURRENT LEVEL: <span class="value">4</span></div>
        <div class="campaign__player-stat" style="border-color:var(--color-amber);">TOTAL XP: <span class="value">45,200/50,000</span></div>
      </div>
      <h1 class="campaign__title">CAMPAIGN MISSION CONTROL BOARD</h1>
      <div class="campaign__subtitle">Neo-Hack: Gridlock v4.1.0</div>
      <div class="campaign__cards" id="campaign-cards">
        <div class="campaign__card completed">
          <span class="campaign__card-status completed">COMPLETED</span>
          <div class="campaign__card-mission">MISSION 1:</div>
          <div class="campaign__card-title">CORE SYSTEMS TUTORIAL</div>
          <div style="font-family:var(--font-title);font-size:var(--text-xl);color:var(--color-stable);margin:0.5rem 0;">RANK: A ✓</div>
          <div class="campaign__card-brief">Infiltrate Berylia Central... Learn the basics of neural hacking, node manipulation, and system breaches.</div>
          <div class="campaign__card-rewards">
            <div>REWARDS:</div>
            <div class="xp">XP: +1500</div>
            <div class="kits">NEW EXPLOIT KITS: Basic Data Tap</div>
          </div>
        </div>
        <div class="campaign__card active">
          <span class="campaign__card-status active">ACTIVE</span>
          <div class="campaign__card-mission">MISSION 2:</div>
          <div class="campaign__card-title">THE BERYLIA BANK RUN</div>
          <div style="font-size:var(--text-xs);color:var(--color-text-muted);margin:0.25rem 0;">DIFFICULTY: NORMAL</div>
          <div class="campaign__card-brief">Breach the central vault of the Berylia Corporation. Extract encrypted financial data before the security grid locks down.</div>
          <div class="campaign__card-rewards">
            <div>REWARDS:</div>
            <div class="xp">XP: +4500</div>
            <div class="kits">NEW EXPLOIT KITS: Encryption Bypass, Decoy Signal</div>
          </div>
        </div>
        <div class="campaign__card locked">
          <span class="campaign__card-status locked">🔒 LOCKED</span>
          <div class="campaign__card-mission">MISSION 3:</div>
          <div class="campaign__card-title">SILICON SILK ROAD HEIST</div>
          <div style="font-size:var(--text-xs);color:var(--color-scarlet);margin:0.25rem 0;">REQUIREMENT: LEVEL 5</div>
          <div class="campaign__card-brief">Intercept a high value data convoy on the Silicon Silk Road. Secure exotic hardware prototypes.</div>
          <div class="campaign__card-rewards">
            <div>REWARDS:</div>
            <div class="xp">XP: +6000</div>
            <div class="kits">NEW EXPLOIT KITS: Advanced Network Scanner, Virus Injector</div>
          </div>
        </div>
        <div class="campaign__card locked">
          <span class="campaign__card-status locked">🔒 LOCKED</span>
          <div class="campaign__card-mission">MISSION 4:</div>
          <div class="campaign__card-title">OPERATION BLACKOUT</div>
          <div style="font-size:var(--text-xs);color:var(--color-scarlet);margin:0.25rem 0;">REQUIREMENT: LEVEL 8</div>
          <div class="campaign__card-brief">Execute a coordinated strike on the city's main power grid. Create chaos and disrupt corporate operations.</div>
          <div class="campaign__card-rewards">
            <div>REWARDS:</div>
            <div class="xp">XP: +8500</div>
            <div class="kits">NEW EXPLOIT KITS: EMP Disruptor, Stealth Protocol</div>
          </div>
        </div>
        <div class="campaign__card locked">
          <span class="campaign__card-status locked">🔒 LOCKED</span>
          <div class="campaign__card-mission">MISSION 5:</div>
          <div class="campaign__card-title">OPERATION CRIMSON TIDE</div>
          <div style="font-size:var(--text-xs);color:var(--color-scarlet);margin:0.25rem 0;">REQUIREMENT: LEVEL 12</div>
          <div class="campaign__card-brief">Infiltrate the highest security tier of the Neo-Tokyo Corporate Tower. Access the mainframe and initiate the Crimson Tide data wipe.</div>
          <div class="campaign__card-rewards">
            <div>REWARDS:</div>
            <div class="xp">XP: +12000</div>
            <div class="kits">NEW EXPLOIT KITS: Master Key, AI Override</div>
          </div>
        </div>
      </div>
      <div class="campaign__footer">
        <button id="btn-camp-back" class="btn-v41">← BACK</button>
        <button class="btn-v41 primary">LAUNCH MISSION</button>
      </div>
    </div>
  `,
  reactPhase: `
    <div id="view-react-phase" class="react-phase">
      <div class="v41-topbar" style="border-bottom-color:rgba(255,0,85,0.3);">
        <span class="v41-topbar__brand">GRIDLOCK_V4.1</span>
        <div class="v41-topbar__nav">
          <span>SEC_LEVEL_OMEGA</span>
          <span style="color:var(--color-scarlet);">BREACH_DETECTED</span>
        </div>
        <div class="v41-topbar__actions"><button>🗺</button><button>🌐</button></div>
      </div>
      <div class="react-phase__banner">
        <h1>REACT NOW</h1>
        <div class="subtitle">S Y S T E M _ I N T E G R I T Y _ C O M P R O M I S E D</div>
      </div>
      <div class="react-phase__body">
        <div>
          <div class="react-phase__logs" id="rp-logs">
            <div class="header"><span>LOGS_041</span><span style="color:var(--color-accent);">●</span></div>
            <div class="entry warn">> ENCRYPT_FAIL: BLOCK_77</div>
            <div class="entry">> HANDSHAKE_TIMEOUT</div>
            <div class="entry info">> RE-ROUTING_NODE_01</div>
            <div class="entry">> BUFFER_OVERFLOW_NULL</div>
            <div class="entry warn">> ROOT_CA_REVOKED</div>
            <div class="entry">> INJECTING_PHANTOM_SIG</div>
            <div class="entry">> BYPASSING_FIREWALL_3</div>
            <div class="entry warn">> CRITICAL_FAILURE_SEC</div>
          </div>
          <div class="react-phase__stability">
            <div class="label">SYSTEM_STABILITY</div>
            <div class="value" id="rp-stability">14%</div>
          </div>
        </div>
        <div class="react-phase__countdown">
          <div class="timer">
            <div class="timer-value" id="rp-timer">15</div>
          </div>
          <div class="timer-label">M I L L I S E C O N D S _ R E M A I N I N G</div>
          <div class="react-phase__qte" id="rp-qte-keys">
            <div class="react-phase__qte-key" data-key="w">W</div>
            <div class="react-phase__qte-key" data-key="a">A</div>
            <div class="react-phase__qte-key pressed" data-key="s">S</div>
            <div class="react-phase__qte-key" data-key="d">D</div>
          </div>
          <div class="react-phase__qte-label">EXECUTE COUNTER-PATTERN SEQUENCE</div>
        </div>
        <div class="react-phase__intel">
          <div class="react-phase__success">
            <div class="label">ATTACKER_SUCCESS</div>
            <div class="value" id="rp-atk-pct">84%</div>
            <div class="bar"><div class="bar-fill" id="rp-atk-bar" style="width:84%;"></div></div>
          </div>
          <div style="border:1px solid var(--color-amber);border-top:4px dashed var(--color-amber);padding:1rem;font-size:var(--text-xs);">
            <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;"><span>NODE_ADDR</span><span style="color:var(--color-accent);">0x88.92.11.4</span></div>
            <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;"><span>PACKET_SIZE</span><span style="color:var(--color-accent);">4.8 GB/S</span></div>
            <div style="display:flex;justify-content:space-between;"><span>THREAT_ORIGIN</span><span style="color:var(--color-scarlet);">VOID_NULL</span></div>
          </div>
          <div style="text-align:center;margin-top:1rem;">
            <div style="font-size:3rem;color:var(--color-scarlet);">⚠</div>
            <div style="color:var(--color-scarlet);letter-spacing:2px;font-size:var(--text-xs);">FIREWALL_CRITICAL</div>
          </div>
        </div>
      </div>
      <div class="react-phase__cta"><button id="btn-counter-measure">I N I T I A L I Z E _ C O U N T E R _ M E A S U R E</button></div>
      <div style="display:flex;justify-content:space-between;padding:0.75rem 1.5rem;border-top:1px solid rgba(0,255,221,0.1);font-size:var(--text-xs);color:var(--color-text-muted);">
        <div><span>ACTIVE VECTOR</span> <span style="color:var(--color-accent);">MESH_NODE_SIGMA_7</span></div>
        <div><span>LATENCY</span> <span style="color:var(--color-accent);">0.002 MS</span></div>
        <div><span>PROTOCOL</span> <span style="color:var(--color-accent);">GHOST_SHELL_V2</span></div>
        <div style="text-align:right;"><div style="color:var(--color-scarlet);letter-spacing:1px;">EMERGENCY_OVERRIDE</div><div style="color:var(--color-accent);">STRIKE_CONFIRMED_01</div></div>
      </div>
    </div>
  `
};

// --- Leaderboard Data ---
const LEADERBOARD_DATA = [
  { rank: 1, id: 'VIXEN-01', faction: 'Cyber-Syndicate', xp: 1250000, tier: 'Master Specialist', rating: '99.8%', badge: 'gold' },
  { rank: 2, id: 'CYPHER_KAI', faction: 'Cyber-Syndicate', xp: 1180500, tier: 'Elite Agent', rating: '99.5%', badge: 'silver' },
  { rank: 3, id: 'NEO_STALKER', faction: 'Cyber-Syndicate', xp: 1100200, tier: 'Elite Agent', rating: '99.2%', badge: 'bronze' },
  { rank: 4, id: 'GHOST_RIDER', faction: '', xp: 980000, tier: 'Advanced Operative', rating: '98.9%' },
  { rank: 5, id: 'BLADE_RUNNER', faction: '', xp: 950100, tier: 'Advanced Operative', rating: '98.5%' },
  { rank: 6, id: 'PHANTOM_X', faction: '', xp: 925000, tier: 'Operative', rating: '98.0%' },
];

function populateLeaderboard() {
  const tbody = document.getElementById('lb-tbody');
  if (!tbody) return;
  const currentPlayer = AppState.player.username || 'PLAYER_ID: NOCTURNE';
  let html = '';
  LEADERBOARD_DATA.forEach(p => {
    const isTop3 = p.rank <= 3;
    html += `<tr class="${isTop3 ? 'top-3' : ''}">
      <td>${isTop3 ? `<div class="leaderboard-hub__rank-badge ${p.badge}">${p.rank}</div>` : p.rank}</td>
      <td><strong>${p.id}</strong>${p.faction ? `<br/><span style="font-size:0.7rem;color:var(--color-text-muted);">▪ ${p.faction}</span>` : ''}</td>
      <td>${p.xp.toLocaleString()}</td><td>${p.tier}</td><td>${p.rating}</td>
      <td>${isTop3 ? '<button class="btn-v41" style="font-size:0.7rem;padding:0.3rem 0.75rem;">VIEW PROFILE ></button>' : ''}</td>
    </tr>`;
  });
  // Current player row
  html += `<tr class="current-player">
    <td>7</td><td><strong style="color:var(--color-accent);">${currentPlayer}</strong></td>
    <td>890,000</td><td>Operative</td><td>97.5%</td>
    <td><button class="btn-v41" style="font-size:0.7rem;padding:0.3rem 0.75rem;">VIEW PROFILE ></button></td>
  </tr>`;
  tbody.innerHTML = html;
}

// --- Core App Logic ---
async function initApp() {
  const appElement = document.getElementById('app');
  
  // Inject HTML — login view is the first screen
  appElement.innerHTML = views.login + views.menu + views.game + views.leaderboard + views.meshHub + views.campaign + views.reactPhase + views.gameover + views.settingsModal + views.diplomacyModal + views.sentinelModal;

  // Ensure only the login view is active initially
  navigateTo('login');

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

      api.connectWebSocket();
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
      
      api.connectWebSocket();
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
  subtitle.innerHTML = 'v4.1.0 // CONTACTING SERVER...';

  const health = await api.health();
  if (health.status === 'healthy') {
    subtitle.innerHTML = 'v4.1.0 // SYSTEM <span style="color:var(--color-player)">ONLINE</span>';
  } else {
    subtitle.innerHTML = 'v4.1.0 // SYSTEM <span style="color:var(--color-enemy)">OFFLINE</span> (GUEST MODE)';
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
    const scenarioId = document.getElementById('sel-scenario').value;
    navigateTo('game');
    if (window.PromoInstance) window.PromoInstance.stop();
    if (window.DemoInstance) {
      window.DemoInstance.start(scenarioId);
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
  
  // Add v4.1 menu buttons dynamically
  const menuButtons = document.querySelector('.menu-buttons');

  const meshBtn = document.createElement('button');
  meshBtn.className = 'btn';
  meshBtn.innerText = '◈ MESH COMMAND HUB';
  meshBtn.id = 'btn-mesh-hub';
  meshBtn.style.cssText = 'color: var(--color-accent); border-color: var(--color-accent);';
  menuButtons.appendChild(meshBtn);

  const campBtn = document.createElement('button');
  campBtn.className = 'btn';
  campBtn.innerText = '⊞ CAMPAIGN';
  campBtn.id = 'btn-campaign';
  campBtn.style.cssText = 'color: var(--color-warning); border-color: var(--color-warning);';
  menuButtons.appendChild(campBtn);

  const lbBtn = document.createElement('button');
  lbBtn.className = 'btn';
  lbBtn.innerText = '⊟ LEADERBOARD';
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

  // v4.1 Navigation handlers
  document.getElementById('btn-mesh-hub').addEventListener('click', () => navigateTo('mesh-hub'));
  document.getElementById('btn-campaign').addEventListener('click', () => navigateTo('campaign'));
  document.getElementById('btn-leaderboard').addEventListener('click', () => navigateTo('leaderboard'));
  document.getElementById('btn-lb-back').addEventListener('click', () => navigateTo('menu'));
  document.getElementById('btn-camp-back').addEventListener('click', () => navigateTo('menu'));

  // Initialize v4.1 leaderboard with placeholder data
  populateLeaderboard();
  
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
      if (!e.key) return;
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
  initDiplomacyEvents();
  
  // Init Game Engine and Demo
  window.GameInstance = new GameEngine();
  window.TerminalInstance = new TerminalManager(window.GameInstance);
  window.DemoInstance = new DemoManager(window.GameInstance);
  window.PromoInstance = new PromoManager(window.GameInstance);

  // Init v4.1 Components
  window.MeshHubInstance = new MeshHub('mesh-topology-canvas');
  window.ReactPhaseInstance = new ReactPhase();
  window.LeaderboardInstance = new LeaderboardHub();
  window.GhostDeployInstance = new GhostDeploy();
  window.CampaignInstance = new Campaign();

  // Start/stop mesh canvas based on view navigation
  window.addEventListener('viewChanged', (e) => {
    if (e.detail.view === 'mesh-hub') {
      window.MeshHubInstance?.start();
    } else {
      window.MeshHubInstance?.stop();
    }
  });
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
