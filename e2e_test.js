const puppeteer = require('puppeteer');

(async () => {
    console.log("Starting End-to-End Game Flow Test...");
    const browser = await puppeteer.launch({
        executablePath: '/usr/bin/chromium',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu', '--disable-webgl', '--disable-software-rasterizer']
    });
    
    // We expect the backend to be running on port 8000
    const page = await browser.newPage();
    
    let hasError = false;
    page.on('console', msg => {
        const type = msg.type();
        const text = msg.text();
        console.log(`[PAGE LOG][${type.toUpperCase()}] ${text}`);
        
        const isIgnoredError = text.includes('favicon.ico') || 
                               text.includes('Failed to load resource') ||
                               text.includes('WebGL') ||
                               text.includes('webgl');
                               
        if (type === 'error' && !isIgnoredError) {
            hasError = true;
        }
    });
    page.on('pageerror', error => {
        console.error('UNHANDLED EXCEPTION:', error.message);
        hasError = true;
    });

    try {
        console.log("Navigating to http://localhost:8000 ...");
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
        
        console.log("Registering a new test user...");
        await page.waitForSelector('#login-username', { visible: true });
        const testUser = `E2E_PUP_${Date.now()}`;
        await page.type('#login-username', testUser);
        await page.type('#login-password', 'testpass123');
        await page.click('#btn-register');
        
        console.log("Checking if Main Menu is visible...");
        // After registration, the app navigates to the 'menu' view, which sets opacity: 1 on #view-menu
        await page.waitForFunction(() => {
            const menu = document.getElementById('view-menu');
            return menu && menu.classList.contains('active');
        }, { timeout: 5000 });
        
        console.log("Waiting for backend healthcheck to complete...");
        await page.waitForFunction(() => {
            const el = document.querySelector('.menu-subtitle');
            return el && el.innerText.includes('ONLINE');
        }, { timeout: 10000 });
        
        console.log("Programmatically clicking 'PLAY' button...");
        await page.evaluate(() => document.getElementById('btn-play').click());
        
        console.log("Waiting for role select transition...");
        await page.waitForSelector('#view-role_select.active', { visible: true, timeout: 5000 });
        
        console.log("Clicking role card...");
        await page.evaluate(() => document.querySelector('.role-card--attacker').click());
        
        // Wait for the view-game to become active
        console.log("Waiting for game view transition...");
        try {
            await page.waitForSelector('#view-game.active', { visible: true, timeout: 5000 });
        } catch(e) {
            await page.screenshot({ path: 'e2e_failure.png' });
            throw new Error("Transition failed. Screenshot saved to e2e_failure.png");
        }
        
        console.log("Adding artificial delay to allow Globe.gl initialization...");
        await new Promise(r => setTimeout(r, 2000));
        
        console.log("Checking if HUD stats are injected...");
        await page.waitForSelector('#hud-count-player', { visible: true, timeout: 5000 });
        
        const canvasContainers = await page.$$('canvas');
        console.log(`Found ${canvasContainers.length} canvas element(s) currently active.`);
        
        if (canvasContainers.length === 0) {
            throw new Error("Canvas did not render! WebGL context likely failed.");
        }
        
        // Simulating second click to ensure context bounds are respected
        console.log("Clicking 'QUIT' to return to menu...");
        await page.evaluate(() => document.getElementById('btn-quit').click());
        await page.waitForSelector('#view-menu.active', { visible: true, timeout: 5000 });
        
        console.log("Clicking 'PLAY' again to simulate multiple sessions...");
        await page.evaluate(() => document.getElementById('btn-play').click());
        await page.waitForSelector('#view-role_select.active', { visible: true, timeout: 5000 });
        await page.evaluate(() => document.querySelector('.role-card--attacker').click());
        await page.waitForSelector('#view-game.active', { visible: true, timeout: 5000 });
        await new Promise(r => setTimeout(r, 2000));
        
        if (hasError) {
            throw new Error("Errors were detected in the browser console during the flow.");
        }
        
        console.log("✅ E2E Test Passed. Game initializes normally without WebGL context leaks.");
    } catch (e) {
        await page.screenshot({ path: 'e2e_failure_debug.png', fullPage: true });
        console.error("❌ E2E Test Failed:", e.message);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
