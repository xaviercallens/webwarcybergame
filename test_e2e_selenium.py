import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    print("Starting Selenium End-to-End Game Flow Test...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")

    # In a typical Linux environment, python selenium will auto-detect the chromium/chrome driver if installed.
    # Otherwise, it attempts to download it if selenium >= 4.10.
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"❌ Failed to launch Chrome driver: {e}")
        sys.exit(1)

    try:
        print("Navigating to http://localhost:8000 ...")
        driver.get("http://localhost:8000")

        print("Handling Login Screen...")
        wait = WebDriverWait(driver, 10)
        
        # Wait for login view
        username_input = wait.until(EC.visibility_of_element_located((By.ID, "login-username")))
        password_input = driver.find_element(By.ID, "login-password")
        
        username_input.send_keys("SELENIUM_TEST")
        password_input.send_keys("test_pass_123")
        
        # Click Register to create user or login if exists
        btn_register = driver.find_element(By.ID, "btn-register")
        driver.execute_script("arguments[0].click();", btn_register)
        
        print("Checking if Main Menu is visible...")
        
        try:
            btn_play = wait.until(EC.visibility_of_element_located((By.ID, "btn-play")))
        except Exception:
            # Maybe it already exists? Try login instead
            btn_login = driver.find_element(By.ID, "btn-login")
            driver.execute_script("arguments[0].click();", btn_login)
            btn_play = wait.until(EC.visibility_of_element_located((By.ID, "btn-play")))
            
        print("Waiting for backend healthcheck to complete...")
        wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "menu-subtitle"), "ONLINE"))

        print("Programmatically clicking 'PLAY' button...")
        driver.execute_script("arguments[0].click();", btn_play)

        print("Waiting for Role Select view...")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#view-role_select.active")))
        
        print("Clicking Attacker Role...")
        attacker_card = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".role-card--attacker")))
        driver.execute_script("arguments[0].click();", attacker_card)

        print("Waiting for game view transition...")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#view-game.active")))

        print("Waiting for Globe.gl WebGL canvas initialization...")
        time.sleep(3) # Let the webgl context build the sphere

        print("Checking if HUD stats and Canvas are injected...")
        canvas = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#canvas-container canvas")))
        
        # Verify canvas dimensions to make sure the sphere area is rendering
        width = int(canvas.get_attribute("width") or 0)
        height = int(canvas.get_attribute("height") or 0)
        
        print(f"Canvas element found. Dimensions: {width}x{height}")
        if width == 0 or height == 0:
            raise Exception("Canvas rendered with 0 width or height (Sphere invisible).")

        print("Clicking 'QUIT' to return to menu...")
        btn_quit = driver.find_element(By.ID, "btn-quit")
        driver.execute_script("arguments[0].click();", btn_quit)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#view-menu.active")))

        print("Clicking 'PLAY' again to simulate multiple sessions...")
        driver.execute_script("arguments[0].click();", btn_play)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#view-role_select.active")))
        attacker_card_2 = driver.find_element(By.CSS_SELECTOR, ".role-card--attacker")
        driver.execute_script("arguments[0].click();", attacker_card_2)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#view-game.active")))
        time.sleep(2)
        
        # Checking for any severe browser console errors about WebGL
        logs = driver.get_log("browser")
        for entry in logs:
            # We ignore favicon 404s
            if entry["level"] == "SEVERE" and "favicon.ico" not in entry["message"]:
                print(f"PAGE ERROR [{entry['level']}]:", entry["message"])

        print("✅ E2E Test Passed. Game initializes correctly via Selenium.")
        sys.exit(0)

    except Exception as e:
        print(f"❌ E2E Test Failed: {e}")
        try:
            driver.save_screenshot("selenium_failure.png")
            print("Screenshot saved to selenium_failure.png")
        except:
            pass
        sys.exit(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
