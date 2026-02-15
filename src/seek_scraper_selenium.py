"""
Seek Job Scraper - Selenium Version (Like LinkedIn)

Uses Selenium WebDriver to handle JavaScript-rendered content
Works exactly like LinkedIn scraper with 3-tier optimization
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import random
import logging
import pickle
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import re

# Import shared driver utility
from driver_utils import create_chrome_driver, safe_quit_driver, test_driver_health

try:
    from optimization import OptimizationManager
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning("Optimization module not available")
    OPTIMIZATION_AVAILABLE = False

# Cookie storage
COOKIES_FILE = Path(__file__).parent.parent / 'data' / 'seek_cookies.pkl'

logger = logging.getLogger(__name__)


def create_seek_driver(headless=True):
    """
    Create Chrome WebDriver for Seek
    Uses shared driver utility with robust error handling
    """
    try:
        driver = create_chrome_driver(
            headless=headless,
            stealth_mode=False,  # Seek doesn't need stealth
            user_profile=False
        )
        return driver
    except Exception as e:
        logger.error(f"Failed to create Seek driver: {e}")
        raise


def load_seek_cookies(driver):
    """Load saved Seek cookies"""
    if not COOKIES_FILE.exists():
        logger.warning(f"No cookies found at {COOKIES_FILE}. Run seek_login.py first!")
        return False
    
    try:
        driver.get("https://www.seek.com.au")
        time.sleep(2)
        
        with open(COOKIES_FILE, 'rb') as f:
            cookies = pickle.load(f)
        
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logger.debug(f"Could not add cookie {cookie.get('name')}: {e}")
        
        logger.info(f"Loaded {len(cookies)} cookies")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        return False


def scrape_seek_jobs(url, max_pages=10, search_config=None):
    """
    Scrape Seek jobs with Selenium (like LinkedIn scraper)
    
    Args:
        url: Seek search URL
        max_pages: Maximum pages to scrape
        search_config: Dict with search metadata
    
    Returns:
        List of job dictionaries
    """
    driver = create_seek_driver(headless=True)  # Headless mode for production
    optimizer = OptimizationManager() if OPTIMIZATION_AVAILABLE else None
    
    all_jobs = []
    
    try:
        # Load cookies
        load_seek_cookies(driver)
        
        # Navigate to search URL
        logger.info(f"Loading Seek search URL: {url}")
        driver.get(url)
        time.sleep(3)  # Wait for JS to load
        
        # Scrape multiple pages
        for page in range(1, max_pages + 1):
            logger.info(f"Scraping Seek page {page}/{max_pages}")
            print(f"\n🟣 SEEK - PAGE {page}")
            print("="*80)
            
            # Wait for job cards to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article[data-card-type='JobCard'], article"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for job cards on page {page}")
                break
            
            # Scroll to load all jobs
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Find job cards - try multiple selectors
            job_cards = []
            selectors = [
                "article[data-card-type='JobCard']",
                "article[data-testid='job-card']",
                "div[data-search-sol-meta]",
                "article"
            ]
            
            for selector in selectors:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    job_cards = cards
                    logger.info(f"Found {len(cards)} job cards using selector: {selector}")
                    break
            
            if not job_cards:
                logger.warning(f"No job cards found on page {page}")
                break
            
            # 3-Tier optimization metrics
            total_cards = len(job_cards)
            tier1_filtered = 0
            tier2_skipped = 0
            tier3_filtered = 0
            filtered_jobs = []
            
            print(f"Found {total_cards} job cards\n")
            
            # Process each job card
            for idx, card in enumerate(job_cards, 1):
                try:
                    # Extract job info
                    job = extract_job_from_seek_card(card, driver, optimizer)
                    
                    if job is None:
                        continue
                    
                    # Check if it was filtered
                    if job.get('_filtered'):
                        tier = job.get('_filter_tier', 1)
                        reason = job.get('_filter_reason', '')
                        
                        if tier == 1:
                            tier1_filtered += 1
                        elif tier == 2:
                            tier2_skipped += 1
                        elif tier == 3:
                            tier3_filtered += 1
                        
                        filtered_jobs.append({
                            'tier': tier,
                            'reason': reason,
                            'title': job.get('title', 'Unknown'),
                            'company': job.get('company', 'Unknown')
                        })
                        continue
                    
                    # Add metadata
                    if search_config:
                        job['source_search_id'] = search_config.get('search_id', '')
                        job['region'] = search_config.get('region', 'australia')
                    
                    job['source'] = 'seek'
                    job['_page'] = page  # Track page number for metrics
                    
                    print(f"   ✅ Job {idx}: {job['title']} at {job['company']}")
                    all_jobs.append(job)
                    
                except StaleElementReferenceException:
                    logger.warning(f"Stale element on card {idx}, skipping")
                    continue
                except Exception as e:
                    logger.error(f"Error processing card {idx}: {e}")
                    continue
            
            # Log filtering details
            if filtered_jobs:
                print(f"\n📋 DETAILED FILTERING ANALYSIS (Page {page}):")
                for filtered in filtered_jobs:
                    tier_name = {1: "TITLE", 2: "DEDUP", 3: "QUALITY"}[filtered['tier']]
                    print(f"   ❌ TIER {filtered['tier']} ({tier_name}): {filtered['title']} at {filtered['company']}")
                    print(f"      Reason: {filtered['reason']}")
            
            # Log metrics
            jobs_scraped = len([j for j in all_jobs if j.get('_page') == page])
            logger.info(f"") 
            logger.info(f"📊 PAGE {page} METRICS:")
            logger.info(f"   Cards found: {total_cards}")
            logger.info(f"   Jobs scraped: {jobs_scraped}")
            logger.info(f"   Tier 1 filtered: {tier1_filtered}")
            logger.info(f"   Tier 2 skipped: {tier2_skipped}")
            logger.info(f"   Tier 3 filtered: {tier3_filtered}")
            logger.info(f"   Filter rate: {(tier1_filtered+tier2_skipped+tier3_filtered)/total_cards*100 if total_cards > 0 else 0:.1f}%")
            print(f"\n📊 PAGE {page} METRICS:")
            print(f"   Cards found: {total_cards}")
            print(f"   Jobs scraped: {jobs_scraped}")
            print(f"   Tier 1 filtered: {tier1_filtered}")
            print(f"   Tier 2 skipped: {tier2_skipped}")
            print(f"   Tier 3 filtered: {tier3_filtered}")
            print(f"   Filter rate: {(tier1_filtered+tier2_skipped+tier3_filtered)/total_cards*100 if total_cards > 0 else 0:.1f}%")
            
            # Try to go to next page
            if page < max_pages:
                next_clicked = click_next_page(driver)
                if not next_clicked:
                    logger.info(f"No more pages after page {page}")
                    break
                time.sleep(3)
        
        # Final comprehensive metrics (like Jora)
        total_tier1 = sum(1 for j in all_jobs if j.get('_filtered') and j.get('_filter_tier') == 1)
        total_tier2 = sum(1 for j in all_jobs if j.get('_filtered') and j.get('_filter_tier') == 2)
        total_tier3 = sum(1 for j in all_jobs if j.get('_filtered') and j.get('_filter_tier') == 3)
        total_filtered = total_tier1 + total_tier2 + total_tier3
        total_cards_processed = len(all_jobs) + total_filtered
        
        logger.info(f"")
        logger.info(f"🎯 SEEK FINAL METRICS:")
        logger.info(f"   Total cards: {total_cards_processed}")
        logger.info(f"   Jobs scraped: {len(all_jobs)}")
        logger.info(f"   Tier 1 filtered: {total_tier1} ({total_tier1/total_cards_processed*100 if total_cards_processed > 0 else 0:.1f}%)")
        logger.info(f"   Tier 2 skipped: {total_tier2} ({total_tier2/total_cards_processed*100 if total_cards_processed > 0 else 0:.1f}%)")
        logger.info(f"   Tier 3 filtered: {total_tier3} ({total_tier3/total_cards_processed*100 if total_cards_processed > 0 else 0:.1f}%)")
        logger.info(f"   Overall efficiency: {total_filtered/total_cards_processed*100 if total_cards_processed > 0 else 0:.1f}%")
        
        print(f"\n🎯 SEEK FINAL METRICS:")
        print(f"   Total cards: {total_cards_processed}")
        print(f"   Jobs scraped: {len(all_jobs)}")
        print(f"   Tier 1 filtered: {total_tier1} ({total_tier1/total_cards_processed*100 if total_cards_processed > 0 else 0:.1f}%)")
        print(f"   Tier 2 skipped: {total_tier2} ({total_tier2/total_cards_processed*100 if total_cards_processed > 0 else 0:.1f}%)")
        print(f"   Tier 3 filtered: {total_tier3} ({total_tier3/total_cards_processed*100 if total_cards_processed > 0 else 0:.1f}%)")
        print(f"   Overall efficiency: {total_filtered/total_cards_processed*100 if total_cards_processed > 0 else 0:.1f}%")
        
        logger.info(f"Total jobs scraped: {len(all_jobs)}")
        
    finally:
        safe_quit_driver(driver)
    
    return all_jobs


def extract_job_from_seek_card(card, driver, optimizer=None):
    """Extract job info from Seek card element"""
    try:
        # Title - try multiple selectors
        title = None
        title_selectors = [
            "a[data-automation='jobTitle']",
            "h3 a",
            "h2 a",
            "a[href*='/job/']"
        ]
        
        for selector in title_selectors:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, selector)
                title = title_elem.text.strip()
                url = title_elem.get_attribute('href')
                if title:
                    break
            except NoSuchElementException:
                continue
        
        if not title:
            return None
        
        # TIER 1: Title filtering
        if optimizer:
            logger.info(f"✅ TIER 1 CHECK: '{title}'")
            should_scrape, reason = optimizer.tier1_should_scrape_title(title)
            if not should_scrape:
                logger.info(f"❌ TIER 1 FILTERED: '{title}' - {reason}")
                return {
                    'title': title,
                    '_filtered': True,
                    '_filter_tier': 1,
                    '_filter_reason': reason
                }
            logger.info(f"✅ TIER 1 PASSED: '{title}'")
        
        # Company
        logger.info(f"📌 Extracting company for: '{title}'")
        company = "Unknown"
        company_selectors = [
            "a[data-automation='jobCompany']",
            "a[data-automation='jobAdvertiser']",
            "span[data-automation='jobCompany']"
        ]
        
        for selector in company_selectors:
            try:
                company = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                if company:
                    logger.info(f"📌 Company found: '{company}'")
                    break
            except NoSuchElementException:
                continue
        logger.info(f"📌 Company result: '{company}'")
        
        # Location
        location = "Australia"
        location_selectors = [
            "a[data-automation='jobLocation']",
            "span[data-automation='jobSuburb']"
        ]
        
        for selector in location_selectors:
            try:
                location = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                if location:
                    break
            except NoSuchElementException:
                continue
        
        # Description snippet
        description = ""
        desc_selectors = [
            "span[data-automation='jobShortDescription']",
            "span[data-automation='jobDescription']"
        ]
        
        for selector in desc_selectors:
            try:
                description = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                if description:
                    break
            except NoSuchElementException:
                continue
        
        # TIER 2: Deduplication
        logger.info(f"📌 Starting TIER 2 check for: '{title}'")
        if optimizer:
            is_duplicate, reason = optimizer.tier2_is_duplicate(url, title, company, [])
            logger.info(f"📌 TIER 2 check completed - duplicate: {is_duplicate}")
            if is_duplicate:
                logger.info(f"❌ TIER 2 FILTERED: '{title}' - {reason}")
                return {
                    'title': title,
                    'company': company,
                    '_filtered': True,
                    '_filter_tier': 2,
                    '_filter_reason': reason
                }
            logger.info(f"✅ TIER 2 PASSED: '{title}' (unique job)")
        
        # TIER 3: Description quality
        if optimizer and description:
            logger.info(f"📌 Starting TIER 3 quality check for: '{title}'")
            has_quality, reason = optimizer.tier3_has_quality_description(description)
            if not has_quality:
                logger.info(f"❌ TIER 3 FILTERED: '{title}' - {reason}")
                return {
                    'title': title,
                    'company': company,
                    '_filtered': True,
                    '_filter_tier': 3,
                    '_filter_reason': reason
                }
            logger.info(f"✅ TIER 3 PASSED (snippet): '{title}' (desc length: {len(description)})")
                # Fetch full description by clicking on the job
        full_description = fetch_job_description(card, driver, url)
        if full_description:
            description = full_description
                # Posted date
        posted_date = None
        try:
            posted_date = card.find_element(By.CSS_SELECTOR, "span[data-automation='jobListingDate']").text.strip()
        except NoSuchElementException:
            pass
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'requirement_text': '',
            'url': url,
            'posted_date': posted_date,
            'source': 'seek'
        }
        
    except Exception as e:
        logger.error(f"Error extracting job from card: {e}")
        return None


def click_next_page(driver):
    """Click next page button on Seek"""
    next_selectors = [
        "a[data-automation='page-next']",
        "a[aria-label='Next']",
        "button[aria-label='Next']",
        "a.next",
        "button.next"
    ]
    
    for selector in next_selectors:
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, selector)
            if next_button.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                next_button.click()
                logger.info("Clicked next page button")
                return True
        except NoSuchElementException:
            continue
        except Exception as e:
            logger.debug(f"Could not click next button with {selector}: {e}")
            continue
    
    return False


def fetch_job_description(card, driver, job_url):
    """
    Fetch full job description from Seek job detail page
    
    Args:
        card: The job card element
        driver: Selenium WebDriver
        job_url: URL of the job posting
    
    Returns:
        Full description text or None
    """
    try:
        # Open job in new tab to avoid losing search results page
        original_window = driver.current_window_handle
        driver.execute_script(f"window.open('{job_url}', '_blank');")
        time.sleep(2)
        
        # Switch to new tab
        windows = driver.window_handles
        driver.switch_to.window(windows[-1])
        
        # Wait for job details to load
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation='jobAdDetails'], div[class*='job-details']"))
            )
        except TimeoutException:
            logger.warning("Timeout waiting for job details")
            driver.close()
            driver.switch_to.window(original_window)
            return None
        
        # Extract full description
        desc_selectors = [
            "div[data-automation='jobAdDetails']",
            "div[data-automation='jobDescription']",
            "div[class*='job-details']",
            "div[class*='_description_']"
        ]
        
        description = None
        for selector in desc_selectors:
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                description = desc_elem.text.strip()
                if description and len(description) > 100:
                    break
            except NoSuchElementException:
                continue
        
        # Close tab and switch back
        driver.close()
        driver.switch_to.window(original_window)
        time.sleep(0.5)
        
        return description
        
    except Exception as e:
        logger.error(f"Error fetching job description: {e}")
        # Make sure we switch back to original window
        try:
            driver.switch_to.window(original_window)
        except:
            pass
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    test_url = "https://www.seek.com.au/artificial-intelligence-jobs/in-All-Perth-WA?daterange=1"
    jobs = scrape_seek_jobs(test_url, max_pages=3)
    
    print(f"\n{'='*80}")
    print(f"Total jobs scraped: {len(jobs)}")
    print(f"{'='*80}\n")
    
    for i, job in enumerate(jobs[:5], 1):
        print(f"{i}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print()
