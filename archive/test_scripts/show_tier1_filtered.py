#!/usr/bin/env python3
"""
Extract Tier 1 filtered jobs from each page
"""

import sys
import json
import logging

sys.path.insert(0, 'src')

# Capture all logs including DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s',
    handlers=[logging.FileHandler('/tmp/tier1_filter_capture.log', mode='w')]
)

from scraper import fetch_all_jobs

# Load test URL
with open('test_url.json') as f:
    data = json.load(f)
    searches = data.get('linkedin', [])

with open('config.json') as f:
    config = json.load(f)

print("=" * 80)
print("🔍 CAPTURING TIER 1 FILTERED JOBS")
print("=" * 80)
print("\nRunning scraper to capture filtered job titles...")
print("This will take ~7 minutes...\n")

# Run scraper
jobs, stats = fetch_all_jobs(
    searches,
    api_key=config.get('api_key'),
    headless=True,
    max_pages=3
)

print(f"\n✅ Scraping complete: {len(jobs)} jobs scraped")

# Parse the log file to extract filtered jobs by page
with open('/tmp/tier1_filter_capture.log', 'r') as f:
    log_content = f.read()

# Extract filtered job titles
import re

# Find all "Tier 1 filtered" entries
filtered_pattern = r'Tier 1 filtered: (.*?) - (.*?)$'
filtered_jobs = re.findall(filtered_pattern, log_content, re.MULTILINE)

# Find page boundaries in the log
page_pattern = r'Fetching page (\d+)/3:'
page_markers = [(int(m.group(1)), m.start()) for m in re.finditer(page_pattern, log_content)]

# Organize filtered jobs by page
page_filtered = {1: [], 2: [], 3: []}

for title, reason in filtered_jobs:
    # Find which page this belongs to based on position in log
    title_pos = log_content.find(f"Tier 1 filtered: {title}")
    
    page_num = 1
    for pg, pos in page_markers:
        if title_pos > pos:
            page_num = pg
    
    page_filtered[page_num].append({'title': title, 'reason': reason})

# Display results
print("\n" + "=" * 80)
print("TIER 1 FILTERED JOBS BY PAGE")
print("=" * 80)

for page in [1, 2, 3]:
    print(f"\n📄 PAGE {page} - {len(page_filtered[page])} jobs filtered:")
    for i, job in enumerate(page_filtered[page], 1):
        print(f"   {i}. {job['title']}")
        print(f"      Reason: {job['reason']}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nPage 1: {len(page_filtered[1])} filtered")
print(f"Page 2: {len(page_filtered[2])} filtered")
print(f"Page 3: {len(page_filtered[3])} filtered")
print(f"Total: {sum(len(page_filtered[p]) for p in [1,2,3])} filtered by Tier 1")
print("\n" + "=" * 80)
