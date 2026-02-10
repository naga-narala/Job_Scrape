# 🚀 PRE-FLIGHT CHECKLIST - Main Test

**Date:** 7 February 2026  
**Status:** Repository cleaned and ready for main test

---

## ✅ Pre-Flight Checklist

### **1. Repository Status**
- [x] All test files archived to `archive/test_scripts/`
- [x] Documentation updated with strict rules (CONTRIBUTING.md)
- [x] README.md cleaned and simplified
- [x] test_url.json preserved
- [x] Root directory clean (20 essential files only)

### **2. Production Code**
- [x] LinkedIn scraper (src/scraper.py) - 35 KB
- [x] Seek scraper (src/seek_scraper.py) - 19 KB  
- [x] Jora scraper (src/jora_scraper.py) - 22 KB
- [x] 3-tier optimization (src/optimization.py) - 11 KB
- [x] Database layer (src/database.py) - 21 KB
- [x] AI scorer (src/scorer.py) - 21 KB
- [x] Main orchestrator (src/main.py) - 25 KB

### **3. Configuration**
- [x] config.json exists (with API key)
- [x] profile.txt exists (11 KB)
- [x] jobs.txt exists (7 KB)
- [x] generated_keywords.json exists (6.7 KB)
- [x] job_searches.json exists (67 searches enabled)

### **4. Authentication** ⚠️
Check before running main test:

```bash
# LinkedIn session check (REQUIRED)
python -c "
import sys; sys.path.insert(0, 'src')
from scraper import create_driver, load_cookies, is_logged_in
driver = create_driver(headless=True)
load_cookies(driver)
print('✅ LinkedIn session valid' if is_logged_in(driver) else '❌ LinkedIn expired - run: python archive/linkedin_login.py')
driver.quit()
"
```

**Expected:** ✅ LinkedIn session valid

### **5. Database**
- [x] data/jobs.db exists (1.6 MB)
- [x] Database accessible

```bash
# Check database
sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;"
```

**Expected:** Some number (database initialized)

---

## 🎯 Main Test Execution Plan

### **Phase 1: Individual Scraper Tests** (15 minutes)

#### Test LinkedIn:
```bash
# Quick test with 1-2 URLs from test_url.json
python -c "
import json
import sys
sys.path.insert(0, 'src')
from scraper import scrape_linkedin_jobs_from_url

with open('test_url.json') as f:
    test_data = json.load(f)
    
# Get first LinkedIn URL
linkedin_url = test_data[0]['url']  # Adjust index if needed
print(f'Testing: {linkedin_url}')

jobs = scrape_linkedin_jobs_from_url(linkedin_url, max_pages=1)
print(f'✅ LinkedIn: {len(jobs)} jobs scraped')
"
```

#### Test Seek:
```bash
# Run Seek scraper with 1 URL
python src/seek_scraper.py
```

#### Test Jora:
```bash
# Run Jora scraper with 1 URL  
python src/jora_scraper.py
```

**Expected Results:**
- LinkedIn: ~20-25 jobs (1 page)
- Seek: ~20-22 jobs (1 page)
- Jora: ~10-15 jobs (1 page)

---

### **Phase 2: Full Workflow Test** (30-45 minutes)

```bash
# Run complete workflow
python src/main.py

# This will:
# 1. Scrape from all enabled sources
# 2. Apply 3-tier filtering
# 3. Save to database
# 4. Score with AI (or parser fallback)
# 5. Send notification email
```

**Watch For:**
- ✅ Scrapers starting successfully
- ✅ Jobs being filtered (Tier 1/2/3 logs)
- ✅ Database saves
- ✅ AI scoring (or parser fallback)
- ✅ Email notification sent

**Expected Duration:** 30-45 minutes (depends on # of searches enabled)

---

### **Phase 3: Results Verification** (10 minutes)

#### Check Database:
```bash
# Total jobs
sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;"

# Jobs by source
sqlite3 data/jobs.db "SELECT source, COUNT(*) FROM jobs GROUP BY source;"

# Jobs by region  
sqlite3 data/jobs.db "SELECT region, COUNT(*) FROM jobs GROUP BY region;"

# Top 10 scored jobs
python -c "
import sys; sys.path.insert(0, 'src')
import database as db
jobs = db.get_all_jobs()
scored = [j for j in jobs if j.get('score')]
sorted_jobs = sorted(scored, key=lambda x: x.get('score', 0), reverse=True)[:10]
print('\n🏆 TOP 10 JOBS:')
for i, job in enumerate(sorted_jobs, 1):
    print(f'{i}. {job[\"score\"]}% - {job[\"title\"][:60]}')
"
```

#### Check Dashboard:
```bash
# Start dashboard
python src/dashboard.py

# Open http://localhost:8000
# Verify:
# - Jobs are displayed
# - Day-wise grouping works
# - Scores are shown
# - Links are clickable
```

---

## 📊 Success Criteria

### **Minimum Requirements:**
- ✅ At least 50 jobs scraped total
- ✅ All 3 scrapers executed without errors
- ✅ 3-tier filtering applied (check logs for tier1/2/3 counts)
- ✅ Jobs saved to database (no duplicates)
- ✅ AI scoring completed (or parser fallback)
- ✅ Dashboard displays jobs correctly

### **Optimal Results:**
- ✅ 100+ jobs scraped
- ✅ 10-30% Tier 1 filtering efficiency
- ✅ 0-5% Tier 2 duplicates
- ✅ 0-5% Tier 3 quality failures
- ✅ 10+ jobs scored 70%+
- ✅ Email notification sent successfully

---

## ⚠️ Troubleshooting

### **If LinkedIn scraper fails:**
```bash
# Re-authenticate
python archive/linkedin_login.py
```

### **If AI scoring fails:**
- Check config.json has OpenRouter API key
- Check API credit balance
- Parser fallback should activate automatically

### **If database errors:**
```bash
# Check database file
ls -lh data/jobs.db

# Check schema
sqlite3 data/jobs.db ".schema jobs"
```

### **If no jobs scraped:**
- Check job_searches.json has enabled searches
- Verify network connection
- Check scraper logs for errors

---

## 📝 Post-Test Actions

After successful main test:

1. **Review Logs:**
   ```bash
   # Check for any warnings/errors
   tail -100 data/logs/*.log
   ```

2. **Analyze Metrics:**
   - Total jobs scraped
   - Filtering efficiency (Tier 1/2/3)
   - Score distribution
   - Source breakdown

3. **Update Documentation:**
   - Add test results to SYSTEM_STATUS.md
   - Note any issues encountered
   - Update README.md if needed

4. **Backup Database:**
   ```bash
   cp data/jobs.db data/jobs.db.backup_$(date +%Y%m%d)
   ```

---

## 🎯 Ready to Launch?

**Final Checklist:**
- [ ] Read CONTRIBUTING.md
- [ ] LinkedIn session valid
- [ ] config.json has API key
- [ ] All 3 scrapers present in src/
- [ ] Database initialized
- [ ] test_url.json preserved
- [ ] Archive organized

**If all checked, proceed with:**
```bash
python src/main.py
```

---

**Good luck with the main test! 🚀**

---

**Notes:**
- Expected runtime: 30-45 minutes
- Monitor console for progress
- Check dashboard after completion
- Save logs for analysis

**Emergency Stop:**
- Press Ctrl+C to stop gracefully
- Database saves are incremental
- Can resume later
