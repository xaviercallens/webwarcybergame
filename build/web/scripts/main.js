import { GameEngine } from './game-engine.js';
import { DemoManager } from './demo-manager.js';
import { PromoManager } from './promo-manager.js';
import { api } from './api-client.js';
import { audio } from './audio-manager.js';
import { initUI, initDiplomacyEvents } from './ui-manager.js';
import { TerminalManager } from './terminal-manager.js';

// v3.2 Modules
import { events, Events } from './game-events.js';
import { StateMachine, ViewState } from './state-machine.js';
import { TurnController } from './turn-controller.js';
import { FogOfWar } from './fog-of-war.js';
import { HotkeyManager } from './hotkey-manager.js';
import { GamepadManager } from './gamepad-manager.js';
import { AccessibilityManager } from './accessibility.js';
import { NodeTooltip } from './components/NodeTooltip.js';
import { ContextMenu } from './components/ContextMenu.js';
import { LogPanel } from './components/LogPanel.js';
import { ToastManager } from './components/Toast.js';
import { Briefing } from './components/Briefing.js';
import { Debrief } from './components/Debrief.js';
import { PauseMenu } from './components/PauseMenu.js';
import { HelpOverlay } from './components/HelpOverlay.js';
import { TutorialEngine } from './tutorial/tutorial-engine.js';

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
        <div class="menu-subtitle">v3.2.0 // AUTHENTICATION REQUIRED</div>
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
        <div class="menu-subtitle">v3.2.0 // SYSTEM ONLINE</div>
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
            <option value="crimson_tide">05 : OPERATION CRIMSON TIDE</option>
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
  roleSelect: `
    <div id="view-role_select" class="view screen-menu" role="region" aria-label="Role Selection">
      <div class="menu-title-container">
        <h1>NEO-HACK</h1>
        <h1 style="color: #fff">GRIDLOCK</h1>
        <div class="menu-subtitle">v3.2.0 // SELECT ROLE</div>
      </div>

      <div style="display: flex; gap: 2rem; justify-content: center; margin-top: 2rem; flex-wrap: wrap;">
        <!-- Attacker Card -->
        <div class="role-card role-card--attacker" tabindex="0" data-role="attacker" role="button" aria-label="Play as Attacker"
          style="width: 320px; padding: 2rem; border: 2px solid var(--color-enemy); background: rgba(255,0,85,0.08); cursor: pointer; text-align: center; transition: all 0.2s ease; position: relative;">
          <div style="font-size: 3rem; margin-bottom: 1rem;">&#x1F4BB;</div>
          <h2 style="color: var(--color-enemy); font-family: var(--font-display); margin: 0 0 0.5rem;">ATTACKER</h2>
          <div style="color: var(--color-enemy); font-size: 0.8rem; letter-spacing: 2px; margin-bottom: 1rem;">[ SCARLET PROTOCOL ]</div>
          <ul style="text-align: left; color: var(--color-text-muted); font-family: var(--font-mono); font-size: 0.8rem; list-style: none; padding: 0; line-height: 1.8;">
            <li>&#x25B8; 3 Action Points / turn</li>
            <li>&#x25B8; 5 Exploit Kits (consumable)</li>
            <li>&#x25B8; Stealth meter (starts 100%)</li>
            <li>&#x25B8; Fog of War — discover nodes</li>
            <li>&#x25B8; Win: Exfiltrate target data</li>
          </ul>
          <div style="margin-top: 1rem; padding: 0.5rem; border: 1px dashed var(--color-enemy); color: var(--color-enemy); font-family: var(--font-mono); font-size: 0.75rem;">
            FAST START | RESOURCE-LIMITED | HIGH RISK
          </div>
        </div>

        <!-- Defender Card -->
        <div class="role-card role-card--defender" tabindex="0" data-role="defender" role="button" aria-label="Play as Defender"
          style="width: 320px; padding: 2rem; border: 2px solid var(--color-player); background: rgba(0,255,221,0.08); cursor: pointer; text-align: center; transition: all 0.2s ease; position: relative;">
          <div style="font-size: 3rem; margin-bottom: 1rem;">&#x1F6E1;</div>
          <h2 style="color: var(--color-player); font-family: var(--font-display); margin: 0 0 0.5rem;">DEFENDER</h2>
          <div style="color: var(--color-player); font-size: 0.8rem; letter-spacing: 2px; margin-bottom: 1rem;">[ IRON BASTION ]</div>
          <ul style="text-align: left; color: var(--color-text-muted); font-family: var(--font-mono); font-size: 0.8rem; list-style: none; padding: 0; line-height: 1.8;">
            <li>&#x25B8; 2 AP / turn (scales to 3 at alert 50%+)</li>
            <li>&#x25B8; 8 Incident Response budget</li>
            <li>&#x25B8; Alert meter — unlocks IR tools</li>
            <li>&#x25B8; Full map visibility</li>
            <li>&#x25B8; Win: Survive 20 turns or isolate attacker</li>
          </ul>
          <div style="margin-top: 1rem; padding: 0.5rem; border: 1px dashed var(--color-player); color: var(--color-player); font-family: var(--font-mono); font-size: 0.75rem;">
            SLOW START | SCALING POWER | TIME ADVANTAGE
          </div>
        </div>
      </div>

      <div style="text-align: center; margin-top: 2rem;">
        <div style="color: var(--color-text-muted); font-family: var(--font-mono); font-size: 0.8rem; margin-bottom: 1rem;">
          SCENARIO: <span id="role-scenario-label" style="color: var(--color-accent);">SANDBOX</span>
          &nbsp;|&nbsp; DIFFICULTY: <span id="role-diff-label" style="color: var(--color-accent);">INTERMEDIATE</span>
        </div>
        <button id="btn-role-back" class="btn" style="min-width: 120px;">&#x25C0; BACK</button>
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
        <button id="btn-lab" class="btn btn-primary" style="position:absolute; top: 4rem; right: 1rem; min-width: 130px; box-shadow: 0 0 10px rgba(0, 255, 221, 0.4); z-index: 1000;">SENTINEL LAB</button>
        
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
          <div>Tap <span style="color: var(--color-player); font-weight: bold;">[\`]</span> or <span style="color: var(--color-player); font-weight: bold;">[C]</span> : Toggle Terminal CLI</div>
          <div>Tap <span style="color: var(--color-player); font-weight: bold;">[Space]</span> : Pause / Resume Time</div>
        </div>

        <!-- Terminal Overlay -->
        <div id="terminal-panel" style="display:none; position: absolute; inset: 0; background: rgba(0,20,30,0.95); z-index: 200; font-family: var(--font-mono); color: var(--color-player); padding: 2rem; flex-direction: column;">
          <div style="flex: 1; overflow-y: auto; margin-bottom: 1rem; padding-right: 1rem;" id="terminal-output">
            <div style="color: var(--color-accent); margin-bottom: 1rem;">Neo-Hack OS v2.0.1 - Terminal Access Granted. Type /help for commands.</div>
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
    <div id="modal-sentinel" class="modal-overlay" style="display:none; position: fixed; inset: 0; background: rgba(0,20,30,0.95); z-index: 1000; justify-content: center; align-items: center; font-family: var(--font-mono);">
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
  `
};

