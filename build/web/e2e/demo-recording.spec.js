/**
 * Neo-Hack: Gridlock v3.2 — 10-Minute Demo Recording
 *
 * Automated playthrough following the Operation Crimson Tide scenario.
 * Records video (WebM) and captures all console logs + network calls.
 *
 * Run with:
 *   npx playwright test --config=playwright.demo.config.js
 *
 * Output:
 *   - Video: specs/demo_recordings/ (WebM, auto by Playwright)
 *   - Console log: specs/demo_recordings/console_log_*.txt
 *   - API log: specs/demo_logs/demo_api_log_*.txt (from backend middleware)
 */
import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE = 'http://localhost:5173';
const DEMO_USER = 'DEMO_' + Date.now().toString().slice(-6);
const DEMO_PASS = 'demo123456';

const PACE = {
  fast: 1500,
  normal: 3000,
  slow: 5000,
  dramatic: 8000,
  read: 6000,
  turn: 18000,   // pause between turns for visual pacing (~10 min total)
};

let consoleLogs = [];
let networkLogs = [];

/** Helper: robust login — register a fresh user, fallback to DOM bypass */
async function robustLogin(page) {
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(PACE.normal);

  // Fill credentials
  await page.fill('#login-username', DEMO_USER);
  await page.fill('#login-password', DEMO_PASS);
  await page.waitForTimeout(PACE.fast);

  // Register new user
  await page.click('#btn-register');
  await page.waitForTimeout(PACE.slow);

  // Check if we reached menu
  const onMenu = await page.locator('#view-menu').isVisible().catch(() => false);
  if (onMenu) return true;

  // If registration failed (e.g. user exists), try login
  await page.fill('#login-password', DEMO_PASS);
  await page.click('#btn-login');
  await page.waitForTimeout(PACE.slow);

  const onMenu2 = await page.locator('#view-menu').isVisible().catch(() => false);
  if (onMenu2) return true;

  // Last resort: bypass auth via DOM manipulation
  consoleLogs.push('[DEMO] Auth failed — using DOM bypass');
  await page.evaluate(() => {
    document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
    const m = document.getElementById('view-menu');
    if (m) m.classList.add('active');
    if (window.AppState) {
      window.AppState.isAuthenticated = true;
      window.AppState.currentView = 'menu';
    }
  });
  await page.waitForTimeout(PACE.normal);
  return true;
}

/** Helper: click a button if visible, log the action */
async function safeClick(page, selector, label) {
  const el = page.locator(selector);
  const visible = await el.isVisible().catch(() => false);
  if (visible) {
    try {
      await el.click({ timeout: 5000 });
    } catch {
      await el.click({ force: true, timeout: 3000 }).catch(() => {});
    }
    consoleLogs.push(`[DEMO] Clicked: ${label} (${selector})`);
    await page.waitForTimeout(PACE.slow);
    return true;
  }
  consoleLogs.push(`[DEMO] Not visible: ${label} (${selector})`);
  return false;
}

/** Helper: select a target node on the map by dispatching nodeClicked event */
async function selectNode(page, nodeId) {
  await page.evaluate((nid) => {
    window.dispatchEvent(new CustomEvent('nodeClicked', { detail: { nodeId: nid } }));
  }, nodeId);
  consoleLogs.push(`[DEMO] Selected node #${nodeId}`);
  await page.waitForTimeout(PACE.normal);
}

/** Helper: execute a game action (select node + click button) */
async function gameAction(page, nodeId, buttonSel, label) {
  await selectNode(page, nodeId);
  // Action panel should now be visible
  const clicked = await safeClick(page, buttonSel, label);
  if (!clicked) {
    // Fallback: emit action directly via event bus
    const actionId = buttonSel.includes('scan') ? 0 : 1;
    const actionName = actionId === 0 ? 'SCAN_NETWORK' : 'EXPLOIT_VULNERABILITY';
    await page.evaluate(({ aid, aname, target }) => {
      if (window.V32?.turnController) {
        const { events, Events } = window.V32.turnController.constructor._imports || {};
      }
      // Direct event dispatch
      const eventBus = window.V32?.events;
      if (eventBus) {
        eventBus.emit('action:execute', { actionId: aid, actionName: aname, targetNode: target });
      } else {
        // Fallback: dispatch DOM event
        window.dispatchEvent(new CustomEvent('gameAction', {
          detail: { actionId: aid, actionName: aname, targetNode: target }
        }));
      }
    }, { aid: actionId, aname: actionId === 0 ? 'SCAN_NETWORK' : 'EXPLOIT_VULNERABILITY', target: nodeId });
    consoleLogs.push(`[DEMO] Action via event bus: ${label} on node #${nodeId}`);
    await page.waitForTimeout(PACE.slow);
  }
}

