const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
    page.on('requestfailed', request => console.log('REQUEST FAILED:', request.url(), request.failure().errorText));
    
    try {
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
        console.log("HTML length:", await page.evaluate(() => document.body.innerHTML.length));
    } catch (e) {
        console.log("Navigation Error:", e);
    }
    await browser.close();
})();
