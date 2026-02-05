#!/usr/bin/env python3
"""
LinkedIn Login Helper
Opens browser for you to manually login, then saves cookies for future use
"""

import sys
sys.path.insert(0, 'src')

from scraper import create_driver, save_cookies, is_logged_in
import time

def main():
    print("=" * 80)
    print("LINKEDIN LOGIN HELPER")
    print("=" * 80)
    print("\nThis will open a browser window for you to login to LinkedIn.")
    print("After logging in, the session will be saved for future scraping.")
    print("\nPress Enter to continue...")
    input()
    
    driver = None
    try:
        # Create browser (NOT headless so you can see it)
        print("\n🌐 Opening browser...")
        driver = create_driver(headless=False)
        
        # Go to LinkedIn
        print("📱 Loading LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        
        print("\n" + "=" * 80)
        print("👤 PLEASE LOGIN TO LINKEDIN IN THE BROWSER WINDOW")
        print("=" * 80)
        print("\nSteps:")
        print("1. Enter your LinkedIn email and password")
        print("2. Complete any security challenges (2FA, etc.)")
        print("3. Wait until you see your LinkedIn feed/homepage")
        print("4. Come back here and press Enter")
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
            print("✅ Cookies saved to linkedin_cookies.pkl")
            
            # Test with a job search
            print("\n🧪 Testing job search...")
            driver.get("https://www.linkedin.com/jobs/search/?keywords=AI%20Engineer&location=Australia&f_TPR=r604800")
            time.sleep(8)
            
            # Check for jobs
            job_cards = driver.find_elements("css selector", "div.job-search-card, li.jobs-search-results__list-item")
            print(f"✅ Found {len(job_cards)} job cards!")
            
            if len(job_cards) > 0:
                print("\n🎉 SUCCESS! LinkedIn scraping is now ready!")
                print("\nYou can now:")
                print("  • Run test_6_urls.py to test 12 URLs")
                print("  • Run main.py for full scraping")
                print("\nThe session will be reused automatically.")
            else:
                print("\n⚠️  No job cards found. LinkedIn may have changed their HTML structure.")
                print("Saving page source for debugging...")
                with open('/tmp/linkedin_logged_in.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print("Saved to /tmp/linkedin_logged_in.html")
        else:
            print("❌ Login failed. Please try again.")
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