// --- Core App Logic ---
async function initApp() {
  const appElement = document.getElementById('app');
  
  // Inject HTML — login view is the first screen
  appElement.innerHTML = views.login + views.menu + views.roleSelect + views.game + views.leaderboard + views.gameover + views.settingsModal + views.diplomacyModal + views.sentinelModal;

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

  // --- v3.2 Turn-Based Play Flow ---
  // Store selected settings for the role select screen
  let pendingScenario = null;

  btnPlay.addEventListener('click', () => {
    pendingScenario = null; // sandbox
    navigateTo('role_select');
    const scenarioLabel = document.getElementById('role-scenario-label');
    const diffLabel = document.getElementById('role-diff-label');
    if (scenarioLabel) scenarioLabel.textContent = 'SANDBOX';
    if (diffLabel) diffLabel.textContent = selDiff ? selDiff.value : 'INTERMEDIATE';
  });

  document.getElementById('btn-demo').addEventListener('click', () => {
    pendingScenario = document.getElementById('sel-scenario').value;
    navigateTo('role_select');
    const scenarioLabel = document.getElementById('role-scenario-label');
    const diffLabel = document.getElementById('role-diff-label');
    if (scenarioLabel) scenarioLabel.textContent = (pendingScenario || 'SANDBOX').toUpperCase().replace(/_/g, ' ');
    if (diffLabel) diffLabel.textContent = selDiff ? selDiff.value : 'INTERMEDIATE';
  });

  // Role select card click handlers
  document.querySelectorAll('.role-card').forEach(card => {
    const startGame = () => {
      const role = card.dataset.role;
      const difficulty = selDiff ? selDiff.value.toLowerCase() : 'intermediate';
      const scenario = pendingScenario || 'default';

      // Navigate to game view
      navigateTo('game');

      // Stop any running demo/promo
      if (window.DemoInstance) window.DemoInstance.stop();
      if (window.PromoInstance) window.PromoInstance.stop();

      // Init the renderer
      if (window.GameInstance) window.GameInstance.init(difficulty.toUpperCase());

      // Start turn-based game via V32 controller
      if (window.V32 && window.V32.turnController) {
        window.V32.turnController.startGame({ role, difficulty, scenario });

        // Show briefing if available
        if (window.V32.briefing) {
          window.V32.briefing.show({ role, scenario, difficulty });
        }

        // Start tutorial for tutorial scenario
        if (scenario === 'tutorial' && window.V32.tutorial) {
          window.V32.tutorial.start();
        }
      }
    };

    card.addEventListener('click', startGame);
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); startGame(); }
    });
  });

  // Role select back button
  document.getElementById('btn-role-back').addEventListener('click', () => {
    navigateTo('menu');
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
      // Don't trigger if user is typing in any input/textarea field
      const tag = document.activeElement ? document.activeElement.tagName : '';
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
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

  // --- v3.2 Systems Init ---
  window.V32 = initV32Systems();
}

/** Initialize all v3.2 turn-based and UI systems */
function initV32Systems() {
  const stateMachine = new StateMachine();
  const turnController = new TurnController();
  const fogOfWar = new FogOfWar();
  const hotkeyManager = new HotkeyManager();
  const gamepadManager = new GamepadManager();
  const a11y = new AccessibilityManager();

  // UI overlays
  const tooltip = new NodeTooltip();
  const contextMenu = new ContextMenu();
  const toastManager = new ToastManager();
  const briefing = new Briefing();
  const debrief = new Debrief();
  const pauseMenu = new PauseMenu();
  const helpOverlay = new HelpOverlay(hotkeyManager);
  const tutorial = new TutorialEngine();

  // Log panel (attach to game UI container)
  const gameUI = document.querySelector('.game-ui') || document.getElementById('hud-layer');
  const logPanel = gameUI ? new LogPanel(gameUI) : null;

  // Load saved hotkey bindings
  hotkeyManager.load();
  gamepadManager.enable();

  // --- Wire renderer to game state updates ---
  events.on(Events.GAME_STATE_UPDATE, ({ gameState }) => {
    if (window.GameInstance && window.GameInstance.renderer) {
      window.GameInstance.renderer.renderGameState(gameState);
    }
  });

  // --- Wire state machine to navigateTo ---
  events.on(Events.VIEW_CHANGE, ({ to }) => {
    navigateTo(to);
  });

  // --- Hotkey routing ---
  events.on(Events.HOTKEY, ({ action }) => {
    switch (action) {
      case 'cancel':
        if (helpOverlay.isOpen) { helpOverlay.hide(); return; }
        if (pauseMenu.isOpen) { pauseMenu.hide(); return; }
        if (stateMachine.current === ViewState.GAME) {
          stateMachine.transitionTo(ViewState.PAUSE);
          pauseMenu.show().then(result => {
            if (result === 'resume') stateMachine.transitionTo(ViewState.GAME);
            else if (result === 'quit') stateMachine.transitionTo(ViewState.MENU);
            else if (result === 'help') helpOverlay.show();
            else if (result === 'settings') {
              document.getElementById('modal-settings')?.classList.add('active');
              stateMachine.transitionTo(ViewState.GAME);
            }
          });
        }
        break;
      case 'help':
        helpOverlay.toggle();
        break;
      case 'toggle_console':
        const termPanel = document.getElementById('terminal-panel');
        if (termPanel) {
          termPanel.style.display = termPanel.style.display === 'none' ? 'flex' : 'none';
          events.emit(Events.CONSOLE_TOGGLE, {});
        }
        break;
      case 'toggle_log':
        if (logPanel) logPanel.toggle();
        break;
      case 'toggle_mission':
        const mp = document.getElementById('mission-panel');
        if (mp) mp.style.display = mp.style.display === 'none' ? 'block' : 'none';
        break;
    }
  });

  // --- Turn end routing ---
  events.on(Events.TURN_END, () => {
    turnController.endTurn();
  });

  // --- Game over routing ---
  events.on(Events.GAME_OVER, async (data) => {
    const choice = await debrief.show(data);
    if (choice === 'replay') {
      stateMachine.forceState(ViewState.MENU);
      stateMachine.transitionTo(ViewState.ROLE_SELECT);
    } else {
      stateMachine.forceState(ViewState.DEBRIEF);
      stateMachine.transitionTo(ViewState.MENU);
    }
  });

  // Expose for debugging
  return {
    stateMachine, turnController, fogOfWar,
    hotkeyManager, gamepadManager, a11y,
    tooltip, contextMenu, toastManager, logPanel,
    briefing, debrief, pauseMenu, helpOverlay, tutorial,
  };
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
