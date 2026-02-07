# 🤖 AI AGENT INSTRUCTIONS
**Job Scraper Project - Agent Operating Guidelines**  
**Last Updated: 7 February 2026**

---

## ⚠️ CRITICAL: READ THIS FIRST

This is a **PRODUCTION-READY, FULLY FUNCTIONAL** system. Your primary responsibility is to **PROTECT** existing functionality while helping the user extend capabilities.

### Golden Rules

1. **NEVER modify protected files without explicit user permission**
2. **ASK before changing any core functionality**
3. **TEST before deploying changes**
4. **DOCUMENT all modifications**
5. **When in doubt, ASK - never assume permission**

---

## 🎯 SYSTEM UNDERSTANDING

### What This System Does

Multi-source job scraper that:
- Scrapes jobs from LinkedIn, Seek, and Jora
- Applies 3-tier optimization filtering
- Scores jobs using AI (OpenRouter API) or fallback parser
- Stores results in SQLite database
- Presents jobs via Flask dashboard
- Sends email notifications for high-scoring matches

### Current Status: PRODUCTION READY

- ✅ LinkedIn scraper: 100% functional (25 jobs/page, 3 pages tested)
- ✅ 3-tier optimization: 30.7% efficiency gain
- ✅ Complete workflow: End-to-end verified
- ✅ Database layer: Stable and working
- ✅ AI scoring: Parser fallback operational
- 🔒 **SYSTEM LOCKED FOR PROTECTION**

---

## 🚫 PROTECTED FILES - REQUIRE PERMISSION

### Critical Files (DO NOT MODIFY without explicit approval):

1. **[src/scraper.py](src/scraper.py)** - LinkedIn scraper
   - Selectors are tuned and working perfectly
   - Pagination logic verified across 3 pages
   - Anti-detection measures effective
   - **Why protected:** 100% success rate on 75 job cards

2. **[src/optimization.py](src/optimization.py)** - 3-tier filtering
   - Tier 1: Title filtering (30.7% efficiency)
   - Tier 2: Description quality checks
   - Tier 3: Deduplication logic
   - **Why protected:** Optimized thresholds, validated keywords

3. **[src/database.py](src/database.py)** - Database operations
   - Schema is stable
   - All queries tested and functional
   - **Why protected:** Schema changes require migration plan

4. **[run_complete_workflow.py](run_complete_workflow.py)** - Workflow orchestration
   - Flow verified end-to-end
   - Uses existing functions correctly
   - **Why protected:** Working integration

5. **[test_url.json](test_url.json)** - Test configuration
   - Format validated with all required fields
   - **Why protected:** Required fields validated

### Configuration Files (Modify with caution):

- **[config.json](config.json)** - Always backup before changes
- **[profile.txt](profile.txt)** - User profile (changes trigger rescore)
- **[jobs.txt](jobs.txt)** - Job search terms (triggers keyword regeneration)

---

## ✅ APPROVED MODIFICATIONS (No Permission Needed)

### 1. New Features (As Separate Modules)
- New scrapers for other job boards
- Additional filtering tiers (Tier 4, 5)
- New dashboard features
- Analytics modules
- **Condition:** Must NOT modify existing working code

### 2. Bug Fixes (With Evidence)
- If scraper fails due to LinkedIn HTML changes
- If errors occur with documented proof
- **Condition:** Must provide error logs/screenshots

### 3. Performance Optimizations (Non-Breaking)
- Faster processing without changing logic
- Better error handling
- **Condition:** Must maintain same output

### 4. Documentation Updates
- README improvements
- Code comments
- This file (AGENT_INSTRUCTIONS.md)
- CODEBASE_REFERENCE.md updates

---

## 📋 PERMISSION REQUEST PROTOCOL

When you need to modify a protected file:

### Template:
```
❗ PERMISSION REQUIRED ❗

File to modify: [filepath]
Reason: [clear explanation]
Evidence: [error logs/screenshots if bug fix]
Proposed change: [specific changes]
Impact: [what will change]
Risk: [Low/Medium/High with justification]

May I proceed with this change? (yes/no)
```

