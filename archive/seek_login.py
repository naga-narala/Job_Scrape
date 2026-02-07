#!/usr/bin/env python3
"""
Seek Login Helper
Opens browser for you to manually login, then saves cookies for future use
"""

import sys
sys.path.insert(0, 'src')

import time
import pickle
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

COOKIES_FILE = Path('data/seek_cookies.pkl')
COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)


def create_driver(headless=False):
    """Create a Chrome driver"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    import os
    driver_path = ChromeDriverManager().install()
    
    if not driver_path.endswith('chromedriver') or 'THIRD_PARTY' in driver_path:
        driver_dir = os.path.dirname(driver_path)
        for file in os.listdir(driver_dir):
            if file == 'chromedriver' or (file.startswith('chromedriver') and not file.endswith('.txt')):
                driver_path = os.path.join(driver_dir, file)
                break
    
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def save_cookies(driver):
    """Save cookies to file"""
    try:
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, 'wb') as f:
            pickle.dump(cookies, f)
        print(f"💾 Saved {len(cookies)} cookies to {COOKIES_FILE}")
        return True
    except Exception as e:
        print(f"❌ Failed to save cookies: {e}")
        return False


def is_logged_in(driver):
    """Check if logged into Seek"""
    try:
        current_url = driver.current_url
        time.sleep(2)
        
        # Check if we're on login page
        if '/sign-in' in current_url or '/login' in current_url:
            return False
        
        # If we're on Seek and not on login, we're logged in
        if 'seek.com.au' in current_url:
            # Try to find user profile indicator
            try:
                # Look for profile/account elements
                driver.find_element("css selector", "[data-testid='user-menu'], .user-profile, [aria-label*='Profile']")
                return True
            except:
                # If on main page and not redirected to login, assume logged in
                if '/jobs' in current_url or current_url.endswith('seek.com.au') or current_url.endswith('seek.com.au/'):
                    return True
        
        return False
    except Exception as e:
        print(f"Error checking login: {e}")
        return False


def main():
    print("=" * 80)
    print("SEEK LOGIN HELPER")
    print("=" * 80)
    print("\nThis will open a browser window for you to login to Seek.")
    print("After logging in, the session will be saved for future scraping.")
    print("\nPress Enter to continue...")
    input()
    
    driver = None
    try:
        # Create browser (NOT headless so you can see it)
        print("\n🌐 Opening browser...")
        driver = create_driver(headless=False)
        
        # Go to Seek
        print("📱 Loading Seek...")
        driver.get("https://www.seek.com.au/")
        time.sleep(3)
        
        print("\n" + "=" * 80)
        print("👤 PLEASE LOGIN TO SEEK IN THE BROWSER WINDOW")
        print("=" * 80)
        print("\nSteps:")
        print("1. Click 'Sign in' in the top right corner")
        print("2. Enter your Seek email and password")
        print("3. Complete any security challenges if prompted")
        print("4. Wait until you're back on the Seek homepage (logged in)")
        print("5. Come back here and press Enter")
        print("\n⚠️  DO NOT close the browser window!")
        print("=" * 80)
        input("\nPress Enter after you've successfully logged in...")
        
        # Check if logged in
        print("\n🔍 Checking login status...")
        if is_logged_in(driver):
            print("✅ Successfully logged in!")
            
            # Save cookies
            print("💾 Saving session cookies...")
            save_cookies(driver)
            print("✅ Cookies saved!")
            
            # Test with a job search
            print("\n🧪 Testing job search...")
            driver.get("https://www.seek.com.au/python-jobs/in-All-Australia")
            time.sleep(5)
            
            # Check for jobs
            page_source = driver.page_source
            if 'job' in page_source.lower() and ('apply' in page_source.lower() or 'listed' in page_source.lower()):
                print("✅ Job search working!")
                print("\n🎉 SUCCESS! Seek scraping is now ready!")
                print("\nYou can now run your scraping scripts.")
                print("The session will be reused automatically.")
            else:
                print("\n⚠️  Could not verify job listings. Check the browser.")
        else:
            print("❌ Login failed. Please try again.")
            print("Make sure you:")
            print("  • Click 'Sign in' in the top right")
            print("  • Complete the full login process")
            print("  • See your profile icon/name in the top right")
            return 1
        
        print("\n✅ Setup complete! Closing browser in 5 seconds...")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if driver:
            driver.quit()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
