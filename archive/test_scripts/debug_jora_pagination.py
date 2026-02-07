#!/usr/bin/env python3
"""
Debug Jora pagination to understand how to navigate to page 2
"""

import sys
sys.path.insert(0, 'src')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
import time

def debug_pagination():
    """Check Jora pagination structure"""
    url = "https://au.jora.com/j?sp=search&trigger_source=serp&a=7d&q=graduate%20artificial%20intelligence%20engineer&l=Australia"
    
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(options=options)
    
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    
    try:
        print(f"\n🌐 Loading: {url}\n")
        driver.get(url)
        time.sleep(5)  # Wait for page load
        
        # Scroll to bottom to load pagination
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        print("🔍 Looking for pagination elements...\n")
        
        # Try to find all pagination-related elements
        pagination_selectors = [
            'nav[aria-label="pagination"]',
            'div.pagination',
            'ul.pagination',
            'div[class*="pagination"]',
            'nav[class*="pagination"]',
            'a[aria-label="Next"]',
            'button[aria-label="Next"]',
            'a.next',
            'button.next',
            'a:contains("Next")',
            'a:contains("›")',
            'a[rel="next"]',
        ]
        
        for selector in pagination_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector.replace(':contains', ''))
                if elements:
                    print(f"✅ Found {len(elements)} elements with selector: {selector}")
                    for idx, elem in enumerate(elements[:3], 1):
                        try:
                            text = elem.text.strip()
                            html = elem.get_attribute('outerHTML')[:200]
                            print(f"   Element {idx}:")
                            print(f"      Text: '{text}'")
                            print(f"      HTML: {html}...")
                            print()
                        except:
                            pass
            except:
                continue
        
        # Check for "load more" or infinite scroll
        print("\n🔍 Checking for 'Load More' buttons...")
        load_more_selectors = [
            'button:contains("Load")',
            'button:contains("More")',
            'a:contains("Load")',
            'button[class*="load"]',
            'button[class*="more"]',
        ]
        
        for selector in load_more_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector.replace(':contains', ''))
                if elements:
                    print(f"✅ Found potential load more: {selector}")
            except:
                continue
        
        # Get page source around bottom of page
        print("\n📄 Page HTML around bottom (last 2000 chars):")
        page_source = driver.page_source
        print(page_source[-2000:])
        
        print("\n\nPress Enter to close...")
        input()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_pagination()
