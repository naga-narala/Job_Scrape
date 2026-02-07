#!/usr/bin/env python3
"""
Debug script to understand Jora card extraction issues
Prints HTML structure and extraction attempts for each card
"""

import sys
sys.path.insert(0, 'src')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
import time

def create_debug_driver():
    """Create Chrome driver for debugging"""
    options = Options()
    # Run in VISIBLE mode to see what's happening
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    # Apply stealth
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    
    return driver

def debug_extraction():
    """Debug Jora card extraction"""
    url = "https://au.jora.com/j?sp=search&trigger_source=serp&a=7d&q=graduate%20artificial%20intelligence%20engineer&l=Australia"
    
    driver = create_debug_driver()
    
    try:
        print(f"\n🌐 Loading: {url}\n")
        driver.get(url)
        time.sleep(3)  # Wait for page load
        
        # Find all job cards
        cards = driver.find_elements(By.CSS_SELECTOR, 'div.job-card.result')
        print(f"📊 Found {len(cards)} job cards\n")
        
        for idx, card in enumerate(cards[:5], 1):  # Debug first 5 cards
            print(f"\n{'='*80}")
            print(f"CARD #{idx}")
            print('='*80)
            
            # Get card HTML
            try:
                card_html = card.get_attribute('outerHTML')
                print(f"\n📄 Card HTML (first 600 chars):")
                print(card_html[:600])
                print("...")
            except Exception as e:
                print(f"❌ Could not get HTML: {e}")
            
            # Get card text
            try:
                card_text = card.text
                print(f"\n📝 Card visible text:")
                print(card_text[:300])
                if len(card_text) > 300:
                    print("...")
            except Exception as e:
                print(f"❌ Could not get text: {e}")
            
            # Try to extract title - Method 1: h2.job-title
            print(f"\n🔍 Extraction attempts:")
            try:
                h2 = card.find_element(By.CSS_SELECTOR, 'h2.job-title')
                h2_text = h2.text.strip()
                print(f"✅ h2.job-title found")
                print(f"   Text: '{h2_text}'")
                print(f"   Length: {len(h2_text)}")
                
                # Check for nested link
                try:
                    link = h2.find_element(By.TAG_NAME, 'a')
                    link_text = link.text.strip()
                    link_href = link.get_attribute('href')
                    print(f"   Nested <a> text: '{link_text}'")
                    print(f"   Nested <a> href: '{link_href}'")
                except Exception as e:
                    print(f"   ❌ No nested <a>: {e}")
                    
            except Exception as e:
                print(f"❌ h2.job-title not found: {e}")
            
            # Try to extract title - Method 2: Any h2
            try:
                h2_any = card.find_element(By.CSS_SELECTOR, 'h2')
                print(f"✅ h2 (any) text: '{h2_any.text.strip()}'")
            except Exception as e:
                print(f"❌ No h2 found: {e}")
            
            # Try to extract link - Method 3: Any link with /job/
            try:
                job_link = card.find_element(By.CSS_SELECTOR, 'a[href*="/job/"]')
                print(f"✅ Job link found: {job_link.get_attribute('href')}")
                print(f"   Link text: '{job_link.text.strip()}'")
            except Exception as e:
                print(f"❌ No job link found: {e}")
            
            print()
        
        print(f"\n{'='*80}")
        print("Press Enter to close browser...")
        input()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_extraction()
