# Workflow Settings Updated for Daily Morning Runs
**Date:** February 15, 2026

## Changes Made

### ✅ 1. Reduced Pages Per Platform
**File:** `config.json`

**Before:**
```json
"linkedin_max_pages": 4,
"seek_max_pages": 4,
"jora_max_pages": 4,
```

**After:**
```json
"linkedin_max_pages": 2,
"seek_max_pages": 2,
"jora_max_pages": 2,
```

**Impact:** 50% reduction in pages scraped per search

---

### ✅ 2. Changed Time Filter to 1 Day
**File:** `job_searches.json`  
**Updated:** All 46 search URLs

**Changes by platform:**

| Platform | Before | After |
|----------|--------|-------|
| **LinkedIn** | `f_TPR=r604800` (7 days) | `f_TPR=r86400` (1 day) |
| **Seek** | `daterange=7` (7 days) | `daterange=1` (1 day) |
| **Jora** | `a=7days` (7 days) | `a=1day` (1 day) |

**Impact:** Only jobs posted in last 24 hours will be scraped

---

### ✅ 3. Scheduling Already Configured
**File:** `config.json`

```json
"check_interval_hours": 24,
"timezone": "Australia/Perth",
```

**How it works:**
- Runs automatically every 24 hours
- Timezone: Australia/Perth (AWST)
- To run at specific time, use system cron or Task Scheduler

---

## New Workflow Performance

### Expected Volume Per Run

**Before (7-day filter, 4 pages):**
```
46 searches × 4 pages × ~20 jobs/page = ~3,680 raw jobs
After deduplication: ~150-200 unique new jobs
```

**After (1-day filter, 2 pages):**
```
46 searches × 2 pages × ~20 jobs/page = ~1,840 raw jobs
After deduplication: ~30-50 unique new jobs per day
```

### Time Estimates

| Metric | Before | After |
|--------|--------|-------|
| Pages scraped | 184 pages | 92 pages |
| Raw jobs | ~3,680 | ~1,840 |
| Unique new jobs | ~150-200 | ~30-50 |
| Run time | ~60-90 min | ~20-30 min |
| AI scoring cost | ~$0.07 | ~$0.02 |

---

## Daily Morning Run Setup

### Option 1: Let Script Run Continuously (Current)
```bash
python3 src/main.py
```
- Runs immediately, then every 24 hours
- Keeps running in background

### Option 2: Schedule with Cron (Recommended)
```bash
# Edit crontab
crontab -e

# Add this line to run every day at 8 AM AWST
0 8 * * * cd /Users/b/Desktop/Projects/Job_Scrape && source venv/bin/activate && python3 src/main.py --run-now >> logs/cron.log 2>&1
```

### Option 3: macOS Launch Agent
Create: `~/Library/LaunchAgents/com.jobscraper.daily.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobscraper.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/b/Desktop/Projects/Job_Scrape/venv/bin/python3</string>
        <string>/Users/b/Desktop/Projects/Job_Scrape/src/main.py</string>
        <string>--run-now</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/b/Desktop/Projects/Job_Scrape/logs/launch_agent.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/b/Desktop/Projects/Job_Scrape/logs/launch_agent_error.log</string>
</dict>
</plist>
```

Then run:
```bash
launchctl load ~/Library/LaunchAgents/com.jobscraper.daily.plist
```

---

## Benefits of New Settings

✅ **Faster runs** - 50% less scraping time  
✅ **Fresher jobs** - Only jobs posted yesterday  
✅ **Less duplication** - Smaller time window  
✅ **Lower AI costs** - Fewer jobs to score (~$0.02/day)  
✅ **Gentler on websites** - Half the requests  
✅ **Perfect for daily runs** - Optimized for morning updates  

---

## Current Workflow Status

**Currently running workflow:**
- Still using OLD settings (4 pages, 7 days)
- Will complete with those settings
- **Next run** will use NEW settings (2 pages, 1 day)

**To apply new settings immediately:**
1. Stop current workflow: `kill $(cat workflow.pid)`
2. Start fresh: `python3 src/main.py --run-now`

---

## Cost Comparison

| Frequency | Old Settings | New Settings |
|-----------|--------------|--------------|
| Per run | $0.07 | $0.02 |
| Daily | $0.07 | $0.02 |
| Weekly | $0.49 | $0.14 |
| Monthly | $2.10 | $0.60 |
| **Yearly** | **$25.55** | **$7.30** |

**Savings:** ~$18/year (71% reduction)

---

## Next Steps

1. ✅ Settings updated
2. ⏳ Current workflow will finish with old settings
3. ✅ Next run will use new settings (2 pages, 1 day)
4. 🔄 Configure morning schedule if desired (cron or Launch Agent)

All changes are saved and will take effect on the next workflow run!
