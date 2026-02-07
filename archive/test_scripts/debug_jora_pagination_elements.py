#!/usr/bin/env python3
"""Debug Jora pagination elements"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
import time

url = 'https://au.jora.com/j?sp=search&trigger_source=serp&a=7d&q=graduate%20artificial%20intelligence%20engineer&l=Australia'

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

stealth(driver, languages=['en-US', 'en'], vendor='Google Inc.', platform='Win32', 
        webgl_vendor='Intel Inc.', renderer='Intel Iris OpenGL Engine', fix_hairline=True)

driver.get(url)
time.sleep(5)

# Scroll to bottom to see pagination
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

print("\n🔍 Looking for pagination elements:\n")

# Check for nav element
nav_elements = driver.find_elements(By.TAG_NAME, 'nav')
print(f"Found {len(nav_elements)} <nav> elements")

# Check for all links
all_links = driver.find_elements(By.TAG_NAME, 'a')
pagination_links = [link for link in all_links if link.text.strip() in ['1', '2', '3', '4', '5', '6', '>', '›', 'Next', '»', 'Previous', '<', '‹']]
print(f"\nFound {len(pagination_links)} potential pagination links:")
for link in pagination_links[:10]:
    print(f"   Text: '{link.text.strip()}' | href: {link.get_attribute('href')[:80] if link.get_attribute('href') else 'None'}")
    print(f"   Class: '{link.get_attribute('class')}'")
    print()

# Check page source for pagination HTML
page_source = driver.page_source.lower()
if 'pagination' in page_source:
    # Extract pagination section
    import re
    pagination_matches = re.findall(r'(<nav[^>]*pagination[^>]*>.*?</nav>)', page_source, re.DOTALL | re.IGNORECASE)
    if pagination_matches:
        print(f"\n📄 Pagination HTML found:")
        print(pagination_matches[0][:500])

driver.quit()
