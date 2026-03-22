/**
 * Neo-Hack: Gridlock v4.1 — WebSocket Multi-User Stress Test
 * Connects N concurrent WebSocket clients to verify real-time stability.
 *
 * Usage:
 *   GCP_URL=wss://neohack-staging-xxx.run.app node tests/ws_multiuser_test.js
 *
 * Prerequisites:
 *   npm install ws node-fetch
 *   Ensure test users TEST_WS_01..TEST_WS_50 are pre-registered.
 */

const WebSocket = require('ws');

const BASE_URL = process.env.GCP_URL || 'ws://localhost:8000';
const HTTP_BASE = BASE_URL.replace('ws://', 'http://').replace('wss://', 'https://');
const TOTAL_USERS = parseInt(process.env.WS_USERS || '50', 10);
const CONNECT_TIMEOUT_MS = 10000;
const SESSION_DURATION_MS = 8000;
const PASSWORD = 'testpass123';

let passed = 0;
let failed = 0;
const errors = [];

async function registerAndLogin(username) {
  const fetch = (await import('node-fetch')).default;

  // Try register (ignore if already exists)
  await fetch(`${HTTP_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password: PASSWORD }),
  }).catch(() => {});

  // Login
  const resp = await fetch(`${HTTP_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password: PASSWORD }),
  });

  if (!resp.ok) throw new Error(`Login failed for ${username}: ${resp.status}`);
  const data = await resp.json();
  return data.access_token;
}

function connectUser(token, userId) {
  return new Promise((resolve, reject) => {
    const wsUrl = `${BASE_URL}/ws/game?token=${token}`;
    const ws = new WebSocket(wsUrl);
    let messagesReceived = 0;

    const timeout = setTimeout(() => {
      ws.close();
      reject(new Error(`User ${userId}: Connection timeout after ${CONNECT_TIMEOUT_MS}ms`));
    }, CONNECT_TIMEOUT_MS);

    ws.on('open', () => {
      clearTimeout(timeout);

      // Send periodic keepalives
      const keepalive = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }));
        }
      }, 2000);

      ws.on('message', () => { messagesReceived++; });

      // Hold connection for session duration then cleanly close
      setTimeout(() => {
        clearInterval(keepalive);
        ws.close();
        resolve({ userId, messagesReceived });
      }, SESSION_DURATION_MS);
    });

    ws.on('error', (err) => {
      clearTimeout(timeout);
      reject(new Error(`User ${userId}: ${err.message}`));
    });

    ws.on('unexpected-response', (req, res) => {
      clearTimeout(timeout);
      reject(new Error(`User ${userId}: Unexpected response ${res.statusCode}`));
    });
  });
}

async function main() {
  console.log('╔═══════════════════════════════════════════════╗');
  console.log('║  Neo-Hack v4.1 — WebSocket Multi-User Test   ║');
  console.log(`║  Target: ${BASE_URL.padEnd(37)}║`);
  console.log(`║  Users:  ${String(TOTAL_USERS).padEnd(37)}║`);
  console.log('╚═══════════════════════════════════════════════╝');
  console.log('');

  // Phase 1: Register & login all users
  console.log(`[1/3] Registering and logging in ${TOTAL_USERS} users...`);
  const tokens = [];
  for (let i = 1; i <= TOTAL_USERS; i++) {
    try {
      const token = await registerAndLogin(`TEST_WS_${String(i).padStart(2, '0')}`);
      tokens.push(token);
    } catch (e) {
      console.error(`  ✗ Failed to auth user ${i}: ${e.message}`);
      failed++;
      errors.push(e.message);
    }
  }
  console.log(`  → ${tokens.length} tokens acquired\n`);

  // Phase 2: Connect all users simultaneously
  console.log(`[2/3] Connecting ${tokens.length} WebSocket sessions...`);
  const startTime = Date.now();

  const results = await Promise.allSettled(
    tokens.map((token, i) => connectUser(token, i + 1))
  );

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`  → Completed in ${elapsed}s\n`);

  // Phase 3: Report
  console.log('[3/3] Results:');
  results.forEach((r) => {
    if (r.status === 'fulfilled') {
      passed++;
    } else {
      failed++;
      errors.push(r.reason?.message || 'Unknown error');
    }
  });

  const successRate = ((passed / TOTAL_USERS) * 100).toFixed(1);
  console.log(`  ✅ Connected: ${passed}/${TOTAL_USERS} (${successRate}%)`);
  console.log(`  ❌ Failed:    ${failed}/${TOTAL_USERS}`);

  if (errors.length > 0) {
    console.log('\n  Errors:');
    errors.slice(0, 10).forEach(e => console.log(`    • ${e}`));
    if (errors.length > 10) console.log(`    ... and ${errors.length - 10} more`);
  }

  console.log('');
  const passThreshold = 0.95;
  if (passed / TOTAL_USERS >= passThreshold) {
    console.log(`✅ PASS — ${successRate}% success rate (threshold: ${passThreshold * 100}%)`);
    process.exit(0);
  } else {
    console.log(`❌ FAIL — ${successRate}% success rate (threshold: ${passThreshold * 100}%)`);
    process.exit(1);
  }
}

main().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});
