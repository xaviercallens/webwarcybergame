/**
 * Puppeteer Capture Script
 * Automates a Chromium browser to navigate to the local Neo-Hack server,
 * progress past the main menu, and take a screenshot of the main game 
 * view rendering (with canvas dimensions logged).
 */
const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({
        executablePath: '/usr/bin/chromium',
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        defaultViewport: { width: 1280, height: 720 }
    });
    
    try {
        const page = await browser.newPage();
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
        
        await page.waitForFunction(() => {
            const el = document.querySelector('.menu-subtitle');
            return el && el.innerText.includes('ONLINE');
        }, { timeout: 10000 });
        
        await page.evaluate(() => document.getElementById('btn-play').click());
        await page.waitForSelector('#view-game.active', { visible: true, timeout: 5000 });
        
        // Wait for Globe.gl to render
        await new Promise(r => setTimeout(r, 4000));
        
        // Let's also grab canvas dimensions
        const dims = await page.evaluate(() => {
            const canvas = document.querySelector('#canvas-container canvas');
            return canvas ? { width: canvas.width, height: canvas.height, styleW: canvas.style.width, styleH: canvas.style.height } : null;
        });
        console.log("Canvas dimensions:", dims);

        await page.screenshot({ path: 'game_view.png' });
        console.log("Screenshot saved to game_view.png");
    } catch (e) {
        console.error(e);
    } finally {
        await browser.close();
    }
})();
