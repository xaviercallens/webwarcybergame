import asyncio
from playwright.async_api import async_playwright

async def main():
    print("[*] Launching Playwright Chromium...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--use-gl=swiftshader', '--disable-dev-shm-usage', '--disable-gpu']
        )
        page = await browser.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        
        print("[*] Navigating to game...")
        await page.goto('http://localhost:8000')
        
        print("[*] Waiting for Main Menu to render...")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="docs/shot_01_main_menu.png")
        print(" -> Saved docs/shot_01_main_menu.png")
        
        print("[*] Launching Gameplay...")
        await page.click('#btn-play')
        await page.wait_for_timeout(5000)
        await page.screenshot(path="docs/shot_02_gameplay.png")
        print(" -> Saved docs/shot_02_gameplay.png")
        
        print("[*] Triggering Auto-Attack and Capturing Action...")
        await page.keyboard.press('Space')
        await page.wait_for_timeout(1000)
        await page.keyboard.press('Space')
        await page.wait_for_timeout(2500)
        await page.screenshot(path="docs/shot_03_combat_action.png")
        print(" -> Saved docs/shot_03_combat_action.png")
        
        print("[*] Triggering Global Cyber War Promo...")
        await page.keyboard.press('q')
        await page.wait_for_timeout(1000)
        await page.click('#btn-promo')
        await page.wait_for_timeout(9000)
        await page.screenshot(path="docs/shot_04_global_war.png")
        print(" -> Saved docs/shot_04_global_war.png")
        
        await browser.close()
        print("[+] All crisp 4K screenshots successfully generated in docs/!")

asyncio.run(main())
