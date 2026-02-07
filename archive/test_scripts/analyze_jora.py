#!/usr/bin/env python3
"""Jora scraper page-by-page analysis - similar to Seek analysis"""

print('\n📊 JORA SCRAPER - PAGE-BY-PAGE ANALYSIS')
print('='*70)
print('Based on most recent 6-page scrape:\n')

# Data from the scraping run
pages = [
    {'page': 1, 'cards': 15, 'scraped': 14, 'tier1': 1, 'tier2': 0, 'tier3': 0},
    {'page': 2, 'cards': 15, 'scraped': 15, 'tier1': 0, 'tier2': 0, 'tier3': 0},
    {'page': 3, 'cards': 15, 'scraped': 13, 'tier1': 2, 'tier2': 0, 'tier3': 0},
    {'page': 4, 'cards': 15, 'scraped': 13, 'tier1': 2, 'tier2': 0, 'tier3': 0},
    {'page': 5, 'cards': 15, 'scraped': 15, 'tier1': 0, 'tier2': 0, 'tier3': 0},
    {'page': 6, 'cards': 1, 'scraped': 1, 'tier1': 0, 'tier2': 0, 'tier3': 0}
]

for p in pages:
    total_filtered = p['tier1'] + p['tier2'] + p['tier3']
    efficiency = (total_filtered / p['cards'] * 100) if p['cards'] > 0 else 0
    
    status = ''
    if efficiency == 0:
        status = '(all quality jobs)'
    elif efficiency < 10:
        status = ''
    elif efficiency < 20:
        status = '⚠️'
    else:
        status = '⭐'
    
    print(f'Page {p["page"]}: {efficiency:.1f}% filtered ({total_filtered} jobs) {status}')
    if total_filtered > 0:
        details = []
        if p['tier1'] > 0:
            details.append(f'Tier 1: {p["tier1"]} (title filtering)')
        if p['tier2'] > 0:
            details.append(f'Tier 2: {p["tier2"]} (duplicates)')
        if p['tier3'] > 0:
            details.append(f'Tier 3: {p["tier3"]} (low quality)')
        print(f'        {" | ".join(details)}')

total_cards = sum(p['cards'] for p in pages)
total_scraped = sum(p['scraped'] for p in pages)
total_tier1 = sum(p['tier1'] for p in pages)
total_tier2 = sum(p['tier2'] for p in pages)
total_tier3 = sum(p['tier3'] for p in pages)
total_filtered = total_tier1 + total_tier2 + total_tier3

print('\n' + '='*70)
print('OVERALL SUMMARY:')
print(f'  Total job cards seen: {total_cards}')
print(f'  Jobs scraped: {total_scraped}')
print(f'  Tier 1 filtered: {total_tier1} ({total_tier1/total_cards*100:.1f}% - Senior/Lead roles)')
print(f'  Tier 2 skipped: {total_tier2} ({total_tier2/total_cards*100:.1f}% - Duplicates)')
print(f'  Tier 3 filtered: {total_tier3} ({total_tier3/total_cards*100:.1f}% - Low quality)')
print(f'  Overall efficiency: {total_filtered/total_cards*100:.1f}%')
print('='*70)

print('\n🎯 KEY INSIGHTS:')
print('  • Pages 2 & 5: 0% filtered (all 15 jobs were quality junior roles)')
print('  • Pages 3 & 4: ~13% filtered (2 Senior jobs each)')
print('  • Page 1: 6.7% filtered (1 Senior job)')
print('  • Page 6: Only 1 job found (end of results)')
print('\n  ✅ Very low filtering rate (6.6%) = most jobs match your profile!')
print('  ✅ All Tier 2/3 passed = no duplicates, high-quality descriptions')
print('='*70)
