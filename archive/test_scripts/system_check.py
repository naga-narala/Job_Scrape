#!/usr/bin/env python3
"""
Complete system check for all scrapers and supporting files
Run before main test to verify everything is ready
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')

print('\n' + '='*80)
print('🔍 COMPREHENSIVE SYSTEM CHECK FOR JOB SCRAPER')
print('='*80)

issues = []
warnings = []
checks_passed = 0
total_checks = 0

# ============================================================================
# 1. CHECK SCRAPER FILES
# ============================================================================
print('\n📂 1. SCRAPER FILES:')
total_checks += 3

scrapers = {
    'LinkedIn': 'src/scraper.py',
    'Seek': 'src/seek_scraper.py',
    'Jora': 'src/jora_scraper.py'
}

for name, filepath in scrapers.items():
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size / 1024  # KB
        print(f'  ✅ {name}: {filepath} ({size:.1f} KB)')
        checks_passed += 1
    else:
        print(f'  ❌ {name}: {filepath} - MISSING!')
        issues.append(f'Missing scraper: {filepath}')

# ============================================================================
# 2. CHECK CORE COMPONENTS
# ============================================================================
print('\n⚙️ 2. CORE COMPONENTS:')
total_checks += 4

components = {
    'Optimization Manager': 'src/optimization.py',
    'Database': 'src/database.py',
    'AI Scorer': 'src/scorer.py',
    'Main Orchestrator': 'src/main.py'
}

for name, filepath in components.items():
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size / 1024
        print(f'  ✅ {name}: {filepath} ({size:.1f} KB)')
        checks_passed += 1
    else:
        print(f'  ❌ {name}: {filepath} - MISSING!')
        issues.append(f'Missing component: {filepath}')

# ============================================================================
# 3. VERIFY IMPORTS
# ============================================================================
print('\n🔬 3. IMPORT VERIFICATION:')
total_checks += 6

# LinkedIn scraper
try:
    from scraper import create_driver, scrape_jobs, load_cookies, is_logged_in
    print('  ✅ LinkedIn scraper imports OK')
    checks_passed += 1
except Exception as e:
    print(f'  ❌ LinkedIn scraper import failed: {e}')
    issues.append(f'LinkedIn scraper import error: {e}')

# Seek scraper
try:
    from seek_scraper import create_seek_driver, scrape_seek_jobs
    print('  ✅ Seek scraper imports OK')
    checks_passed += 1
except Exception as e:
    print(f'  ❌ Seek scraper import failed: {e}')
    issues.append(f'Seek scraper import error: {e}')

# Jora scraper
try:
    from jora_scraper import create_jora_driver, scrape_jora_jobs
    print('  ✅ Jora scraper imports OK')
    checks_passed += 1
except Exception as e:
    print(f'  ❌ Jora scraper import failed: {e}')
    issues.append(f'Jora scraper import error: {e}')

# Optimization
try:
    from optimization import OptimizationManager
    opt = OptimizationManager('test_search')
    print('  ✅ Optimization Manager OK')
    checks_passed += 1
except Exception as e:
    print(f'  ❌ Optimization Manager failed: {e}')
    issues.append(f'Optimization import error: {e}')

# Database
try:
    from database import get_all_jobs, save_jobs, init_database
    print('  ✅ Database module OK')
    checks_passed += 1
except Exception as e:
    print(f'  ❌ Database module failed: {e}')
    issues.append(f'Database import error: {e}')

# Scorer
try:
    from scorer import score_jobs
    print('  ✅ AI Scorer module OK')
    checks_passed += 1
except Exception as e:
    print(f'  ❌ AI Scorer failed: {e}')
    issues.append(f'Scorer import error: {e}')

# ============================================================================
# 4. CHECK CONFIGURATION FILES
# ============================================================================
print('\n⚙️ 4. CONFIGURATION FILES:')
total_checks += 5

# config.json
try:
    with open('config.json') as f:
        config = json.load(f)
    if config.get('openrouter_api_key'):
        print('  ✅ config.json with API key configured')
        checks_passed += 1
    else:
        print('  ⚠️ config.json exists but no API key')
        warnings.append('OpenRouter API key not configured in config.json')
except Exception as e:
    print(f'  ❌ config.json error: {e}')
    issues.append('config.json missing or invalid')

# generated_keywords.json
try:
    with open('generated_keywords.json') as f:
        keywords = json.load(f)
    title_kw = len(keywords.get('title_keywords', []))
    exclude_kw = len(keywords.get('exclude_keywords', []))
    print(f'  ✅ generated_keywords.json ({title_kw} title, {exclude_kw} exclude)')
    checks_passed += 1
except Exception as e:
    print(f'  ❌ generated_keywords.json error: {e}')
    issues.append('generated_keywords.json missing')

# job_searches.json
try:
    with open('job_searches.json') as f:
        data = json.load(f)
    searches = data if isinstance(data, list) else data.get('searches', [])
    enabled = [s for s in searches if s.get('enabled', True)]
    print(f'  ✅ job_searches.json ({len(searches)} total, {len(enabled)} enabled)')
    checks_passed += 1
except Exception as e:
    print(f'  ❌ job_searches.json error: {e}')
    issues.append('job_searches.json missing')

# profile.txt
if Path('profile.txt').exists():
    size = Path('profile.txt').stat().st_size
    print(f'  ✅ profile.txt ({size:,} bytes)')
    checks_passed += 1
else:
    print('  ❌ profile.txt missing')
    issues.append('profile.txt missing')

# jobs.txt
if Path('jobs.txt').exists():
    size = Path('jobs.txt').stat().st_size
    print(f'  ✅ jobs.txt ({size:,} bytes)')
    checks_passed += 1
else:
    print('  ❌ jobs.txt missing')
    issues.append('jobs.txt missing')

# ============================================================================
# 5. CHECK AUTHENTICATION
# ============================================================================
print('\n🔑 5. AUTHENTICATION STATUS:')
total_checks += 3

# LinkedIn
try:
    from scraper import create_driver, load_cookies, is_logged_in
    driver = create_driver(headless=True)
    load_cookies(driver)
    if is_logged_in(driver):
        print('  ✅ LinkedIn session valid')
        checks_passed += 1
    else:
        print('  ❌ LinkedIn session expired')
        warnings.append('Run: python linkedin_login.py')
    driver.quit()
except Exception as e:
    print(f'  ⚠️ LinkedIn check failed: {e}')
    warnings.append('Could not verify LinkedIn session')

# Seek
if Path('seek_cookies.pkl').exists():
    size = Path('seek_cookies.pkl').stat().st_size
    print(f'  ✅ Seek cookies exist ({size} bytes)')
    checks_passed += 1
else:
    print('  ⚠️ Seek cookies missing')
    warnings.append('Run: python seek_login.py (optional)')

# Jora
if Path('jora_cookies.pkl').exists():
    size = Path('jora_cookies.pkl').stat().st_size
    print(f'  ✅ Jora cookies exist ({size} bytes)')
    checks_passed += 1
else:
    print('  ⚠️ Jora cookies missing (will create new session)')

# ============================================================================
# 6. CHECK DATABASE
# ============================================================================
print('\n💾 6. DATABASE STATUS:')
total_checks += 1

try:
    from database import get_all_jobs
    jobs = get_all_jobs()
    linkedin_jobs = [j for j in jobs if j.get('source') == 'linkedin']
    seek_jobs = [j for j in jobs if j.get('source') == 'seek']
    jora_jobs = [j for j in jobs if j.get('source') == 'jora']
    
    print(f'  ✅ Database accessible ({len(jobs)} total jobs)')
    print(f'     • LinkedIn: {len(linkedin_jobs)}')
    print(f'     • Seek: {len(seek_jobs)}')
    print(f'     • Jora: {len(jora_jobs)}')
    checks_passed += 1
except Exception as e:
    print(f'  ⚠️ Database not initialized (will be created on first run)')
    warnings.append('Database will be initialized on first scrape')

# ============================================================================
# FINAL RESULTS
# ============================================================================
print('\n' + '='*80)
print('📊 FINAL RESULTS:')
print('='*80)

print(f'\n✅ Checks passed: {checks_passed}/{total_checks}')

if issues:
    print(f'\n❌ CRITICAL ISSUES ({len(issues)}):')
    for issue in issues:
        print(f'   • {issue}')

if warnings:
    print(f'\n⚠️ WARNINGS ({len(warnings)}):')
    for warning in warnings:
        print(f'   • {warning}')

print('\n' + '='*80)

if not issues:
    print('🎉 ALL CRITICAL SYSTEMS OPERATIONAL!')
    print('\n✅ LinkedIn Scraper: READY')
    print('✅ Seek Scraper: READY')
    print('✅ Jora Scraper: READY')
    print('✅ 3-Tier Optimization: READY')
    print('✅ Configuration: READY')
    
    if warnings:
        print(f'\n⚠️ {len(warnings)} minor warnings (can be ignored)')
    
    print('\n🚀 SYSTEM IS READY FOR MAIN TEST!')
    print('\nRun: python src/main.py')
else:
    print('🛑 CRITICAL ISSUES MUST BE FIXED BEFORE TESTING!')
    print('\nFix the issues listed above, then run this check again.')

print('='*80 + '\n')

# Exit code
sys.exit(0 if not issues else 1)
