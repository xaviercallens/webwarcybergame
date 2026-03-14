const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
    console.log('[*] Launching Puppeteer for High-Res Screenshots...');
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=swiftshader', '--disable-dev-shm-usage', '--disable-gpu']
    });
    const page = await browser.newPage();
    
    // Set a high-res viewport for beautiful screenshots
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });
    
    console.log('[*] Navigating to local game instance...');
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
    
    // 1. Main Menu Screenshot
    console.log('[*] Capturing Main Menu...');
    await page.waitForTimeout(2000); // Wait for neat glitch effects to settle or Globe to spin
    await page.screenshot({ path: 'docs/shot_01_main_menu.png' });
    
    // 2. Gameplay Screenshot
    console.log('[*] Launching Game...');
    await page.click('#btn-play');
    await page.waitForTimeout(4000); // Wait for Globe to render points and connections
    console.log('[*] Capturing Gameplay...');
    await page.screenshot({ path: 'docs/shot_02_gameplay.png' });
    
    // 3. Action / Combat Screenshot
    console.log('[*] Simulating Attack Sequence...');
    await page.keyboard.press('Space'); // Auto-attack
    await page.waitForTimeout(1000); 
    await page.keyboard.press('Space'); // Auto-attack again
    await page.waitForTimeout(2000); // Wait for attack physical lasers to draw
    console.log('[*] Capturing Combat Action...');
    await page.screenshot({ path: 'docs/shot_03_combat.png' });
    
    // 4. Promo Mode
    console.log('[*] Returning to Menu and launching Promo...');
    // Press Q to quit
    await page.keyboard.press('q');
    await page.waitForTimeout(1000);
    await page.click('#btn-promo');
    // Wait for the camera to zoom and multi-colored nodes to explode
    await page.waitForTimeout(7000); 
    console.log('[*] Capturing Global Cyber War Simulation...');
    await page.screenshot({ path: 'docs/shot_04_global_war.png' });

    await browser.close();
    console.log('[+] All Screenshots successfully captured and saved to docs/!');
})();