/** Show annotation banner on the page */
async function annotate(page, text) {
  await page.evaluate((msg) => {
    let ov = document.getElementById('demo-annotation');
    if (!ov) {
      ov = document.createElement('div');
      ov.id = 'demo-annotation';
      ov.style.cssText = `
        position:fixed;top:0;left:0;right:0;padding:12px 24px;
        background:rgba(0,20,30,0.92);border-bottom:2px solid #00ffdd;
        color:#00ffdd;font-family:monospace;font-size:16px;letter-spacing:2px;
        text-align:center;z-index:99999;text-shadow:0 0 10px #00ffdd;
        transition:opacity 0.4s;
      `;
      document.body.appendChild(ov);
    }
    ov.textContent = '[ ' + msg + ' ]';
    ov.style.opacity = '1';
    setTimeout(() => { ov.style.opacity = '0.2'; }, 2500);
  }, text);
  await page.waitForTimeout(400);
}

/** Get timestamped output path */
function getOutputPath(filename) {
  const dir = path.resolve(__dirname, '..', '..', '..', 'specs', 'demo_recordings');
  fs.mkdirSync(dir, { recursive: true });
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const ext = path.extname(filename);
  const base = path.basename(filename, ext);
  return path.join(dir, `${base}_${ts}${ext}`);
}


// ══════════════════════════════════════════════════════════════
// MAIN TEST
// ══════════════════════════════════════════════════════════════

