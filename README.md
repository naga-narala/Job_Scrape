# Job Scraper - Multi-Source AI-Powered Job Search

**Production-ready job scraper** with 3-tier optimization that scrapes LinkedIn, Seek, and Jora, scores jobs with AI against your profile, and presents matches via dashboard.

**Status:** ✅ All 3 scrapers operational | 🚀 Ready for production

**📖 Complete Documentation:** [MASTER_CONTEXT.md](MASTER_CONTEXT.md) - Single source of truth for developers & AI agents

---

## ⚡ Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure (copy example and add your API key)
cp config.json.example config.json
# Edit config.json: add OpenRouter API key

# Authenticate scrapers (one-time)
python archive/linkedin_login.py    # LinkedIn (required)
python archive/seek_login.py       # Seek (optional, works without)
```

### 2. Run Scraper
```bash
# Full workflow (scrape + score + notify)
python src/main.py

# Or run components separately
python src/scraper.py              # LinkedIn only
python src/seek_scraper.py         # Seek only  
python src/jora_scraper.py         # Jora only
```

### 3. View Results
```bash
# Start dashboard
python src/dashboard.py
# Open http://localhost:8000
```

---

## 🎯 Features

### **3 Production-Ready Scrapers**
- **LinkedIn**: Selenium-based, cookie auth, 25 jobs/page
- **Seek**: Selenium-based, 8+ pages, full descriptions
- **Jora**: Selenium + stealth mode, anti-Cloudflare, 6.6% filtering (best match rate!)

### **3-Tier Optimization System**
1. **Tier 1 (Title Filtering)**: Filters Senior/Lead/Manager roles during scraping
2. **Tier 2 (Deduplication)**: Hash-based duplicate detection (90-day lookback)
3. **Tier 3 (Quality Check)**: Ensures descriptions ≥200 chars with technical keywords

### **AI Scoring with Fallback**
- **Primary**: DeepSeek Chat (fast, cheap)
- **Fallback 1**: Claude 3.5 Haiku
- **Fallback 2**: Regex-based parser (when AI unavailable)

### **Smart Features**
- **Auto Rescore**: Rescores 70-79% jobs when profile changes
- **Email Notifications**: Gmail SMTP with 3 retries
- **Web Dashboard**: Day-wise grouping, application tracking
- **Perth Timezone**: All timestamps in AWST

---

## 📁 Project Structure

```
Job_Scrape/
├── src/                          # Production code
│   ├── scraper.py                # LinkedIn scraper ⭐
│   ├── seek_scraper.py           # Seek scraper ⭐
│   ├── jora_scraper.py           # Jora scraper ⭐
│   ├── optimization.py           # 3-tier filtering
│   ├── database.py               # SQLite operations
│   ├── scorer.py                 # AI scoring with fallback
│   ├── main.py                   # Main orchestrator
│   ├── dashboard.py              # Web UI
│   └── ...                       # Other utilities
│
├── archive/                      # Non-essential files
│   ├── test_scripts/             # Test files
│   ├── debug_scripts/            # Debug utilities
│   ├── documentation/            # Old docs
│   ├── linkedin_login.py         # Re-authentication
│   └── seek_login.py             # Re-authentication
│
├── data/                         # Database
│   └── jobs.db                   # SQLite database
│
├── config.json                   # Configuration (not in git)
├── config.json.example           # Template
├── profile.txt                   # Your profile
├── jobs.txt                      # Target job roles
├── generated_keywords.json       # Auto-generated from jobs.txt
├── job_searches.json             # Search configurations
├── test_url.json                 # Testing URLs
│
├── CONTRIBUTING.md               # ⚠️ READ BEFORE CHANGING CODE
├── SYSTEM_STATUS.md              # Current system status
├── CODEBASE_REFERENCE.md         # Function inventory
├── ARCHITECTURE.md               # Future design
└── README.md                     # This file
```

---

## ⚙️ Configuration

### **config.json** (Required)
```json
{
  "openrouter_api_key": "sk-or-v1-xxxxx",
  "linkedin_max_pages": 3,
  "seek_max_pages": 8,
  "jora_max_pages": 6,
  "email_from": "your@gmail.com",
  "email_password": "app-password-here",
  "email_to": "your@gmail.com"
}
```

### **profile.txt** (Your Profile)
- Update with your skills, experience, preferences
- Triggers auto-rescore when changed

### **jobs.txt** (Target Roles)
- List desired job titles (one per line)
- Auto-generates keywords for Tier 1 filtering
- Triggers keyword regeneration when changed

### **test_url.json** (Testing)
- Keep this file - used for testing scrapers
- Contains sample URLs for each source

---

## 🚀 Usage

### **Daily Job Search**
```bash
# Run full workflow (recommended)
python src/main.py

# This will:
# 1. Scrape jobs from all enabled sources
# 2. Apply 3-tier filtering
# 3. Save to database (deduplicate)
# 4. Score with AI (or parser fallback)
# 5. Send email notification for 75%+ matches
```

### **View Jobs Dashboard**
```bash
python src/dashboard.py
# Open http://localhost:8000

# Features:
# - Day-wise grouping ("Today", "Yesterday", etc.)
# - Job rejection (click X button)
# - Mark as applied
# - Direct links to job postings
```

### **Test Individual Scrapers**
```bash
# Test with sample URLs from test_url.json
import json
with open('test_url.json') as f:
    urls = json.load(f)

