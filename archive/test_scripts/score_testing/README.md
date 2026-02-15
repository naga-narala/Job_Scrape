# Component-Based Scoring Test

## Purpose

This folder contains a standalone test script to validate the new **component-based AI scoring system** before integrating it into the main application.

## What This Tests

Instead of getting opaque scores like "75% match", the new system:
1. **Extracts individual job requirements** as weighted components
2. **Scores each component separately** (matched ✅, partial ⚠️, not matched ❌)
3. **Calculates final score** from component weights
4. **Shows transparent breakdown** of why a job scored what it did

## Test Script

**File:** `test_component_scoring.py`

**What it does:**
- Selects 15 random jobs from your existing database
- Scores each using the new component-based system
- Displays detailed component breakdown with visual indicators
- Compares new scores vs old scores
- Shows summary statistics

**Usage:**

```bash
# Activate virtual environment
source .venv/bin/activate

# Run test (will cost ~$0.045 for 15 jobs)
python score_testing/test_component_scoring.py
```

## Expected Output

For each job, you'll see:

```
================================================================================
Job 1/15
================================================================================
├─ Title: Graduate AI Engineer
├─ Company: Tech Corp
├─ Location: Perth, WA
├─ Source: linkedin
├─ New Score: 85%
├─ Recommendation: 🟢 APPLY
├─ Old Score: 72% (↑ 13.0% difference)
└─ Components:
    ✅ Python (20%) [important]
       └─ Candidate has strong Python experience from academic projects
    ✅ Machine Learning (25%) [important]
       └─ Matches candidate's ML coursework and projects
    ⚠️ Professional Experience (15%) [preferred]
       └─ Candidate is fresh graduate, partial match with internship
    ❌ 2+ Years Experience (10%) [dealbreaker]
       └─ Candidate has 0 years professional experience
    ✅ Perth Location (10%) [important]
       └─ Exact location match
    
   Score Breakdown:
   ├─ Total Possible: 100%
   ├─ Earned: 85%
   ├─ Lost to Dealbreakers: 10%
   └─ Lost to Gaps: 5%
```

## Summary Statistics

At the end, you'll see:

- **Average scores** (new vs old)
- **Recommendation breakdown** (APPLY/REVIEW/SKIP counts)
- **Component match rates** (% matched, partial, not matched)
- **Category analysis** (which types of requirements most common)

## Cost

- **Model:** Claude 3.5 Sonnet ($0.003/job)
- **15 Jobs:** ~$0.045 total
- **Production estimate:** 255 jobs/day × $0.003 = $0.765/day = $23/month

## Integration Plan

**If test results look good:**

1. ✅ **Update database schema** - Add `job_components` table
2. ✅ **Modify scorer.py** - Replace current prompt with component-based prompt
3. ✅ **Update dashboard** - Display component tags below job cards
4. ✅ **Add filtering** - Make component tags clickable filters
5. ✅ **Update config** - Change primary model to Claude Sonnet, increase max_tokens to 2000

## Notes

- ⚠️ **Read-only testing** - This script DOES NOT modify any existing files
- ⚠️ **Uses production API key** - Will consume OpenRouter credits
- ⚠️ **Random selection** - Different jobs each run for variety
- ⚠️ **Comparison data** - Shows old scores if available for validation

## Why Component-Based?

**Current problem:** "Job scored 33%, but why?"

**New solution:**
- Transparent: See exactly which requirements matched/didn't match
- Weighted: Important skills count more than nice-to-haves
- Universal: Works for ANY career field (AI, marketing, nursing, etc.)
- Actionable: Know what skills to highlight or improve

**Example:**
Instead of "65% match", you see:
- ✅ Python (20%) - Strong match
- ✅ Remote Work (15%) - Perfect
- ⚠️ ML Experience (25%) - Partial (has academic, needs professional)
- ❌ 5+ Years (15%) - Not satisfied
- ✅ Bachelor's Degree (10%) - Match

= 65% total (20 + 15 + 12.5 + 0 + 10 + 7.5)