### Example:
```
❗ PERMISSION REQUIRED ❗

File to modify: src/scraper.py
Reason: LinkedIn changed their HTML structure, job cards no longer loading
Evidence: [show error logs with "selector not found"]
Proposed change: Update selector from "li.scaffold-layout__list-item" to "li.job-card-new"
Impact: Will restore scraping functionality
Risk: Low (selector change only, maintains same logic)

May I proceed with this change? (yes/no)
```

---

## 🔍 BEFORE MAKING ANY CHANGES

### Mandatory Checklist:

1. ✅ **Identify the file** to be modified
2. ✅ **Check SYSTEM_STATUS.md** - Is it a protected file?
3. ✅ **Check this file** - Do I need permission?
4. ✅ **Justify the change** - Why is it necessary?
5. ✅ **Ask user permission** if protected
6. ✅ **Wait for approval** - Do not proceed without explicit "yes"
7. ✅ **Create backup** - Always backup before changes
8. ✅ **Test changes** - Verify functionality maintained
9. ✅ **Document change** - Update SYSTEM_STATUS.md

---

## 📚 CODEBASE KNOWLEDGE

### Core Modules & Responsibilities

1. **[src/main.py](src/main.py)** - Entry point & orchestration
   - `run_daily_job()` - Main workflow coordinator
   - `load_config()` - Configuration loader
   - `load_job_searches()` - Search URL loader

2. **[src/scraper.py](src/scraper.py)** - LinkedIn scraping (PROTECTED)
   - `create_driver()` - Chrome WebDriver with stealth
   - `fetch_jobs_from_url()` - Multi-page scraper
   - `extract_job_from_card()` - Job data extraction
   - Uses cookies from `data/linkedin_cookies.pkl`

3. **[src/seek_scraper.py](src/seek_scraper.py)** - Seek scraping
   - HTTP requests-based (not Selenium)
   - `SeekScraper.search_jobs()` - Main search method

4. **[src/jora_scraper.py](src/jora_scraper.py)** - Jora scraping
   - Selenium-based with stealth mode
   - `JoraScraper.search_jobs()` - Main search method

5. **[src/database.py](src/database.py)** - Database layer (PROTECTED)
   - `init_database()` - Table creation
   - `insert_job()` - Job insertion with deduplication
   - `insert_score()` - AI score storage
   - `get_unscored_jobs()` - Jobs needing scoring

6. **[src/scorer.py](src/scorer.py)** - AI scoring engine
   - `score_job_with_fallback()` - Multi-model fallback
   - Uses OpenRouter API (Claude, GPT-4, Llama)
   - Falls back to parser if API fails

7. **[src/job_parser.py](src/job_parser.py)** - Fallback parser
   - Regex-based scoring when AI unavailable
   - `JobDescriptionParser.parse_job()` - Pattern matching

8. **[src/optimization.py](src/optimization.py)** - 3-tier filtering (PROTECTED)
   - Tier 1: `is_title_relevant()` - Title keyword matching
   - Tier 2: `is_description_relevant()` - Description quality
   - Tier 3: `should_skip_duplicate()` - Deduplication

9. **[src/keyword_generator.py](src/keyword_generator.py)** - Keyword generation
   - Auto-generates from jobs.txt changes
   - Saves to generated_keywords.json

10. **[src/dashboard.py](src/dashboard.py)** - Flask web UI
    - Runs on port 8000
    - Shows jobs, scores, filtering

### Database Schema (SQLite)

**Tables:**
- `jobs` - Job listings (job_id_hash PK, title, company, url, description, etc.)
- `scores` - AI scores (job_id FK, score, matched_keywords, not_matched, model_used)
- `notifications` - Email tracking
- `profile_changes` - Profile modification log
- `rejections` - Rejected jobs tracking

### Configuration Files

- **[config.json](config.json)** - API keys, SMTP settings, thresholds
- **[job_searches.json](job_searches.json)** - Search URLs with metadata
- **[generated_keywords.json](generated_keywords.json)** - Auto-generated keywords
- **[profile.txt](profile.txt)** - User profile for AI matching
- **[jobs.txt](jobs.txt)** - Target job titles (triggers keyword regen)

