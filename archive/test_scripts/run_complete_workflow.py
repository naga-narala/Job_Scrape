#!/usr/bin/env python3
"""
Complete workflow with MAXIMUM verbosity and detailed step tracking
"""

import sys
import json
import hashlib
import logging
from datetime import datetime

sys.path.insert(0, 'src')

# Configure VERBOSE logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

import database as db
from scraper import fetch_all_jobs
from scorer import score_job_with_fallback, load_profile  
from optimization import OptimizationManager

def main():
    print("=" * 80)
    print("🔍 COMPLETE WORKFLOW - DETAILED METRICS")
    print("=" * 80)
    
    # Load configuration
    with open('config.json') as f:
        config = json.load(f)
    
    with open('test_url.json') as f:
        data = json.load(f)
        searches = data.get('linkedin', [])
    
    # Initialize database
    db.init_database()
    
    # Initialize optimizer
    optimizer = OptimizationManager('config.json')
    
    # Get max_pages from config
    max_pages = config.get('linkedin_max_pages', 3)
    
    print(f"\n📋 TEST CONFIGURATION:")
    print(f"   URL: {searches[0]['url']}")
    print(f"   Keyword: {searches[0]['keyword']}")
    print(f"   Max pages: {max_pages}")
    
    # PHASE 1: SCRAPING
    print("\n" + "=" * 80)
    print("PHASE 1: SCRAPING (with Tier 1 filtering)")
    print("=" * 80)
    
    jobs, stats = fetch_all_jobs(
        searches,
        api_key=config.get('api_key'),
        headless=True,  # Headless mode
        max_pages=max_pages,
        config=config  # Pass config for pagination setting
    )
    
    print(f"\n✅ SCRAPING RESULTS:")
    print(f"   Jobs scraped: {len(jobs)}")
    print(f"   Stats: {stats}")
    
    if not jobs:
        print("\n❌ NO JOBS SCRAPED - Workflow cannot continue")
        print("   Check if LinkedIn selectors are correct")
        return
    
    # Show scraped jobs
    print(f"\n📋 SCRAPED JOBS:")
    for i, job in enumerate(jobs, 1):
        print(f"\n   {i}. {job['title']}")
        print(f"      Company: {job['company']}")
        print(f"      Location: {job['location']}")
        print(f"      Description: {len(job['description'])} chars")
    
    # PHASE 2: TIER 2 - Deduplication (skip for now in test)
    print("\n" + "=" * 80)
    print("PHASE 2: TIER 3 FILTERING (Description Quality)")
    print("=" * 80)
    
    tier3_passed = []
    tier3_filtered = []
    
    for job in jobs:
        has_quality, reason = optimizer.tier3_has_quality_description(
            job['description']
        )
        
        if has_quality:
            tier3_passed.append(job)
            print(f"   ✅ PASS: {job['title']}")
        else:
            tier3_filtered.append({'job': job, 'reason': reason})
            print(f"   ❌ FILTER: {job['title']} - {reason}")
    
    print(f"\n   Passed: {len(tier3_passed)}")
    print(f"   Filtered: {len(tier3_filtered)}")
    
    # PHASE 3: Deduplication & Database Insert
    print("\n" + "=" * 80)
    print("PHASE 3: DEDUPLICATION & DATABASE INSERT")
    print("=" * 80)
    
    new_jobs = []
    duplicate_jobs = []
    
    import sqlite3
    conn = sqlite3.connect('data/jobs.db')
    
    for job in tier3_passed:
        hash_string = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        job_hash = hashlib.md5(hash_string.encode()).hexdigest()
        
        is_dup, reason = optimizer.tier2_is_duplicate(
            job['url'],
            job['title'],
            job['company'],
            []  # We'll check database directly
        )
        
        # Check database
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_id_hash = ?", (job_hash,))
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            new_jobs.append(job)
            job['job_id_hash'] = job_hash
            db.insert_job(job)
            print(f"   ✅ NEW: {job['title']}")
        else:
            duplicate_jobs.append({'job': job, 'reason': 'Already in database'})
            print(f"   ⏭️  DUPLICATE: {job['title']}")
    
    conn.close()
    
    print(f"\n   New jobs: {len(new_jobs)}")
    print(f"   Duplicates: {len(duplicate_jobs)}")
    
    # PHASE 4: AI SCORING - SKIPPED
    print("\n" + "=" * 80)
    print("PHASE 4: AI SCORING - SKIPPED")
    print("=" * 80)
    print("\n   ⏭️  AI Scoring skipped (as requested)")
    print("   All jobs saved to database ready for scoring later")
    
    scored_count = 0
    failed_count = 0
    
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    
    print(f"\n📄 PAGINATION:")
    print(f"   Pages scraped: {max_pages} (configured)")
    
    print(f"\n🔍 SCRAPING:")
    print(f"   Total jobs scraped: {len(jobs)}")
    
    print(f"\n🎯 3-TIER FILTERING:")
    print(f"   Tier 1 (Title): Applied during scraping")
    print(f"   Tier 3 (Description Quality): {len(tier3_filtered)} filtered")
    print(f"   Deduplication: {len(duplicate_jobs)} duplicates")
    print(f"   Passed all filters: {len(new_jobs)}")
    
    print(f"\n💾 DATABASE:")
    print(f"   New jobs saved: {len(new_jobs)}")
    print(f"   Ready for AI scoring later")
    
    print("\n" + "=" * 80)
    print("✅ WORKFLOW COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
