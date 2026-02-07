# Contributing Guidelines - Job Scraper Project

## 🚨 CRITICAL RULES - READ BEFORE MAKING ANY CHANGES

### **NEVER BREAK EXISTING FUNCTIONALITY**

This project has **production-ready scrapers** that are tested and working. Any changes must preserve existing functionality.

---

## ✅ Production Files - DO NOT MODIFY WITHOUT TESTING

### **Core Scrapers** (Production Ready)
```
src/scraper.py          # LinkedIn scraper - STABLE
src/seek_scraper.py     # Seek scraper - STABLE  
src/jora_scraper.py     # Jora scraper - STABLE
```

**Rules:**
- ❌ DO NOT change scraper architecture without full testing
- ❌ DO NOT modify selectors without verifying they still work
- ❌ DO NOT change function signatures (breaks main.py integration)
- ✅ Test changes with test_url.json before committing
- ✅ Run full workflow test after ANY scraper change

### **Core Components** (Production Ready)
```
src/optimization.py     # 3-tier filtering system - STABLE
src/database.py         # SQLite database operations - STABLE
src/scorer.py           # AI scoring with fallback - STABLE
src/main.py             # Main orchestrator - STABLE
```

**Rules:**
- ❌ DO NOT change database schema without migration script
- ❌ DO NOT modify optimization tiers (breaks efficiency metrics)
- ❌ DO NOT change scorer fallback chain
- ✅ Maintain backward compatibility
- ✅ Test database operations with existing data

### **Configuration Files** (User Data)
```
config.json                   # API keys, settings
generated_keywords.json       # Auto-generated from jobs.txt
generated_search_urls.json    # Auto-generated LinkedIn URLs
job_searches.json            # Manual search configurations
profile.txt                   # User profile (triggers rescore)
jobs.txt                      # Target job roles (triggers keyword regen)
test_url.json                # Testing URLs - KEEP THIS
```

**Rules:**
- ❌ DO NOT commit config.json (contains API keys)
- ❌ DO NOT delete test_url.json (needed for testing)
- ❌ DO NOT modify generated_*.json manually (auto-generated)
- ✅ Use config.json.example as template
- ✅ Regenerate keywords if jobs.txt changes

### **Authentication Files** (Session Data)
```
linkedin_cookies.pkl    # LinkedIn session
seek_cookies.pkl       # Seek session
jora_cookies.pkl       # Jora session
```

**Rules:**
- ❌ DO NOT commit cookie files (sensitive data)
- ❌ DO NOT share cookies between users
- ✅ Re-login if cookies expire (see archive/linkedin_login.py)

---

## 📋 Testing Requirements

### **Before Committing ANY Code Changes:**

1. **Test Individual Scraper:**
   ```bash
   # Use test_url.json for quick verification
   python -c "
   import json
   with open('test_url.json') as f:
       test_urls = json.load(f)
   # Test your changed scraper with one URL
   "
   ```

2. **Test Integration:**
   ```bash
   # Run main workflow with limited scope
   python src/main.py
   ```

3. **Verify Database:**
   ```bash
   # Check jobs were saved correctly
   sqlite3 data/jobs.db "SELECT COUNT(*) FROM jobs;"
   ```

4. **Check No Regressions:**
   - All 3 scrapers still work
   - 3-tier optimization still active
   - Database saves correctly
   - No import errors

---

## 🔧 Safe Change Guidelines

### **Adding New Features:**

