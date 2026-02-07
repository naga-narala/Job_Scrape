#!/usr/bin/env python3
"""Simple system readiness check"""

from pathlib import Path
import json

print('\n🚀 QUICK SYSTEM CHECK\n')
print('='*70)

ready = True

# Check all 3 scrapers exist
print('\n✅ SCRAPERS:')
for scraper in ['src/scraper.py', 'src/seek_scraper.py', 'src/jora_scraper.py']:
    if Path(scraper).exists():
        print(f'   ✅ {scraper}')
    else:
        print(f'   ❌ {scraper} MISSING!')
        ready = False

# Check core files
print('\n✅ CORE COMPONENTS:')
for core in ['src/optimization.py', 'src/database.py', 'src/scorer.py', 'src/main.py']:
    if Path(core).exists():
        print(f'   ✅ {core}')
    else:
        print(f'   ❌ {core} MISSING!')
        ready = False

# Check config
print('\n✅ CONFIGURATION:')
for cfg in ['config.json', 'generated_keywords.json', 'job_searches.json', 'profile.txt', 'jobs.txt']:
    if Path(cfg).exists():
        print(f'   ✅ {cfg}')
    else:
        print(f'   ❌ {cfg} MISSING!')
        ready = False

# Check authentication
print('\n⚠️ AUTHENTICATION (optional):')
if Path('linkedin_cookies.pkl').exists():
    print('   ✅ LinkedIn cookies')
else:
    print('   ⚠️ LinkedIn cookies missing - run: python linkedin_login.py')

if Path('seek_cookies.pkl').exists():
    print('   ✅ Seek cookies')
else:
    print('   ⚠️ Seek cookies missing (will work without, or run: python seek_login.py)')

if Path('jora_cookies.pkl').exists():
    print('   ✅ Jora cookies')
else:
    print('   ⚠️ Jora cookies missing (scraper will create session automatically)')

# Check database
print('\n💾 DATABASE:')
if Path('data/jobs.db').exists():
    print('   ✅ Database exists')
else:
    print('   ⚠️ Database not initialized (will be created on first run)')

# Check job searches config
print('\n🔍 JOB SEARCHES:')
try:
    with open('job_searches.json') as f:
        data = json.load(f)
    searches = data if isinstance(data, list) else data.get('searches', [])
    enabled = [s for s in searches if s.get('enabled', True)]
    linkedin = [s for s in enabled if s.get('source') == 'linkedin']
    seek = [s for s in enabled if s.get('source') == 'seek']
    jora = [s for s in enabled if s.get('source') == 'jora']
    
    print(f'   Total: {len(searches)} | Enabled: {len(enabled)}')
    print(f'   • LinkedIn: {len(linkedin)} searches')
    print(f'   • Seek: {len(seek)} searches')
    print(f'   • Jora: {len(jora)} searches')
except:
    print('   ❌ Could not read job_searches.json')
    ready = False

print('\n' + '='*70)
if ready:
    print('\n🎉 ALL SYSTEMS READY FOR MAIN TEST!')
    print('\n✅ All 3 scrapers installed')
    print('✅ All supporting files present')
    print('✅ Configuration complete')
    print('\n🚀 You can now run: python src/main.py')
else:
    print('\n❌ SYSTEM NOT READY - Fix missing files above')

print('='*70 + '\n')
