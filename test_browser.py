from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
    page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
    page.on("requestfailed", lambda req: print(f"REQUEST FAILED: {req.url} {req.failure}"))
    print("Navigating to http://localhost:8000...")
    page.goto("http://localhost:8000")
    page.wait_for_timeout(3000)
    print("App innerHTML:", page.evaluate("document.getElementById('app').innerHTML"))
    browser.close()
