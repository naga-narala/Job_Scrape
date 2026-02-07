#!/usr/bin/env python3
"""
Debug script to see what LinkedIn returns and what selectors work
"""

import sys
import time
sys.path.insert(0, 'src')

from scraper import create_driver, load_cookies
from selenium.webdriver.common.by import By

# Load URL from test_url.json
import json
with open('test_url.json') as f:
    data = json.load(f)
    url = data['linkedin'][0]['url']

print("🔍 Debugging LinkedIn page structure...")
print(f"URL: {url}\n")

driver = create_driver(headless=False)  # Visible for debugging
load_cookies(driver)

print("Loading page...")
driver.get(url)
time.sleep(10)  # Wait for page to load

print("\n📊 Testing selectors:")

selectors = [
    "ul.jobs-search__results-list",
    "ul.jobs-search__results-list > li",
    "li.jobs-search-results__list-item",
    "li.scaffold-layout__list-item",
    "div.job-card-container",
    "li[class*='job']",
    "div[class*='job-card']",
    "ul[class*='jobs-search'] li",
]

for selector in selectors:
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        print(f"✓ '{selector}': {len(elements)} elements")
    except Exception as e:
        print(f"✗ '{selector}': ERROR - {e}")

# Save page source
with open('/tmp/linkedin_debug.html', 'w', encoding='utf-8') as f:
    f.write(driver.page_source)

print("\n✅ Page source saved to: /tmp/linkedin_debug.html")
print("Review the HTML to see the correct selectors")

# Try to find first job title
print("\n🔍 Looking for job titles...")
title_selectors = [
    "h3.base-search-card__title",
    "a.base-card__full-link",
    "span.job-card-list__title",
    "h3[class*='title']",
]

for selector in title_selectors:
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        if elements:
            print(f"✓ '{selector}': {len(elements)} titles")
            if len(elements) > 0:
                print(f"   First title: {elements[0].text.strip()[:60]}")
    except Exception as e:
        print(f"✗ '{selector}': ERROR")

print("\nKeeping browser open for manual inspection...")
print("Press Ctrl+C when done")

try:
    time.sleep(300)  # Keep open for 5 minutes
except KeyboardInterrupt:
    print("\nClosing browser...")

driver.quit()
