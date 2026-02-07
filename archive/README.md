# Archive Directory

This directory contains non-essential files that have been moved from the root directory to keep the repository clean.

**Last Cleanup:** 7 February 2026

---

## 📁 Directory Structure

### `test_scripts/`
**25 files** - Test and workflow scripts

These scripts were used during development and testing. They are kept for reference and potential future use.

**Examples:**
- `test_jora_workflow.py` - Full Jora scraper test
- `test_seek_workflow_final.py` - Seek scraper end-to-end test
- `run_complete_workflow.py` - Complete workflow with metrics
- `debug_*.py` - Various debugging scripts
- `analyze_*.py` - Analysis scripts for metrics

**Usage:**
```bash
# Run archived test scripts from root
python archive/test_scripts/test_jora_workflow.py
```

---

### `documentation/`
**8 files** - Old and redundant documentation

Previous documentation files that have been superseded by the current clean documentation set.

**Files:**
- `README_OLD.md` - Original verbose README
- `AGENT_INSTRUCTIONS.md` - Now replaced by .github/copilot-instructions.md
- `SEEK_TEST_RESULTS.md` - Seek scraper test results
- `PROJECT_STATUS_SUMMARY.md` - Old status summary

**Note:** These are kept for historical reference only. Refer to root directory for current documentation.

---

### `debug_scripts/`
**Debug utilities and HTML snapshots**

- `jora_debug_page.html` - Debug HTML snapshot from Jora

---

### `analysis_scripts/`
**Analysis and metrics scripts**

Currently empty - reserved for future analysis scripts.

---

## 🔑 Authentication Scripts (Root of archive/)

### `linkedin_login.py`
**Purpose:** Manual LinkedIn authentication to save cookies

**When to use:**
- First-time setup
- When LinkedIn session expires (cookies invalid)
- When scraper shows "Not logged in" error

**Usage:**
```bash
python archive/linkedin_login.py
# Opens browser → Manual login → Saves cookies → Close browser
```

**Output:** `linkedin_cookies.pkl` in root directory

---

### `seek_login.py`
**Purpose:** Manual Seek authentication to save cookies

**When to use:**
- Optional (Seek scraper works without authentication)
- If you want to access premium/saved jobs
- For faster scraping (authenticated sessions may be faster)

**Usage:**
```bash
python archive/seek_login.py
# Opens browser → Manual login → Saves cookies → Close browser
```

**Output:** `seek_cookies.pkl` in root directory

---

## ⚠️ Important Notes

### **Do NOT Delete This Directory**
- Scripts may be needed for debugging
- Authentication scripts are essential for re-login
- Documentation provides historical context

### **Adding New Files**
When archiving new test/debug files:

```bash
# Test scripts
mv test_*.py archive/test_scripts/

# Debug scripts
mv debug_*.py archive/debug_scripts/

# Old documentation
mv OLD_*.md archive/documentation/
```

### **Retrieving Archived Files**
If you need a test script:

```bash
# Copy back to root (don't move, keep archive intact)
cp archive/test_scripts/test_jora_workflow.py .

# Or run directly from archive
python archive/test_scripts/test_jora_workflow.py
```

---

## 📊 Archive Statistics

| Category | Count | Purpose |
|----------|-------|---------|
| Test Scripts | 25 | Development testing |
| Documentation | 8 | Historical reference |
| Auth Scripts | 2 | Re-authentication |
| Debug Files | 1+ | Debugging utilities |

**Total Archived:** 36+ files

---

## 🚀 Quick Access

### **Need to re-authenticate?**
```bash
# LinkedIn
python archive/linkedin_login.py

# Seek
python archive/seek_login.py
```

### **Need to test scrapers?**
```bash
# Jora full test
python archive/test_scripts/test_jora_workflow.py

# Seek full test
python archive/test_scripts/test_seek_workflow_final.py
```

### **Need old documentation?**
```bash
# View original README
cat archive/documentation/README_OLD.md

# View test results
cat archive/documentation/SEEK_TEST_RESULTS.md
```

---

## 📝 Maintenance

This archive should be:
- ✅ Kept organized by category
- ✅ Updated when new files are archived
- ✅ Preserved (do not delete)
- ❌ Not used for production code

---

**Remember:** Production code lives in `src/`, not in `archive/`!
