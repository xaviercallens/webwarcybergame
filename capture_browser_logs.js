/**
 * Capture browser logs and identify issues
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function captureLogs() {
  const logFile = path.join(__dirname, 'browser_logs.txt');
  const logs = [];
  
  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-blink-features=AutomationControlled']
  });

  const context = await browser.createContext();
  const page = await context.newPage();

  // Capture all console messages
  page.on('console', msg => {
    const entry = `[${msg.type().toUpperCase()}] ${msg.text()}`;
    logs.push(entry);
    console.log(entry);
  });

  // Capture errors
  page.on('pageerror', err => {
    const entry = `[ERROR] ${err.message}`;
    logs.push(entry);
    console.log(entry);
  });

  // Capture request/response errors
  page.on('requestfailed', req => {
    const entry = `[REQUEST_FAILED] ${req.url()} - ${req.failure().errorText}`;
    logs.push(entry);
    console.log(entry);
  });

  console.log('Starting browser navigation to http://127.0.0.1:39099...\n');
  logs.push('=== BROWSER LOG CAPTURE STARTED ===');

  try {
    // Navigate to the game
    await page.goto('http://127.0.0.1:39099', { waitUntil: 'networkidle', timeout: 30000 });
    logs.push('✓ Page loaded successfully');
    console.log('✓ Page loaded successfully');

    // Wait for app initialization
    await page.waitForTimeout(3000);

    // Check if login view is visible
    const loginView = await page.$('#view-login');
    if (loginView) {
      logs.push('✓ Login view visible');
      console.log('✓ Login view visible');
    } else {
      logs.push('⚠ Login view not found');
      console.log('⚠ Login view not found');
    }

    // Check for any errors in the page
    const errors = await page.evaluate(() => {
      return {
        hasErrors: !!window.__errors,
        appState: window.AppState,
        gameInstance: !!window.GameInstance,
        v32: !!window.V32,
        renderer: !!window.GameInstance?.renderer
      };
    });

    logs.push(`App State: ${JSON.stringify(errors)}`);
    console.log(`App State: ${JSON.stringify(errors)}`);

    // Try to login
    console.log('\nAttempting login...');
    logs.push('--- Attempting Login ---');

    await page.fill('#login-username', 'testuser');
    await page.fill('#login-password', 'password123');
    await page.click('#btn-login');

    // Wait for response
    await page.waitForTimeout(2000);

    // Check if we're on menu or still on login
    const menuView = await page.$('#view-menu');
    const loginError = await page.$('#login-error');
    const errorText = loginError ? await loginError.textContent() : null;

    if (menuView) {
      logs.push('✓ Successfully navigated to menu');
      console.log('✓ Successfully navigated to menu');

      // Wait a bit more for menu to fully load
      await page.waitForTimeout(2000);

      // Try to start a game
      console.log('\nStarting game...');
      logs.push('--- Starting Game ---');

      // Click role select button (Play button)
      const playBtn = await page.$('button:has-text("PLAY")');
      if (playBtn) {
        await playBtn.click();
        await page.waitForTimeout(2000);

        // Check if role select is visible
        const roleSelect = await page.$('#view-role-select');
        if (roleSelect) {
          logs.push('✓ Role select view visible');
          console.log('✓ Role select view visible');

          // Click attacker role
          const attackerCard = await page.$('[data-role="attacker"]');
          if (attackerCard) {
            await attackerCard.click();
            await page.waitForTimeout(3000);

            // Check if game view is visible
            const gameView = await page.$('#view-game');
            if (gameView) {
              logs.push('✓ Game view loaded');
              console.log('✓ Game view loaded');

              // Check canvas
              const canvas = await page.$('canvas');
              if (canvas) {
                const canvasInfo = await canvas.evaluate(el => ({
                  width: el.width,
                  height: el.height,
                  display: el.style.display,
                  hasContext: !!el.getContext('2d')
                }));
                logs.push(`Canvas info: ${JSON.stringify(canvasInfo)}`);
                console.log(`Canvas info: ${JSON.stringify(canvasInfo)}`);
              } else {
                logs.push('⚠ Canvas not found');
                console.log('⚠ Canvas not found');
              }
            } else {
              logs.push('⚠ Game view not loaded');
              console.log('⚠ Game view not loaded');
            }
          }
        }
      }
    } else if (errorText) {
      logs.push(`✗ Login failed: ${errorText}`);
      console.log(`✗ Login failed: ${errorText}`);
    } else {
      logs.push('⚠ Login response unclear');
      console.log('⚠ Login response unclear');
    }

  } catch (e) {
    logs.push(`✗ Error: ${e.message}`);
    console.log(`✗ Error: ${e.message}`);
  }

  // Save logs to file
  fs.writeFileSync(logFile, logs.join('\n'));
  console.log(`\n✓ Logs saved to ${logFile}`);

  await browser.close();
}

captureLogs().catch(console.error);
