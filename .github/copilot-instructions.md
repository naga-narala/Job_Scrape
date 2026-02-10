# AI Agent Instructions for Job Scraper

## 📌 PRIMARY REFERENCE

**🎯 MASTER_CONTEXT.md is the SINGLE SOURCE OF TRUTH**

Before writing ANY code, read: [MASTER_CONTEXT.md](../MASTER_CONTEXT.md)

**Quick Navigation:**
- System architecture → [MASTER_CONTEXT.md § System Architecture](../MASTER_CONTEXT.md#system-architecture)
- Function lookup → [MASTER_CONTEXT.md § Appendix A](../MASTER_CONTEXT.md#appendix-a-function-inventory)
- Protected files → [MASTER_CONTEXT.md § Protected Components](../MASTER_CONTEXT.md#protected-components)
- Database schema → [MASTER_CONTEXT.md § Database Schema](../MASTER_CONTEXT.md#database-schema)
- Verified selectors → [MASTER_CONTEXT.md § Appendix D](../MASTER_CONTEXT.md#appendix-d-verified-selectors)

**Documentation Archive:** `archive/documentation/` contains superseded .md files

---

## System Overview

**Production-ready** multi-source job scraper with 3-tier optimization that scrapes LinkedIn/Seek/Jora, scores jobs with AI against user profile, and presents matches via dashboard.

### Architecture Pattern: Sequential Optimization Pipeline
```
Scraping → Tier 1 (Title) → Tier 2 (Dedup) → Tier 3 (Quality) → AI Scoring → Dashboard
```

**Current AI Models (as of 2026-02-09):**
- Primary: `google/gemini-2.0-flash-exp:free` (cheapest, good quality)
- Fallbacks: `deepseek/deepseek-chat`, `anthropic/claude-3.5-haiku`
- Keyword Gen: `anthropic/claude-3.5-sonnet` (best for extraction)
- Final Fallback: Regex parser (`job_parser.py`)

## Key Components

### 1. Scrapers (Different Approaches Per Platform)
- **LinkedIn** ([src/scraper.py](../src/scraper.py)): Selenium + cookie auth, 25 jobs/page, pagination with "aria-label" detection
- **Seek** ([src/seek_scraper.py](../src/seek_scraper.py)): HTTP requests + BeautifulSoup, URL pattern: `/keyword-jobs/in-Location?daterange=1`
- **Jora** ([src/jora_scraper.py](../src/jora_scraper.py)): Selenium stealth mode, fetches full descriptions via detail pages (v2026-02-05)

**Critical Pattern**: Each scraper implements 3-tier optimization inline:
```python
# Tier 1: Title filtering (before clicking job) - 30% savings
if not optimizer.tier1_should_scrape_title(title):
    tier1_filtered += 1
    continue

# Tier 2: Deduplication check (before database insert) - 0-5% savings
job_hash = generate_job_hash(title, company, url)
if optimizer.tier2_is_duplicate(job_hash):
    tier2_skipped += 1
    continue
    
# Tier 3: Description quality (before AI scoring) - 5-10% savings
has_quality, reason = optimizer.tier3_has_quality_description(description)
if not has_quality:
    tier3_filtered += 1
    continue
```

### 2. AI Scoring System ([src/scorer.py](../src/scorer.py))

**Fallback Chain**: Primary → Secondary → Tertiary → Parser-Filter
```python
# Current config (google/gemini-2.0-flash-exp:free is PRIMARY)
models = {
    "primary": "google/gemini-2.0-flash-exp:free",
    "fallbacks": ["deepseek/deepseek-chat", "anthropic/claude-3.5-haiku"]
}
# If all AI models fail → job_parser.py regex scoring
```

**Dynamic Keyword Loading**: Keywords from `generated_keywords.json` (auto-regenerated when `jobs.txt` changes)

**Parser-Filter Pattern**: When AI unavailable, `job_parser.py` uses regex to auto-reject based on:
- Seniority level from `dealbreakers.exclude_seniority` (e.g., Senior, Lead, Principal)
- Experience requirements (>2 years)
- Visa requirements (PR/Citizenship)
- **CRITICAL**: Jobs scored 0% with `model_used='parser-filter'` should NOT be re-scored (they failed dealbreaker checks)

### 3. Database Schema ([src/database.py](../src/database.py))

**Tables**: `jobs`, `scores`, `rejections`, `notifications`, `profile_changes`

**Critical Hash Functions**:
```python
job_hash = generate_job_hash(title, company, url)  # Deduplication
profile_hash = get_profile_hash()  # Triggers smart rescore
```

**Perth Timezone Pattern**: ALL timestamps use `get_perth_now()` - never use naive datetime

### 4. Optimization System ([src/optimization.py](../src/optimization.py))

**Hybrid Title Filtering (Tier 1)** - 30%+ efficiency:
- **Standalone keywords**: "graduate", "junior", "intern" → AUTO-ACCEPT (no domain needed)
- **Domain + Role**: "ml" + "engineer" → ACCEPT | "java" + "developer" → REJECT (if java not in domain keywords)
- **False positives**: Regex patterns to catch irrelevant jobs (e.g., "Infrastructure Engineer")
- **Dealbreaker exclusions**: Loaded from `generated_keywords.json` → `dealbreakers.exclude_seniority`

**Tier 2** (dedup): Check job_hash exists in last 90 days (configurable)
**Tier 3** (quality): Description ≥100 chars (configurable) + technical keyword presence

**Metrics Tracking**: All scrapers report `tier1_filtered`, `tier2_skipped`, `tier3_filtered`


## Developer Workflows

### Running Scrapers
```bash
# Full workflow (scrape → score → notify) - RECOMMENDED
python src/main.py --run-now

# Individual scrapers (for debugging)
python src/scraper.py          # LinkedIn only (requires cookies)
python src/seek_scraper.py     # Seek only
python src/jora_scraper.py     # Jora only

# Dashboard
python src/dashboard.py        # Starts Flask on port 8000
```

### Authentication Setup
```bash
# LinkedIn: One-time manual login to save cookies (expires 30-60 days)
python archive/linkedin_login.py

# Verify session validity
python -c "import sys; sys.path.insert(0, 'src'); \
from scraper import create_driver, load_cookies, is_logged_in; \
driver = create_driver(headless=True); load_cookies(driver); \
print('✅ Valid' if is_logged_in(driver) else '❌ Expired'); driver.quit()"
```

### Keyword Regeneration (Automatic)
```python
# src/main.py checks jobs.txt hash on each run (Step 0)
jobs_txt_hash = calculate_jobs_txt_hash()
if jobs_txt_hash != get_last_jobs_txt_hash():
    generate_keywords()  # Updates generated_keywords.json
    generate_search_urls()  # Updates generated_search_urls.json
```

### Smart Rescore (Automatic)
```python
# Triggered when profile.txt changes (Step 1 in main.py)
# Rescores jobs scoring 70-79% from last 7 days
# Configured in config.json:
{
  "rescore_threshold_min": 70,
  "rescore_threshold_max": 79,
  "rescore_max_age_days": 7
}
```

### Dashboard
```bash
# Start dashboard (port 8000 by default)
python src/dashboard.py

# Custom port
PORT=8080 python src/dashboard.py

# Access at http://localhost:8000
```

**Dashboard Features**:
- Day-wise grouping ("Today", "Yesterday", "2 days ago", etc.)
- Job rejection with categories (click "X" button)
- Application tracking (mark as "Applied")
- Rejected jobs hidden from main view but queryable in DB


## Project-Specific Conventions

### 1. Region Handling
Jobs have `region` field: `'australia'` or `'us'`
- Australian jobs: LinkedIn AU, Seek, Jora
- US remote jobs: LinkedIn US searches

### 2. Configuration Pattern
```python
# Always load from config.json (not hardcoded)
with open('config.json') as f:
    config = json.load(f)
max_pages = config.get('linkedin_max_pages', 3)
```

### 3. Error Handling in Scrapers
```python
# Multiple selector fallbacks (don't fail on first miss)
for selector in ['.job-title', '.job-card-title', '[data-job-title]']:
    try:
        title = element.find_element(By.CSS_SELECTOR, selector).text
        break
    except: continue
```

### 4. Logging Pattern
```python
# Structured logging with context
logger.info(f"[{search_name}] Page {page}: {jobs_count} jobs scraped")
```

### 5. File Paths (Always Absolute)
```python
# Use Path() for cross-platform compatibility
from pathlib import Path
DB_PATH = Path(__file__).parent.parent / 'data' / 'jobs.db'
```

## Testing & Debugging

### Quick Tests (No Full Scrape)
```bash
# Test with limited URLs (2 per source, 1 page each) - ~5-10 min
python src/main.py --test

# Score unscored jobs only (skip scraping)
python -c "import sys; sys.path.insert(0, 'src'); \
from main import run_scoring_phase; run_scoring_phase()"
```

### Database Inspection
```bash
# Check all jobs with scores
python -c "import sys; sys.path.insert(0, 'src'); \
import database as db; jobs = db.get_all_jobs(); \
print(f'Total: {len(jobs)}'); \
[print(f'{j[\"score\"]}% - {j[\"title\"]}') for j in sorted(jobs, key=lambda x: x.get('score',0), reverse=True)[:10]]"

# Check database size and table counts
sqlite3 data/jobs.db "SELECT 'Jobs:', COUNT(*) FROM jobs UNION \
SELECT 'Scores:', COUNT(*) FROM scores UNION \
SELECT 'Rejections:', COUNT(*) FROM rejections;"
```

### Common Issues

**Scraper returns 0 jobs**:
1. Check LinkedIn session: `python archive/linkedin_login.py`
2. Verify selectors in [MASTER_CONTEXT Appendix D](../MASTER_CONTEXT.md#appendix-d-verified-selectors)
3. Check Tier 1 filtering isn't too aggressive (review `generated_keywords.json`)

**AI scoring fails**:
- Check OpenRouter API key in `config.json` → `openrouter_api_key`
- Verify model names match OpenRouter catalog
- Parser-filter fallback will activate (jobs scored 0% with `model_used='parser-filter'`)

**Dashboard shows "No jobs"**:
- Check database: `sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;"`
- Verify scores exist: `sqlite3 data/jobs.db "SELECT COUNT(*) FROM scores;"`
- Check threshold: `match_threshold` in config.json (default 30%)


## Integration Points

### OpenRouter API ([src/scorer.py](../src/scorer.py))
```python
# POST to https://openrouter.ai/api/v1/chat/completions
headers = {
    "Authorization": f"Bearer {config['openrouter_api_key']}",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Job Scraper"
}
```

### Email Notifications ([src/notifier.py](../src/notifier.py))
- Gmail SMTP with app password (NOT regular password)
- Config keys: `email_smtp_host`, `email_smtp_port`, `email_from`, `email_password`, `email_to`
- 3 retry attempts with exponential backoff
- Fallback: Save HTML to `data/notifications/` and auto-open in browser

### External Dependencies
- Selenium WebDriver (Chrome): Auto-downloads chromedriver via webdriver-manager
- OpenRouter: Primary AI scoring (paid but cheap - Gemini Flash is free tier)
- Brave Search API: Unused currently (can be added for job discovery)


## Critical "Do Not Break" Rules

1. **Never modify LinkedIn selectors** without verifying in [MASTER_CONTEXT Appendix D](../MASTER_CONTEXT.md#appendix-d-verified-selectors) - they're battle-tested
2. **Don't bypass 3-tier optimization** - it's integral to scraper performance
3. **Don't re-score parser-filter jobs** - they failed regex checks for good reason
4. **Always use Perth timezone** functions from `database.py`
5. **Don't change job_hash algorithm** - would break deduplication for existing jobs
6. **Preserve model fallback chain** - primary fails often, fallbacks are essential

## Multi-Tenant Future Considerations

See [MASTER_CONTEXT § Planning & Roadmap](../MASTER_CONTEXT.md#planning--roadmap) for planned SaaS architecture. Current design keeps user data in separate SQLite DB to simplify migration to PostgreSQL multi-tenant setup later.

**Current User Isolation**:
- Single `jobs.db` per instance
- `profile.txt` and `jobs.txt` at root level
- Future: `users/user_001/` structure

## Quick Reference Commands

```bash
# Full workflow (scrape → score → notify)
python src/main.py --run-now

# Generate keywords from jobs.txt
python src/keyword_generator.py

# Generate LinkedIn search URLs
python src/url_generator.py

# Start dashboard
python src/dashboard.py
```