---

## 🔄 WORKFLOW UNDERSTANDING

### Complete Workflow (run_complete_workflow.py)

1. **Load Configuration** - config.json, job_searches.json
2. **Keyword Check** - Regenerate if jobs.txt changed
3. **Profile Change** - Detect and trigger rescore if needed
4. **Scraping** - LinkedIn/Seek/Jora with Tier 1 filtering
5. **Tier 2 Filtering** - Description quality check
6. **Tier 3 Filtering** - Deduplication
7. **Database Insert** - Save jobs
8. **AI Scoring** - Score unscored jobs (with fallback)
9. **Notifications** - Email high-scoring matches

### LinkedIn Scraping Flow

```
create_driver() → load_cookies() → navigate to search URL
  → scroll to load job cards → extract each card
  → Tier 1 filter (title keywords) → click card
  → extract description → build job dict
  → next page (pagination) → repeat
```

### AI Scoring Flow with Fallback

```
Build prompt (job + profile) → Try Claude 3.5 Sonnet
  → If fail: Try GPT-4 → If fail: Try Llama
  → If all fail: Use parser fallback
  → Parse response → Save to database
```

---

## 🏗️ ARCHITECTURE PRINCIPLES

### Current: Single-User Local Application

```
/Job_Scrape/
├── jobs.txt                    # User's target roles
├── profile.txt                 # User's profile
├── config.json                 # Settings
├── generated_keywords.json     # Auto-generated
├── data/
│   └── jobs.db                # SQLite database
└── src/                       # Source code
```

### Future: Multi-Tenant SaaS (Design Awareness)

- Code uses service pattern (easy to extract)
- User-agnostic design (works for any role)
- Config-driven (no hardcoded values)
- Database-ready (SQLite → PostgreSQL migration path)

### Design Principles to Maintain

1. ✅ **Modular** - Easy to extract services
2. ✅ **User-agnostic** - Works for any job role
3. ✅ **Config-driven** - No hardcoded keywords/dealbreakers
4. ✅ **Database-ready** - Can migrate to PostgreSQL
5. ✅ **Service pattern** - Functions wrapped in services

### What to AVOID

- ❌ Hardcoded AI/ML keywords
- ❌ Hardcoded dealbreakers
- ❌ Direct file reads (use abstraction)
- ❌ Global state variables
- ❌ Platform-specific code

---

## 📊 PERFORMANCE BENCHMARKS (DO NOT DEGRADE)

### Current Metrics:

- **Scraping Speed:** ~7 minutes for 75 job cards (3 pages)
- **Success Rate:** 100% (52/52 jobs scraped successfully)
- **Filtering Efficiency:** 30.7% Tier 1 reduction
- **Quality Pass Rate:** 100% Tier 3 acceptance
- **Deduplication:** 0% false positives

### Quality Standards to Maintain:

- ✅ All 25 jobs per page captured
- ✅ Zero missed job cards
- ✅ Complete description extraction
- ✅ Accurate company/title extraction
- ✅ No duplicate filtering of new jobs

---

## 🔧 COMMON TASKS & HOW TO HANDLE

### Task: User wants to add new job board

**Approach:**
1. Create NEW file: `src/newboard_scraper.py`
2. Follow existing scraper patterns (see seek_scraper.py)
3. Do NOT modify existing scrapers
4. Add integration point in main.py (with permission)
5. Test thoroughly before suggesting integration

### Task: LinkedIn scraper stopped working

**Approach:**
1. Capture error logs
2. Check if LinkedIn changed HTML structure
3. Request permission with evidence
4. Only modify selectors/logic if approved
5. Test with test_url.json before full deployment

### Task: User wants different filtering thresholds

**Approach:**
1. Suggest config.json modification (safer)
2. If code change needed, request permission
3. Explain current thresholds (30.7% efficiency)
4. New thresholds must be justified with data

### Task: User wants to customize keywords

**Approach:**
1. Direct user to edit jobs.txt (triggers auto-regen)
2. Do NOT modify generated_keywords.json directly
3. Explain keyword generation flow
4. If they want manual override, ask permission to modify generator

