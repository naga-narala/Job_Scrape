# AI Agent Instructions for Job Scraper

## System Overview

Multi-source job scraper with 3-tier optimization that scrapes LinkedIn/Seek/Jora, scores jobs with AI against user profile, and presents matches via dashboard. **This is production-ready code - verify thoroughly before suggesting changes.**

### Architecture Pattern: Sequential Optimization Pipeline
```
Scraping → Tier 1 (Title) → Tier 2 (Dedup) → Tier 3 (Quality) → AI Scoring → Dashboard
```

**Critical Files to Review Before Changes:**
- [SYSTEM_STATUS.md](SYSTEM_STATUS.md) - What's verified working (don't break it)
- [CODEBASE_REFERENCE.md](CODEBASE_REFERENCE.md) - Complete function inventory & workflows
- [ARCHITECTURE.md](ARCHITECTURE.md) - Future multi-tenant design considerations

## Key Components

### 1. Scrapers (Different Approaches Per Platform)
- **LinkedIn** ([src/scraper.py](src/scraper.py)): Selenium + cookie auth, 25 jobs/page, pagination with "aria-label" detection
- **Seek** ([src/seek_scraper.py](src/seek_scraper.py)): HTTP requests + BeautifulSoup, URL pattern: `/keyword-jobs/in-Location`
- **Jora** ([src/jora_scraper.py](src/jora_scraper.py)): Selenium stealth mode, fetches full descriptions via detail pages

**Critical Pattern**: Each scraper implements 3-tier optimization inline:
```python
# Tier 1: Title filtering (before clicking job)
if not optimizer.tier1_should_scrape_title(title):
    tier1_filtered += 1
    continue

# Tier 2: Deduplication check
if optimizer.tier2_is_duplicate(job_hash):
    tier2_skipped += 1
    continue
    
# Tier 3: Description quality
has_quality, reason = optimizer.tier3_has_quality_description(description)
```

### 2. AI Scoring System ([src/scorer.py](src/scorer.py))

**Fallback Chain**: Primary → Secondary → Tertiary → Parser-Filter
```python
models = {
    "primary": "deepseek/deepseek-chat",
    "fallbacks": ["anthropic/claude-3.5-haiku"]
}
# If all AI models fail → job_parser.py regex scoring
```

**Dynamic Keyword Loading**: Keywords from `generated_keywords.json` (auto-regenerated when `jobs.txt` changes)

**Parser-Filter Pattern**: When AI unavailable, `job_parser.py` uses regex to auto-reject based on:
- Seniority level (Senior/Lead/Principal)
- Experience requirements (>2 years)
- Visa requirements (PR/Citizenship)
- Jobs scored 0% with `model_used='parser-filter'` should NOT be re-scored

### 3. Database Schema ([src/database.py](src/database.py))

**Tables**: `jobs`, `scores`, `notifications`, `profile_history`

**Critical Hash Functions**:
```python
job_hash = generate_job_hash(title, company, url)  # Deduplication
profile_hash = get_profile_hash()  # Triggers smart rescore
```

**Perth Timezone Pattern**: ALL timestamps use `get_perth_now()` - never use naive datetime

### 4. Optimization System ([src/optimization.py](src/optimization.py))

**Tier 1** (30%+ efficiency): Title filtering with `title_keywords`, `exclude_keywords`
**Tier 2** (dedup): Check job_hash exists in last 90 days
**Tier 3** (quality): Description ≥200 chars + technical keyword presence

**Metrics Tracking**: All scrapers report `tier1_filtered`, `tier2_skipped`, `tier3_filtered`

## Developer Workflows

### Running Scrapers
```bash
# LinkedIn scraper (requires cookies from linkedin_login.py)
python src/scraper.py

# Seek scraper (no auth needed)
python src/seek_scraper.py

# Complete workflow with all phases
python run_complete_workflow.py
```

### Authentication Setup
```bash
# LinkedIn: One-time manual login to save cookies
python linkedin_login.py  # Interactive browser login

# Seek: One-time manual login
python seek_login.py

# Verify session validity
python -c "from src.scraper import create_driver, load_cookies, is_logged_in; \
driver = create_driver(headless=True); load_cookies(driver); \
print('✅ Valid' if is_logged_in(driver) else '❌ Expired'); driver.quit()"
```