✅ **SAFE:**
- Add new scraper (don't modify existing ones)
- Add new utility functions
- Add new documentation
- Add new test scripts (in archive/test_scripts/)
- Add new configuration options (preserve existing ones)

❌ **UNSAFE:**
- Modify existing scraper selectors
- Change database schema
- Alter optimization tier logic
- Change scorer model chain
- Rename existing functions/files

### **Modifying Existing Code:**

**Required Steps:**
1. Create backup branch
2. Test BEFORE and AFTER with same URLs
3. Verify output consistency
4. Check all 3 scrapers still work
5. Document what changed and why
6. Update SYSTEM_STATUS.md

**Example - Modifying LinkedIn Scraper:**
```bash
# 1. Backup current version
cp src/scraper.py src/scraper.py.backup

# 2. Make changes
# ... edit src/scraper.py ...

# 3. Test with test_url.json
python test_linkedin_scraper.py  # (create this test)

# 4. Compare results
diff old_results.txt new_results.txt

# 5. If broken, restore backup
mv src/scraper.py.backup src/scraper.py
```

---

## 📁 File Structure Rules

### **Root Directory** (Keep Clean)
Only essential files in root:
- README.md, SYSTEM_STATUS.md, CODEBASE_REFERENCE.md, ARCHITECTURE.md
- config.json.example (template only)
- requirements.txt, Dockerfile, docker-compose.yml
- test_url.json (testing)

### **Archive Directory** (For Non-Essential Files)
```
archive/
  ├── test_scripts/         # Test files (test_*.py, run_*.py)
  ├── debug_scripts/        # Debug files (debug_*.py)
  ├── documentation/        # Old/redundant docs
  ├── linkedin_login.py     # Re-authentication script
  └── seek_login.py         # Re-authentication script
```

**Rules:**
- ✅ Move completed test scripts to archive/test_scripts/
- ✅ Keep archive/ organized by type
- ❌ DO NOT delete archive/ (may need scripts later)

### **Source Directory** (Production Code)
```
src/
  ├── scraper.py          # LinkedIn scraper
  ├── seek_scraper.py     # Seek scraper
  ├── jora_scraper.py     # Jora scraper
  ├── optimization.py     # 3-tier filtering
  ├── database.py         # Database operations
  ├── scorer.py           # AI scoring
  ├── main.py             # Main orchestrator
  ├── keyword_generator.py
  ├── url_generator.py
  ├── rescore_manager.py
  ├── notifier.py
  ├── dashboard.py
  └── job_parser.py
```

**Rules:**
- ✅ All production code in src/
- ✅ No test files in src/
- ❌ DO NOT create subdirectories without reason

---

## 🛡️ Critical Architecture Patterns

### **3-Tier Optimization** (DO NOT BREAK)
```python
# TIER 1: Title filtering (before description fetch)
if not optimizer.tier1_should_scrape_title(title):
    continue

# TIER 2: Deduplication (after basic data)
if optimizer.tier2_is_duplicate(url, title, company, []):
    continue

# TIER 3: Description quality (after full fetch)
has_quality, reason = optimizer.tier3_has_quality_description(description)
if not has_quality:
    continue
```

**Rules:**
- ✅ ALL scrapers must implement all 3 tiers
- ✅ Tier order must be maintained (1 → 2 → 3)
- ❌ DO NOT skip tiers
- ❌ DO NOT change tier logic without testing impact

### **Scraper Architecture** (Consistent Pattern)
```python
def scrape_PLATFORM_jobs(url, max_pages=3, search_config=None):
    """
    Standard scraper signature - ALL scrapers must follow this
    
    Args:
        url: Search URL
        max_pages: Number of pages to scrape
        search_config: Search configuration dict
    
    Returns:
        List of job dicts with standard fields
    """
```

**Standard Job Dict:**
```python
{
    'title': str,           # Required
    'company': str,         # Required
    'location': str,        # Required
    'description': str,     # Required (full text)
    'url': str,             # Required (unique)
    'posted_date': str,     # Optional
    'employment_type': str, # Optional
    'source': str,          # 'linkedin', 'seek', or 'jora'
    'region': str,          # 'australia' or 'us'
}
```

**Rules:**
- ✅ All scrapers return same dict structure
- ✅ Required fields must always be present
- ❌ DO NOT add new required fields without updating all scrapers
- ❌ DO NOT change field names

### **AI Scoring Fallback Chain** (DO NOT BREAK)
```
Primary Model → Secondary Model → Tertiary Model → Parser-Filter
deepseek-chat → claude-haiku → [other] → regex-based
```

**Rules:**
- ✅ Maintain fallback order
- ✅ Parser-filter is last resort (never skip)
- ❌ DO NOT remove fallback models
- ❌ DO NOT re-score parser-filter jobs (already failed quality checks)

---

## 🚀 Deployment Checklist

Before deploying ANY changes to production:

- [ ] All 3 scrapers tested individually
- [ ] Full workflow test completed successfully
- [ ] Database integrity verified (no corruption)
- [ ] No new errors in logs
- [ ] Configuration files validated
- [ ] Cookie authentication still works
- [ ] Dashboard displays jobs correctly
- [ ] AI scoring functioning (or parser fallback works)
- [ ] SYSTEM_STATUS.md updated
- [ ] Git commit with clear message

---

## 📝 Documentation Requirements

When making changes, update:

1. **SYSTEM_STATUS.md** - Current status of components
2. **CODEBASE_REFERENCE.md** - Function inventory if adding/removing functions
3. **This file (CONTRIBUTING.md)** - If changing development process

---

## ⚠️ Common Mistakes to Avoid

### ❌ **Breaking Changes:**
```python
# BAD - Changing function signature
def scrape_jobs(url, pages):  # Removed search_config parameter!
    
# GOOD - Maintain backward compatibility
def scrape_jobs(url, max_pages=3, search_config=None):
```

### ❌ **Forgetting 3-Tier Optimization:**
```python
# BAD - No optimization
for job_card in job_cards:
    job = extract_job(job_card)
    all_jobs.append(job)  # Scraping everything!
    
# GOOD - All 3 tiers
if not optimizer.tier1_should_scrape_title(title):
    continue
if optimizer.tier2_is_duplicate(url, title, company, []):
    continue
has_quality, _ = optimizer.tier3_has_quality_description(description)
if not has_quality:
    continue
```

### ❌ **Hardcoding Configuration:**
```python
# BAD - Hardcoded
max_pages = 3
api_key = "sk-xxxxx"

# GOOD - Load from config
max_pages = config.get('linkedin_max_pages', 3)
api_key = config.get('openrouter_api_key')
```

---

## 🆘 What to Do If You Break Something

1. **Stop immediately**
2. **Check git status:** `git status`
3. **Restore last working version:**
   ```bash
   git checkout -- src/scraper.py  # Replace with broken file
   ```
4. **Test the restored version:**
   ```bash
   python test_scraper_with_url.py
   ```
5. **Review what went wrong before trying again**

---

## 📞 Getting Help

If unsure about a change:

1. Check SYSTEM_STATUS.md for current status
2. Check CODEBASE_REFERENCE.md for function details
3. Test in archive/test_scripts/ first
4. Create backup before modifying production code

---

## 🎯 Remember

> **The scrapers work perfectly right now. Any change risks breaking them.**
> **Test thoroughly. Preserve functionality. Document changes.**

**When in doubt, DON'T change it.**