### Task: Database query optimization

**Approach:**
1. Identify slow query
2. Suggest index creation (safe)
3. If schema change needed, request permission
4. Provide migration script if approved

### Task: User wants new dashboard features

**Approach:**
1. Modify dashboard.py (safe, non-protected)
2. Add new routes/templates
3. Do NOT modify database schema without permission
4. Test locally before suggesting deployment

---

## 🐛 DEBUGGING GUIDELINES

### When Scraper Fails:

1. **Check cookies first:** Session may have expired
   - Solution: Run `python linkedin_login.py`
2. **Check selectors:** LinkedIn HTML may have changed
   - Evidence: Save HTML snapshot to `/tmp/linkedin_debug.html`
   - Request permission to update selectors
3. **Check pagination:** Button selector may have changed
   - Test with test_url.json first

### When AI Scoring Fails:

1. **Check API key:** Verify in config.json
2. **Check model availability:** OpenRouter may be down
3. **Parser fallback:** Should activate automatically
4. **Rate limits:** May need to slow down requests

### When Database Errors Occur:

1. **Check schema:** Run `init_database()` to add missing columns
2. **Check disk space:** SQLite needs space for writes
3. **Check permissions:** Database file must be writable
4. **Backup first:** Always backup data/jobs.db before fixes

---

## 📝 DOCUMENTATION STANDARDS

### When Adding New Features:

1. **Update CODEBASE_REFERENCE.md** - Add function documentation
2. **Update README.md** - Add user-facing instructions
3. **Add code comments** - Explain complex logic
4. **Update this file** - If workflow changes

### When Fixing Bugs:

1. **Update SYSTEM_STATUS.md** - Log the fix
2. **Add comments** - Explain what was broken and why
3. **Update tests** - Prevent regression

---

## ✅ TESTING REQUIREMENTS

### Before Deploying Changes:

1. **Unit tests:** Test individual functions
2. **Integration tests:** Test workflow end-to-end
3. **Test with test_url.json:** Use small dataset first
4. **Manual verification:** Check dashboard shows correct data
5. **Performance test:** Ensure no degradation

### Test Files Available:

- `test_url.json` - Single URL test config
- `test_complete_workflow.py` - End-to-end workflow test
- `run_parser_scoring.py` - Parser fallback test

---

## 🔐 SECURITY CONSIDERATIONS

### API Keys & Credentials:

- **NEVER log API keys** to console or files
- **NEVER commit config.json** to git (use config.json.example)
- **NEVER expose SMTP passwords** in error messages

### Cookie Handling:

- Cookies stored in `data/linkedin_cookies.pkl`
- Must be kept secure (contains session data)
- Expires after ~30-60 days (refresh with linkedin_login.py)

---

## 💡 BEST PRACTICES

### When User Asks "Can you...":

1. **Assess impact:** Is this a protected file?
2. **Check permissions:** Do I need to ask?
3. **Suggest alternatives:** Can we achieve this without modifying core?
4. **Request permission:** If modification needed
5. **Provide backup plan:** What if change fails?

### When Implementing Changes:

1. **Start small:** Make minimal changes
2. **Test incrementally:** Don't change everything at once
3. **Document as you go:** Update docs immediately
4. **Backup critical files:** Before modifying
5. **Verify functionality:** Test before marking complete

### When Uncertain:

1. **ASK the user** - Don't guess
2. **Explain options** - Give user choice
3. **Provide context** - Why is this complex?
4. **Suggest safer path** - If one exists
5. **Wait for approval** - Don't assume

---

## 🎯 RESPONSE TEMPLATES

### When Change Requires Permission:

```
I need to modify [FILE] to [REASON]. This file is protected because [PROTECTION_REASON].

Proposed changes:
- [Change 1]
- [Change 2]

Risks: [Low/Medium/High]
Impact: [Description]

May I proceed with this modification? (yes/no)
```

### When Alternative Exists:

