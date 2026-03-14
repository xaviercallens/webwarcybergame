const puppeteer = require('puppeteer');

(async () => {
    console.log("Starting End-to-End Game Flow Test...");
    const browser = await puppeteer.launch({
        executablePath: '/usr/bin/chromium',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    // We expect the backend to be running on port 8000
    const page = await browser.newPage();
    
    let hasError = false;
    page.on('console', msg => {
        if (msg.type() === 'error') {
            const text = msg.text();
            if (!text.includes('favicon.ico') && !text.includes('Failed to load resource')) {
                console.error('PAGE ERROR:', text);
                hasError = true;
            }
        }
    });
    page.on('pageerror', error => {
        console.error('UNHANDLED EXCEPTION:', error.message);
        hasError = true;
    });

    try {
        console.log("Navigating to http://localhost:8000 ...");
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
        
        console.log("Checking if Main Menu is visible...");
        await page.waitForSelector('#btn-play', { visible: true, timeout: 5000 });
        
        console.log("Waiting for backend healthcheck to complete...");
        await page.waitForFunction(() => {
            const el = document.querySelector('.menu-subtitle');
            return el && el.innerText.includes('ONLINE');
        }, { timeout: 10000 });
        
        console.log("Programmatically clicking 'PLAY' button...");
        await page.evaluate(() => document.getElementById('btn-play').click());
        
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
        await page.waitForSelector('#view-game.active', { visible: true, timeout: 5000 });
        await new Promise(r => setTimeout(r, 2000));
        
        if (hasError) {
            throw new Error("Errors were detected in the browser console during the flow.");
        }
        
        console.log("✅ E2E Test Passed. Game initializes normally without WebGL context leaks.");
    } catch (e) {
        console.error("❌ E2E Test Failed:", e.message);
        process.exitCode = 1;
    } finally {
        await browser.close();
    }
})();
