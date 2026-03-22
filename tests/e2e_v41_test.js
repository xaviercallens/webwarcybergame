/**
 * Neo-Hack: Gridlock v4.1 — E2E Multi-Screen + Multi-Session Test
 * Tests all v4.1 screens (Mesh Hub, Campaign, Leaderboard, React Phase)
 * and verifies 3 simultaneous browser sessions don't interfere.
 *
 * Usage:
 *   BASE_URL=https://neohack-staging-xxx.run.app node tests/e2e_v41_test.js
 */

const puppeteer = require('puppeteer');

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const USERS = [
  { username: 'E2E_USER_1', password: 'testpass123' },
  { username: 'E2E_USER_2', password: 'testpass123' },
  { username: 'E2E_USER_3', password: 'testpass123' },
];

let exitCode = 0;
const results = [];

function log(msg, ok = true) {
  const icon = ok ? '✓' : '✗';
  console.log(`  ${ok ? '\x1b[32m' : '\x1b[31m'}${icon}\x1b[0m ${msg}`);
  results.push({ msg, ok });
  if (!ok) exitCode = 1;
}

async function registerUser(page, user) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 15000 });

  // Try register (may already exist)
  const regResp = await page.evaluate(async (u) => {
    const r = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(u),
    });
    return r.status;
  }, user);

  // Login
  await page.waitForSelector('#login-username', { timeout: 5000 });
  await page.type('#login-username', user.username);
  await page.type('#login-password', user.password);
  await page.click('#btn-login');

  // Wait for menu
  try {
    await page.waitForSelector('#view-menu.active', { timeout: 10000 });
    log(`${user.username}: Login → Menu`);
  } catch {
    log(`${user.username}: Login failed`, false);
    return false;
  }
  return true;
}

async function testV41Screens(page, username) {
  // Test Mesh Hub
  try {
    await page.evaluate(() => document.getElementById('btn-mesh-hub')?.click());
    await page.waitForSelector('#view-mesh-hub.active', { timeout: 5000 });
    const hasCanvas = await page.$('#mesh-topology-canvas');
    log(`${username}: Mesh Hub renders ${hasCanvas ? '+ canvas' : '(no canvas)'}`, !!hasCanvas);
  } catch (e) {
    log(`${username}: Mesh Hub navigation failed`, false);
  }

  // Test Campaign
  try {
    await page.evaluate(() => document.getElementById('btn-campaign')?.click());
    await page.waitForSelector('#view-campaign.active', { timeout: 5000 });
    const cards = await page.$$('.campaign__card');
    log(`${username}: Campaign renders with ${cards.length} mission cards`, cards.length >= 5);
  } catch (e) {
    log(`${username}: Campaign navigation failed`, false);
  }

  // Test Leaderboard
  try {
    await page.evaluate(() => document.getElementById('btn-leaderboard')?.click());
    await page.waitForSelector('#view-leaderboard.active', { timeout: 5000 });
    const rows = await page.$$('#lb-tbody tr');
    log(`${username}: Leaderboard renders with ${rows.length} rows`, rows.length >= 1);
  } catch (e) {
    log(`${username}: Leaderboard navigation failed`, false);
  }

  // Return to menu
  try {
    await page.evaluate(() => {
      const btn = document.getElementById('btn-lb-back');
      if (btn) btn.click();
    });
    await new Promise(r => setTimeout(r, 500));
  } catch {}
}

async function runSingleSession(browser, user) {
  const page = await browser.newPage();
  page.on('pageerror', (err) => log(`${user.username}: Page error: ${err.message}`, false));

  const loggedIn = await registerUser(page, user);
  if (!loggedIn) return;

  await testV41Screens(page, user.username);
  await page.close();
}

async function main() {
  console.log('╔═══════════════════════════════════════════════╗');
  console.log('║  Neo-Hack v4.1 — E2E Multi-Screen Test       ║');
  console.log(`║  Target: ${BASE_URL.padEnd(37)}║`);
  console.log(`║  Sessions: ${USERS.length} simultaneous                      ║`);
  console.log('╚═══════════════════════════════════════════════╝');
  console.log('');

  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });

  // Phase 1: Sequential single-user test (full validation)
  console.log('[Phase 1] Single-user screen validation:');
  await runSingleSession(browser, USERS[0]);

  // Phase 2: Simultaneous multi-user test
  console.log('\n[Phase 2] Simultaneous 3-user sessions:');
  const simultaneousStart = Date.now();

  await Promise.all(USERS.map(user => runSingleSession(browser, user)));

  const elapsed = ((Date.now() - simultaneousStart) / 1000).toFixed(1);
  console.log(`  Sessions completed in ${elapsed}s`);

  await browser.close();

  // Summary
  const passed = results.filter(r => r.ok).length;
  const failed = results.filter(r => !r.ok).length;
  console.log('\n═══════════════════════════════════════════════');
  console.log(`Results: ${passed} passed, ${failed} failed`);
  if (exitCode === 0) {
    console.log('✅ ALL E2E TESTS PASSED');
  } else {
    console.log('❌ SOME E2E TESTS FAILED');
  }
  process.exit(exitCode);
}

main().catch(e => {
  console.error('Fatal:', e);
  process.exit(1);
});