### Keyword Regeneration (Automatic)
```python
# src/main.py checks jobs.txt hash on each run
jobs_txt_hash = calculate_jobs_txt_hash()
if jobs_txt_hash != get_last_jobs_txt_hash():
    generate_keywords()  # Updates generated_keywords.json
    generate_search_urls()  # Updates generated_search_urls.json
```

### Smart Rescore (Automatic)
```python
# Triggered when profile.txt changes
# Rescores jobs scoring 70-79% from last 7 days
# Configured in config.json:
"rescore_threshold_min": 70,
"rescore_threshold_max": 79,
"rescore_max_age_days": 7
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
# Test single LinkedIn URL (3 pages)
python test_debug_pagination.py

# Test 6 different search URLs
python test_6_urls.py

# Score unscored jobs only
python run_scoring.py
```

### Database Inspection
```bash
# Check all jobs with scores
python -c "import sys; sys.path.insert(0, 'src'); \
import database as db; jobs = db.get_all_jobs(); \
print(f'Total: {len(jobs)}'); \
[print(f'{j[\"score\"]}% - {j[\"title\"]}') for j in sorted(jobs, key=lambda x: x.get('score',0), reverse=True)[:10]]"

# Check database size
ls -lh data/jobs.db
```

### Common Issues

**Scraper returns 0 jobs**:
1. Check LinkedIn session: `python linkedin_login.py`
2. Verify selectors in [SYSTEM_STATUS.md](SYSTEM_STATUS.md#verified-working-components)
3. Check Tier 1 filtering isn't too aggressive (`generated_keywords.json`)

**AI scoring fails**:
- Check OpenRouter API key in `config.json`
- Verify model names match OpenRouter catalog
- Parser-filter fallback will activate (score=0% for mismatches)

**Dashboard shows "No jobs"**:
- Check `data/jobs.db` exists: `ls -lh data/jobs.db`
- Verify jobs in DB: `python -c "import sys; sys.path.insert(0, 'src'); import database; print(len(database.get_all_jobs()))"`

## Integration Points

### OpenRouter API ([src/scorer.py](src/scorer.py))
```python
# POST to https://openrouter.ai/api/v1/chat/completions
headers = {
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Job Scraper"
}
```

### Email Notifications ([src/notifier.py](src/notifier.py))
- Gmail SMTP with app password (NOT regular password)
- HTML email template: `templates/notification.html`
- 3 retry attempts with exponential backoff
- Fallback: Save HTML to `data/notifications/` and auto-open in browser

### External Dependencies
- Selenium WebDriver (Chrome): Auto-downloads chromedriver
- OpenRouter: Primary AI scoring (paid but cheap)
- Brave Search API: Unused currently (can be added for job discovery)

## Critical "Do Not Break" Rules

1. **Never modify LinkedIn selectors** without verifying in [SYSTEM_STATUS.md](SYSTEM_STATUS.md) - they're battle-tested
2. **Don't bypass 3-tier optimization** - it's integral to scraper performance
3. **Don't re-score parser-filter jobs** - they failed regex checks for good reason
4. **Always use Perth timezone** functions from `database.py`
5. **Don't change job_hash algorithm** - would break deduplication for existing jobs
6. **Preserve model fallback chain** - primary fails often, fallbacks are essential

## Multi-Tenant Future Considerations

See [ARCHITECTURE.md](ARCHITECTURE.md) for planned SaaS architecture. Current design keeps user data in separate SQLite DB to simplify migration to PostgreSQL multi-tenant setup later.

**Current User Isolation**:
- Single `jobs.db` per instance
- `profile.txt` and `jobs.txt` at root level
- Future: `users/user_001/` structure

## Quick Reference Commands

```bash
# Full workflow (scrape → score → notify)
python src/main.py

# Generate keywords from jobs.txt
python src/keyword_generator.py

# Generate LinkedIn search URLs
python src/url_generator.py

# Start dashboard
python src/dashboard.py

# Complete workflow with metrics
python run_complete_workflow.py
```
