#!/usr/bin/env python3
import sys
import os
import json
import logging
import argparse
from pathlib import Path
import schedule
import time
import pytz
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

import database as db
import scraper
import scorer
import rescore_manager
import notifier
from url_generator import URLGenerator

try:
    from optimization import OptimizationManager
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False

try:
    from keyword_generator import KeywordGenerator
    KEYWORD_GEN_AVAILABLE = True
except ImportError:
    KEYWORD_GEN_AVAILABLE = False

try:
    from seek_scraper import SeekScraper
    SEEK_AVAILABLE = True
except ImportError:
    SEEK_AVAILABLE = False

try:
    from jora_scraper import JoraScraper
    JORA_AVAILABLE = True
except ImportError:
    JORA_AVAILABLE = False

# Setup logging
LOG_DIR = Path(__file__).parent.parent / 'data' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / 'job_scraper.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / 'config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error("config.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config.json: {e}")
        sys.exit(1)


def load_job_searches():
    """
    Load job searches from test_url.json (if exists), otherwise generated_search_urls.json
    Falls back to job_searches.json if generation hasn't run yet
    """
    # TEST MODE: Check for test_url.json first
    test_path = Path(__file__).parent.parent / 'test_url.json'
    if test_path.exists():
        logger.info("🧪 TEST MODE: Loading from test_url.json")
        print("\n⚠️  TEST MODE DETECTED - Using test_url.json (3 URLs only)")
        try:
            with open(test_path, 'r') as f:
                test_data = json.load(f)
            
            # Flatten test URLs into search format
            searches = []
            for source, urls in test_data.items():
                if isinstance(urls, list):
                    searches.extend(urls)
            
            logger.info(f"Loaded {len(searches)} test URLs")
            print(f"   Loaded {len(searches)} test URLs\n")
            return searches
        except Exception as e:
            logger.warning(f"Could not load test URLs: {e}, falling back to production URLs")
    
    # Try new generated URLs first
    generated_path = Path(__file__).parent.parent / 'generated_search_urls.json'
    if generated_path.exists():
        try:
            with open(generated_path, 'r') as f:
                url_data = json.load(f)
            
            # Convert to search format
            searches = []
            for source, urls in url_data.items():
                for url_obj in urls:
                    searches.append({
                        'id': url_obj['search_id'],
                        'url': url_obj['url'],
                        'source': source,
                        'keyword': url_obj['keyword'],
                        'location': url_obj['location'],
                        'region': 'australia',  # Default
                        'enabled': True
                    })
            
            logger.info(f"Loaded {len(searches)} searches from generated URLs")
            return searches
        except Exception as e:
            logger.warning(f"Could not load generated URLs: {e}, falling back to job_searches.json")
    
    # Fall back to old format
    searches_path = Path(__file__).parent.parent / 'job_searches.json'
    try:
        with open(searches_path, 'r') as f:
            data = json.load(f)
        return data.get('searches', [])
    except FileNotFoundError:
        logger.error("Neither generated_search_urls.json nor job_searches.json found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in search files: {e}")
        sys.exit(1)


def get_perth_time():
    """Get current time in Perth timezone"""
    perth_tz = pytz.timezone('Australia/Perth')
    return datetime.now(perth_tz)


def get_next_run_time(interval_hours=24):
    """Calculate next run time"""
    perth_tz = pytz.timezone('Australia/Perth')
    next_run = datetime.now(perth_tz)
    from datetime import timedelta
    next_run = next_run + timedelta(hours=interval_hours)
    return next_run.strftime('%Y-%m-%d %H:%M:%S %Z')


