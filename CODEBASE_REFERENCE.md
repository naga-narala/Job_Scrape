# 🔍 JOB SCRAPER CODEBASE REFERENCE
**Complete Function & Workflow Documentation**  
*Version: 2026-02-05*

---

## 📋 TABLE OF CONTENTS

1. [System Overview](#system-overview)
2. [Complete Workflow](#complete-workflow)
3. [Core Modules](#core-modules)
4. [File Structure](#file-structure)
5. [Function Inventory](#function-inventory)
6. [Database Schema](#database-schema)
7. [Configuration Files](#configuration-files)
8. [Integration Points](#integration-points)

---

## 🎯 SYSTEM OVERVIEW

### Purpose
Multi-source job scraper that fetches jobs from LinkedIn, Seek, and Jora, scores them with AI, applies 3-tier optimization, and presents results via dashboard.

### Key Features
- **Multi-source scraping**: LinkedIn (Selenium), Seek (requests), Jora (Selenium)
- **3-Tier Optimization**: Title filtering, Description quality, Deduplication
- **AI Scoring**: LLM-based job matching with fallback models
- **Smart Rescore**: Auto-rescore on profile changes
- **Auto-keyword generation**: Updates keywords when jobs.txt changes
- **Dashboard**: Flask-based web UI with reject functionality
- **Email notifications**: HTML email alerts for high-scoring jobs

### Technology Stack
- **Scraping**: Selenium WebDriver, Requests, BeautifulSoup4
- **Database**: SQLite3
- **AI**: OpenRouter API (Claude, GPT-4, Llama)
- **Web**: Flask
- **Scheduling**: schedule library
- **Parser**: Custom regex-based job description parser

---

## 🔄 COMPLETE WORKFLOW

### Daily Execution Flow (main.py → run_daily_job)

```
START
  │
  ├─[Step 0]─► Check if jobs.txt changed
  │            └─► If yes: Regenerate keywords (keyword_generator.py)
  │                       └─► Save to generated_keywords.json
  │
  ├─[Step 1]─► Detect profile.txt changes (rescore_manager.py)
  │            └─► If changed: Smart rescore jobs (40-85% range)
  │                           └─► Update scores in database
  │
  ├─[Step 2]─► Load search URLs from generated_search_urls.json
  │            │
  │            ├─► LINKEDIN: scraper.fetch_all_jobs()
  │            │    ├─► Selenium WebDriver + cookies
  │            │    ├─► Tier 1: Title pre-screening
  │            │    ├─► Extract: title, company, location, description
  │            │    ├─► Extract requirement_text from "Qualifications" section
  │            │    └─► Return jobs with source='linkedin'
  │            │
  │            ├─► SEEK: SeekScraper.search_jobs()
  │            │    ├─► HTTP requests + BeautifulSoup
  │            │    ├─► Build URL: /keyword-jobs/in-Location
  │            │    ├─► Extract: title, company, location, description
  │            │    └─► Return jobs with source='seek'
  │            │
  │            └─► JORA: JoraScraper.search_jobs()
  │                 ├─► Selenium WebDriver + stealth mode
  │                 ├─► Build URL: /j?q=keyword&l=location&a=24h
  │                 ├─► Extract: title, company, location
  │                 ├─► Call get_job_details() for each job URL
  │                 ├─► Fetch full description from detail page
  │                 └─► Return jobs with source='jora'
  │
  ├─[Step 3]─► Save to database (database.py)
  │            │
  │            ├─► For each job:
  │            │    ├─► Tier 2: Description quality check
  │            │    │    └─► optimization.is_description_relevant()
  │            │    │         ├─► Check length ≥ 200 chars
  │            │    │         └─► Check technical keywords (77 keywords)
  │            │    │
  │            │    ├─► Tier 3: Deduplication check
  │            │    │    └─► optimization.should_skip_duplicate()
  │            │    │         ├─► Generate job_hash(title, company, url)
  │            │    │         └─► Check if exists in last 90 days
  │            │    │
  │            │    └─► If passes filters:
  │            │         └─► database.insert_job()
  │            │              ├─► Save to jobs table
  │            │              └─► Add to new_jobs list
  │            │
  │            └─► Log optimization metrics:
  │                 ├─► Tier 2 filtered count
  │                 ├─► Tier 3 duplicate count
  │                 └─► Efficiency gain %
  │
  ├─[Step 4]─► Score new jobs (scorer.py)
  │            │
  │            ├─► Load profile.txt
  │            ├─► Load generated_keywords.json
  │            ├─► Build dynamic prompt with keywords
  │            │
  │            ├─► For each unscored job:
  │            │    │
  │            │    ├─► Try primary model (Claude)
  │            │    │    └─► scorer.call_openrouter()
  │            │    │         ├─► POST to api.openrouter.ai
  │            │    │         ├─► Include profile + job description
  │            │    │         └─► Request structured JSON response
  │            │    │
  │            │    ├─► If fails: Try secondary model (GPT-4)
  │            │    ├─► If fails: Try tertiary model (Llama-70B)
  │            │    │
  │            │    ├─► Parse response:
  │            │    │    └─► scorer.parse_score_response()
  │            │    │         ├─► Extract score (0-100)
  │            │    │         ├─► Extract matched_requirements[]
  │            │    │         ├─► Extract not_matched_requirements[]
  │            │    │         └─► Extract key_points[]
  │            │    │
  │            │    └─► database.insert_score()
  │            │         ├─► Save to scores table
  │            │         └─► Link to job_id
  │            │
  │            └─► If all models fail:
  │                 └─► Use job_parser.parse_job()
  │                      ├─► Regex-based fallback scoring
  │                      ├─► Save with model_used='parser-filter'
  │                      └─► Auto-score 0% if critical mismatches
  │
  ├─[Step 5]─► Send notifications (notifier.py)
  │            │
  │            ├─► Get jobs with score ≥ threshold (config.json)
  │            ├─► Filter: not yet notified
  │            │
  │            ├─► Build HTML email (notifier.build_email_html)
  │            │    ├─► Group by date
  │            │    ├─► Show score, title, company, location
  │            │    ├─► Add "View on Dashboard" links
  │            │    └─► Include rejection categories
  │            │
  │            ├─► Send via SMTP (notifier.send_email_notification)
  │            │    └─► Use config: smtp_server, from_email, to_email
  │            │
  │            ├─► Save HTML copy (notifier.save_html_notification)
  │            │    └─► Save to data/notifications/{date}.html
  │            │
  │            └─► database.mark_notified()
  │                 └─► Update notified=1, notified_at=now
  │
  └─[Step 6]─► Complete
               ├─► Log final statistics
               ├─► Calculate next run time (+24 hours)
               └─► Schedule next execution
END
```

---

## 🗂️ CORE MODULES

### 1. main.py (Entry Point & Orchestration)

**Purpose**: Coordinates the entire scraping workflow

**Key Functions**:

#### `run_daily_job()`
- **Called by**: Scheduler (every 24 hours) or manual execution
- **Purpose**: Main workflow orchestrator
- **Flow**:
  1. Load config.json
  2. Auto-regenerate keywords if jobs.txt changed
  3. Check for profile changes → trigger rescore
  4. Fetch jobs from LinkedIn, Seek, Jora
  5. Save to database with 3-tier filtering
  6. Score new jobs with AI
  7. Send email notifications
- **Returns**: None
- **Side effects**: Writes to database, sends emails, saves logs

#### `load_config()`
- **Purpose**: Load configuration from config.json
- **Returns**: `dict` with all config values
- **Used by**: All modules need API keys, thresholds, SMTP settings

#### `load_job_searches()`
- **Purpose**: Load search URLs from generated_search_urls.json
- **Returns**: `list[dict]` with search configurations
- **Format**: `[{id, url, source, keyword, location, enabled}, ...]`

#### `run_test_mode()`
- **Purpose**: Test with limited URLs (2 per source)
- **Used for**: Quick testing before full scrape

#### `start_daemon()`
- **Purpose**: Run as background daemon with scheduling
- **Schedule**: Every 24 hours at configured time

---

### 2. scraper.py (LinkedIn Scraper)

**Purpose**: Scrape jobs from LinkedIn using Selenium

**Key Functions**:

#### `create_driver(headless=True, use_profile=False)`
- **Purpose**: Initialize Chrome WebDriver with stealth mode
- **Parameters**:
  - `headless`: Run browser in background
  - `use_profile`: Use saved browser profile
- **Returns**: Selenium WebDriver instance
- **Features**:
  - Anti-detection (disable automation flags)
  - Custom user agent
  - Auto-install ChromeDriver

#### `load_cookies(driver)`
- **Purpose**: Load saved LinkedIn cookies from `data/linkedin_cookies.pkl`
- **Why**: Avoid login on every run
- **Used by**: `fetch_jobs_from_url()`

#### `save_cookies(driver)`
- **Purpose**: Save cookies after successful login
- **Called by**: Manual login helper

#### `manual_login_helper()`
- **Purpose**: Interactive LinkedIn login to save cookies
- **Process**:
  1. Open LinkedIn login page
  2. Wait for user to login manually
  3. Save cookies to file
  4. Instructions for future runs

#### `extract_job_from_card(card, search_config, driver, optimizer=None)`
- **Purpose**: Extract job data from LinkedIn job card element
- **Parameters**:
  - `card`: Selenium WebElement (job card)
  - `search_config`: Search metadata
  - `driver`: WebDriver instance
  - `optimizer`: OptimizationManager instance
- **Extraction process**:
  1. Click card to expand details
  2. Wait for description to load
  3. Extract title, company, location
  4. Extract full description
  5. **Extract requirement_text**: Look for "Qualifications" section
  6. Extract posted_date, employment_type
  7. Build absolute URL
- **Tier 1 filtering**:
  - If optimizer provided: Check title keywords
  - Skip if title doesn't match 37 title keywords
- **Returns**: `dict` or `None` if filtered
- **Format**:
```python
{
    'title': str,
    'company': str,
    'location': str,
    'description': str,
    'requirement_text': str,  # NEW: Separate requirements section
    'url': str,
    'posted_date': str,
    'employment_type': str,
    'source': 'linkedin',
    'source_search_id': str
}
```

#### `fetch_jobs_from_url(url, search_config, driver, max_pages=3)`
- **Purpose**: Scrape multiple pages from single LinkedIn search URL
- **Parameters**:
  - `url`: LinkedIn search URL
  - `search_config`: Search metadata
  - `driver`: WebDriver instance
  - `max_pages`: Max pages to scrape (default 3)
- **Process**:
  1. Load page with cookies
  2. Wait for job cards to render
  3. Scroll to load all cards
  4. Find all job card elements
  5. For each card: Call `extract_job_from_card()`
  6. Try to navigate to next page
  7. Repeat until max_pages or no more results
- **Optimization**: Uses Tier 1 title filtering
- **Returns**: `list[dict]` of jobs
- **Logs**: 3-tier optimization metrics

#### `fetch_all_jobs(searches, api_key=None, headless=True, max_pages=3)`
- **Purpose**: Scrape all LinkedIn searches in list
- **Parameters**:
  - `searches`: List of search configs
  - `api_key`: (unused, legacy)
  - `headless`: Run browser in background
  - `max_pages`: Pages per search
- **Process**:
  1. Initialize driver once
  2. Load cookies
  3. For each search: Call `fetch_jobs_from_url()`
  4. Aggregate all jobs
  5. Close driver
- **Returns**: `(jobs_list, strategy_stats)`
- **Used by**: `main.run_daily_job()`

---

### 3. seek_scraper.py (Seek Scraper)

**Purpose**: Scrape jobs from Seek.com.au using HTTP requests

**Key Class**: `SeekScraper`

#### `__init__(self, cookies=None, delay_range=(2, 5))`
- **Purpose**: Initialize scraper with session
- **Parameters**:
  - `cookies`: Optional browser cookies
  - `delay_range`: Random delay between requests (anti-bot)
- **Sets up**: Requests session with browser headers

#### `search_jobs(keyword, location, max_results=50)`
- **Purpose**: Search Seek for jobs
- **Parameters**:
  - `keyword`: Job search term
  - `location`: City/region
  - `max_results`: Max jobs to fetch
- **URL format**: `https://www.seek.com.au/{keyword}-jobs/in-All-{location}?daterange=1`
- **Process**:
  1. Build search URL
  2. Make HTTP GET request
  3. Parse HTML with BeautifulSoup
  4. Find job cards
  5. For each card: Call `_extract_job_from_card()`
- **Returns**: `list[dict]` of jobs

#### `_extract_job_from_card(card)`
- **Purpose**: Extract job data from Seek HTML element
- **Extraction**:
  - Title from `<h3>` or `<a>` tag
  - Company from metadata
  - Location from metadata
  - Description from summary (NOT full description)
  - URL from href attribute
- **Returns**: Job dict with `source='seek'`

#### `scrape_jobs_from_url(url, max_jobs=50)`
- **Purpose**: Scrape from direct Seek URL
- **Used by**: Test scripts
- **Returns**: Job list

---

### 4. jora_scraper.py (Jora Scraper)

**Purpose**: Scrape jobs from Jora.com using Selenium

**Key Class**: `JoraScraper`

#### `__init__(self, headless=True)`
- **Purpose**: Initialize Jora scraper
- **Parameters**:
  - `headless`: Run Chrome in background
- **Setup**: Chrome with stealth mode (anti-detection)

#### `_init_driver()`
- **Purpose**: Create WebDriver with stealth plugins
- **Features**:
  - Selenium-stealth to bypass bot detection
  - Custom user agent
  - Randomized viewport size

#### `search_jobs(keyword, location="Perth WA", time_filter="24h", max_results=50)`
- **Purpose**: Search Jora for jobs
- **Parameters**:
  - `keyword`: Search term
  - `location`: City + state
  - `time_filter`: "24h", "3d", "7d", "14d"
  - `max_results`: Max jobs to return
- **URL format**: `https://au.jora.com/j?sp=search&trigger_source=serp&a=24h&q={keyword}&l={location}`
- **Process**:
  1. Build URL with parameters
  2. Load page with Selenium
  3. Wait 8 seconds for JavaScript to render
  4. Try multiple selectors to find job cards:
     - `<article>` tags
     - `<h2>` / `<h3>` links
     - Class containing "job"
     - Data attributes
     - Links with "/job/" in href
  5. For each element: Call `_parse_job_element()`
  6. **NEW**: Call `get_job_details()` for each job URL
  7. **NEW**: Update job with full description
- **Returns**: Job list with descriptions

#### `_parse_job_element(element)`
- **Purpose**: Extract basic job info from search result
- **Extraction**:
  - Title from link text
  - Company from nearby text
  - Location from text patterns
  - URL from href
  - **OLD**: Description was hardcoded to empty
  - **NEW**: Description fetched separately
- **Returns**: Job dict (without description)

#### `get_job_details(job_url)` 
- **Purpose**: Fetch full description from job detail page
- **Parameters**: `job_url` - Full URL to job posting
- **Process**:
  1. Navigate to job URL
  2. Wait for description element
  3. Find description container (CSS: `div[class*='description']`)
  4. Extract text content
- **Returns**: Description string or None
- **Called by**: `search_jobs()` (NEW - was unused before)

#### `close()`
- **Purpose**: Clean up WebDriver
- **Called by**: Context manager `__exit__`

#### `__enter__` / `__exit__`
- **Purpose**: Context manager support
- **Usage**: `with JoraScraper() as scraper:`

---

### 5. database.py (SQLite Database Layer)

**Purpose**: All database operations for jobs, scores, notifications

**Key Functions**:

#### `init_database()`
- **Purpose**: Create all tables if not exist
- **Tables created**:
  - `jobs` - Job listings
  - `scores` - AI scores for jobs
  - `notifications` - Email notification log
  - `profile_changes` - Profile version history
  - `rejections` - Rejected job tracking (NEW)
- **Migrations**: Adds new columns if missing

#### `insert_job(job_data)`
- **Purpose**: Insert new job or update if exists
- **Parameters**: Job dict with all fields
- **Process**:
  1. Generate `job_id_hash` from title + company + URL
  2. Check if job exists (by hash)
  3. If exists: Update `last_seen_date`, keep `is_active=1`
  4. If new: Insert with all fields
- **Fields**:
  - `job_id_hash` (PK)
  - `title`, `company`, `location`
  - `description`, `requirement_text` (NEW)
  - `url`, `posted_date`, `employment_type`
  - `source` ('linkedin', 'seek', 'jora')
  - `source_search_id`
  - `scraped_date`, `last_seen_date`
  - `is_active`, `applied`, `notified`
  - `rejected`, `rejected_date` (NEW)
  - `status`, `remarks`
- **Returns**: `job_id_hash`

#### `insert_score(job_id, score_data, profile_hash)`
- **Purpose**: Save AI score for job
- **Parameters**:
  - `job_id`: job_id_hash
  - `score_data`: Dict with score, matched, not_matched, key_points, model_used
  - `profile_hash`: MD5 of profile.txt
- **Process**:
  1. Delete old score if exists
  2. Insert new score
  3. Store matched/not_matched as JSON strings
- **Fields**:
  - `job_id` (FK to jobs)
  - `score` (0-100)
  - `matched_requirements` (JSON array)
  - `not_matched_requirements` (JSON array)
  - `key_points` (JSON array)
  - `model_used` (e.g., 'claude-3.5-sonnet')
  - `profile_hash` (track which profile version)
  - `scored_date`

#### `get_unscored_jobs()`
- **Purpose**: Get jobs that need scoring
- **Returns**: Jobs without entry in scores table
- **Used by**: Scoring workflow

#### `get_all_jobs(include_inactive=False)`
- **Purpose**: Get all jobs with scores
- **Returns**: List of dicts with job + score merged
- **SQL**: LEFT JOIN jobs with scores
- **Filters**: Only active jobs unless `include_inactive=True`

#### `get_high_scoring_unnotified(threshold)`
- **Purpose**: Get jobs for email notification
- **Parameters**: `threshold` - Min score (e.g., 70)
- **Returns**: Jobs with `score >= threshold AND notified = 0`

#### `mark_notified(job_id, notification_type, status)`
- **Purpose**: Mark job as notified
- **Updates**: `notified=1`, `notified_at=now`, `notification_type`

#### `reject_job(job_id, rejection_category, rejection_notes='')` (NEW)
- **Purpose**: Mark job as rejected
- **Parameters**:
  - `job_id`: job_id_hash
  - `rejection_category`: Reason for rejection
  - `rejection_notes`: Optional notes
- **Process**:
  1. Update jobs: `rejected=1`, `rejected_date=now`
  2. Insert into rejections table
- **Categories**: From dashboard UI (e.g., "Low Salary", "Wrong Tech Stack")

#### `get_rejected_jobs()` (NEW)
- **Purpose**: Get all rejected jobs with reasons
- **Returns**: Jobs with rejection_category, rejection_notes

#### `get_rejection_stats()` (NEW)
- **Purpose**: Get count by rejection category
- **Returns**: `[{category, count}, ...]`
- **Used by**: Dashboard stats page

#### `get_jobs_for_rescore(min_score, max_score, max_age_days, exclude_profile_hash)`
- **Purpose**: Find jobs eligible for smart rescore
- **Filters**:
  - Score in range (e.g., 40-85%)
  - Scraped within last N days
  - Not scored with current profile
- **Used by**: `rescore_manager.trigger_smart_rescore()`

#### `delete_score(job_id)`
- **Purpose**: Remove old score before rescoring
- **Used by**: Rescore workflow

#### `get_profile_hash()` / `get_last_profile_hash()`
- **Purpose**: Track profile.txt changes
- **Returns**: MD5 hash of profile.txt
- **Used by**: Rescore detection

#### `insert_profile_change(profile_hash)`
- **Purpose**: Log profile change event
- **Stores**: hash, changed_at timestamp

---

### 6. scorer.py (AI Scoring Engine)

**Purpose**: Score jobs using LLM APIs with fallback strategy

**Key Functions**:

#### `load_keywords()`
- **Purpose**: Load keywords from generated_keywords.json
- **Returns**: Dict with title_keywords, technical_skills, strong_keywords
- **Used by**: Prompt building

#### `load_jobs_txt_metadata()`
- **Purpose**: Load original jobs.txt for context
- **Returns**: Dict with target_roles, location, work_type
- **Used by**: Prompt building

#### `build_dynamic_prompt_template()`
- **Purpose**: Create scoring prompt with loaded keywords
- **Returns**: Jinja2 template string
- **Includes**:
  - Profile content
  - Job description
  - Keywords to check
  - Expected JSON output format
  - Scoring criteria

#### `load_profile()`
- **Purpose**: Load user profile from profile.txt
- **Returns**: Profile text content
- **Used by**: All scoring functions

#### `build_prompt(job, profile_content)`
- **Purpose**: Build complete scoring prompt for single job
- **Parameters**:
  - `job`: Job dict
  - `profile_content`: User profile text
- **Returns**: Complete prompt string with job + profile
- **Template**: Uses `build_dynamic_prompt_template()`

#### `call_openrouter(model, prompt, api_key, max_tokens=500)`
- **Purpose**: Call OpenRouter API with specific model
- **Parameters**:
  - `model`: Model identifier (e.g., 'anthropic/claude-3.5-sonnet')
  - `prompt`: Complete scoring prompt
  - `api_key`: OpenRouter API key
  - `max_tokens`: Response length limit
- **API**: `POST https://openrouter.ai/api/v1/chat/completions`
- **Returns**: Response text
- **Errors**: Raises `RateLimitError`, `ModelUnavailableError`, `ScoringError`

#### `parse_score_response(response_content)`
- **Purpose**: Extract structured data from LLM response
- **Parsing strategies**:
  1. Try JSON.parse() on full response
  2. Extract JSON from markdown code blocks
  3. Find JSON object with regex
  4. Manual field extraction with regex
- **Returns**: Dict with:
  - `score`: 0-100
  - `matched_requirements`: List of strings
  - `not_matched_requirements`: List of strings
  - `key_points`: List of strings
- **Fallback**: Returns None if parsing fails

#### `score_job_with_fallback(job, profile_content, models_config, api_key)`
- **Purpose**: Score single job with model fallback chain
- **Parameters**:
  - `job`: Job dict
  - `profile_content`: Profile text
  - `models_config`: Model priority list from config.json
  - `api_key`: OpenRouter API key
- **Fallback chain**:
  1. Try primary model (claude-3.5-sonnet)
  2. If rate limit: Wait and retry
  3. If model unavailable: Try secondary (gpt-4-turbo)
  4. If fails: Try tertiary (meta-llama/llama-3.1-70b)
  5. If all fail: Use parser-based fallback
- **Parser fallback**: `job_parser.parse_job()`
  - Regex-based keyword matching
  - Auto-score 0% if critical mismatches
  - Save with `model_used='parser-filter'`
- **Returns**: Score dict or None

#### `score_batch(jobs, profile_content, models_config, api_key)`
- **Purpose**: Score list of jobs
- **Process**:
  1. For each job: Call `score_job_with_fallback()`
  2. Collect results
  3. Log success/failure stats
- **Returns**: List of (job_id, score_data) tuples
- **Used by**: `main.run_daily_job()`

---

### 7. job_parser.py (Fallback Parser)

**Purpose**: Regex-based job parsing when AI scoring fails

**Key Class**: `JobDescriptionParser`

#### `parse_job(description, title="", location="")` (Static method)
- **Purpose**: Parse job using regex patterns
- **Parameters**:
  - `description`: Job description text
  - `title`: Job title
  - `location`: Job location
- **Process**:
  1. Check for critical exclusions:
     - "no sponsorship" → auto-reject (score 0)
     - "senior", "lead", "principal" in title → auto-reject
     - Missing degree (if required)
  2. Match required skills (Python, Machine Learning, etc.)
  3. Match preferred skills
  4. Calculate score based on matches
  5. Build matched/not_matched lists
- **Returns**: Dict with:
  - `score`: 0-100
  - `matched_requirements`: List
  - `not_matched_requirements`: List
  - `key_points`: List
  - `model_used`: 'parser-filter'
- **Used by**: `scorer.score_job_with_fallback()` as final fallback

---

### 8. optimization.py (3-Tier Filtering)

**Purpose**: Pre-filter jobs before full scraping/scoring

**Key Class**: `OptimizationManager`

#### `__init__(config=None)`
- **Purpose**: Initialize with config and keywords
- **Loads**: generated_keywords.json
- **Extracts**:
  - `title_keywords` (37 keywords) - For Tier 1
  - `technical_skills` (77 keywords) - For Tier 2
  - `strong_keywords` (25 keywords) - For Tier 2

#### `is_title_relevant(title)` - **TIER 1**
- **Purpose**: Pre-screen by job title
- **Check**: Does title contain any of 37 title keywords?
- **Keywords**: "engineer", "developer", "scientist", "analyst", "graduate", "junior", "ai", "machine learning", etc.
- **Returns**: `(bool, str)` - (passes, reason)
- **Used by**: `scraper.extract_job_from_card()` during scraping
- **Benefit**: Skip API calls for irrelevant jobs

#### `is_description_relevant(description, title)` - **TIER 2**
- **Purpose**: Check description quality
- **Checks**:
  1. Length ≥ 200 characters (too short = low quality)
  2. Contains at least 1 technical keyword from 77 keywords
  3. Contains at least 1 strong keyword from 25 keywords
- **Returns**: `(bool, str)` - (passes, reason)
- **Used by**: `main.run_daily_job()` before saving to database
- **Benefit**: Reject low-quality or generic job posts

#### `should_skip_duplicate(job_hash, db_conn)` - **TIER 3**
- **Purpose**: Check for duplicate in last 90 days
- **Check**: Is job_hash already in database?
- **Window**: Last 90 days (configurable)
- **Returns**: `(bool, str)` - (should_skip, reason)
- **Used by**: `main.run_daily_job()` before inserting
- **Benefit**: Avoid re-processing same jobs

---

### 9. keyword_generator.py (Auto Keyword Generation)

**Purpose**: Generate search keywords from jobs.txt

**Key Class**: `KeywordGenerator`

#### `__init__()`
- **Purpose**: Initialize with paths
- **Paths**:
  - `jobs_file`: jobs.txt
  - `output_file`: generated_keywords.json
  - `hash_file`: .jobs_txt_hash (track changes)

#### `needs_regeneration()`
- **Purpose**: Check if jobs.txt changed
- **Process**:
  1. Calculate MD5 hash of jobs.txt
  2. Compare with saved hash in .jobs_txt_hash
  3. Return True if different
- **Used by**: `main.run_daily_job()` Step 0

#### `generate_keywords()`
- **Purpose**: Generate keywords from jobs.txt
- **Process**:
  1. Parse jobs.txt for role names
  2. Build keyword variations:
     - Title keywords (base roles)
     - Technical skills (from description patterns)
     - Strong keywords (critical terms)
     - Location keywords
  3. Save to generated_keywords.json
  4. Save hash to .jobs_txt_hash
- **Returns**: Dict with all keyword lists
- **Format**:
```json
{
  "title_keywords": ["engineer", "developer", ...],
  "technical_skills": ["python", "tensorflow", ...],
  "strong_keywords": ["ai", "machine learning", ...],
  "locations": ["perth", "melbourne", ...]
}
```
- **Called by**: `main.run_daily_job()` if needs_regeneration()

---

### 10. url_generator.py (Search URL Generator)

**Purpose**: Generate search URLs for all platforms

**Key Class**: `URLGenerator`

#### `__init__(config_path='config.json')`
- **Purpose**: Load config and keywords
- **Loads**:
  - config.json (platform settings)
  - generated_keywords.json (search terms)

#### `generate_linkedin_urls()`
- **Purpose**: Build LinkedIn search URLs
- **Format**: `https://www.linkedin.com/jobs/search/?keywords={keyword}&geoId={geo_id}&f_TPR=r86400`
- **Parameters**:
  - `keywords`: From generated_keywords.json
  - `geoId`: Australia = 101452733
  - `f_TPR`: Time filter (r86400 = last 24 hours)
- **Returns**: List of URL dicts

#### `generate_seek_urls()`
- **Purpose**: Build Seek search URLs
- **Format**: `https://www.seek.com.au/{keyword}-jobs/in-All-{location}?daterange=1`
- **Parameters**:
  - `keyword`: URL-encoded keyword
  - `location`: Perth, Melbourne, etc.
  - `daterange=1`: Last 24 hours
- **Returns**: List of URL dicts

#### `generate_jora_urls()`
- **Purpose**: Build Jora search URLs
- **Format**: `https://au.jora.com/j?sp=search&trigger_source=serp&a=24h&q={keyword}&l={location}`
- **Parameters**:
  - `q`: Keyword (URL-encoded)
  - `l`: Location (e.g., "Perth WA")
  - `a`: Time filter (24h, 3d, 7d)
- **Returns**: List of URL dicts

#### `generate_all_urls()`
- **Purpose**: Generate URLs for all platforms
- **Process**:
  1. Call `generate_linkedin_urls()`
  2. Call `generate_seek_urls()`
  3. Call `generate_jora_urls()`
  4. Combine into single dict
  5. Save to generated_search_urls.json
- **Returns**: Dict `{linkedin: [...], seek: [...], jora: [...]}`
- **File format**:
```json
{
  "linkedin": [
    {
      "url": "https://...",
      "source": "linkedin",
      "keyword": "Graduate AI Engineer",
      "location": "Remote",
      "search_id": "linkedin_graduate_ai_engineer_remote"
    }
  ],
  "seek": [...],
  "jora": [...]
}
```

---

### 11. rescore_manager.py (Smart Rescore)

**Purpose**: Detect profile changes and rescore affected jobs

**Key Functions**:

#### `detect_profile_change()`
- **Purpose**: Check if profile.txt changed
- **Process**:
  1. Get current profile hash
  2. Get last profile hash from database
  3. Compare
  4. If different: Log change to profile_changes table
- **Returns**: `bool` - True if changed
- **Used by**: `main.run_daily_job()` Step 1

#### `trigger_smart_rescore(profile_content, config)`
- **Purpose**: Rescore jobs affected by profile change
- **Parameters**:
  - `profile_content`: New profile text
  - `config`: Config dict with API keys, models
- **Process**:
  1. Get jobs in 40-85% score range (borderline jobs)
  2. Filter: Scraped in last 30 days
  3. Filter: Not scored with current profile
  4. For each job:
     - Delete old score
     - Score with new profile
     - Save new score
  5. Log rescore count
- **Why 40-85%**: Jobs most likely to change with profile update
- **Returns**: Count of rescored jobs
- **Used by**: `main.run_daily_job()` if profile changed

---

### 12. notifier.py (Email Notifications)

**Purpose**: Send HTML email notifications for high-scoring jobs

**Key Functions**:

#### `build_email_html(jobs, date_str)`
- **Purpose**: Build HTML email body
- **Parameters**:
  - `jobs`: List of jobs to include
  - `date_str`: Date string for header
- **Process**:
  1. Group jobs by scraped date
  2. Build HTML table with:
     - Score badge (color-coded)
     - Job title + company
     - Location
     - Key matched requirements
     - "View Details" link to dashboard
     - Rejection category dropdown
  3. Add dashboard link
  4. Style with inline CSS
- **Returns**: HTML string

#### `send_email_notification(jobs, config)`
- **Purpose**: Send email via SMTP
- **Parameters**:
  - `jobs`: Jobs to notify about
  - `config`: Config with SMTP settings
- **Process**:
  1. Build HTML with `build_email_html()`
  2. Create MIME message
  3. Connect to SMTP server
  4. Send email
  5. Mark jobs as notified in database
- **Config needed**:
  - `smtp_server`, `smtp_port`
  - `from_email`, `to_email`
  - `smtp_username`, `smtp_password`
- **Returns**: Success boolean

#### `save_html_notification(jobs)`
- **Purpose**: Save HTML copy of notification
- **File**: `data/notifications/{date}.html`
- **Used for**: Backup, debugging, manual review

#### `notify_new_matches(config)`
- **Purpose**: Main notification workflow
- **Process**:
  1. Get threshold from config (e.g., 70%)
  2. Get unnotified jobs above threshold
  3. If jobs found:
     - Build and send email
     - Save HTML copy
     - Mark as notified
- **Called by**: `main.run_daily_job()` Step 5

---

### 13. dashboard.py (Web UI)

**Purpose**: Flask web interface for viewing and managing jobs

**Key Routes**:

#### `GET /` → `index()`
- **Purpose**: Main dashboard page
- **Shows**:
  - Jobs from last 7 days
  - Sorted by score (high to low)
  - Grouped by date
  - Color-coded score badges
  - Source badges (LinkedIn/Seek/Jora)
- **Template**: templates/dashboard.html
- **Features**:
  - Filter by score threshold (slider)
  - Pagination
  - Reject button modal (NEW)

#### `GET /all` → `show_all()`
- **Purpose**: Show all jobs (no date filter)
- **Same as**: index() but no 7-day limit

#### `GET /stats` → `stats()`
- **Purpose**: Statistics page
- **Shows**:
  - Total jobs count
  - Jobs above threshold
  - Average score
  - Top companies
  - Score distribution chart
  - Rejection statistics (NEW)
- **Template**: templates/stats.html

#### `GET /applied` → `applied_jobs()`
- **Purpose**: Show jobs marked as applied
- **Filters**: `applied = 1`

#### `POST /mark_applied/<job_id>` → `mark_applied(job_id)`
- **Purpose**: Mark job as applied
- **Updates**: `applied = 1`
- **Returns**: JSON success

#### `POST /update_status/<job_id>` → `update_status(job_id)`
- **Purpose**: Update job status
- **Body**: `{status: str, remarks: str}`
- **Updates**: jobs.status, jobs.remarks

#### `POST /reject/<job_id>` → `reject_job_route(job_id)` (NEW)
- **Purpose**: Mark job as rejected
- **Body**: `{category: str, notes: str}`
- **Process**:
  1. Call `database.reject_job()`
  2. Update `rejected=1`, `rejected_date=now`
  3. Insert rejection record
- **Returns**: JSON success
- **Categories**: From form (Low Salary, Wrong Stack, etc.)

#### `POST /rescore/<job_id>` → `rescore_job(job_id)`
- **Purpose**: Manually rescore single job
- **Process**:
  1. Load job from database
  2. Load profile
  3. Score with AI
  4. Save new score
- **Returns**: JSON with new score

---

## 📊 DATABASE SCHEMA

### Table: `jobs`
```sql
CREATE TABLE jobs (
    job_id_hash TEXT PRIMARY KEY,      -- MD5(title + company + url)
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    requirement_text TEXT,              -- NEW: Separate requirements section
    url TEXT,
    posted_date TEXT,
    employment_type TEXT,
    source TEXT,                        -- 'linkedin', 'seek', 'jora'
    source_search_id TEXT,
    scraped_date DATE,
    last_seen_date DATE,
    is_active BOOLEAN DEFAULT 1,
    applied BOOLEAN DEFAULT 0,
    notified BOOLEAN DEFAULT 0,
    notified_at TEXT,
    notification_type TEXT,
    rejected BOOLEAN DEFAULT 0,         -- NEW: Rejection flag
    rejected_date DATE,                 -- NEW: When rejected
    status TEXT,
    remarks TEXT
);
```

### Table: `scores`
```sql
CREATE TABLE scores (
    job_id TEXT PRIMARY KEY,
    score INTEGER,                      -- 0-100
    matched_requirements TEXT,          -- JSON array
    not_matched_requirements TEXT,      -- JSON array
    key_points TEXT,                    -- JSON array
    model_used TEXT,                    -- e.g., 'claude-3.5-sonnet'
    profile_hash TEXT,                  -- MD5 of profile.txt
    scored_date DATE,
    FOREIGN KEY(job_id) REFERENCES jobs(job_id_hash)
);
```

### Table: `rejections` (NEW)
```sql
CREATE TABLE rejections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    rejection_category TEXT NOT NULL,   -- Reason for rejection
    rejection_notes TEXT,               -- Optional notes
    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(job_id_hash)
);
```

### Table: `notifications`
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    notification_type TEXT,
    status TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES jobs(job_id_hash)
);
```

### Table: `profile_changes`
```sql
CREATE TABLE profile_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_hash TEXT UNIQUE,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚙️ CONFIGURATION FILES

### config.json
```json
{
  "api_key": "sk-or-...",              // OpenRouter API key
  "models": {
    "primary": "anthropic/claude-3.5-sonnet",
    "secondary": "openai/gpt-4-turbo",
    "tertiary": "meta-llama/llama-3.1-70b-instruct"
  },
  "notification_threshold": 70,        // Min score for email
  "rescore_threshold_min": 40,         // Smart rescore range
  "rescore_threshold_max": 85,
  "rescore_max_age_days": 30,
  "linkedin_max_pages": 3,             // Pages per search
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "from_email": "user@gmail.com",
  "to_email": "user@gmail.com",
  "smtp_username": "user@gmail.com",
  "smtp_password": "app_password",
  "optimization": {                    // 3-tier settings
    "enabled": true,
    "tier1_title_filter": true,
    "tier2_description_filter": true,
    "tier3_deduplication": true,
    "min_description_length": 200,
    "dedup_window_days": 90
  }
}
```

### jobs.txt
```
Graduate AI Engineer
Junior Machine Learning Engineer
Data Scientist
AI Research Assistant
...
```
- **Purpose**: Define target job roles
- **Used by**: keyword_generator.py
- **Hash tracked**: Auto-regenerate keywords on change

### generated_keywords.json
```json
{
  "title_keywords": ["engineer", "developer", "scientist", ...],
  "technical_skills": ["python", "tensorflow", "pytorch", ...],
  "strong_keywords": ["ai", "machine learning", "deep learning", ...],
  "locations": ["perth", "melbourne", "sydney", ...]
}
```
- **Generated by**: keyword_generator.py
- **Used by**: Optimizer, scorer, URL generator

### generated_search_urls.json
```json
{
  "linkedin": [{url, source, keyword, location, search_id}, ...],
  "seek": [...],
  "jora": [...]
}
```
- **Generated by**: url_generator.py
- **Used by**: main.load_job_searches()

### profile.txt
```
I am a recent graduate with a degree in Computer Science...
Skills: Python, TensorFlow, PyTorch, Machine Learning...
```
- **Purpose**: User profile for AI scoring
- **Hash tracked**: Triggers smart rescore on change

---

## 🔗 INTEGRATION POINTS

### External APIs

1. **OpenRouter API**
   - **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
   - **Used by**: scorer.py
   - **Purpose**: AI job scoring
   - **Models**: Claude, GPT-4, Llama
   - **Fallback chain**: Primary → Secondary → Tertiary → Parser

2. **LinkedIn** (via Selenium)
   - **URL**: `https://www.linkedin.com/jobs/search/`
   - **Auth**: Cookies saved in `data/linkedin_cookies.pkl`
   - **Rate limit**: Managed by delays and page limits

3. **Seek** (via HTTP)
   - **URL**: `https://www.seek.com.au/`
   - **Auth**: None (public search)
   - **Rate limit**: Random delays (2-5 seconds)

4. **Jora** (via Selenium)
   - **URL**: `https://au.jora.com/`
   - **Auth**: None
   - **Anti-bot**: Selenium-stealth plugin

### File System

1. **Database**: `data/jobs.db` (SQLite3)
2. **Logs**: `data/logs/job_scraper.log`
3. **Cookies**: `data/linkedin_cookies.pkl`
4. **Notifications**: `data/notifications/{date}.html`
5. **Keywords**: `generated_keywords.json`
6. **URLs**: `generated_search_urls.json`
7. **Profile**: `profile.txt`
8. **Config**: `config.json`

### Scheduler

- **Library**: `schedule`
- **Frequency**: Every 24 hours
- **Time**: Configured in main.py (default: 9 AM Perth time)
- **Mode**: Daemon background process

---

## 🎯 WORKFLOW DECISION TREE

### When to Use Each Function

**Need to scrape LinkedIn jobs?**
→ `scraper.fetch_all_jobs(searches, ...)`
  ├─ For single URL: `fetch_jobs_from_url(url, ...)`
  └─ For single job card: `extract_job_from_card(card, ...)`

**Need to scrape Seek jobs?**
→ `SeekScraper().search_jobs(keyword, location)`
  └─ For single card: `_extract_job_from_card(card)`

**Need to scrape Jora jobs?**
→ `JoraScraper().search_jobs(keyword, location)`
  ├─ For single element: `_parse_job_element(element)`
  └─ For description: `get_job_details(url)`

**Need to save jobs to database?**
→ `database.insert_job(job_data)`
  ├─ Check first: `optimization.is_description_relevant(desc, title)`
  └─ Check first: `optimization.should_skip_duplicate(hash, conn)`

**Need to score a job?**
→ `scorer.score_job_with_fallback(job, profile, models, api_key)`
  ├─ Build prompt: `build_prompt(job, profile)`
  ├─ Call API: `call_openrouter(model, prompt, key)`
  ├─ Parse: `parse_score_response(response)`
  └─ Fallback: `job_parser.parse_job(desc, title, loc)`

**Need to rescore jobs?**
→ `rescore_manager.trigger_smart_rescore(profile, config)`
  ├─ Check first: `detect_profile_change()`
  └─ Find jobs: `database.get_jobs_for_rescore(min, max, days, hash)`

**Need to send notifications?**
→ `notifier.notify_new_matches(config)`
  ├─ Get jobs: `database.get_high_scoring_unnotified(threshold)`
  ├─ Build HTML: `build_email_html(jobs, date)`
  ├─ Send: `send_email_notification(jobs, config)`
  └─ Mark sent: `database.mark_notified(job_id, type, status)`

**Need to generate keywords?**
→ `keyword_generator.KeywordGenerator().generate_keywords()`
  └─ Check first: `needs_regeneration()`

**Need to generate search URLs?**
→ `url_generator.URLGenerator().generate_all_urls()`

**Need to view/manage jobs?**
→ Start dashboard: `python src/dashboard.py`
  ├─ View: Visit http://localhost:8000
  ├─ Reject: POST /reject/<job_id> with {category, notes}
  └─ Rescore: POST /rescore/<job_id>

---

## 🚫 ANTI-PATTERNS - DO NOT CREATE

### ❌ NEVER Create These (Already Exist):

1. **New Scraper Classes**
   - DON'T: Create `LinkedInScraper` class
   - USE: `scraper.fetch_all_jobs()` function

2. **New Database Functions**
   - DON'T: Create `save_job_to_db()`
   - USE: `database.insert_job()`

3. **New Scoring Functions**
   - DON'T: Create `score_with_ai()`
   - USE: `scorer.score_job_with_fallback()`

4. **New Keyword Generators**
   - DON'T: Create `generate_search_terms()`
   - USE: `keyword_generator.KeywordGenerator()`

5. **New URL Builders**
   - DON'T: Create `build_linkedin_url()`
   - USE: `url_generator.URLGenerator()`

6. **New Parsers**
   - DON'T: Create `parse_description()`
   - USE: `job_parser.parse_job()`

7. **New Optimization Checkers**
   - DON'T: Create `filter_by_title()`
   - USE: `optimization.is_title_relevant()`

8. **Duplicate Dashboard Routes**
   - DON'T: Create `/jobs/reject`
   - USE: Existing `/reject/<job_id>`

### ✅ CORRECT Pattern:

1. Check this document first
2. Find existing function that does what you need
3. Use it with correct parameters
4. If truly missing: Extend existing module, don't create new one

---

## 📝 QUICK REFERENCE CHEAT SHEET

### Most Common Operations

```python
# Scrape jobs from all sources
searches = load_job_searches()
jobs = scraper.fetch_all_jobs(searches, api_key, max_pages=3)

# Save to database with filtering
for job in jobs:
    is_relevant, reason = optimizer.is_description_relevant(job['description'], job['title'])
    if is_relevant:
        should_skip, reason = optimizer.should_skip_duplicate(job_hash, db_conn)
        if not should_skip:
            job_id = database.insert_job(job)

# Score jobs
unscored = database.get_unscored_jobs()
for job in unscored:
    score_data = scorer.score_job_with_fallback(job, profile, models, api_key)
    database.insert_score(job['job_id_hash'], score_data, profile_hash)

# Send notifications
notifier.notify_new_matches(config)

# Start dashboard
# Terminal: python src/dashboard.py
# Browser: http://localhost:8000
```

---

## 🔍 TROUBLESHOOTING GUIDE

### Problem: LinkedIn returns 0 jobs
**Solution**: Refresh cookies with `python linkedin_login.py`
**Reason**: Cookies expired, need re-login

### Problem: Jora jobs have empty descriptions
**Check**: `jora_scraper.search_jobs()` calls `get_job_details()`
**Fixed**: 2026-02-05 - Now fetches descriptions

### Problem: All jobs score 0%
**Check**: AI API key valid in config.json
**Fallback**: Using parser-filter (check `model_used` field)

### Problem: Dashboard shows 0 jobs
**Check**: Jobs have scores ≥ threshold in config.json
**Fix**: Lower `notification_threshold` or wait for scoring

### Problem: Keywords not updating
**Check**: Run `python src/keyword_generator.py` manually
**Auto**: Should trigger on jobs.txt change in main workflow

### Problem: Duplicate jobs appearing
**Check**: Tier 3 deduplication enabled in config.json
**Verify**: `optimization.should_skip_duplicate()` returning True

---

## 📅 VERSION HISTORY

### 2026-02-05 - Current Version
- ✅ All 5 IMPROVEMENTS_NEEDED.md completed
- ✅ Requirement text extraction (Issue #1)
- ✅ Reject button with categories (Issue #2)
- ✅ Multi-source support (Issue #3)
- ✅ 3-Tier optimization (Issue #4)
- ✅ Job-agnostic keywords (Issue #5)
- ✅ Jora description fetching fixed
- ✅ LinkedIn URL format fixed (geoId)
- ✅ Repository cleaned (11 files removed)

### Future Enhancements (Not Yet Implemented)
- [ ] Salary extraction from descriptions
- [ ] Job expiry tracking
- [ ] Application deadline alerts
- [ ] Interview scheduling integration
- [ ] Skills gap analysis
- [ ] Company research automation

---

## 🎓 BEST PRACTICES FOR FUTURE DEVELOPMENT

### Before Writing Code:

1. **Search this document** for existing functionality
2. **Check function inventory** for similar operations
3. **Review workflow** to understand integration points
4. **Verify database schema** before adding columns
5. **Check config.json** for existing settings

### When Adding Features:

1. **Extend existing modules** rather than creating new ones
2. **Follow naming conventions**: `verb_noun()` for functions
3. **Use existing database functions**: Don't write raw SQL
4. **Add to workflow diagram**: Update this document
5. **Test with test scripts**: Create test_*.py file

### When Debugging:

1. **Check logs**: `data/logs/job_scraper.log`
2. **Verify config**: API keys, thresholds, paths
3. **Test individual components**: Each module has `main()` function
4. **Use dashboard**: Visual debugging of data
5. **Check database**: `sqlite3 data/jobs.db`

---

## 📧 CONTACT & MAINTENANCE

**Last Updated**: 2026-02-05  
**Created By**: GitHub Copilot + User  
**Purpose**: Prevent duplicate code, ensure consistency, maintain codebase quality

**⚠️ CRITICAL**: Attach this document to every future chat session to ensure AI responses align with existing codebase architecture and avoid creating unnecessary duplicate functions or files.

---

END OF CODEBASE REFERENCE