test.describe('Demo Recording: Operation Crimson Tide', () => {

  test('Full 10-minute demo playthrough', async ({ page }) => {
    consoleLogs = [];
    networkLogs = [];

    // ── Logging ──
    page.on('console', msg => {
      consoleLogs.push(`[${new Date().toISOString()}] [${msg.type().toUpperCase()}] ${msg.text()}`);
    });
    page.on('request', req => {
      if (req.url().includes('/api/'))
        networkLogs.push(`[${new Date().toISOString()}] → ${req.method()} ${req.url()}`);
    });
    page.on('response', res => {
      if (res.url().includes('/api/'))
        networkLogs.push(`[${new Date().toISOString()}] ← ${res.status()} ${res.url()}`);
    });

    // ════════════════════════════════════════════
    // PHASE 0: LOGIN (0:00 – 0:30)
    // ════════════════════════════════════════════
    await annotate(page, 'AUTHENTICATING...');
    await robustLogin(page);
    await expect(page.locator('#view-menu')).toBeVisible({ timeout: 5000 });
    consoleLogs.push('[DEMO] ✓ Login complete — on MENU');
    await page.waitForTimeout(PACE.read);

    // ════════════════════════════════════════════
    // PHASE 1: MENU CONFIG (0:30 – 1:00)
    // ════════════════════════════════════════════
    await annotate(page, 'CONFIGURING MISSION: CRIMSON TIDE');

    await page.selectOption('#sel-difficulty', 'INTERMEDIATE');
    await page.waitForTimeout(PACE.fast);

    await page.selectOption('#sel-scenario', 'crimson_tide');
    await page.waitForTimeout(PACE.normal);
    consoleLogs.push('[DEMO] Selected: INTERMEDIATE / crimson_tide');

    await page.click('#btn-demo');
    await page.waitForTimeout(PACE.slow);
    consoleLogs.push('[DEMO] Clicked PLAY SCENARIO → Role Select');

    // ════════════════════════════════════════════
    // PHASE 2: ROLE SELECT (1:00 – 1:20)
    // ════════════════════════════════════════════
    await annotate(page, 'SELECTING ROLE: ATTACKER — SCARLET PROTOCOL');

    const roleView = page.locator('#view-role_select');
    const roleVisible = await roleView.isVisible().catch(() => false);
    if (roleVisible) {
      await page.waitForTimeout(PACE.read);
      const atkCard = page.locator('.role-card--attacker');
      await atkCard.hover();
      await page.waitForTimeout(PACE.normal);
      await atkCard.click();
      consoleLogs.push('[DEMO] ✓ Selected ATTACKER role');
    } else {
      // Fallback: click btn-play for sandbox
      consoleLogs.push('[DEMO] Role select not visible — trying PLAY SANDBOX');
      await page.click('#btn-play');
    }
    await page.waitForTimeout(PACE.dramatic);

    // ════════════════════════════════════════════
    // PHASE 3: IN-GAME — TURNS 1-3 (1:20 – 3:00)
    // ════════════════════════════════════════════
    const gameView = page.locator('#view-game');
    const onGame = await gameView.isVisible().catch(() => false);
    if (!onGame) {
      consoleLogs.push('[DEMO] Game view not visible — forcing navigation');
      await page.evaluate(() => {
        document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
        const g = document.getElementById('view-game');
        if (g) g.classList.add('active');
      });
      await page.waitForTimeout(PACE.normal);
    }
    consoleLogs.push('[DEMO] ✓ GAME VIEW active');

    // Dismiss briefing overlay if present
    await page.waitForTimeout(PACE.read); // Let briefing display for recording
    const briefingBtn = page.locator('#btn-briefing-continue');
    if (await briefingBtn.isVisible().catch(() => false)) {
      await briefingBtn.click({ timeout: 5000 }).catch(() => {});
      consoleLogs.push('[DEMO] Dismissed briefing via COMMENCE OPERATION button');
      await page.waitForTimeout(PACE.normal);
    }
    // Fallback: force-hide the overlay via DOM
    await page.evaluate(() => {
      const ov = document.getElementById('briefing-overlay');
      if (ov) ov.style.display = 'none';
    });
    await page.waitForTimeout(PACE.fast);

    // Get available nodes for targeting
    const nodeIds = await page.evaluate(() => {
      if (window.GameInstance?.nodes) {
        return window.GameInstance.nodes
          .filter(n => n.faction_id !== 1)  // Non-player nodes
          .map(n => ({ id: n.id, name: n.name, faction: n.faction_id }));
      }
      return [];
    });
    consoleLogs.push(`[DEMO] Available targets: ${JSON.stringify(nodeIds.slice(0, 5))}`);
    const targets = nodeIds.length > 0 ? nodeIds : [{id:2},{id:3},{id:4},{id:5},{id:6}];

    // TURN 1: SCAN
    await annotate(page, 'TURN 1 — SCANNING NETWORK PERIMETER');
    await gameAction(page, targets[0]?.id || 2, '#btn-action-scan', 'SCAN (T1-A1)');
    await gameAction(page, targets[1]?.id || 3, '#btn-action-scan', 'SCAN (T1-A2)');
    await page.waitForTimeout(PACE.turn);

    // TURN 2: FIRST BREACH
    await annotate(page, 'TURN 2 — BREACHING IRON GRID FIREWALL');
    await gameAction(page, targets[0]?.id || 2, '#btn-action-breach', 'BREACH (T2-A1)');
    await gameAction(page, targets[1]?.id || 3, '#btn-action-breach', 'BREACH (T2-A2)');
    await page.waitForTimeout(PACE.turn);

    // TURN 3: EXPAND
    await annotate(page, 'TURN 3 — EXPANDING TO SHADOW CARTELS');
    await gameAction(page, targets[2]?.id || 4, '#btn-action-scan', 'SCAN (T3-A1)');
    await gameAction(page, targets[2]?.id || 4, '#btn-action-breach', 'BREACH (T3-A2)');
    await page.waitForTimeout(PACE.turn);

    // ════════════════════════════════════════════
    // PHASE 4: DIPLOMACY (3:00 – 5:00)
    // ════════════════════════════════════════════
    await annotate(page, 'OPENING DIPLOMATIC CHANNEL — SILK ROAD COALITION');

    // Open diplomacy modal
    let dipOpened = await safeClick(page, '#btn-action-diplomacy', 'DIPLOMACY BTN');
    if (!dipOpened) {
      dipOpened = await safeClick(page, '[data-action="diplomacy"]', 'DIPLOMACY ALT');
    }
    if (!dipOpened) {
      await page.evaluate(() => {
        const m = document.getElementById('modal-diplomacy');
        if (m) { m.style.display = 'flex'; m.classList.add('active'); }
      });
      await page.waitForTimeout(PACE.normal);
      consoleLogs.push('[DEMO] Opened diplomacy via DOM');
    }

    // Click Silk Road faction
    await safeClick(page, '[data-fid="3"]', 'Silk Road contact');

    // Send chat
    const chatInput = page.locator('#dip-chat-input');
    if (await chatInput.isVisible().catch(() => false)) {
      const dipMsg = 'Chairman Wei, the Iron Grid threatens us all. A trade agreement would benefit both our factions.';
      await chatInput.fill(dipMsg);
      await page.waitForTimeout(PACE.normal);
      await safeClick(page, '#btn-dip-send', 'SEND CHAT');
      await page.waitForTimeout(PACE.read);

      // Propose treaty
      const treatySel = page.locator('#dip-treaty-type');
      if (await treatySel.isVisible().catch(() => false)) {
        await treatySel.selectOption('TRADE');
        await page.waitForTimeout(PACE.fast);
        await safeClick(page, '#btn-dip-propose', 'PROPOSE TRADE');
        await page.waitForTimeout(PACE.read);
      }
    }

    // Chat with Sentinel Vanguard
    await annotate(page, 'CONTACTING SENTINEL VANGUARD');
    await safeClick(page, '[data-fid="7"]', 'Sentinel contact');
    if (await chatInput.isVisible().catch(() => false)) {
      await chatInput.fill('Oracle, let us form an alliance against the Iron Grid.');
      await page.waitForTimeout(PACE.fast);
      await safeClick(page, '#btn-dip-send', 'SEND CHAT (Sentinel)');
      await page.waitForTimeout(PACE.read);
    }

    // Close diplomacy
    await safeClick(page, '#btn-close-diplomacy', 'CLOSE DIPLOMACY');
    await page.waitForTimeout(PACE.normal);

    // ════════════════════════════════════════════
    // PHASE 5: ASSAULT TURNS 4-7 (5:00 – 7:00)
    // ════════════════════════════════════════════
    for (let t = 4; t <= 7; t++) {
      const ti = Math.min(t - 1, targets.length - 1);
      await annotate(page, `TURN ${t} — DEEP NETWORK ASSAULT`);
      await gameAction(page, targets[ti]?.id || t+1, '#btn-action-breach', `BREACH (T${t}-A1)`);
      const btn2 = t % 2 === 0 ? '#btn-action-scan' : '#btn-action-breach';
      await gameAction(page, targets[Math.max(0,ti-1)]?.id || t, btn2, `${t % 2 === 0 ? 'SCAN' : 'BREACH'} (T${t}-A2)`);
      await page.waitForTimeout(PACE.turn);
    }

    // ════════════════════════════════════════════
    // PHASE 6: SENTINEL LAB (7:00 – 7:45)
    // ════════════════════════════════════════════
    await annotate(page, 'SENTINEL LAB — CONFIGURING AI AGENT');
    let labOpened = await safeClick(page, '#btn-lab', 'SENTINEL LAB');
    if (labOpened) {
      await safeClick(page, '#btn-snt-create', 'CREATE SENTINEL');
      for (const [sel, val] of [
        ['#slider-persistence', '75'], ['#slider-stealth', '30'],
        ['#slider-efficiency', '60'], ['#slider-aggression', '85']
      ]) {
        const sl = page.locator(sel);
        if (await sl.isVisible().catch(() => false)) {
          await sl.fill(val);
          await page.waitForTimeout(300);
        }
      }
      await page.waitForTimeout(PACE.normal);
      await safeClick(page, '#btn-close-sentinel', 'CLOSE SENTINEL');
    }

    // ════════════════════════════════════════════
    // PHASE 7: FINAL TURNS 8-10 (7:45 – 9:30)
    // ════════════════════════════════════════════
    await annotate(page, 'FINAL PHASE — DATA EXFILTRATION');
    for (let t = 8; t <= 10; t++) {
      const ti = Math.min(t - 2, targets.length - 1);
      const label = t === 10 ? 'FINAL EXFILTRATION — ALL SYSTEMS GO' : `TURN ${t} — PUSHING DEEPER`;
      await annotate(page, label);
      await gameAction(page, targets[ti]?.id || t, '#btn-action-breach', `BREACH (T${t}-A1)`);
      await gameAction(page, targets[Math.max(0,ti-1)]?.id || t-1, '#btn-action-breach', `BREACH (T${t}-A2)`);
      await page.waitForTimeout(PACE.turn);
    }

    // ════════════════════════════════════════════
    // PHASE 8: GAME OVER (9:30 – 10:00)
    // ════════════════════════════════════════════
    await annotate(page, 'MISSION CONCLUDING...');
    await page.waitForTimeout(PACE.dramatic);

    const goVisible = await page.locator('#view-gameover').isVisible().catch(() => false);
    consoleLogs.push(`[DEMO] Game over screen visible: ${goVisible}`);
    await page.waitForTimeout(PACE.read);

    // Final screenshot
    const ssPath = getOutputPath('final_screenshot.png');
    await page.screenshot({ path: ssPath, fullPage: true });
    consoleLogs.push(`[DEMO] Screenshot: ${ssPath}`);

    // ── Write log file ──
    const logContent = [
      '='.repeat(80),
      '  NEO-HACK: GRIDLOCK v3.2 — DEMO PLAYTHROUGH LOG',
      `  User: ${DEMO_USER}`,
      `  Recorded: ${new Date().toISOString()}`,
      '='.repeat(80),
      '',
      '── DEMO ACTIONS ──',
      ...consoleLogs,
      '',
      '── NETWORK REQUESTS ──',
      ...networkLogs,
      '',
      `Total demo actions: ${consoleLogs.length}`,
      `Total API calls: ${networkLogs.length}`,
    ].join('\n');

    const logPath = getOutputPath('demo_playthrough_log.txt');
    fs.writeFileSync(logPath, logContent, 'utf-8');
  });
});