def run_daily_job():
    """Main workflow executed every 24 hours"""
    print("\n" + "=" * 70)
    print("🚀 JOB SCRAPER STARTING")
    print("=" * 70)
    logger.info("=" * 70)
    logger.info(f"Starting daily job run - {get_perth_time().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("=" * 70)
    
    try:
        # Load configuration
        config = load_config()
        
        # Step 0: Auto-regenerate keywords if jobs.txt changed (Issue #5)
        if KEYWORD_GEN_AVAILABLE:
            try:
                keyword_gen = KeywordGenerator()
                if keyword_gen.needs_regeneration():
                    print(f"\n{'=' * 70}")
                    print("🔄 JOBS.TXT CHANGED - REGENERATING KEYWORDS")
                    print(f"{'=' * 70}")
                    logger.info("Detected jobs.txt changes - regenerating keywords...")
                    keywords = keyword_gen.generate_keywords()
                    print(f"✅ Keywords regenerated successfully")
                    logger.info(f"Keywords regenerated: {len(keywords.get('title_keywords', []))} title keywords")
                else:
                    logger.info("Keywords up-to-date - no regeneration needed")
            except Exception as e:
                logger.warning(f"Keyword auto-regeneration failed: {e}")
                print(f"⚠️  Keyword auto-regeneration failed (continuing with existing keywords)")
        
        searches = load_job_searches()
        
        # Show startup summary
        enabled = [s for s in searches if s.get('enabled', True)]
        linkedin_searches = [s for s in enabled if s.get('source') == 'linkedin']
        seek_searches = [s for s in enabled if s.get('source') == 'seek']
        jora_searches = [s for s in enabled if s.get('source') == 'jora']
        max_pages = config.get('linkedin_max_pages', 3)
        
        print(f"\n📋 CONFIGURATION:")
        print(f"   Total searches: {len(enabled)}")
        print(f"   📘 LinkedIn: {len(linkedin_searches)}")
        print(f"   🟣 Seek: {len(seek_searches)}")
        print(f"   🔵 Jora: {len(jora_searches)}")
        print(f"   Pages per search: {max_pages}")
        print(f"   Expected jobs: ~{len(enabled) * 20}")
        print(f"   Estimated time: ~{len(enabled) * 1.5:.0f} minutes")
        print(f"\nStarting in 3 seconds...")
        time.sleep(3)
        
        # Initialize database
        db.init_database()
        
        # Step 1: Check for profile changes and trigger smart rescore
        profile_content = scorer.load_profile()
        if rescore_manager.detect_profile_change():
            logger.info("Profile changed! Triggering smart rescore...")
            rescored_count = rescore_manager.trigger_smart_rescore(profile_content, config)
            logger.info(f"Re-scored {rescored_count} eligible jobs")
        
        # Step 2: Fetch jobs from all sources
        print(f"\n{'=' * 70}")
        print("📥 FETCHING JOBS FROM ALL SOURCES")
        print(f"{'=' * 70}")
        logger.info("Fetching jobs from all sources...")
        
        all_jobs = []
        source_stats = {'linkedin': 0, 'seek': 0, 'jora': 0}
        
        # Fetch from LinkedIn (existing scraper)
        if linkedin_searches:
            logger.info(f"Fetching from LinkedIn: {len(linkedin_searches)} searches")
            linkedin_jobs, strategy_stats = scraper.fetch_all_jobs(
                linkedin_searches,
                config.get('jsearch_api_key'),
                max_pages=max_pages
            )
            for job in linkedin_jobs:
                job['source'] = 'linkedin'  # Ensure source is set
            all_jobs.extend(linkedin_jobs)
            source_stats['linkedin'] = len(linkedin_jobs)
            logger.info(f"LinkedIn: {len(linkedin_jobs)} jobs, Strategy: {strategy_stats}")
        
        # Fetch from Seek (with pagination: 3 pages per search)
        if seek_searches and SEEK_AVAILABLE:
            logger.info(f"Fetching from Seek: {len(seek_searches)} searches")
            seek_scraper = SeekScraper()
            seek_jobs_count = 0
            for search in seek_searches:
                try:
                    jobs = seek_scraper.search_jobs(
                        search['keyword'],
                        search['location'],
                        max_pages=3  # Scrape 3 pages per search
                    )
                    for job in jobs:
                        job['source_search_id'] = search['id']
                        all_jobs.append(job)
                    seek_jobs_count += len(jobs)
                except Exception as e:
                    logger.error(f"Seek search error: {e}")
            source_stats['seek'] = seek_jobs_count
            logger.info(f"Seek: {seek_jobs_count} jobs")
        elif seek_searches:
            logger.warning("Seek searches configured but SeekScraper not available")
        
        # Fetch from Jora (with max_results=100)
        if jora_searches and JORA_AVAILABLE:
            logger.info(f"Fetching from Jora: {len(jora_searches)} searches")
            jora_scraper = JoraScraper()
            jora_jobs_count = 0
            for search in jora_searches:
                try:
                    jobs = jora_scraper.search_jobs(
                        search['keyword'],
                        search['location'],
                        max_results=100  # Increased from default 50
                    )
                    for job in jobs:
                        job['source_search_id'] = search['id']
                        all_jobs.append(job)
                    jora_jobs_count += len(jobs)
                except Exception as e:
                    logger.error(f"Jora search error: {e}")
            source_stats['jora'] = jora_jobs_count
            logger.info(f"Jora: {jora_jobs_count} jobs")
        elif jora_searches:
            logger.warning("Jora searches configured but JoraScraper not available")
        
        print(f"\n{'=' * 70}")
        print(f"✅ SCRAPING COMPLETE")
        print(f"{'=' * 70}")
        print(f"📊 Total jobs fetched: {len(all_jobs)}")
        print(f"   📘 LinkedIn: {source_stats['linkedin']}")
        print(f"   🟣 Seek: {source_stats['seek']}")
        print(f"   🔵 Jora: {source_stats['jora']}")
        
        logger.info(f"Fetched {len(all_jobs)} total jobs")
        logger.info(f"Source breakdown: {source_stats}")
        
        # Step 3: Deduplicate and insert new jobs (with Tier 2 & 3 filtering)
        print(f"\n{'=' * 70}")
        print("💾 SAVING TO DATABASE (with optimizations)")
        print(f"{'=' * 70}")
        
        new_jobs = []
        duplicate_count = 0
        tier2_filtered = 0
        tier3_filtered = 0
        
        # Initialize optimization manager for Tier 2 and Tier 3
        opt_manager = None
        if OPTIMIZATION_AVAILABLE:
            try:
                opt_manager = OptimizationManager()
                logger.info(f"Optimization manager initialized")
            except Exception as e:
                logger.warning(f"Could not initialize optimization manager: {e}")
        
        # Get existing jobs for deduplication
        existing_jobs = db.get_all_jobs()
        
        for job in all_jobs:
            job_title = job.get('title', '')
            job_desc = job.get('description', '')
            job_hash = db.generate_job_hash(
                url = job.get('url', '')
            job_company = job.get('company', '')
            
            # TIER 2: Deduplication check (check database first - cheapest operation)
            if opt_manager:
                is_duplicate, dup_reason = opt_manager.tier2_is_duplicate(
                    job_url, job_title, job_company, existing_jobs
                )
                if is_duplicate:
                    tier2_filtered += 1
                    logger.debug(f"Tier 2 (Dedup) filtered: {job_title} - {dup_reason}")
                    # Update last_seen_date for duplicate
                    job_hash = db.generate_job_hash(job_title, job_company, job_url)
                    db.update_job_last_seen(job_hash)
                    continue
            
            # TIER 3: Description quality check (before saving to database)
            if opt_manager:
                has_quality, quality_reason = opt_manager.tier3_has_quality_description(job_desc)
                if not has_quality:
                    tier3_filtered += 1
                    logger.debug(f"Tier 3 (Quality) filtered: {job_title} - {quality
            
            # Passed all filters - insert into database
            job_id = db.insert_job(job)
            if job_id:
                job['id'] = job_id
                new_jobs.append(job)
            else:
                duplicate_count += 1
                # Update last_seen_date for duplicate
                db.update_job_last_seen(job_hash)
        
        print(f"✅ New jobs: {len(new_jobs)}")
        print(f"🔄 Duplicates (DB fallback): {duplicate_count}")
        if opt_manager:
            print(f"⚡ Tier 2 (Deduplication) filtered: {tier2_filtered}")
            print(f"⚡ Tier 3 (Description Quality) filtered: {tier3_filtered}")
            total_filtered = tier2_filtered + tier3_filtered
            total_processed = len(all_jobs)
            savings_pct = (total_filtered / total_processed * 100) if total_processed > 0 else 0
            print(f"💰 Optimization savings: {total_filtered}/{total_processed} ({savings_pct:.1f}%)")
        logger.info(f"New jobs: {len(new_jobs)}, Duplicates: {duplicate_count}, Tier2: {tier2_filtered}, Tier3: {tier3_filtered}")
        
        # Step 4: Mark jobs as inactive if not seen
        for search in searches:
            if not search.get('enabled', True):
                continue
            
            # Get all job hashes from this search in current fetch
            seen_hashes = [
                db.generate_job_hash(j['title'], j.get('company', ''), j['url'])
                for j in all_jobs
                if j.get('source_search_id') == search['id']
            ]
            
            db.mark_jobs_inactive(search['id'], seen_hashes)
        
        # Step 5: Score new unscored jobs
        unscored = db.get_unscored_jobs()
        
        if unscored:
            print(f"\n{'=' * 70}")
            print(f"🎯 SCORING {len(unscored)} NEW JOBS")
            print(f"{'=' * 70}")
            logger.info(f"Scoring {len(unscored)} unscored jobs...")
            
            score_summary = scorer.score_batch(
                unscored,
                profile_content,
                config.get('ai_models', {}),
                config.get('openrouter_api_key')
            )
            
            print(f"\n✅ Scoring complete:")
            print(f"   ✓ Scored: {score_summary.get('scored', 0)}")
            print(f"   ❌ Failed: {score_summary.get('failed', 0)}")
            print(f"   📊 Average score: {score_summary.get('average_score', 0):.1f}%")
            
            # Insert scores into database
            profile_hash = db.get_profile_hash()
            for score_data in score_summary['scores']:
                if score_data.get('job_id'):
                    db.insert_score(score_data['job_id'], score_data, profile_hash)
            
            logger.info(f"Scored: {score_summary['scored']}, Failed: {score_summary['failed']}, Avg: {score_summary['avg_score']}%")
        else:
            print(f"\n✓ No new jobs to score")
            logger.info("No new jobs to score")
        
        # Step 6: Send notifications for high-scoring new matches
        print(f"\n{'=' * 70}")
        print("📧 NOTIFICATIONS")
        print(f"{'=' * 70}")
        
        notification_result = notifier.notify_new_matches(config)
        
        if notification_result['success']:
            if notification_result['method'] == 'email':
                print(f"✅ Email sent for {notification_result['notified']} match(es)")
                logger.info(f"✓ Email notification sent for {notification_result['notified']} match(es)")
            elif notification_result['method'] == 'html':
                print(f"✅ HTML notification created for {notification_result['notified']} match(es)")
                print(f"   File: {notification_result.get('file')}")
                logger.info(f"✓ HTML notification created for {notification_result['notified']} match(es)")
                logger.info(f"  File: {notification_result.get('file')}")
        else:
            print(f"ℹ️  No new matches to notify")
        
        # Step 7: Log summary
        high_matches = db.count_jobs_above_threshold(config.get('match_threshold', 75))
        
        print(f"\n{'=' * 70}")
        print("✅ RUN COMPLETE")
        print(f"{'=' * 70}")
        print(f"📊 Total matches (≥50%): {high_matches}")
        print(f"📅 Next run: {get_next_run_time(config.get('check_interval_hours', 24))}")
        print(f"🌐 View dashboard: http://localhost:8000")
        print(f"{'=' * 70}\n")
        
        logger.info("=" * 70)
        logger.info("Daily run completed successfully")
        logger.info(f"Total matches (75%+): {high_matches}")
        logger.info(f"Next run: {get_next_run_time(config.get('check_interval_hours', 24))}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error in daily job run: {e}", exc_info=True)
        raise


def run_test_mode():
    """Test mode - validates configuration and runs limited test"""
    print("=" * 70)
    print("RUNNING TEST MODE")
    print("=" * 70)
    
    try:
        # Test 1: Load config
        print("\n1. Loading configuration...")
        config = load_config()
        print(f"   ✓ Config loaded")
        print(f"   - AI Model: {config.get('ai_models', {}).get('primary')}")
        print(f"   - Match Threshold: {config.get('match_threshold')}%")
        
        # Test 2: Load profile
        print("\n2. Loading profile...")
        profile = scorer.load_profile()
        print(f"   ✓ Profile loaded ({len(profile)} characters)")
        if len(profile.strip()) < 100:
            print("   ⚠ WARNING: Profile is short. Consider adding more details.")
        
        # Test 3: Initialize database
        print("\n3. Initializing database...")
        db.init_database()
        print("   ✓ Database initialized")
        
        # Test 4: Load job searches
        print("\n4. Loading job searches...")
        searches = load_job_searches()
        enabled_searches = [s for s in searches if s.get('enabled', True)]
        print(f"   ✓ {len(enabled_searches)} enabled search(es) found")
        for s in enabled_searches[:3]:
            print(f"   - {s.get('name')}")
        
        # Test 5: Fetch sample jobs (first search only, limit 3)
        if enabled_searches:
            print("\n5. Fetching sample jobs (3 max)...")
            first_search = enabled_searches[0]
            
            # Get args to check for --visible flag
            import sys
            visible = '--visible' in sys.argv
            
            jobs, strategy = scraper.fetch_all_jobs(
                [first_search],
                config.get('brave_search_api_key'),
                headless=not visible,
                max_pages=1  # Only 1 page for test mode
            )
            
            if jobs:
                jobs = jobs[:10]  # Limit to 10 for testing
                print(f"   ✓ Fetched {len(jobs)} sample job(s)")
                
                # Insert jobs into database for testing
                print("\n6. Inserting jobs into database...")
                for job in jobs:
                    job_id = db.insert_job(job)
                    if job_id:
                        job['id'] = job_id
                        print(f"   ✓ Inserted: {job['title'][:60]}")
                
                # Test 7: Score sample jobs
                print("\n7. Scoring sample jobs with AI...")
                profile_hash = db.get_profile_hash()
                for i, job in enumerate(jobs, 1):
                    try:
                        result = scorer.score_job_with_fallback(
                            job,
                            profile,
                            config.get('ai_models', {}),
                            config.get('openrouter_api_key')
                        )
                        print(f"   Job {i}: {job['title'][:50]}")
                        print(f"          Score: {result['score']}% ({result['model_used']})")
                        print(f"          Reason: {result['reasoning'][:100]}...")
                        
                        # Save score to database for testing
                        if job.get('id'):
                            result['job_id'] = job['id']
                            db.insert_score(job['id'], result, profile_hash)
                    except Exception as e:
                        print(f"   ✗ Failed to score job {i}: {e}")
                
                # Test 8: Test notification for high-scoring jobs
                print("\n8. Testing notification system...")
                notification_result = notifier.notify_new_matches(config)
                
                if notification_result['notified'] > 0:
                    if notification_result['method'] == 'email':
                        print(f"   ✓ Email sent for {notification_result['notified']} match(es)")
                    elif notification_result['method'] == 'html':
                        print(f"   ✓ HTML notification created for {notification_result['notified']} match(es)")
                        print(f"   📄 File: {notification_result.get('file')}")
                else:
                    print(f"   ℹ No matches above threshold ({config.get('match_threshold', 75)}%)")
                
                # Test 9: Test email with sample job
                print("\n9. Testing email notification...")
                test_job = {
                    'title': 'Test Job',
                    'company': 'Test Company',
                    'location': 'Test Location',
                    'url': 'https://test.com',
                    'score': 85,
                    'reasoning': 'This is a test notification',
                    'first_seen_date': str(db.get_perth_date())
                }
                
                email_success = notifier.send_email_notification([test_job], config)
                if email_success:
                    print("   ✓ Test email sent successfully")
                else:
                    print("   ✗ Email failed (check logs)")
                    print("   ℹ Creating HTML notification instead...")
                    html_path = notifier.save_html_notification([test_job])
                    if html_path:
                        print(f"   ✓ HTML notification created: {html_path}")
            else:
                print(f"   ✗ No jobs fetched (strategy: {strategy})")
        
        print("\n" + "=" * 70)
        print("TEST COMPLETED")
        print("If all tests passed, run with --daemon to start automation")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        logger.error(f"Test mode failed: {e}", exc_info=True)
        sys.exit(1)


def start_daemon():
    """Run as background service with scheduling"""
    logger.info("Starting Job Scraper in daemon mode")
    
    config = load_config()
    interval_hours = config.get('check_interval_hours', 24)
    
    logger.info(f"Check interval: every {interval_hours} hours")
    
    # Run immediately on startup
    logger.info("Running initial job...")
    run_daily_job()
    
    # Schedule future runs
    schedule.every(interval_hours).hours.do(run_daily_job)
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
        sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='LinkedIn Job Scraper with AI Matching',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as background service (runs every 24h)'
    )
    
    parser.add_argument(
        '--run-now',
        action='store_true',
        help='Run immediately and exit (no scheduling)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: validate config and run limited test'
    )
    parser.add_argument(
        '--visible',
        action='store_true',
        help='Show browser window during scraping (for testing/debugging)'
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_test_mode()
    elif args.run_now:
        run_daily_job()
    elif args.daemon:
        start_daemon()
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python src/main.py --test        # Test configuration")
        print("  python src/main.py --run-now     # Run once immediately")
        print("  python src/main.py --daemon      # Run as service (24h interval)")


if __name__ == "__main__":
    main()
