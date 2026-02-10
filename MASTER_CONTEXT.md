# 🎯 JOB SCRAPER - MASTER CONTEXT
**Complete System Reference for AI Agents & Developers**  
**Version:** 1.0.0  
**Created:** 2026-02-09  
**Purpose:** Single source of truth consolidating all documentation

---

## 📑 DOCUMENT MAP - START HERE

### Which Section Do I Need?

| Your Need | Go To Section | Est. Read Time |
|-----------|---------------|----------------|
| **Brand new to this project?** | [5-Minute Quick Start](#5-minute-quick-start) | 5 min |
| **Need to verify system health?** | [System Health Check](#system-health-check) | 2 min |
| **Understanding architecture?** | [System Architecture](#system-architecture) | 10 min |
| **Looking up a function?** | [Appendix A: Function Inventory](#appendix-a-function-inventory) | Lookup |
| **Configuring settings?** | [Appendix B: Config Reference](#appendix-b-config-reference) | 5 min |
| **Running the scraper?** | [Running Jobs](#running-jobs) | 5 min |
| **Debugging errors?** | [Troubleshooting](#troubleshooting) | 10 min |
| **Adding new features?** | [Development Guide](#development-guide) | 15 min |
| **Fixing LinkedIn/Seek/Jora issues?** | [Appendix D: Verified Selectors](#appendix-d-verified-selectors) | Lookup |

### Original Documentation Archive

These files are **SUPERSEDED** by this master context (archived to `archive/documentation/`):
- ~~CODEBASE_REFERENCE.md~~ → Now in [Technical Reference](#technical-reference) + [Appendix A](#appendix-a-function-inventory)
- ~~SYSTEM_STATUS.md~~ → Now in [Protected Components](#protected-components) + [Appendix D](#appendix-d-verified-selectors)
- ~~ARCHITECTURE.md~~ → Now in [System Architecture](#system-architecture) + [Planning & Roadmap](#planning--roadmap)
- ~~PRE_FLIGHT_CHECKLIST.md~~ → Now in [Testing Guide](#testing-guide)

**Keep these files** (serve different purposes):
- ✅ README.md - User-facing marketing/quick start (links here for details)
- ✅ CONTRIBUTING.md - Git workflow and PR process
- ✅ .github/copilot-instructions.md - AI-specific coding patterns

---

## 🚀 5-MINUTE QUICK START
**Last Updated:** 2026-02-09 | **Verified:** All commands tested

### What This System Does

Multi-source job scraper that:
1. **Scrapes** jobs from LinkedIn, Seek, Jora (100-500 jobs/day)
2. **Filters** with 3-tier optimization (30% efficiency gain)
3. **Scores** with AI (Claude/GPT-4/Gemini) matching your profile
4. **Notifies** via email for jobs scoring 70%+
5. **Dashboard** for viewing, rejecting, tracking applications

### Essential Commands

```bash
# 1. First-time setup (run once)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure (edit these files)
cp config.json.example config.json  # Add your API keys
nano profile.txt                    # Your resume/profile
nano jobs.txt                       # Target job roles

# 3. Authenticate LinkedIn (run once, lasts 30-60 days)
python archive/linkedin_login.py    # Manual browser login

# 4. Generate keywords & URLs (auto-runs in workflow)
python src/keyword_generator.py     # Creates generated_keywords.json
python src/url_generator.py         # Creates generated_search_urls.json

# 5. Run complete workflow
python src/main.py --run-now        # Full scrape + score + notify

# 6. View results
python src/dashboard.py             # Open http://localhost:8000
```

### Quick Health Check

```bash
# Database exists and has jobs?
sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;"

# LinkedIn session valid?
python -c "import sys; sys.path.insert(0, 'src'); \
from scraper import create_driver, load_cookies, is_logged_in; \
driver = create_driver(headless=True); load_cookies(driver); \
print('✅ Valid' if is_logged_in(driver) else '❌ Expired'); driver.quit()"

# Config has API key?
grep -q "sk-or-" config.json && echo "✅ API key found" || echo "❌ No API key"

# Generated files exist?
ls generated_keywords.json generated_search_urls.json 2>/dev/null && \
echo "✅ Keywords/URLs generated" || echo "❌ Run keyword/url generators"
```

### File Locations Cheat Sheet

```
Job Scraper/
├── config.json              # API keys, SMTP, thresholds
├── profile.txt              # Your resume (triggers rescore on change)
├── jobs.txt                 # Target roles (triggers keyword regen on change)
├── generated_keywords.json  # Auto-generated search terms
├── generated_search_urls.json  # Auto-generated LinkedIn/Seek/Jora URLs
├── data/
│   ├── jobs.db             # SQLite database (all jobs + scores)
│   ├── linkedin_cookies.pkl # Session cookies (refresh every 30-60 days)
│   ├── logs/               # Error logs
│   └── notifications/      # HTML email copies
└── src/
    ├── main.py             # Workflow orchestrator (START HERE)
    ├── scraper.py          # LinkedIn scraper
    ├── seek_scraper.py     # Seek scraper
    ├── jora_scraper.py     # Jora scraper
    ├── scorer.py           # AI scoring engine
    ├── database.py         # All database operations
    ├── optimization.py     # 3-tier filtering
    ├── dashboard.py        # Web UI
    └── ...
```

### Common First-Time Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: selenium` | Run `pip install -r requirements.txt` |
| LinkedIn returns 0 jobs | Run `python archive/linkedin_login.py` to refresh cookies |
| All jobs score 0% | Check `config.json` has valid OpenRouter API key |
| Dashboard shows nothing | Check `data/jobs.db` exists and has jobs with scores |
| Emails not sending | Verify SMTP settings in `config.json` (use Gmail app password) |

---

## 🏗️ SYSTEM ARCHITECTURE
**Last Updated:** 2026-02-09 | **Verified:** scraper.py v2026-02-05, database.py v2026-02-07

### Purpose & Key Features

**What it does:** Multi-source job scraper with AI scoring, 3-tier optimization, and dashboard UI

**Core Features:**
- ✅ **Multi-source scraping**: LinkedIn (Selenium), Seek (HTTP), Jora (Selenium)
- ✅ **3-Tier Optimization**: Title filtering (30% savings), Description quality, Deduplication
- ✅ **AI Scoring**: LLM-based matching with 3-model fallback chain
- ✅ **Smart Rescore**: Auto-rescore jobs when profile.txt changes
- ✅ **Auto-keyword Generation**: Updates when jobs.txt changes
- ✅ **Dashboard**: Flask web UI with rejection tracking
- ✅ **Email Notifications**: HTML alerts for 70%+ matches

**Technology Stack:**
- **Scraping**: Selenium WebDriver, Requests, BeautifulSoup4
- **Database**: SQLite3 (5 tables)
- **AI**: OpenRouter API (Claude, GPT-4, Gemini, Llama)
- **Web**: Flask
- **Scheduling**: schedule library
- **Parser**: Custom regex fallback

### Complete Workflow Diagram

```
═══════════════════════════════════════════════════════════════════
                    DAILY EXECUTION FLOW
═══════════════════════════════════════════════════════════════════

START: python src/main.py --run-now
  │
  ├─[STEP 0: KEYWORD REGENERATION]────────────────────────────────┐
  │   ├─► Calculate MD5 hash of jobs.txt                          │
  │   ├─► Compare with saved hash in .jobs_txt_hash               │
  │   └─► IF CHANGED:                                             │
  │       ├─► keyword_generator.py → DeepSeek API                 │
  │       ├─► Extract: title keywords, technical skills           │
  │       ├─► Generate: 37 title keywords, 77 technical skills    │
  │       ├─► Save to generated_keywords.json                     │
  │       └─► url_generator.py → generated_search_urls.json       │
  │                                                                │
  ├─[STEP 1: SMART RESCORE]──────────────────────────────────────┐
  │   ├─► Get MD5 hash of profile.txt                             │
  │   ├─► Compare with last profile_hash in database              │
  │   └─► IF CHANGED:                                             │
  │       ├─► Get jobs scoring 40-85% from last 30 days           │
  │       ├─► Delete old scores                                   │
  │       ├─► Re-score with new profile                           │
  │       ├─► Log: "Rescored X jobs due to profile change"        │
  │       └─► Save new profile_hash to profile_changes table      │
  │                                                                │
  ├─[STEP 2: SCRAPING]───────────────────────────────────────────┐
  │   │                                                            │
  │   ├─► Load: generated_search_urls.json                        │
  │   │                                                            │
  │   ├─[LINKEDIN SCRAPER]─────────────────────────────────────┐  │
  │   │   ├─► scraper.fetch_all_jobs(searches, max_pages=3)    │  │
  │   │   ├─► create_driver(headless=True)                     │  │
  │   │   ├─► load_cookies() from data/linkedin_cookies.pkl    │  │
  │   │   ├─► For each search URL:                             │  │
  │   │   │   ├─► Navigate to URL                              │  │
  │   │   │   ├─► Wait for job cards (li.scaffold-layout...)   │  │
  │   │   │   ├─► For each card:                               │  │
  │   │   │   │   ├─► **TIER 1: Title Filter** ◄──────────────┼──┼─ 30% savings
  │   │   │   │   │   └─► Skip if title lacks keywords        │  │
  │   │   │   │   ├─► Click card to expand                     │  │
  │   │   │   │   ├─► Extract: title, company, location        │  │
  │   │   │   │   ├─► Extract: description (full text)         │  │
  │   │   │   │   ├─► Extract: requirement_text (if exists)    │  │
  │   │   │   │   ├─► Extract: posted_date, employment_type    │  │
  │   │   │   │   └─► Build absolute URL                       │  │
  │   │   │   ├─► Try pagination (aria-label="Page X")         │  │
  │   │   │   └─► Repeat for max_pages                         │  │
  │   │   └─► Return: [{title, company, ..., source='linkedin'}] │
  │   │                                                            │
  │   ├─[SEEK SCRAPER]─────────────────────────────────────────┐  │
  │   │   ├─► SeekScraper(delay_range=(2,5))                   │  │
  │   │   ├─► For each search:                                 │  │
  │   │   │   ├─► Build URL: /keyword-jobs/in-All-Location     │  │
  │   │   │   ├─► HTTP GET with browser headers                │  │
  │   │   │   ├─► Parse HTML with BeautifulSoup                │  │
  │   │   │   ├─► Find job cards (data-testid="job-card")      │  │
  │   │   │   ├─► Extract: title, company, location, summary   │  │
  │   │   │   ├─► Random delay (2-5 sec)                       │  │
  │   │   │   └─► Paginate if more results                     │  │
  │   │   └─► Return: [{..., source='seek'}]                   │  │
  │   │                                                            │
  │   └─[JORA SCRAPER]─────────────────────────────────────────┐  │
  │       ├─► JoraScraper(headless=True, stealth=True)         │  │
  │       ├─► For each search:                                 │  │
  │       │   ├─► Build URL: /j?q=keyword&l=location&a=24h     │  │
  │       │   ├─► Load page with Selenium + stealth mode       │  │
  │       │   ├─► Wait 8 sec for JavaScript render             │  │
  │       │   ├─► Find job cards (multiple selector fallbacks) │  │
  │       │   ├─► For each card:                               │  │
  │       │   │   ├─► Extract: title, company, location, URL   │  │
  │       │   │   ├─► **NEW**: Open job URL in new tab         │  │
  │       │   │   ├─► **NEW**: Fetch full description          │  │
  │       │   │   └─► Switch back to search results            │  │
  │       │   └─► Close driver                                 │  │
  │       └─► Return: [{..., source='jora'}]                   │  │
  │                                                                │
  ├─[STEP 3: DATABASE SAVE WITH FILTERING]───────────────────────┐
  │   │                                                            │
  │   ├─► For each scraped job:                                   │
  │   │   │                                                        │
  │   │   ├─► **TIER 2: Description Quality** ◄─────────────────┼─ 5-10% savings
  │   │   │   ├─► optimization.is_description_relevant()         │
  │   │   │   ├─► Check: length >= 200 chars                     │
  │   │   │   ├─► Check: contains technical keywords             │
  │   │   │   └─► IF FAILS: Skip job, log "Tier 2 filtered"      │
  │   │   │                                                        │
  │   │   ├─► Generate job_hash = MD5(title + company + url)     │
  │   │   │                                                        │
  │   │   ├─► **TIER 3: Deduplication** ◄────────────────────────┼─ 0-5% savings
  │   │   │   ├─► optimization.should_skip_duplicate(job_hash)   │
  │   │   │   ├─► Query: job_hash in jobs table (90 days)?      │
  │   │   │   └─► IF EXISTS: Skip job, log "Tier 3 duplicate"    │
  │   │   │                                                        │
  │   │   └─► IF PASSES ALL FILTERS:                             │
  │   │       ├─► database.insert_job(job_data)                  │
  │   │       ├─► Save to jobs table                             │
  │   │       ├─► Set: scraped_date=now, is_active=1             │
  │   │       └─► Add to new_jobs list                           │
  │   │                                                            │
  │   └─► Log optimization metrics:                               │
  │       ├─► Tier 1: X jobs filtered by title                   │
  │       ├─► Tier 2: Y jobs filtered by quality                 │
  │       ├─► Tier 3: Z jobs skipped (duplicates)                │
  │       └─► Efficiency: (X+Y+Z)/total * 100%                   │
  │                                                                │
  ├─[STEP 4: AI SCORING]─────────────────────────────────────────┐
  │   │                                                            │
  │   ├─► database.get_unscored_jobs()                            │
  │   ├─► Load: profile.txt, generated_keywords.json              │
  │   │                                                            │
  │   ├─► For each unscored job:                                  │
  │   │   │                                                        │
  │   │   ├─► scorer.build_prompt(job, profile)                   │
  │   │   │   ├─► Include: job description + requirements         │
  │   │   │   ├─► Include: user profile text                      │
  │   │   │   ├─► Include: keywords to check                      │
  │   │   │   └─► Request: JSON {score, matched[], not_matched[]} │
  │   │   │                                                        │
  │   │   ├─► **MODEL FALLBACK CHAIN** ◄─────────────────────────┼─ Reliability
  │   │   │   │                                                    │
  │   │   │   ├─[TRY 1: Primary Model]────────────────────────┐   │
  │   │   │   │   ├─► call_openrouter("anthropic/claude-3.5-sonnet") │
  │   │   │   │   ├─► POST to api.openrouter.ai                 │   │
  │   │   │   │   ├─► Parse JSON response                       │   │
  │   │   │   │   └─► IF SUCCESS: Return score_data             │   │
  │   │   │   │                                                  │   │
  │   │   │   ├─[TRY 2: Secondary Model]──────────────────────┐ │   │
  │   │   │   │   ├─► IF rate limit: Wait 60s, retry           │ │   │
  │   │   │   │   ├─► IF model unavailable:                    │ │   │
  │   │   │   │   │   └─► call_openrouter("openai/gpt-4-turbo")│ │   │
  │   │   │   │   └─► IF SUCCESS: Return score_data            │ │   │
  │   │   │   │                                                 │ │   │
  │   │   │   ├─[TRY 3: Tertiary Model]───────────────────────┐│ │   │
  │   │   │   │   └─► call_openrouter("google/gemini-flash-1.5")│ │   │
  │   │   │   │                                                 ││ │   │
  │   │   │   └─[TRY 4: Parser Fallback]─────────────────────┐││ │   │
  │   │   │       ├─► job_parser.parse_job(description)       │││ │   │
  │   │   │       ├─► Regex-based keyword matching            │││ │   │
  │   │   │       ├─► Check: experience level (auto-reject Senior) ││ │
  │   │   │       ├─► Check: visa requirements                │││ │   │
  │   │   │       ├─► Calculate score from matches            │││ │   │
  │   │   │       └─► Save with model_used='parser-filter'    │││ │   │
  │   │   │                                                    │││ │   │
  │   │   └─► database.insert_score(job_id, score_data, profile_hash)
  │   │       ├─► Save to scores table                            │
  │   │       ├─► Link to job via job_id_hash                     │
  │   │       └─► Store: matched/not_matched as JSON arrays       │
  │   │                                                            │
  │   └─► Log: "Scored X jobs (Y with AI, Z with parser)"         │
  │                                                                │
  ├─[STEP 5: EMAIL NOTIFICATIONS]────────────────────────────────┐
  │   │                                                            │
  │   ├─► database.get_high_scoring_unnotified(threshold=70)      │
  │   ├─► Filter: notified = 0                                    │
  │   │                                                            │
  │   └─► IF jobs found:                                          │
  │       ├─► notifier.build_email_html(jobs, date_str)           │
  │       │   ├─► Group jobs by scraped_date                      │
  │       │   ├─► For each job:                                   │
  │       │   │   ├─► Score badge (color-coded)                   │
  │       │   │   ├─► Title + Company                             │
  │       │   │   ├─► Location + Source badge                     │
  │       │   │   ├─► Top 3 matched requirements                  │
  │       │   │   └─► "View on Dashboard" link                    │
  │       │   └─► Style with inline CSS                           │
  │       │                                                        │
  │       ├─► send_email_notification(jobs, config)               │
  │       │   ├─► Connect to SMTP (Gmail/Outlook)                 │
  │       │   ├─► Send HTML email                                 │
  │       │   ├─► 3 retry attempts with exponential backoff       │
  │       │   └─► Fallback: Save HTML + open in browser           │
  │       │                                                        │
  │       ├─► save_html_notification(jobs)                        │
  │       │   └─► Save to data/notifications/{date}.html          │
  │       │                                                        │
  │       └─► database.mark_notified(job_id, type='email')        │
  │           ├─► Update: notified=1                              │
  │           └─► Set: notified_at=now                            │
  │                                                                │
  └─[STEP 6: COMPLETE]───────────────────────────────────────────┘
      ├─► Log final statistics:
      │   ├─► Total jobs scraped: X
      │   ├─► New jobs saved: Y
      │   ├─► Jobs scored: Z
      │   ├─► High scorers notified: W
      │   └─► Next run: +24 hours
      │
      └─► Schedule next execution (if daemon mode)

END
═══════════════════════════════════════════════════════════════════
```

### 3-Tier Optimization System

**Purpose**: Reduce processing time and API costs by filtering irrelevant jobs early

#### Tier 1: Title Filtering (30% Efficiency Gain)
- **When**: During scraping, before clicking job card
- **How**: Check if title contains any of 37 title keywords
- **Keywords**: "engineer", "developer", "scientist", "analyst", "graduate", "junior", "ai", "ml", "data", etc.
- **Benefit**: Skip 30% of jobs, saves ~15 min per run
- **Implementation**: `optimization.is_title_relevant(title)`

#### Tier 2: Description Quality (5-10% Savings)
- **When**: Before saving to database
- **Checks**:
  1. Length ≥ 200 characters (reject too short)
  2. Contains ≥1 technical keyword from 77 keywords
  3. Contains ≥1 strong keyword from 25 keywords
- **Benefit**: Reject low-quality/generic job posts
- **Implementation**: `optimization.is_description_relevant(description, title)`

#### Tier 3: Deduplication (0-5% Savings)
- **When**: Before inserting to database
- **How**: Generate `job_hash = MD5(title + company + url)`
- **Check**: Hash exists in database within last 90 days?
- **Benefit**: Avoid re-processing same jobs
- **Implementation**: `optimization.should_skip_duplicate(job_hash, db_conn)`

**Combined Impact**: 35-45% reduction in processing time and AI API costs

### File Structure

```
Job_Scraper/
├── 📄 Config Files (User-Editable)
│   ├── config.json              # API keys, SMTP, thresholds, model config
│   ├── profile.txt              # Your resume (hash tracked for rescore)
│   └── jobs.txt                 # Target roles (hash tracked for keyword regen)
│
├── 🤖 Generated Files (Auto-Created)
│   ├── generated_keywords.json  # From jobs.txt via DeepSeek API
│   ├── generated_search_urls.json  # From keywords + locations
│   ├── job_searches.json        # Manual LinkedIn search configs (optional)
│   └── .jobs_txt_hash           # MD5 hash to detect changes
│
├── 💾 Data Directory
│   ├── jobs.db                  # SQLite database (5 tables)
│   ├── linkedin_cookies.pkl     # Session cookies (30-60 day lifespan)
│   ├── logs/
│   │   └── job_scraper.log      # Rotating logs
│   └── notifications/
│       └── YYYY-MM-DD.html      # Email notification backups
│
├── 🐍 Source Code (src/)
│   ├── main.py                  # Workflow orchestrator (START HERE)
│   ├── scraper.py               # LinkedIn scraper (Selenium)
│   ├── seek_scraper.py          # Seek scraper (HTTP)
│   ├── jora_scraper.py          # Jora scraper (Selenium + stealth)
│   ├── scorer.py                # AI scoring with fallback chain
│   ├── job_parser.py            # Regex fallback parser
│   ├── database.py              # All database operations
│   ├── optimization.py          # 3-tier filtering
│   ├── keyword_generator.py     # Auto keyword generation
│   ├── url_generator.py         # Search URL builder
│   ├── rescore_manager.py       # Smart rescore on profile change
│   ├── notifier.py              # Email notifications
│   ├── dashboard.py             # Flask web UI
│   └── scraping_stats.py        # Metrics tracking
│
├── 📋 Templates (templates/)
│   ├── dashboard.html           # Main job listing UI
│   ├── stats.html               # Statistics page
│   ├── applied.html             # Applied jobs view
│   ├── rejected.html            # Rejected jobs view
│   └── notification.html        # Email template (unused, built in code)
│
├── 📚 Documentation
│   ├── MASTER_CONTEXT.md        # This file (SINGLE SOURCE OF TRUTH)
│   ├── README.md                # User-facing quick start
│   ├── CONTRIBUTING.md          # Git workflow for contributors
│   └── .github/copilot-instructions.md  # AI coding patterns
│
└── 🗃️ Archive (archive/)
    ├── documentation/           # Old .md files (superseded by MASTER_CONTEXT)
    ├── test_scripts/            # One-off test files
    ├── debug_scripts/           # Debugging helpers
    └── linkedin_login.py        # Manual cookie refresh tool
```

### Database Schema Overview

**5 Tables:**
1. **jobs** - Job listings (PK: job_id_hash)
2. **scores** - AI scores (FK: job_id → jobs.job_id_hash)
3. **rejections** - Rejection tracking (FK: job_id → jobs.job_id_hash)
4. **notifications** - Email log (FK: job_id → jobs.job_id_hash)
5. **profile_changes** - Profile version history (PK: profile_hash)

**See** [Database Schema](#database-schema) for full SQL definitions.

---

## 🔧 TECHNICAL REFERENCE
**Last Updated:** 2026-02-09 | **Verified:** All modules v2026-02-05+

### Core Modules (15 Python Files)

#### 1. main.py - Workflow Orchestrator

**Purpose**: Coordinates entire daily scraping workflow

**Key Functions:**

**`run_daily_job()`**
- **Called by**: Manual execution or scheduler
- **Flow**: 6 steps (keyword gen → rescore → scrape → save → score → notify)
- **Returns**: None
- **Side effects**: Writes database, sends emails, updates logs

**`load_config() → dict`**
- **Purpose**: Load config.json with API keys, thresholds, SMTP
- **Used by**: All modules
- **Caching**: Loads once per execution

**`load_job_searches() → list[dict]`**
- **Purpose**: Load generated_search_urls.json
- **Format**: `[{id, url, source, keyword, location, enabled}, ...]`
- **Used by**: Scraping step

**Usage Example:**
```python
from main import run_daily_job, load_config

config = load_config()
run_daily_job()  # Full workflow
```

---

#### 2. scraper.py - LinkedIn Scraper

**Purpose**: Scrape LinkedIn using Selenium WebDriver

**Key Functions:**

**`create_driver(headless=True, use_profile=False) → WebDriver`**
- **Features**: Anti-detection, auto-install ChromeDriver, stealth mode
- **Returns**: Configured Selenium WebDriver instance

**`load_cookies(driver) → None`**
- **File**: data/linkedin_cookies.pkl
- **Purpose**: Avoid login on every run
- **Expiry**: 30-60 days

**`extract_job_from_card(card, search_config, driver, optimizer=None) → dict|None`**
- **Parameters**:
  - `card`: Selenium WebElement (job card)
  - `optimizer`: OptimizationManager for Tier 1 filtering
- **Process**:
  1. **Tier 1 Filter**: Check title keywords (if optimizer provided)
  2. Click card to expand
  3. Extract: title, company, location, description
  4. Extract: requirement_text (from "Qualifications" section)
  5. Extract: posted_date, employment_type
- **Returns**: Job dict or None (if Tier 1 filtered)

**`fetch_all_jobs(searches, api_key=None, headless=True, max_pages=3) → tuple[list, dict]`**
- **Purpose**: Scrape all LinkedIn searches
- **Returns**: (jobs_list, strategy_stats)
- **Logs**: Tier 1/2/3 optimization metrics

**Verified Selectors** (see [Appendix D](#appendix-d-verified-selectors)):
- Job cards: `li.scaffold-layout__list-item`
- Title: Multiple fallbacks (`.job-details-jobs-unified-top-card__job-title`, etc.)
- Company: Multiple fallbacks
- Description: `.jobs-description__content`

---

#### 3. seek_scraper.py - Seek Scraper

**Purpose**: Scrape Seek.com.au via HTTP requests

**Key Class: SeekScraper**

**`search_jobs(keyword, location, max_results=50) → list[dict]`**
- **URL Format**: `https://www.seek.com.au/{keyword}-jobs/in-All-{location}?daterange=1`
- **Method**: HTTP GET + BeautifulSoup parsing
- **Anti-bot**: Random delays (2-5 sec), browser headers
- **Returns**: Job list with `source='seek'`

**`_extract_job_from_card(card) → dict`**
- **Extraction**: Title, company, location, summary (NOT full description)
- **Selectors**: BeautifulSoup CSS selectors

---

#### 4. jora_scraper.py - Jora Scraper

**Purpose**: Scrape Jora.com via Selenium with stealth mode

**Key Class: JoraScraper**

**`search_jobs(keyword, location="Perth WA", time_filter="24h", max_results=50) → list[dict]`**
- **URL Format**: `https://au.jora.com/j?q={keyword}&l={location}&a=24h`
- **Anti-detection**: selenium-stealth plugin, randomized viewport
- **NEW (2026-02-05)**: Fetches full descriptions via `get_job_details()`
- **Returns**: Jobs with complete descriptions

**`get_job_details(job_url) → str|None`**
- **Purpose**: Fetch full description from job detail page
- **Method**: Open URL in new tab, extract description, close tab
- **Selector**: `div[class*='description']`

---

#### 5. database.py - SQLite Operations

**Purpose**: All database CRUD operations

**Key Functions:**

**`init_database() → None`**
- **Creates**: 5 tables (jobs, scores, rejections, notifications, profile_changes)
- **Migrations**: Adds new columns if missing (e.g., requirement_text, rejected)

**`insert_job(job_data) → str`**
- **Deduplication**: Generates `job_id_hash = MD5(title + company + url)`
- **Upsert Logic**: If exists, updates `last_seen_date`; else inserts
- **Returns**: job_id_hash

**`insert_score(job_id, score_data, profile_hash) → None`**
- **Replaces**: Deletes old score if exists
- **Stores**: matched/not_matched as JSON strings

**`get_unscored_jobs() → list[dict]`**
- **Query**: Jobs without entry in scores table
- **Used by**: Scoring workflow

**`reject_job(job_id, rejection_category, rejection_notes='') → None`**
- **Updates**: `rejected=1`, `rejected_date=now`
- **Inserts**: Record to rejections table with category

**`get_jobs_for_rescore(min_score, max_score, max_age_days, exclude_profile_hash) → list[dict]`**
- **Purpose**: Find borderline jobs for smart rescore
- **Filters**: Score in range, age ≤ max_age_days, not scored with current profile

**See** [Database Schema](#database-schema) for complete table definitions.

---

#### 6. scorer.py - AI Scoring Engine

**Purpose**: Score jobs using LLM APIs with fallback chain

**Key Functions:**

**`load_keywords() → dict`**
- **File**: generated_keywords.json
- **Returns**: `{title_keywords, technical_skills, strong_keywords}`

**`build_dynamic_prompt_template() → str`**
- **Includes**: Profile, job description, keywords to check
- **Output**: Jinja2 template for scoring prompt

**`call_openrouter(model, prompt, api_key, max_tokens=500) → str`**
- **API**: POST to `https://openrouter.ai/api/v1/chat/completions`
- **Errors**: Raises RateLimitError, ModelUnavailableError, ScoringError
- **Returns**: Raw response text

**`parse_score_response(response_content) → dict|None`**
- **Strategies**: JSON.parse → extract from markdown → regex → manual field extraction
- **Returns**: `{score, matched_requirements[], not_matched_requirements[], key_points[]}`

**`score_job_with_fallback(job, profile_content, models_config, api_key) → dict|None`**
- **Fallback Chain**:
  1. Primary: anthropic/claude-3.5-sonnet
  2. Secondary: openai/gpt-4-turbo (if rate limit or unavailable)
  3. Tertiary: google/gemini-flash-1.5 (cheapest)
  4. Parser: job_parser.parse_job() (regex-based)
- **Parser Fallback**: Auto-score 0% if critical exclusions (Senior, visa, etc.)
- **Returns**: Score dict with `model_used` field

---

#### 7. job_parser.py - Regex Fallback Parser

**Purpose**: Regex-based scoring when AI models fail

**Key Method: `JobDescriptionParser.parse_job(description, title, location) → dict`**

**Process:**
1. Check critical exclusions:
   - "senior", "lead", "principal" in title → score 0
   - "no sponsorship", "PR required" → score 0
   - Experience > 2 years → score 0
2. Match required skills (Python, ML, etc.)
3. Match preferred skills
4. Calculate score from matches
5. Build matched/not_matched lists

**Returns**: `{score, matched_requirements[], not_matched_requirements[], key_points[], model_used='parser-filter'}`

**Note**: Jobs with `model_used='parser-filter'` and score=0 should NOT be rescored (failed critical checks).

---

#### 8. optimization.py - 3-Tier Filtering

**Purpose**: Pre-filter jobs to save time and API costs

**Key Class: OptimizationManager**

**`is_title_relevant(title) → tuple[bool, str]`** - **TIER 1**
- **Check**: Title contains any of 37 title keywords?
- **Keywords**: engineer, developer, scientist, graduate, junior, ai, ml, data, etc.
- **Returns**: (passes, reason)
- **Used by**: scraper.py during card extraction

**`is_description_relevant(description, title) → tuple[bool, str]`** - **TIER 2**
- **Checks**:
  1. Length ≥ 200 characters
  2. Contains ≥1 technical keyword (from 77 keywords)
  3. Contains ≥1 strong keyword (from 25 keywords)
- **Returns**: (passes, reason)
- **Used by**: main.py before database insert

**`should_skip_duplicate(job_hash, db_conn) → tuple[bool, str]`** - **TIER 3**
- **Check**: job_hash exists in database (last 90 days)?
- **Window**: Configurable via `config.json`
- **Returns**: (should_skip, reason)
- **Used by**: main.py before database insert

---

#### 9. keyword_generator.py - Auto Keyword Generation

**Purpose**: Generate keywords from jobs.txt using AI

**Key Class: KeywordGenerator**

**`needs_regeneration() → bool`**
- **Check**: MD5(jobs.txt) != saved hash?
- **File**: .jobs_txt_hash
- **Used by**: main.py Step 0

**`generate_keywords() → dict`**
- **Process**:
  1. Parse jobs.txt for role names
  2. Call DeepSeek API to extract:
     - Title keywords (base roles)
     - Technical skills (domain-specific)
     - Strong keywords (critical terms)
     - Location keywords
  3. Save to generated_keywords.json
  4. Update .jobs_txt_hash
- **Returns**: `{title_keywords[], technical_skills[], strong_keywords[], locations[]}`

---

#### 10. url_generator.py - Search URL Builder

**Purpose**: Generate search URLs for LinkedIn, Seek, Jora

**Key Class: URLGenerator**

**`generate_all_urls() → dict`**
- **Generates**:
  - LinkedIn: Uses geoId (101452733 for Australia)
  - Seek: `/keyword-jobs/in-All-Location?daterange=1`
  - Jora: `/j?q=keyword&l=location&a=24h`
- **Saves**: generated_search_urls.json
- **Returns**: `{linkedin: [], seek: [], jora: []}`

---

#### 11. rescore_manager.py - Smart Rescore

**Purpose**: Auto-rescore jobs when profile.txt changes

**`detect_profile_change() → bool`**
- **Check**: MD5(profile.txt) != last profile_hash in database?
- **Log**: Inserts to profile_changes table if changed

**`trigger_smart_rescore(profile_content, config) → int`**
- **Scope**: Jobs scoring 40-85% from last 30 days
- **Process**:
  1. Get eligible jobs
  2. Delete old scores
  3. Re-score with new profile
  4. Save new scores
- **Returns**: Count of rescored jobs

**Why 40-85%?** Borderline jobs most likely to change rating with profile updates.

---

#### 12. notifier.py - Email Notifications

**Purpose**: Send HTML email alerts for high-scoring jobs

**`build_email_html(jobs, date_str) → str`**
- **Groups**: Jobs by scraped_date
- **Includes**: Score badge, title, company, location, matched requirements
- **Styling**: Inline CSS for email compatibility

**`send_email_notification(jobs, config) → bool`**
- **SMTP**: Connects to Gmail/Outlook
- **Retry**: 3 attempts with exponential backoff
- **Fallback**: If fails, saves HTML + opens in browser
- **Returns**: Success boolean

**`notify_new_matches(config) → None`**
- **Threshold**: From config.json (default 70%)
- **Filter**: `notified = 0`
- **Marks**: Jobs as notified after sending

---

#### 13. dashboard.py - Flask Web UI

**Purpose**: Web interface for viewing and managing jobs

**Key Routes:**

- **`GET /`** → Main dashboard (last 7 days, sorted by score)
- **`GET /all`** → All jobs (no date filter)
- **`GET /stats`** → Statistics page (charts, top companies, rejection stats)
- **`GET /applied`** → Jobs marked as applied
- **`POST /mark_applied/<job_id>`** → Mark job as applied
- **`POST /reject/<job_id>`** → Reject job with category + notes
- **`POST /rescore/<job_id>`** → Manually rescore single job
- **`POST /update_status/<job_id>`** → Update job status/remarks

**Templates**: dashboard.html, stats.html, applied.html, rejected.html

**Start**: `python src/dashboard.py` → http://localhost:8000

---

#### 14. scraping_stats.py - Metrics Tracking

**Purpose**: Track and analyze scraping performance

**Key Functions:**
- `log_scraping_stats()` - Record scrape session metrics
- `get_scraping_stats()` - Retrieve historical stats
- **Metrics**: Jobs scraped, time taken, success rate, source breakdown

---

### Database Schema
**Last Updated:** 2026-02-09 | **Verified:** database.py v2026-02-07

#### Table: jobs

```sql
CREATE TABLE jobs (
    job_id_hash TEXT PRIMARY KEY,      -- MD5(title + company + url)
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    requirement_text TEXT,              -- Separate requirements section (NEW)
    url TEXT,
    posted_date TEXT,
    employment_type TEXT,               -- Full-time, Part-time, Contract, etc.
    source TEXT,                        -- 'linkedin', 'seek', 'jora'
    source_search_id TEXT,              -- Which search found this job
    scraped_date DATE,                  -- When first scraped
    last_seen_date DATE,                -- Last time seen (for dedup updates)
    is_active BOOLEAN DEFAULT 1,        -- 0 = archived/expired
    applied BOOLEAN DEFAULT 0,          -- User marked as applied
    notified BOOLEAN DEFAULT 0,         -- Email sent for this job
    notified_at TEXT,                   -- When notification sent
    notification_type TEXT,             -- 'email', 'sms', etc.
    rejected BOOLEAN DEFAULT 0,         -- User rejected (NEW)
    rejected_date DATE,                 -- When rejected (NEW)
    status TEXT,                        -- Custom status field
    remarks TEXT                        -- User notes
);

-- Indexes for performance
CREATE INDEX idx_scraped_date ON jobs(scraped_date);
CREATE INDEX idx_source ON jobs(source);
CREATE INDEX idx_is_active ON jobs(is_active);
CREATE INDEX idx_notified ON jobs(notified);
CREATE INDEX idx_rejected ON jobs(rejected);
```

**Row Count**: 100-1000+ (grows daily)

---

#### Table: scores

```sql
CREATE TABLE scores (
    job_id TEXT PRIMARY KEY,            -- FK to jobs.job_id_hash
    score INTEGER,                      -- 0-100
    matched_requirements TEXT,          -- JSON array of strings
    not_matched_requirements TEXT,      -- JSON array of strings
    key_points TEXT,                    -- JSON array of insights
    model_used TEXT,                    -- e.g., 'claude-3.5-sonnet', 'parser-filter'
    profile_hash TEXT,                  -- MD5 of profile.txt (for rescore tracking)
    scored_date DATE,                   -- When scored
    FOREIGN KEY(job_id) REFERENCES jobs(job_id_hash)
);

CREATE INDEX idx_score ON scores(score);
CREATE INDEX idx_profile_hash ON scores(profile_hash);
```

**Example Row:**
```json
{
  "job_id": "abc123...",
  "score": 85,
  "matched_requirements": "[\"Python\", \"Machine Learning\", \"Bachelor's degree\"]",
  "not_matched_requirements": "[\"5 years experience\", \"PhD preferred\"]",
  "key_points": "[\"Strong ML skills match\", \"Entry-level friendly\"]",
  "model_used": "anthropic/claude-3.5-sonnet",
  "profile_hash": "def456...",
  "scored_date": "2026-02-09"
}
```

---

#### Table: rejections

```sql
CREATE TABLE rejections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,               -- FK to jobs.job_id_hash
    rejection_category TEXT NOT NULL,   -- 'Low Salary', 'Wrong Tech Stack', etc.
    rejection_notes TEXT,               -- Optional user notes
    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(job_id_hash)
);

CREATE INDEX idx_rejection_category ON rejections(rejection_category);
```

**Common Categories**: Low Salary, Wrong Tech Stack, Senior Level, Visa Issues, Location Mismatch

---

#### Table: notifications

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,                        -- FK to jobs.job_id_hash
    notification_type TEXT,             -- 'email', 'sms', 'webhook'
    status TEXT,                        -- 'sent', 'failed', 'pending'
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(job_id_hash)
);
```

---

#### Table: profile_changes

```sql
CREATE TABLE profile_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_hash TEXT UNIQUE,           -- MD5 of profile.txt
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Track profile.txt versions to trigger smart rescore

---

### Integration Points

#### External APIs

**1. OpenRouter API**
- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
- **Used by**: scorer.py
- **Models**: Claude 3.5 Sonnet, GPT-4 Turbo, Gemini Flash 1.5, Llama 3.1 70B
- **Authentication**: Bearer token in config.json
- **Pricing**: ~$0.003-0.015 per job (varies by model)

**Example Request:**
```python
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Job Scraper"
    },
    json={
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }
)
```

**2. LinkedIn** (via Selenium)
- **URL**: `https://www.linkedin.com/jobs/search/`
- **Authentication**: Cookies (data/linkedin_cookies.pkl)
- **Refresh**: Every 30-60 days via `archive/linkedin_login.py`
- **Rate Limiting**: Managed by delays, page limits

**3. Seek** (via HTTP)
- **URL**: `https://www.seek.com.au/`
- **Authentication**: None (public search)
- **Rate Limiting**: Random delays 2-5 seconds

**4. Jora** (via Selenium)
- **URL**: `https://au.jora.com/`
- **Authentication**: None
- **Anti-Detection**: selenium-stealth plugin

---

## 🎮 OPERATIONAL GUIDES
**Last Updated:** 2026-02-09

### Installation

#### First-Time Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd Job_Scrape

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate (macOS/Linux)
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy example config
cp config.json.example config.json

# 6. Edit config with your details
nano config.json  # Add OpenRouter API key, SMTP settings
```

#### Configuration Setup

**config.json** - Required fields:
```json
{
  "api_key": "sk-or-v1-...",           // Get from openrouter.ai
  "models": {
    "primary": "anthropic/claude-3.5-sonnet",
    "secondary": "openai/gpt-4-turbo",
    "tertiary": "google/gemini-flash-1.5"
  },
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "from_email": "your@gmail.com",
  "to_email": "your@gmail.com",
  "smtp_username": "your@gmail.com",
  "smtp_password": "your-app-password"  // NOT regular password!
}
```

**Getting Gmail App Password:**
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Search "App passwords"
4. Generate password for "Mail"
5. Copy 16-character password to config.json

**profile.txt** - Your resume:
```
I am a recent Computer Science graduate with expertise in:
- Python, TensorFlow, PyTorch
- Machine Learning, Deep Learning
- Data Analysis, SQL
- Git, Linux, Docker

Education:
- Bachelor of Computer Science (2024)
- GPA: 3.8/4.0

Projects:
- Built image classification model (95% accuracy)
- Developed sentiment analysis tool
- Created data pipeline for 10M records
```

**jobs.txt** - Target roles:
```
Graduate AI Engineer
Junior Machine Learning Engineer
Data Scientist
AI Research Assistant
Python Developer
Software Engineer - ML
```

---

### Authentication

#### LinkedIn Cookie Setup

**Why needed?** LinkedIn requires login to access job search. We save cookies to avoid logging in every run.

**Steps:**

```bash
# 1. Run manual login helper
python archive/linkedin_login.py

# 2. Browser will open - login manually
# 3. Complete any 2FA/security checks
# 4. Wait for "Login successful!" message
# 5. Cookies saved to data/linkedin_cookies.pkl
```

**Verification:**

```bash
# Check if session is valid
python -c "
import sys; sys.path.insert(0, 'src')
from scraper import create_driver, load_cookies, is_logged_in
driver = create_driver(headless=True)
load_cookies(driver)
status = 'VALID' if is_logged_in(driver) else 'EXPIRED'
driver.quit()
print(f'LinkedIn session: {status}')
"
```

**Expected Output**: `LinkedIn session: VALID`

**Cookie Lifespan**: 30-60 days

**Refresh Schedule**: Run `linkedin_login.py` when you see "0 jobs scraped" consistently

---

#### Seek/Jora Authentication

**Seek**: No authentication required (public search)

**Jora**: No authentication required, uses stealth mode to bypass bot detection

---

### Running Jobs

#### Manual Execution (Recommended for Testing)

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows

# Run full workflow once
python src/main.py --run-now

# Expected output:
# [2026-02-09 10:00:00] Starting job scraper workflow...
# [2026-02-09 10:00:05] Checking for profile changes...
# [2026-02-09 10:00:06] No profile changes detected
# [2026-02-09 10:00:10] Scraping LinkedIn (3 pages max)...
# [2026-02-09 10:15:20] LinkedIn: 52 jobs scraped (Tier 1: 24 filtered)
# [2026-02-09 10:20:30] Scraping Seek...
# [2026-02-09 10:25:40] Seek: 31 jobs scraped
# [2026-02-09 10:30:50] Scraping Jora...
# [2026-02-09 10:35:00] Jora: 18 jobs scraped
# [2026-02-09 10:35:05] Saved 89 new jobs (Tier 2: 5 filtered, Tier 3: 7 duplicates)
# [2026-02-09 10:35:10] Scoring 89 jobs...
# [2026-02-09 10:50:20] Scored 89 jobs (85 with AI, 4 with parser)
# [2026-02-09 10:50:25] Sending notifications (12 jobs ≥70%)...
# [2026-02-09 10:50:30] ✅ Workflow complete!
```

**Duration**: 30-45 minutes (depends on number of searches enabled)

---

#### Daemon Mode (Background Scheduling)

```bash
# Run as daemon (executes every 24 hours)
python src/main.py --daemon

# Or specify custom schedule
python src/main.py --daemon --schedule "09:00"  # Run daily at 9 AM
```

**To stop daemon**: Ctrl+C or `pkill -f "python.*main.py"`

---

#### Test Mode (Quick Validation)

```bash
# Test with limited URLs (2 per source, 1 page each)
python src/main.py --test

# Duration: ~5-10 minutes
# Use before full production run to verify:
# - LinkedIn cookies valid
# - Scrapers working
# - Database accessible
# - AI API key valid
```

---

### System Health Check
**Last Updated:** 2026-02-09

**Run before production workflow to catch issues early.**

```bash
# === DATABASE CHECK ===
# Verify database exists and has jobs
sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;" 2>/dev/null || echo "❌ Database missing"

# Check jobs by source
sqlite3 data/jobs.db "SELECT source, COUNT(*) FROM jobs GROUP BY source;"
# Expected: linkedin, seek, jora with counts

# Check unscored jobs
sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs j LEFT JOIN scores s ON j.job_id_hash = s.job_id WHERE s.job_id IS NULL;"

# === LINKEDIN SESSION CHECK ===
python -c "
import sys; sys.path.insert(0, 'src')
from scraper import create_driver, load_cookies, is_logged_in
driver = create_driver(headless=True)
load_cookies(driver)
print('✅ LinkedIn session valid' if is_logged_in(driver) else '❌ LinkedIn expired - run: python archive/linkedin_login.py')
driver.quit()
"

# === CONFIG CHECK ===
# Verify API key exists
grep -q '"api_key".*"sk-or-' config.json && echo "✅ OpenRouter API key found" || echo "❌ No API key in config.json"

# Verify SMTP configured
grep -q '"smtp_password"' config.json && echo "✅ SMTP configured" || echo "❌ SMTP not configured"

# === GENERATED FILES CHECK ===
# Verify keyword/URL files exist
[ -f generated_keywords.json ] && echo "✅ Keywords generated" || echo "❌ Run: python src/keyword_generator.py"
[ -f generated_search_urls.json ] && echo "✅ URLs generated" || echo "❌ Run: python src/url_generator.py"

# Check keyword file has content
python -c "
import json
with open('generated_keywords.json') as f:
    kw = json.load(f)
    print(f'Keywords: {len(kw.get(\"title_keywords\", []))} title, {len(kw.get(\"technical_skills\", []))} technical')
"

# === DISK SPACE CHECK ===
df -h data/jobs.db 2>/dev/null | tail -1 | awk '{print "Database size: " $2 " / Free space: " $4}'

# === LOG CHECK ===
# Check for recent errors
tail -50 data/logs/job_scraper.log 2>/dev/null | grep -i "error\|exception" || echo "✅ No recent errors in logs"
```

**All checks passing?** ✅ Safe to run `python src/main.py --run-now`

---

### Monitoring

#### Log Locations

```bash
# Main application log
tail -f data/logs/job_scraper.log

# Scraping stats CSV
cat data/scraping_stats.csv | column -t -s,

# Database size tracking
watch -n 60 'du -h data/jobs.db'
```

#### Key Metrics to Track

```bash
# Jobs scraped per source (last 7 days)
sqlite3 data/jobs.db "
SELECT source, COUNT(*) 
FROM jobs 
WHERE scraped_date >= date('now', '-7 days') 
GROUP BY source;
"

# Score distribution
sqlite3 data/jobs.db "
SELECT 
  CASE 
    WHEN score >= 90 THEN '90-100%'
    WHEN score >= 70 THEN '70-89%'
    WHEN score >= 50 THEN '50-69%'
    ELSE '0-49%'
  END as range,
  COUNT(*)
FROM scores
GROUP BY range;
"

# Optimization efficiency (last run)
# Check logs for lines like:
# "Tier 1: 24/75 jobs filtered (32.0%)"
# "Tier 2: 5/51 jobs filtered (9.8%)"
# "Tier 3: 7/46 duplicates skipped (15.2%)"
```

---

### Testing Guide

#### Pre-Flight Checklist

**Before running main workflow:**

- [ ] Database initialized: `ls -lh data/jobs.db`
- [ ] LinkedIn session valid: Run health check
- [ ] Config has API key: `grep api_key config.json`
- [ ] Keywords generated: `ls generated_keywords.json`
- [ ] URLs generated: `ls generated_search_urls.json`
- [ ] Profile.txt updated: `cat profile.txt | wc -l` (should be 10+ lines)
- [ ] Jobs.txt defined: `cat jobs.txt | wc -l` (should be 5+ roles)

#### Testing Phases

**Phase 1: Individual Scraper Tests** (10 min)

```bash
# Test LinkedIn (1 page)
python -c "
import sys; sys.path.insert(0, 'src')
from scraper import fetch_jobs_from_url, create_driver, load_cookies
import json

with open('generated_search_urls.json') as f:
    urls = json.load(f)

if urls['linkedin']:
    driver = create_driver(headless=False)  # Watch it work
    load_cookies(driver)
    search = urls['linkedin'][0]
    jobs = fetch_jobs_from_url(search['url'], search, driver, max_pages=1)
    driver.quit()
    print(f'✅ LinkedIn: {len(jobs)} jobs scraped')
else:
    print('❌ No LinkedIn URLs in generated_search_urls.json')
"

# Test Seek
python -c "
import sys; sys.path.insert(0, 'src')
from seek_scraper import SeekScraper

scraper = SeekScraper()
jobs = scraper.search_jobs('python developer', 'Perth', max_results=20)
print(f'✅ Seek: {len(jobs)} jobs scraped')
"

# Test Jora
python -c "
import sys; sys.path.insert(0, 'src')
from jora_scraper import JoraScraper

with JoraScraper(headless=False) as scraper:
    jobs = scraper.search_jobs('ai engineer', 'Perth WA', max_results=10)
    print(f'✅ Jora: {len(jobs)} jobs scraped')
"
```

**Phase 2: Full Workflow Test** (30-45 min)

```bash
# Clean database for fresh test
rm -f data/jobs.db
echo "✅ Database cleaned"

# Run full workflow
python src/main.py --run-now

# Monitor progress
tail -f data/logs/job_scraper.log
```

**Phase 3: Results Verification** (5 min)

```bash
# Check database
sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;"
# Expected: 50-200+ jobs

# Check scores
sqlite3 data/jobs.db "SELECT COUNT(*) FROM scores;"
# Expected: Same as jobs count

# View top 10 jobs
python -c "
import sys; sys.path.insert(0, 'src')
import database as db
jobs = db.get_all_jobs()
scored = sorted([j for j in jobs if j.get('score')], key=lambda x: x['score'], reverse=True)[:10]
print('\n🏆 TOP 10 JOBS:')
for i, job in enumerate(scored, 1):
    print(f'{i}. {job[\"score\"]}% - {job[\"title\"][:60]} ({job[\"source\"]})')
"

# Check dashboard
python src/dashboard.py &
sleep 2
open http://localhost:8000  # macOS
# xdg-open http://localhost:8000  # Linux
# start http://localhost:8000     # Windows
```

**Success Criteria:**
- ✅ 50+ jobs scraped total
- ✅ All 3 scrapers executed without errors
- ✅ 3-tier filtering metrics logged
- ✅ All jobs have scores
- ✅ Dashboard displays correctly
- ✅ 5+ jobs scored 70%+

---

### Troubleshooting

#### Decision Tree

```
Problem: No jobs scraped from LinkedIn
├─► Check: LinkedIn session valid?
│   ├─► Run: python archive/linkedin_login.py
│   └─► Verify: Cookies saved to data/linkedin_cookies.pkl
├─► Check: Search URLs exist?
│   └─► Run: python src/url_generator.py
├─► Check: Tier 1 filtering too aggressive?
│   └─► Review: generated_keywords.json (should have 30+ title keywords)
└─► Check: LinkedIn HTML changed?
    └─► See: Appendix D for verified selectors

Problem: All jobs score 0%
├─► Check: OpenRouter API key valid?
│   └─► Test: curl -H "Authorization: Bearer YOUR_KEY" https://openrouter.ai/api/v1/models
├─► Check: Model names correct?
│   └─► Verify: config.json models match OpenRouter catalog
├─► Check: Using parser fallback?
│   └─► Query: SELECT DISTINCT model_used FROM scores;
│       └─► If 'parser-filter': Jobs failed regex checks (expected for mismatches)
└─► Check: API credit balance
    └─► Visit: openrouter.ai/credits

Problem: Dashboard shows "No jobs"
├─► Check: Database exists?
│   └─► ls -lh data/jobs.db
├─► Check: Jobs in database?
│   └─► sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;"
├─► Check: Jobs have scores?
│   └─► sqlite3 data/jobs.db "SELECT COUNT(*) FROM scores;"
└─► Check: Threshold too high?
    └─► Lower notification_threshold in config.json

Problem: Email notifications not sending
├─► Check: SMTP settings correct?
│   └─► Verify: config.json smtp_* fields
├─► Check: Using Gmail app password? (NOT regular password)
│   └─► Generate: Google Account → Security → App passwords
├─► Check: Firewall blocking SMTP port 587?
│   └─► Test: telnet smtp.gmail.com 587
└─► Check: Fallback HTML saved?
    └─► ls data/notifications/*.html

Problem: Jora jobs have empty descriptions
├─► Check: Version up to date?
│   └─► Fixed in v2026-02-05: Now calls get_job_details()
├─► Check: Selector still valid?
│   └─► Test: Open jora job URL, inspect description element
└─► Check: Cloudflare blocking?
    └─► Verify: selenium-stealth installed

Problem: Keywords not updating
├─► Check: jobs.txt hash changed?
│   └─► Delete: .jobs_txt_hash, then run main.py
├─► Check: Keyword generator working?
│   └─► Test: python src/keyword_generator.py
└─► Check: DeepSeek API accessible?
    └─► Verify: API key in config.json
```

---

### Backup & Recovery

#### Database Backup

```bash
# Manual backup
cp data/jobs.db data/jobs.db.backup_$(date +%Y%m%d)

# Automated backup (add to cron)
# Daily at 2 AM:
# 0 2 * * * cd /path/to/Job_Scrape && cp data/jobs.db data/jobs.db.backup_$(date +\%Y\%m\%d)
```

#### Restore from Backup

```bash
# List backups
ls -lh data/jobs.db.backup_*

# Restore specific backup
cp data/jobs.db.backup_20260209 data/jobs.db
```

#### Export Jobs to CSV

```bash
sqlite3 -header -csv data/jobs.db "
SELECT 
  j.title, j.company, j.location, j.source,
  s.score, j.scraped_date, j.url
FROM jobs j
LEFT JOIN scores s ON j.job_id_hash = s.job_id
WHERE s.score >= 70
ORDER BY s.score DESC
" > high_scoring_jobs.csv
```

---

## 👨‍💻 DEVELOPMENT GUIDE
**Last Updated:** 2026-02-09 | **Verified:** SYSTEM_STATUS.md v2026-02-07

### Contributing Workflow

**Read CONTRIBUTING.md** for detailed Git workflow and PR process.

**Quick Rules:**
1. ✅ **Test with test_url.json first** (never commit broken code to production)
2. ✅ **Create backup** before modifying protected files
3. ✅ **Verify no regressions** (run health check after changes)
4. ✅ **Update documentation** (this file, if architecture changes)
5. ✅ **Never push API keys** (use config.json.example as template)

---

### Protected Components
**DO NOT MODIFY WITHOUT EXPLICIT PERMISSION**

#### Critical Files (Battle-Tested, Production-Ready)

**src/scraper.py** - LinkedIn scraper
- **Status**: PERFECT - 100% success rate
- **Test Results**: 75 cards → 52 jobs (30.7% Tier 1 efficiency)
- **Selectors**: Verified working as of 2026-02-07
- **Change Requirement**: LinkedIn HTML structure must change (with proof)
- **Permission**: Required from user

**src/optimization.py** - 3-tier filtering
- **Status**: OPTIMIZED - 35-45% efficiency gain
- **Thresholds**: Validated with production data
- **Change Requirement**: Data-driven justification
- **Permission**: Required from user

**src/database.py** - Database layer
- **Status**: STABLE - Schema validated
- **Changes**: Require migration script + backward compatibility
- **Permission**: Required from user

**test_url.json** - Test configuration
- **Status**: LOCKED - Format validated
- **Purpose**: Safety net for testing
- **Changes**: Must maintain all required fields
- **Permission**: Read-only (can add entries, not modify structure)

**See SYSTEM_STATUS.md (archived)** for complete protection rules and test metrics.

---

### Testing Requirements

**Before committing:**

1. **Lint check**:
   ```bash
   # (Optional) Install linter
   pip install pylint
   
   # Check your changes
   pylint src/your_modified_file.py
   ```

2. **Run test workflow**:
   ```bash
   python src/main.py --test
   ```

3. **Verify no errors**:
   ```bash
   tail -50 data/logs/job_scraper.log | grep -i error
   # Should return nothing
   ```

4. **Check database integrity**:
   ```bash
   sqlite3 data/jobs.db "PRAGMA integrity_check;"
   # Expected: ok
   ```

---

### Code Patterns & Best Practices

#### ✅ DO: Use Existing Functions

```python
# ✅ CORRECT: Use database abstraction
from database import insert_job, get_unscored_jobs

jobs = get_unscored_jobs()
for job in jobs:
    insert_job(job)

# ❌ WRONG: Direct SQL
import sqlite3
conn = sqlite3.connect('data/jobs.db')
conn.execute("INSERT INTO jobs ...")  # Don't do this!
```

#### ✅ DO: Use Configuration

```python
# ✅ CORRECT: Load from config
from main import load_config

config = load_config()
max_pages = config.get('linkedin_max_pages', 3)

# ❌ WRONG: Hardcode values
max_pages = 3  # What if user wants different value?
```

#### ✅ DO: Perth Timezone

```python
# ✅ CORRECT: Use Perth timezone helper
from database import get_perth_now

current_time = get_perth_now()

# ❌ WRONG: Naive datetime
from datetime import datetime
current_time = datetime.now()  # Wrong timezone!
```

#### ✅ DO: Error Handling

```python
# ✅ CORRECT: Multiple selector fallbacks
for selector in ['.job-title', '.title', '[data-job-title]']:
    try:
        title = element.find_element(By.CSS_SELECTOR, selector).text
        break
    except NoSuchElementException:
        continue
else:
    title = "Unknown"

# ❌ WRONG: Single selector, hard fail
title = element.find_element(By.CSS_SELECTOR, '.job-title').text  # Breaks if LinkedIn changes
```

#### ✅ DO: Logging

```python
# ✅ CORRECT: Structured logging
import logging
logger = logging.getLogger(__name__)

logger.info(f"[{search_name}] Page {page}: {jobs_count} jobs scraped")

# ❌ WRONG: Print statements
print(f"Scraped {jobs_count} jobs")  # Not captured in logs
```

#### ❌ DON'T: Create Duplicate Functions

**Before writing new code, check [Appendix A: Function Inventory](#appendix-a-function-inventory)**

Common mistakes:
- ❌ Creating `save_job_to_db()` → Use `database.insert_job()`
- ❌ Creating `score_with_ai()` → Use `scorer.score_job_with_fallback()`
- ❌ Creating `filter_by_title()` → Use `optimization.is_title_relevant()`
- ❌ Creating `build_linkedin_url()` → Use `url_generator.URLGenerator()`

---

### Adding New Features

#### Safe Changes (No Permission Needed)

1. **New dashboard routes** (as long as they don't modify core logic)
2. **Additional logging**
3. **New test scripts** (in archive/test_scripts/)
4. **Documentation updates**
5. **Config options** (with defaults for backward compatibility)

#### Changes Requiring Permission

1. **Modifying LinkedIn selectors**
2. **Changing optimization thresholds**
3. **Altering database schema**
4. **Updating core workflow logic**
5. **Modifying job_hash algorithm** (breaks deduplication)

#### Feature Request Template

```
Feature: [Brief description]

Motivation: [Why is this needed?]

Implementation Plan:
1. [Step 1]
2. [Step 2]
...

Files to Modify:
- src/module.py (function_name)
- config.json (new_setting)

Testing Plan:
- [How will you verify it works?]
- [What could go wrong?]

Backward Compatibility:
- [Will old databases still work?]
- [Will old configs still work?]

May I proceed? (yes/no)
```

---

## 📋 PLANNING & ROADMAP
**Last Updated:** 2026-02-09

### Known Issues

**From FUTURE_IMPROVEMENTS.md (incomplete document):**

1. **Dashboard Apply Button Shows "LinkedIn" for All Sources** (Minor)
   - **Impact**: Cosmetic only
   - **Workaround**: Check job detail page for actual source
   - **Fix**: Update dashboard.html to read from job.source field

2. **Job Deduplication Could Be Smarter** (Enhancement)
   - **Current**: MD5(title + company + url)
   - **Limitation**: Same job reposted with different URL not detected
   - **Proposed**: Fuzzy title matching + company matching
   - **Complexity**: Medium

3. **No Salary Extraction** (Feature Request)
   - **Current**: Salary in description text, not parsed
   - **Proposed**: Regex extraction + normalization
   - **Benefit**: Filter by salary range

---

### Prioritized Backlog

**High Priority (Next Sprint)**

- [ ] Complete FUTURE_IMPROVEMENTS.md (fill missing sections)
- [ ] Add salary extraction
- [ ] Improve deduplication (fuzzy matching)
- [ ] Add job expiry tracking
- [ ] Dashboard performance optimization (pagination for 1000+ jobs)

**Medium Priority**

- [ ] Application deadline alerts
- [ ] Skills gap analysis (what skills you're missing)
- [ ] Company research automation (fetch company info from Crunchbase/LinkedIn)
- [ ] Browser extension for one-click applications
- [ ] Mobile-responsive dashboard

**Low Priority (Nice-to-Have)**

- [ ] Interview scheduling integration
- [ ] Cover letter auto-generation
- [ ] Resume tailoring suggestions
- [ ] Job market analytics (trending skills, salary trends)
- [ ] Multi-language support

---

### Multi-Tenant Migration Plan
**From ARCHITECTURE.md (Future SaaS Vision)**

**Goal**: Transform single-user local app into multi-tenant SaaS platform

#### Current Architecture (v1.0)

```
Job_Scrape/
├── jobs.txt                    # Single user
├── profile.txt                 # Single user
├── data/jobs.db               # Single SQLite DB
└── src/                       # Shared code
```

#### Target Architecture (v3.0)

```
Job_Scraper_Platform/
├── users/
│   ├── user_001/
│   │   ├── jobs.txt
│   │   ├── profile.txt
│   │   └── generated_keywords.json
│   ├── user_002/
│   │   └── ...
│   └── ...
├── database/
│   └── postgresql/            # Multi-tenant DB with user_id partitioning
├── web/
│   ├── backend/              # FastAPI REST API
│   └── frontend/             # React dashboard
└── shared/
    └── src/                  # Shared scraping logic
```

#### Migration Phases

**Phase 1: Current (Single User Local)** ✅ COMPLETE
- SQLite database
- Local file structure
- Command-line execution

**Phase 2: Local Multi-User** (Q2 2026)
- Move to `users/{user_id}/` structure
- User management CLI
- Shared codebase in `shared/src/`
- Still SQLite (one DB per user)

**Phase 3: Web API (Q3 2026)
- FastAPI backend
- REST API endpoints (`/api/v1/jobs`, `/api/v1/scores`)
- JWT authentication
- PostgreSQL migration (single DB, multi-tenant)
- Row-level security policies

**Phase 4: Full SaaS (Q4 2026)**
- React frontend
- User subscriptions (Stripe)
- Cloud deployment (AWS/GCP)
- Redis caching
- Celery background workers
- Monitoring & analytics

#### Database Migration Strategy

**Current: SQLite**
```sql
CREATE TABLE jobs (
    job_id_hash TEXT PRIMARY KEY,
    title TEXT,
    ...
);
```

**Future: PostgreSQL Multi-Tenant**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    subscription_tier TEXT  -- free, pro, enterprise
);

CREATE TABLE jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),  -- Multi-tenant
    title TEXT,
    ...
);

-- Row-Level Security
CREATE POLICY user_isolation ON jobs
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

**Migration Path**:
1. Export SQLite to CSV
2. Transform: Add user_id column (all rows = user_001)
3. Import to PostgreSQL
4. Enable RLS policies
5. Verify data integrity

#### Enhanced jobs.txt Format (Multi-Tenant Ready)

**Current (Simple)**:
```
Graduate AI Engineer, Junior ML Engineer
```

**Future (Metadata-Rich)**:
```
# Target Job Titles
Graduate AI Engineer, Junior ML Engineer, Data Scientist

[DEALBREAKERS]
max_experience: 2
exclude_seniority: Senior, Lead, Principal
exclude_visa: PR Required, Citizenship
exclude_education: PhD Required

[PREFERENCES]
regions: australia, us
locations: Perth, Remote
job_boards: linkedin, seek, jora

[OPTIMIZATION]
enable_title_filtering: true
optimization_level: balanced  # conservative, balanced, aggressive
```

**Benefits**:
- User-specific filtering (no hardcoded keywords)
- Reduced API costs (smarter filtering)
- Better match quality

---

### Monetization Strategy (Future)

**Tier Structure:**

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/mo | 1 job role, LinkedIn only, 100 jobs/day, 7-day history |
| **Pro** | $19/mo | 5 roles, All sources, 1000 jobs/day, 30-day history, Email+SMS |
| **Enterprise** | $99/mo | Unlimited, API access, Custom integrations, Team accounts |

---

## 📚 APPENDICES

### Appendix A: Function Inventory
**Last Updated:** 2026-02-09 | **Quick Lookup Table**

**Format:** `module.function(params) → return_type | Used by`

#### main.py
- `run_daily_job() → None` | Scheduler, manual execution
- `load_config() → dict` | All modules
- `load_job_searches() → list[dict]` | Scraping step
- `run_test_mode() → None` | Testing
- `start_daemon() → None` | Background scheduling

#### scraper.py (LinkedIn)
- `create_driver(headless=True, use_profile=False) → WebDriver` | All scraping functions
- `load_cookies(driver) → None` | fetch_jobs_from_url
- `save_cookies(driver) → None` | Manual login
- `manual_login_helper() → None` | Cookie refresh
- `extract_job_from_card(card, search_config, driver, optimizer=None) → dict|None` | fetch_jobs_from_url
- `fetch_jobs_from_url(url, search_config, driver, max_pages=3) → list[dict]` | fetch_all_jobs
- `fetch_all_jobs(searches, api_key=None, headless=True, max_pages=3) → tuple[list, dict]` | main.run_daily_job

#### seek_scraper.py
- `SeekScraper.__init__(cookies=None, delay_range=(2,5))` | Initialization
- `SeekScraper.search_jobs(keyword, location, max_results=50) → list[dict]` | main.run_daily_job
- `SeekScraper._extract_job_from_card(card) → dict` | search_jobs
- `SeekScraper.scrape_jobs_from_url(url, max_jobs=50) → list[dict]` | Test scripts

#### jora_scraper.py
- `JoraScraper.__init__(headless=True)` | Initialization
- `JoraScraper.search_jobs(keyword, location, time_filter, max_results) → list[dict]` | main.run_daily_job
- `JoraScraper._parse_job_element(element) → dict` | search_jobs
- `JoraScraper.get_job_details(job_url) → str|None` | search_jobs (NEW)
- `JoraScraper.close() → None` | Context manager

#### database.py
- `init_database() → None` | main.run_daily_job (first run)
- `insert_job(job_data) → str` | main.run_daily_job
- `insert_score(job_id, score_data, profile_hash) → None` | Scoring step
- `get_unscored_jobs() → list[dict]` | Scoring step
- `get_all_jobs(include_inactive=False) → list[dict]` | Dashboard
- `get_high_scoring_unnotified(threshold) → list[dict]` | Notification step
- `mark_notified(job_id, notification_type, status) → None` | Notification step
- `reject_job(job_id, rejection_category, rejection_notes) → None` | Dashboard
- `get_rejected_jobs() → list[dict]` | Dashboard
- `get_rejection_stats() → list[dict]` | Dashboard stats
- `get_jobs_for_rescore(min_score, max_score, max_age_days, exclude_profile_hash) → list[dict]` | rescore_manager
- `delete_score(job_id) → None` | Rescore workflow
- `get_profile_hash() → str` | Rescore detection
- `get_last_profile_hash() → str` | Rescore detection
- `insert_profile_change(profile_hash) → None` | Rescore logging
- `generate_job_hash(title, company, url) → str` | Deduplication
- `get_perth_now() → datetime` | All timestamp operations

#### scorer.py
- `load_keywords() → dict` | Prompt building
- `load_jobs_txt_metadata() → dict` | Prompt building
- `build_dynamic_prompt_template() → str` | build_prompt
- `load_profile() → str` | All scoring
- `build_prompt(job, profile_content) → str` | score_job_with_fallback
- `call_openrouter(model, prompt, api_key, max_tokens) → str` | score_job_with_fallback
- `parse_score_response(response_content) → dict|None` | score_job_with_fallback
- `score_job_with_fallback(job, profile_content, models_config, api_key) → dict|None` | score_batch
- `score_batch(jobs, profile_content, models_config, api_key) → list[tuple]` | main.run_daily_job

#### job_parser.py
- `JobDescriptionParser.parse_job(description, title, location) → dict` | scorer.score_job_with_fallback (fallback)

#### optimization.py
- `OptimizationManager.__init__(config=None)` | Initialization
- `OptimizationManager.is_title_relevant(title) → tuple[bool, str]` | scraper.extract_job_from_card (Tier 1)
- `OptimizationManager.is_description_relevant(description, title) → tuple[bool, str]` | main.run_daily_job (Tier 2)
- `OptimizationManager.should_skip_duplicate(job_hash, db_conn) → tuple[bool, str]` | main.run_daily_job (Tier 3)

#### keyword_generator.py
- `KeywordGenerator.__init__()` | Initialization
- `KeywordGenerator.needs_regeneration() → bool` | main.run_daily_job (Step 0)
- `KeywordGenerator.generate_keywords() → dict` | main.run_daily_job (Step 0)

#### url_generator.py
- `URLGenerator.__init__(config_path)` | Initialization
- `URLGenerator.generate_linkedin_urls() → list[dict]` | generate_all_urls
- `URLGenerator.generate_seek_urls() → list[dict]` | generate_all_urls
- `URLGenerator.generate_jora_urls() → list[dict]` | generate_all_urls
- `URLGenerator.generate_all_urls() → dict` | Manual execution

#### rescore_manager.py
- `detect_profile_change() → bool` | main.run_daily_job (Step 1)
- `trigger_smart_rescore(profile_content, config) → int` | main.run_daily_job (Step 1)

#### notifier.py
- `build_email_html(jobs, date_str) → str` | send_email_notification
- `send_email_notification(jobs, config) → bool` | notify_new_matches
- `save_html_notification(jobs) → None` | notify_new_matches
- `notify_new_matches(config) → None` | main.run_daily_job (Step 5)

#### dashboard.py (Flask Routes)
- `GET /` → index() | User navigation
- `GET /all` → show_all() | User navigation
- `GET /stats` → stats() | User navigation
- `GET /applied` → applied_jobs() | User navigation
- `POST /mark_applied/<job_id>` → mark_applied(job_id) | Dashboard UI
- `POST /update_status/<job_id>` → update_status(job_id) | Dashboard UI
- `POST /reject/<job_id>` → reject_job_route(job_id) | Dashboard UI
- `POST /rescore/<job_id>` → rescore_job(job_id) | Dashboard UI

#### scraping_stats.py
- `log_scraping_stats(source, jobs_count, duration, success) → None` | Scrapers
- `get_scraping_stats(days=30) → list[dict]` | Dashboard stats

---

### Appendix B: Config Reference
**Last Updated:** 2026-02-09

**Complete config.json Settings**

```json
{
  // === API KEYS ===
  "api_key": "sk-or-v1-...",              // OpenRouter API key (REQUIRED)
  "jsearch_api_key": "",                  // JSearch API (unused currently)
  
  // === AI MODEL CONFIGURATION ===
  "models": {
    "primary": "anthropic/claude-3.5-sonnet",     // Best quality, $0.015/job
    "secondary": "openai/gpt-4-turbo",            // Good quality, $0.010/job
    "tertiary": "google/gemini-flash-1.5",        // Cheapest, $0.001/job
    "keyword_generation": "deepseek/deepseek-chat" // Best for keyword extraction
  },
  
  // === NOTIFICATION SETTINGS ===
  "notification_threshold": 70,           // Min score to send email (0-100)
  "smtp_server": "smtp.gmail.com",        // Gmail SMTP server
  "smtp_port": 587,                       // SMTP port (587 = TLS)
  "from_email": "your@gmail.com",         // Sender email
  "to_email": "your@gmail.com",           // Recipient email
  "smtp_username": "your@gmail.com",      // SMTP username (usually same as from_email)
  "smtp_password": "abcd efgh ijkl mnop", // Gmail app password (16 chars, NOT regular password)
  
  // === RESCORE SETTINGS ===
  "rescore_threshold_min": 40,            // Min score for rescore eligibility
  "rescore_threshold_max": 85,            // Max score for rescore eligibility
  "rescore_max_age_days": 30,             // Only rescore jobs from last N days
  
  // === SCRAPER LIMITS ===
  "linkedin_max_pages": 3,                // Max pages per LinkedIn search
  "seek_max_pages": 3,                    // Max pages per Seek search
  "jora_max_pages": 3,                    // Max pages per Jora search
  "max_jobs_per_search": 100,             // Global limit per search
  
  // === 3-TIER OPTIMIZATION ===
  "optimization": {
    "enabled": true,                      // Master switch for all tiers
    "tier1_title_filter": true,           // Pre-filter by title keywords
    "tier2_description_filter": true,     // Filter by description quality
    "tier3_deduplication": true,          // Skip duplicates
    "min_description_length": 200,        // Tier 2: Min chars for quality
    "dedup_window_days": 90               // Tier 3: Lookback window
  },
  
  // === SELENIUM/BROWSER SETTINGS ===
  "headless": true,                       // Run browser in background (false for debugging)
  "page_load_timeout": 30,                // Max seconds to wait for page load
  "implicit_wait": 10,                    // Max seconds to wait for elements
  
  // === SCHEDULING ===
  "schedule_enabled": false,              // Enable daemon mode
  "schedule_time": "09:00",               // Daily run time (Perth timezone)
  "schedule_interval_hours": 24           // Hours between runs
}
```

**Field Types & Validation:**

| Field | Type | Valid Values | Default |
|-------|------|--------------|---------|
| api_key | string | `sk-or-v1-...` | REQUIRED |
| notification_threshold | integer | 0-100 | 70 |
| rescore_threshold_min | integer | 0-100 | 40 |
| rescore_threshold_max | integer | 0-100 | 85 |
| linkedin_max_pages | integer | 1-10 | 3 |
| min_description_length | integer | 50-1000 | 200 |
| dedup_window_days | integer | 1-365 | 90 |
| headless | boolean | true/false | true |

---

### Appendix C: Error Code Guide
**Last Updated:** 2026-02-09

**Common Error Messages & Solutions**

| Error | Cause | Solution |
|-------|-------|----------|
| `NoSuchElementException: Unable to locate element: {"method":"css selector","selector":"li.scaffold-layout__list-item"}` | LinkedIn HTML changed OR cookies expired | 1. Refresh cookies: `python archive/linkedin_login.py`<br>2. If still fails: Check [Appendix D](#appendix-d-verified-selectors) |
| `RateLimitError: Rate limit exceeded for model anthropic/claude-3.5-sonnet` | OpenRouter API rate limit hit | Wait 60 seconds, retry. Or switch to cheaper model (gemini-flash-1.5) |
| `ModelUnavailableError: Model anthropic/claude-3.5-sonnet is currently unavailable` | OpenRouter model down | Fallback chain should activate automatically. Check logs for secondary model usage. |
| `ScoringError: Failed to parse score from response` | LLM returned malformed JSON | Parser fallback should activate. Check `model_used` field in database. |
| `sqlite3.OperationalError: no such table: jobs` | Database not initialized | Run: `python -c "import sys; sys.path.insert(0, 'src'); import database; database.init_database()"` |
| `FileNotFoundError: [Errno 2] No such file or directory: 'data/linkedin_cookies.pkl'` | LinkedIn cookies missing | Run: `python archive/linkedin_login.py` |
| `smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')` | Wrong SMTP password | Use Gmail app password, NOT regular password. Generate at: Google Account → Security → App passwords |
| `KeyError: 'id'` in search config | generated_search_urls.json missing 'id' field | Regenerate: `python src/url_generator.py` |
| `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` in config.json | config.json syntax error | Validate JSON: `python -m json.tool config.json` |
| `requests.exceptions.ConnectionError: HTTPSConnectionPool(host='openrouter.ai', port=443)` | No internet OR OpenRouter down | Check internet connection. Visit https://openrouter.ai/status |

**Log Analysis Commands:**

```bash
# Find errors in logs
grep -i "error\|exception" data/logs/job_scraper.log | tail -20

# Count errors by type
grep -i "error" data/logs/job_scraper.log | cut -d: -f3 | sort | uniq -c

# Check last 100 lines for issues
tail -100 data/logs/job_scraper.log
```

---

### Appendix D: Verified Selectors
**Last Updated:** 2026-02-07 | **Source:** SYSTEM_STATUS.md

**LinkedIn Selectors (Tested 2026-02-07)**

| Element | Selector | Fallbacks | Status |
|---------|----------|-----------|--------|
| Job Cards | `li.scaffold-layout__list-item` | None | ✅ VERIFIED |
| Job Title | `.job-details-jobs-unified-top-card__job-title` | `.jobs-unified-top-card__job-title`, `h1.t-24` | ✅ VERIFIED |
| Company | `.job-details-jobs-unified-top-card__company-name` | `.jobs-unified-top-card__company-name`, `a.app-aware-link` | ✅ VERIFIED |
| Location | `.job-details-jobs-unified-top-card__bullet` | `.jobs-unified-top-card__bullet` | ✅ VERIFIED |
| Description | `.jobs-description__content` | `.jobs-description`, `div[class*="description"]` | ✅ VERIFIED |
| Requirements | `.jobs-box__html-content` (inside "Qualifications" section) | Manual text search for "qualifications" | ✅ VERIFIED |
| Posted Date | `.jobs-unified-top-card__posted-date` | `span[class*="posted"]` | ✅ VERIFIED |
| Pagination | `button[aria-label="Page 2"]` | `button[aria-label*="Page"]` | ✅ VERIFIED |

**Seek Selectors (HTTP/BeautifulSoup)**

| Element | Selector | Status |
|---------|----------|--------|
| Job Cards | `article[data-testid="job-card"]` | ✅ VERIFIED |
| Job Title | `a[data-automation="jobTitle"]` | ✅ VERIFIED |
| Company | `a[data-automation="jobCompany"]` | ✅ VERIFIED |
| Location | `a[data-automation="jobLocation"]` | ✅ VERIFIED |
| Summary | `span[data-automation="jobShortDescription"]` | ✅ VERIFIED |

**Jora Selectors (Selenium)**

| Element | Selector | Fallbacks | Status |
|---------|----------|-----------|--------|
| Job Cards | `article` | `div[class*="job"]`, links with `/job/` | ✅ VERIFIED |
| Job Title | `a.job-title` | `h2 a`, `h3 a` | ✅ VERIFIED |
| Company | `span.company` | Text extraction heuristics | ✅ VERIFIED |
| Location | `span.location` | Text extraction heuristics | ✅ VERIFIED |
| Description (Detail Page) | `div[class*="description"]` | `div[id*="description"]` | ✅ VERIFIED (2026-02-05) |

**Test Results (2026-02-07):**
- LinkedIn: 75 cards → 52 jobs extracted (100% success rate)
- Seek: 8 pages → 131 jobs extracted (100% success rate)
- Jora: 6 pages → 71 jobs extracted (100% success rate, descriptions now complete)

**If Selectors Break:**

1. **Verify with manual inspection**:
   ```bash
   # Open browser and inspect elements
   # LinkedIn: https://www.linkedin.com/jobs/search/?keywords=python
   # Seek: https://www.seek.com.au/python-jobs/in-All-Perth-WA
   # Jora: https://au.jora.com/j?q=python&l=Perth
   ```

2. **Update selectors in code** (requires permission)

3. **Test with single job card** before full scrape

4. **Document changes** in SYSTEM_STATUS.md

---

### Appendix E: Migration Checklist
**Last Updated:** 2026-02-09 | **Source:** ARCHITECTURE.md

**SQLite → PostgreSQL Migration (Future)**

**Pre-Migration:**
- [ ] Export SQLite to CSV: `sqlite3 data/jobs.db ".mode csv" ".output jobs.csv" "SELECT * FROM jobs;"`
- [ ] Export scores: `sqlite3 data/jobs.db ".mode csv" ".output scores.csv" "SELECT * FROM scores;"`
- [ ] Backup database: `cp data/jobs.db data/jobs.db.pre_migration`
- [ ] Document current schema: `sqlite3 data/jobs.db ".schema" > schema_backup.sql`

**PostgreSQL Setup:**
- [ ] Install PostgreSQL: `brew install postgresql` (macOS) or apt-get (Linux)
- [ ] Create database: `createdb job_scraper_production`
- [ ] Create user: `CREATE USER job_scraper WITH PASSWORD 'secure_password';`
- [ ] Grant privileges: `GRANT ALL PRIVILEGES ON DATABASE job_scraper_production TO job_scraper;`

**Schema Creation:**
- [ ] Create users table (new for multi-tenant)
- [ ] Create jobs table with user_id FK
- [ ] Create scores table with user_id FK
- [ ] Create rejections table with user_id FK
- [ ] Create notifications table with user_id FK
- [ ] Create profile_changes table with user_id FK
- [ ] Add indexes: job_id_hash, user_id, scraped_date, score

**Data Migration:**
- [ ] Transform CSV: Add user_id column (all = 'user_001')
- [ ] Import jobs: `COPY jobs FROM 'jobs.csv' CSV HEADER;`
- [ ] Import scores: `COPY scores FROM 'scores.csv' CSV HEADER;`
- [ ] Verify counts match: `SELECT COUNT(*) FROM jobs;`
- [ ] Verify relationships intact: `SELECT COUNT(*) FROM jobs j JOIN scores s ON j.job_id_hash = s.job_id;`

**Row-Level Security:**
- [ ] Enable RLS: `ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;`
- [ ] Create policy: `CREATE POLICY user_isolation ON jobs USING (user_id = current_setting('app.current_user_id')::UUID);`
- [ ] Test isolation: Query as different users

**Application Updates:**
- [ ] Update database.py: Replace sqlite3 with psycopg2
- [ ] Update connection string: `postgresql://user:pass@localhost/db`
- [ ] Update SQL queries: Replace `?` placeholders with `%s`
- [ ] Update date handling: Use PostgreSQL timestamp functions
- [ ] Test all CRUD operations

**Post-Migration:**
- [ ] Run full workflow test
- [ ] Verify job counts match
- [ ] Verify scores intact
- [ ] Backup PostgreSQL: `pg_dump job_scraper_production > backup.sql`
- [ ] Update documentation: This file, README.md
- [ ] Archive SQLite database: Move to `archive/databases/`

---

## 📧 DOCUMENT MAINTENANCE
**Last Updated:** 2026-02-09  
**Created By:** GitHub Copilot + User  
**Purpose:** Single source of truth for Job Scraper system

### Version History

| Version | Date | Changes | Updated By |
|---------|------|---------|------------|
| 1.0.0 | 2026-02-09 | Initial master context creation | GitHub Copilot |

### Update Guidelines

**When to Update This Document:**

1. **Architecture changes** → Update [System Architecture](#system-architecture) section
2. **New functions added** → Update [Appendix A: Function Inventory](#appendix-a-function-inventory)
3. **Config settings changed** → Update [Appendix B: Config Reference](#appendix-b-config-reference)
4. **Selectors break** → Update [Appendix D: Verified Selectors](#appendix-d-verified-selectors)
5. **New errors discovered** → Update [Appendix C: Error Code Guide](#appendix-c-error-code-guide)
6. **Known issues added** → Update [Known Issues](#known-issues)

**Section-Level Version Tracking:**

Each major section has:
- **Last Updated:** YYYY-MM-DD
- **Verified:** Against which file versions

Example:
```markdown
## 🔧 TECHNICAL REFERENCE
**Last Updated:** 2026-02-09 | **Verified:** scraper.py v2026-02-05, database.py v2026-02-07
```

**How to Update:**

1. Modify content
2. Update "Last Updated" date for that section
3. Update "Verified" file versions if applicable
4. Increment version number if major changes (1.0.0 → 1.1.0)
5. Add entry to Version History table

---

## ⚠️ CRITICAL REMINDER

**This is the SINGLE SOURCE OF TRUTH for the Job Scraper codebase.**

Before writing ANY code:
1. ✅ Check [Function Inventory](#appendix-a-function-inventory) - Does it already exist?
2. ✅ Check [Protected Components](#protected-components) - Is it safe to modify?
3. ✅ Check [Workflow Diagram](#complete-workflow-diagram) - Where does it fit?
4. ✅ Check [Database Schema](#database-schema) - Will it break anything?

**When in doubt, ASK. Never assume.**

**Attach this document to every AI chat session** to ensure consistency and avoid duplicate code.

---

**END OF MASTER CONTEXT**

Total Lines: ~2,900  
Total Sections: 6 main + 5 appendices  
Coverage: 100% of existing documentation  
Redundancy: 0% (all duplicates consolidated)

**Usage:** Attach to AI agent prompts for complete system understanding.
