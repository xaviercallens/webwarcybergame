import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_login_flow():
    print("Connecting to Remote Selenium WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # The selenium container is running on the host network or accessible via localhost:4444
    driver = webdriver.Remote(
        command_executor='http://localhost:4444/wd/hub',
        options=options
    )
    
    try:
        print("Navigating to local frontend...")
        # Since Selenium is in a docker container on the same network 'windsurf-project_default', 
        # it can access the frontend container via 'http://frontend:5173'
        driver.get("http://frontend:5173")
        
        print("Clearing persistent tokens from test container...")
        driver.execute_script("localStorage.clear();")
        driver.refresh()
        
        # Wait for the login screen to render
        print("Waiting for login screen...")
        wait = WebDriverWait(driver, 10)
        
        username_input = wait.until(EC.presence_of_element_located((By.ID, "login-username")))
        password_input = driver.find_element(By.ID, "login-password")
        login_btn = driver.find_element(By.ID, "btn-login")
        register_btn = driver.find_element(By.ID, "btn-register")
        
        print("Registering a new test user...")
        # Add a timestamp to avoid conflicts if run multiple times
        import time as pytime
        test_user = f"TEST_OP_{int(pytime.time())}"
        
        username_input.send_keys(test_user)
        password_input.send_keys("secure_password123")
        driver.execute_script("arguments[0].click();", register_btn)
        
        print("Waiting for authentication success and menu transition...")
        # Wait for the menu title to become visible, indicating we are past the login screen
        # We can look for the btn-play ID which is on the menu view
        play_btn = wait.until(EC.element_to_be_clickable((By.ID, "btn-play")))
        
        print("Successfully reached the main menu!")
        
        # Check if the player name updated in the player card
        # Let the DOM settle after the view transition
        pytime.sleep(2)
        injected_username = driver.find_element(By.ID, "input-username")
        actual_user = injected_username.get_attribute("value")
        
        print(f"Verified Player Callsign: {actual_user} (Expected: {test_user})")
        assert test_user in actual_user, "Callsign mismatch!"
        
        print("Clicking PLAY...")
        driver.execute_script("arguments[0].click();", play_btn)
        
        # Wait for game view
        game_canvas = wait.until(EC.presence_of_element_located((By.ID, "canvas-container")))
        print("Game canvas loaded successfully!")
        
        print("--- ALL UI TESTS PASSED ---")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_login_flow()