```
I can achieve this in two ways:

Option 1 (SAFER): [Non-protected approach]
- Pros: [Benefits]
- Cons: [Limitations]

Option 2 (REQUIRES PERMISSION): [Protected file modification]
- Pros: [Benefits]
- Cons: [Risks]

Which approach would you prefer?
```

### When Reporting Issue:

```
⚠️ Issue detected in [COMPONENT]:

Error: [Description]
Evidence: [Logs/screenshots]
Affected functionality: [What's broken]

Recommended fix: [Solution]
Requires permission: [Yes/No]

Would you like me to proceed with the fix?
```

---

## 📅 MAINTENANCE TASKS

### Regular Maintenance (User can do, no permission needed):

1. **Cookie refresh:** `python linkedin_login.py`
   - When: Session expires (LinkedIn redirects to login)
   - Frequency: Every 30-60 days

2. **Database cleanup:** Delete old jobs (>90 days)
   - When: Database size grows
   - Method: SQL query with date filter

3. **Log rotation:** Archive old logs
   - When: Logs exceed 100MB
   - Location: `data/logs/`

### Code Maintenance (Requires permission):

- Selector updates (LinkedIn HTML changes)
- Performance optimizations
- Schema migrations
- API integration changes

---

## 🚨 EMERGENCY PROTOCOLS

### If LinkedIn Scraper Completely Breaks:

1. **Save evidence:** HTML snapshot + error logs
2. **Notify user immediately:** "LinkedIn scraper broken, HTML structure changed"
3. **Do NOT attempt auto-fix:** Wait for user instructions
4. **Provide diagnosis:** What changed and why it broke
5. **Suggest manual verification:** User should check LinkedIn's site

### If Database Corrupted:

1. **Stop all writes immediately**
2. **Notify user:** "Database corruption detected"
3. **Do NOT attempt auto-repair:** Wait for user backup restoration
4. **Suggest backup:** User should restore from backup
5. **Provide recovery options:** If no backup exists

### If API Keys Exposed:

1. **Alert user immediately:** Security breach
2. **Recommend key rotation:** User must generate new keys
3. **Check git history:** If committed, provide cleanup instructions
4. **Update .gitignore:** Prevent future exposure

---

## 🎓 LESSONS LEARNED

### What Works (Don't Change):

1. ✅ **Multiple fallback selectors** - Prevents failures
2. ✅ **Tier 1 at scrape time** - 30.7% efficiency gain
3. ✅ **Page-by-page processing** - Reliable, doesn't miss jobs
4. ✅ **Hash-based deduplication** - Fast and accurate
5. ✅ **Explicit search config fields** - Prevents KeyError

### What to Avoid (Never Do):

1. ❌ Don't remove fallback selectors (reduces reliability)
2. ❌ Don't skip Tier 1 filtering (wastes time)
3. ❌ Don't change job hash algorithm (breaks deduplication)
4. ❌ Don't remove required fields from search config
5. ❌ Don't modify working code "just to refactor"

### Optimization Insights:

- **Tier 1 filtering** saves ~30% of scraping time
- **Parser fallback** ensures 0% job loss when API fails
- **Cookie reuse** prevents daily logins
- **Pagination** reliably fetches 25 jobs/page
- **3-tier strategy** balances speed and accuracy

---

## 🔒 FINAL REMINDER

**This system is production-ready and fully functional.**

Your role as an AI agent is to:
1. ✅ **PROTECT** existing functionality
2. ✅ **EXTEND** capabilities safely
3. ✅ **ASK** before modifying protected files
4. ✅ **TEST** all changes thoroughly
5. ✅ **DOCUMENT** modifications clearly

### Remember:

> **"A working system is more valuable than a 'perfect' system."**

> **"If it ain't broke, DON'T fix it! 🔒"**

> **"When in doubt, ASK. Never assume permission."**

---

**End of Agent Instructions**

*For detailed function documentation, see [CODEBASE_REFERENCE.md](CODEBASE_REFERENCE.md)*  
*For system status, see [SYSTEM_STATUS.md](SYSTEM_STATUS.md)*  
*For architecture design, see [ARCHITECTURE.md](ARCHITECTURE.md)*
