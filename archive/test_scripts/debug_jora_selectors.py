#!/usr/bin/env python3
"""
Debug Jora HTML Structure
Find the correct selectors for job cards
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from jora_scraper_selenium import create_jora_driver, load_jora_cookies
from selenium.webdriver.common.by import By


def inspect_jora_page():
    """Inspect Jora page structure to find job cards"""
    
    test_url = "https://au.jora.com/j?sp=search&trigger_source=serp&a=7d&q=graduate%20artificial%20intelligence%20engineer&l=Australia"
    
    driver = create_jora_driver(headless=False)  # Show browser
    load_jora_cookies(driver)
    
    print("\n" + "="*70)
    print("🔍 INSPECTING JORA PAGE STRUCTURE")
    print("="*70 + "\n")
    
    driver.get(test_url)
    print(f"✅ Loaded URL: {test_url}")
    
    # Wait for page to load
    print("⏳ Waiting 10 seconds for page to fully load...")
    time.sleep(10)
    
    # Save page source
    html_path = Path(__file__).parent / 'jora_debug_page.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"💾 Saved HTML to: {html_path}")
    
    # Try multiple selectors
    selectors_to_try = [
        ('article', By.TAG_NAME),
        ('div[class*="job"]', By.CSS_SELECTOR),
        ('div[class*="card"]', By.CSS_SELECTOR),
        ('div[data-job-id]', By.CSS_SELECTOR),
        ('div[id*="job"]', By.CSS_SELECTOR),
        ('[class*="result"]', By.CSS_SELECTOR),
        ('[class*="listing"]', By.CSS_SELECTOR),
        ('a[href*="/job/"]', By.CSS_SELECTOR),
        ('h2', By.TAG_NAME),
        ('h3', By.TAG_NAME),
    ]
    
    print("\n" + "="*70)
    print("🔍 TESTING SELECTORS")
    print("="*70 + "\n")
    
    for selector, by_type in selectors_to_try:
        try:
            elements = driver.find_elements(by_type, selector)
            print(f"✅ {selector:40s} → {len(elements):3d} elements")
            
            if len(elements) > 0 and len(elements) < 50:
                # Show first element sample
                first = elements[0]
                text = first.text[:100].replace('\n', ' ')
                classes = first.get_attribute('class') or ''
                print(f"   Sample: {text}...")
                print(f"   Classes: {classes[:60]}")
                print()
        except Exception as e:
            print(f"❌ {selector:40s} → Error: {str(e)[:50]}")
    
    print("\n" + "="*70)
    print("🔍 LOOKING FOR JOB LINKS")
    print("="*70 + "\n")
    
    # Find all links
    all_links = driver.find_elements(By.TAG_NAME, 'a')
    job_links = [l for l in all_links if l.get_attribute('href') and '/job/' in l.get_attribute('href')]
    
    print(f"Total links: {len(all_links)}")
    print(f"Job links (/job/ in href): {len(job_links)}")
    
    if job_links:
        print("\n📋 Sample job links:")
        for i, link in enumerate(job_links[:10], 1):
            try:
                text = link.text.strip()
                href = link.get_attribute('href')
                classes = link.get_attribute('class') or ''
                print(f"{i}. {text[:60]}")
                print(f"   URL: {href[:80]}")
                print(f"   Classes: {classes[:60]}")
                print()
            except:
                pass
    
    print("\n" + "="*70)
    print("Press Ctrl+C to close browser...")
    print("="*70)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ Closing browser...")
        driver.quit()


if __name__ == '__main__':
    inspect_jora_page()
