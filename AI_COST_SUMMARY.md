# AI Model Usage & Cost Summary
**Date:** February 15, 2026

## Current Configuration

### 🎯 Primary Scoring Model
**Model:** `deepseek/deepseek-chat`  
**Provider:** OpenRouter API  
**Cost:** $0.14 per 1M input tokens, $0.28 per 1M output tokens

**What it does:**
- Analyzes every job against your profile
- Component-based scoring (technical skills, experience, education)
- Hireability assessment (visa eligibility, risk factors)
- Generates recommendation (APPLY/CLARIFY/SKIP)
- Creates detailed explanation

**Tokens per job:**
- Input: ~2,000 tokens (profile + job description + prompt)
- Output: ~500 tokens (analysis + structured JSON)
- **Cost per job: $0.00042** (0.42 cents per job)

### 💸 Fallback Models (if DeepSeek fails)
1. `openai/gpt-3.5-turbo` - $0.50/$1.50 per 1M tokens
2. `meta-llama/llama-3.1-8b-instruct:free` - **FREE**
3. `anthropic/claude-3-haiku` - $0.25/$1.25 per 1M tokens

### 🔑 Keyword Generation (rarely used)
**Model:** `anthropic/claude-3.5-sonnet`  
**Cost:** $3/$15 per 1M tokens  
**Note:** Only runs when generating new keywords. Your keywords are already generated, so this won't be used in regular runs.

---

## Cost Estimate for Full Run

### Expected Job Flow
```
920 jobs scraped (46 searches × ~20 jobs each)
  ↓
~150-200 unique new jobs (after deduplication)
  ↓
~150-200 jobs scored with AI
```

### 💰 Total Cost Breakdown

| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| DeepSeek Scoring | 175 jobs (avg) | $0.00042/job | **$0.07** |
| Keyword Gen | 0 runs | $0 | $0.00 |
| **TOTAL** | | | **~$0.07** ✅ |

### 🔄 Recurring Cost Estimates

| Frequency | Cost |
|-----------|------|
| Per run | $0.07 |
| Daily | $0.07 |
| Weekly | $0.49 |
| Monthly | $2.10 |
| **Yearly** | **$25.55** |

---

## Cost Comparison with Other Models

For 175 jobs:

| Model | Cost | vs DeepSeek |
|-------|------|-------------|
| **DeepSeek** ✅ | **$0.07** | Baseline |
| GPT-3.5 Turbo | $0.31 | 4x more |
| Claude Sonnet | $1.05 | 14x more |
| GPT-4 | $2.62 | 35x more |

---

## Why DeepSeek?

✅ **Extremely cost-effective** - 35x cheaper than GPT-4  
✅ **High quality** - Competitive performance with GPT-3.5  
✅ **Fast response** - Low latency for scoring  
✅ **Reliable** - Multiple fallback models if it fails  
✅ **Smart optimization** - Only scores NEW jobs (skips duplicates)

---

## What Gets Scored?

**YES - Scored with AI:**
- ✅ New unique jobs
- ✅ Jobs passing title/description filters
- ✅ Jobs not already in database

**NO - Skipped (free):**
- ❌ Duplicate jobs (same title + company)
- ❌ Jobs already scored in last 90 days
- ❌ Jobs filtered by title keywords
- ❌ Jobs with insufficient description

**Result:** You only pay for quality, relevant, new jobs!

---

## Monthly Budget Recommendation

**Conservative estimate:** $5/month  
**Covers:** Daily runs + some keyword regeneration + buffer

**Your OpenRouter account should have:**
- At least $10 credit to start safely
- Auto-reload or monitor balance monthly

---

## Bottom Line

🎉 **Running the full workflow costs approximately 7 cents** 🎉

This includes:
- Scraping 46 search URLs
- Processing ~920 raw jobs
- Scoring ~175 unique new jobs with AI
- Full hybrid analysis (component + hireability)

**It's incredibly affordable to run this daily!**