# Test LinkedIn
python src/scraper.py

# Test Seek
python src/seek_scraper.py

# Test Jora
python src/jora_scraper.py
```

---

## 🔐 Authentication

### **LinkedIn** (Required)
```bash
python archive/linkedin_login.py
# Opens browser, login manually, saves cookies
# Cookies valid for ~30 days
```

### **Seek** (Optional)
```bash
python archive/seek_login.py
# Opens browser, login manually, saves cookies
# Scraper works without auth (public jobs)
```

### **Jora** (Automatic)
- No manual login required
- Scraper creates session automatically
- Uses selenium-stealth for anti-detection

---

## 📊 Performance Metrics

### **LinkedIn Scraper**
- Speed: ~2 min per 3 pages
- Efficiency: 30.7% Tier 1 filtering
- Jobs per page: 25
- Success rate: 100%

### **Seek Scraper**
- Speed: ~3 min per 8 pages
- Efficiency: 22.5% Tier 1 filtering
- Jobs collected: 131 (8 pages)
- Description quality: 800-5,000 chars

### **Jora Scraper**
- Speed: ~2 min per 6 pages
- Efficiency: 6.6% Tier 1 filtering (BEST!)
- Jobs collected: 71 (6 pages)
- Description quality: 935-8,090 chars
- Tier 2/3: 0% filtered (all unique, high quality)

---

## 🛡️ Important Rules

### **⚠️ Before Making ANY Changes:**

1. **Read CONTRIBUTING.md first** - Contains critical rules
2. **Test with test_url.json** - Verify scraper still works
3. **Create backups** - Copy files before editing
4. **Check for regressions** - Ensure all 3 scrapers still work

### **🚫 Never Modify Without Testing:**
- `src/scraper.py` - LinkedIn scraper (selectors are tuned)
- `src/seek_scraper.py` - Seek scraper (pagination verified)
- `src/jora_scraper.py` - Jora scraper (stealth mode critical)
- `src/optimization.py` - 3-tier filtering (thresholds optimized)
- `src/database.py` - Database operations (schema stable)

### **✅ Safe to Modify:**
- `profile.txt` - Your profile (triggers auto-rescore)
- `jobs.txt` - Target jobs (regenerates keywords)
- `job_searches.json` - Add/remove searches
- `config.json` - Update settings

---

## 🐛 Troubleshooting

### **LinkedIn scraper fails**
```bash
# Check session validity
python -c "import sys; sys.path.insert(0, 'src'); \
from scraper import create_driver, load_cookies, is_logged_in; \
driver = create_driver(headless=True); load_cookies(driver); \
print('✅ Valid' if is_logged_in(driver) else '❌ Expired'); driver.quit()"

# If expired, re-login
python archive/linkedin_login.py
```

### **AI scoring fails**
- Check OpenRouter API key in config.json
- Verify API credit balance
- Parser fallback activates automatically (scores based on regex)

### **Database errors**
```bash
# Check database exists
ls -lh data/jobs.db

# View job count
sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;"

# Reinitialize (CAUTION: deletes all data)
python -c "import sys; sys.path.insert(0, 'src'); \
import database; database.init_database()"
```

### **No jobs in dashboard**
```bash
# Check database has jobs
python -c "import sys; sys.path.insert(0, 'src'); \
import database; print(f'Total: {len(database.get_all_jobs())}')"

# Verify dashboard port
python src/dashboard.py  # Default: http://localhost:8000
```

---

## 📚 Documentation

- **CONTRIBUTING.md** - Development guidelines and rules
- **SYSTEM_STATUS.md** - Current status of all components
- **CODEBASE_REFERENCE.md** - Complete function inventory
- **ARCHITECTURE.md** - Future multi-tenant design

---

## 🎯 Workflow Phases

### **Phase 1: Scraping**
- Scrapes from enabled sources (LinkedIn/Seek/Jora)
- Applies Tier 1 filtering (title keywords)
- Fetches full job descriptions
- Applies Tier 2 (dedup) and Tier 3 (quality)

### **Phase 2: Storage**
- Generates job hash (title + company + URL)
- Checks for duplicates (90-day window)
- Inserts new jobs into database
- Updates existing jobs (last_seen_date)

### **Phase 3: Scoring**
- Loads user profile from profile.txt
- Scores with AI (DeepSeek → Claude → Parser)
- Stores scores in scores table
- Links scores to jobs via job_id

### **Phase 4: Notification**
- Filters jobs with score ≥75%
- Generates HTML email
- Sends via Gmail SMTP (3 retries)
- Fallback: Saves HTML locally and auto-opens

### **Phase 5: Dashboard**
- Queries jobs from database
- Groups by day ("Today", "Yesterday")
- Displays with scores and actions
- Allows rejection and application tracking

---

## 📝 License

Private project - All rights reserved

---

## 🆘 Support

For issues or questions:
1. Check CONTRIBUTING.md for development rules
2. Review SYSTEM_STATUS.md for current state
3. Test with test_url.json before reporting issues
4. Ensure cookies are valid (re-login if expired)

---

**Last Updated:** 7 February 2026  
**Version:** 2.0 - Production Ready (All 3 Scrapers)
