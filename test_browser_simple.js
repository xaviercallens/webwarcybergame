/**
 * Simple browser test to identify issues
 */

const { chromium } = require('playwright');

async function testBrowser() {
  console.log('Starting browser test...\n');
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const logs = [];
  const errors = [];

  page.on('console', msg => {
    const text = `[${msg.type()}] ${msg.text()}`;
    logs.push(text);
    if (msg.type() === 'error' || msg.type() === 'warning') {
      errors.push(text);
    }
  });

  page.on('pageerror', err => {
    const text = `[pageerror] ${err.message}`;
    logs.push(text);
    errors.push(text);
  });

  try {
    console.log('Loading page...');
    await page.goto('http://127.0.0.1:39099', { waitUntil: 'networkidle', timeout: 30000 });
    console.log('✓ Page loaded\n');

    await page.waitForTimeout(2000);

    // Check page state
    const pageInfo = await page.evaluate(() => ({
      title: document.title,
      hasApp: !!document.getElementById('app'),
      hasLoginView: !!document.getElementById('view-login'),
      hasGameInstance: !!window.GameInstance,
      hasV32: !!window.V32,
      hasRenderer: !!window.GameInstance?.renderer,
      appStateAuth: window.AppState?.isAuthenticated
    }));

    console.log('Page State:');
    console.log(JSON.stringify(pageInfo, null, 2));

    console.log('\nConsole Logs:');
    logs.forEach(log => console.log(log));

    if (errors.length > 0) {
      console.log('\nErrors/Warnings:');
      errors.forEach(err => console.log(err));
    }

  } catch (e) {
    console.error('Error:', e.message);
  } finally {
    await browser.close();
  }
}

testBrowser().catch(console.error);
