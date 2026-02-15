"""
Jora Scraper - Selenium-based (Production Ready)

Matches LinkedIn/Seek scraper architecture:
- Uses Selenium for JavaScript-rendered pages
- Full 3-tier optimization (Title, Dedup, Quality)
- Fetches complete job descriptions
- Supports pagination (unlimited pages)
- Cookie-based authentication

Author: AI Agent
Created: 7 February 2026
Status: Production Ready
"""

import time
import random
import logging
import pickle
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import shared driver utility
import sys
sys.path.insert(0, str(Path(__file__).parent))
from driver_utils import create_chrome_driver, safe_quit_driver, test_driver_health
from optimization import OptimizationManager

# Setup logging
logger = logging.getLogger(__name__)


def create_jora_driver(headless=True):
    """
    Create Chrome WebDriver with stealth mode for Jora
    Uses shared driver utility with robust error handling
    
    Args:
        headless: Run in headless mode (default: True)
    
    Returns:
        Selenium WebDriver instance
    """
    try:
        driver = create_chrome_driver(
            headless=headless,
            stealth_mode=True,  # Jora needs stealth mode
            user_profile=False
        )
        logger.info("✅ Jora driver initialized with stealth mode")
        return driver
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Jora driver: {e}")
        raise


def load_jora_cookies(driver):
    """
    Load Jora cookies from data/jora_cookies.pkl
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        Number of cookies loaded
    """
    cookie_file = Path(__file__).parent.parent / 'data' / 'jora_cookies.pkl'
    
    if not cookie_file.exists():
        logger.warning(f"⚠️ No cookie file found at {cookie_file}")
        return 0
    
    try:
        # Navigate to Jora first (required for cookies to work)
        driver.get("https://au.jora.com")
        time.sleep(1)
        
        # Load cookies
        with open(cookie_file, 'rb') as f:
            cookies = pickle.load(f)
        
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logger.debug(f"Could not add cookie {cookie.get('name', 'unknown')}: {e}")
        
        logger.info(f"✅ Loaded {len(cookies)} cookies for Jora")
        return len(cookies)
        
    except Exception as e:
        logger.error(f"❌ Failed to load Jora cookies: {e}")
        return 0


def scrape_jora_jobs(url, max_pages=10, search_config=None):
    """
    Scrape jobs from Jora with pagination and 3-tier optimization
    
    Args:
        url: Jora search URL
        max_pages: Maximum pages to scrape (default: 10)
        search_config: Search configuration dict with id, keyword, location, etc.
    
    Returns:
        List of job dictionaries
    """
    driver = None
    all_jobs = []
    
    # Metrics
    total_cards = 0
    tier1_filtered = 0
    tier2_skipped = 0
    tier3_filtered = 0
    
    try:
        # Initialize driver and optimizer
        driver = create_jora_driver(headless=True)
        optimizer = OptimizationManager()
        
        # Load cookies
        load_jora_cookies(driver)
        
        logger.info(f"🔷 JORA: Starting scrape from {url}")
        logger.info(f"🔷 JORA: Max pages: {max_pages}")
        
        # Navigate to search URL
        driver.get(url)
        time.sleep(5)  # Wait for initial load
        
        # Paginate through results (Jora uses numbered page buttons)
        for page_num in range(1, max_pages + 1):
            logger.info(f"🔷 JORA: Scraping page {page_num}/{max_pages}")
            print(f"\n🔷 JORA: Page {page_num} of {max_pages}")
            
            # Wait for job cards to load
            try:
                WebDriverWait(driver, 15).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.job-card")) > 0
                )
                time.sleep(2)  # Extra wait for dynamic content
            except Exception as e:
                logger.warning(f"⚠️ Timeout waiting for jobs on page {page_num}: {e}")
            
            # Find job cards - Jora uses div.job-card (specifically with class "result")
            job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job-card.result")
            
            # If no results with that specific combo, try fallback
            if not job_cards:
                job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job-card")
            
            if not job_cards:
                logger.warning(f"⚠️ No job cards found on page {page_num}")
                break
            
            page_jobs = 0
            page_tier1_filtered = 0
            page_tier2_skipped = 0
            page_tier3_filtered = 0
            
            logger.info(f"📊 Found {len(job_cards)} job cards on page {page_num}")
            print(f"   📊 {len(job_cards)} job cards found")
            
            total_cards += len(job_cards)
            
            for card_idx, card in enumerate(job_cards, 1):
                try:
                    # Extract job from card with 3-tier filtering
                    job = extract_job_from_jora_card(card, driver, optimizer, search_config)
                    
                    if job is None:
                        continue
                    
                    # Check filter reason
                    if job.get('_filtered_tier1'):
                        page_tier1_filtered += 1
                        tier1_filtered += 1
                        continue
                    
                    if job.get('_filtered_tier2'):
                        page_tier2_skipped += 1
                        tier2_skipped += 1
                        continue
                    
                    if job.get('_filtered_tier3'):
                        page_tier3_filtered += 1
                        tier3_filtered += 1
                        continue
                    
                    # Clean up internal flags
                    job.pop('_filtered_tier1', None)
                    job.pop('_filtered_tier2', None)
                    job.pop('_filtered_tier3', None)
                    
                    all_jobs.append(job)
                    page_jobs += 1
                    
                    print(f"      ✅ Job {card_idx}: {job['title'][:60]}")
                    
                except Exception as e:
                    logger.debug(f"Error extracting job from card {card_idx}: {e}")
                    continue
            
            # Page summary
            total_filtered = page_tier1_filtered + page_tier2_skipped + page_tier3_filtered
            efficiency = (total_filtered / len(job_cards) * 100) if len(job_cards) > 0 else 0
            
            print(f"\n   📊 Page {page_num} Summary:")
            print(f"      • Jobs scraped: {page_jobs}")
            print(f"      • Tier 1 filtered: {page_tier1_filtered}")
            print(f"      • Tier 2 skipped: {page_tier2_skipped}")
            print(f"      • Tier 3 filtered: {page_tier3_filtered}")
            print(f"      • Efficiency: {efficiency:.1f}%")
            
            logger.info(f"""
📊 PAGE {page_num} METRICS:
   Cards found: {len(job_cards)}
   Jobs scraped: {page_jobs}
   Tier 1 filtered: {page_tier1_filtered}
   Tier 2 skipped: {page_tier2_skipped}
   Tier 3 filtered: {page_tier3_filtered}
   Efficiency: {efficiency:.1f}%""")
            
            # Try to go to next page
            if page_num < max_pages:
                if not click_next_page_jora(driver):
                    logger.info(f"✅ No more pages available (stopped at page {page_num})")
                    break
                time.sleep(3)  # Wait for next page to load
        
        # Final summary
        total_filtered = tier1_filtered + tier2_skipped + tier3_filtered
        overall_efficiency = (total_filtered / total_cards * 100) if total_cards > 0 else 0
        
        # Set optimizer metrics before final display
        if optimizer:
            optimizer.metrics['jobs_scraped'] = len(all_jobs)
        
        print(f"\n{'='*70}")
        print(f"🎯 JORA SCRAPING COMPLETE")
        print(f"{'='*70}")
        print(f"Total job cards seen: {total_cards}")
        if total_cards > 0:
            print(f"Tier 1 (Title filter): {tier1_filtered} filtered ({tier1_filtered/total_cards*100:.1f}%)")
            print(f"Tier 2 (Deduplication): {tier2_skipped} skipped ({tier2_skipped/total_cards*100:.1f}%)")
            print(f"Tier 3 (Quality filter): {tier3_filtered} filtered ({tier3_filtered/total_cards*100:.1f}%)")
            print(f"✓ Jobs scraped: {len(all_jobs)} ({len(all_jobs)/total_cards*100:.1f}%)")
            print(f"Overall efficiency: {overall_efficiency:.1f}%")
        else:
            print(f"Tier 1 filtered: {tier1_filtered}")
            print(f"Tier 2 skipped: {tier2_skipped}")
            print(f"Tier 3 filtered: {tier3_filtered}")
            print(f"✓ Jobs scraped: {len(all_jobs)}")
        print(f"{'='*70}\n")
        
        logger.info(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         JORA FINAL SCRAPING METRICS                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
  
  Total cards seen: {total_cards}
  Tier 1 (Title filter): {tier1_filtered} filtered ({tier1_filtered/total_cards*100 if total_cards > 0 else 0:.1f}%)
  Tier 2 (Deduplication): {tier2_skipped} skipped ({tier2_skipped/total_cards*100 if total_cards > 0 else 0:.1f}%)
  Tier 3 (Quality filter): {tier3_filtered} filtered ({tier3_filtered/total_cards*100 if total_cards > 0 else 0:.1f}%)
  ✓ Jobs scraped: {len(all_jobs)} ({len(all_jobs)/total_cards*100 if total_cards > 0 else 0:.1f}%)
  
  Total filtered: {total_filtered} ({overall_efficiency:.1f}%)
""")
        
    except Exception as e:
        logger.error(f"❌ Error during Jora scraping: {e}")
        raise
    finally:
        if driver:
            safe_quit_driver(driver)
            logger.info("✅ Jora driver closed")
    
    return all_jobs


def extract_job_from_jora_card(card, driver, optimizer, search_config=None):
    """
    Extract job data from Jora job card with 3-tier filtering
    
    Args:
        card: Selenium WebElement (div.job-card)
        driver: Selenium WebDriver instance
        optimizer: OptimizationManager instance
        search_config: Search configuration dict
    
    Returns:
        Job dict or None if filtered
    """
    try:
        # Extract title and URL - Jora uses h2.job-title with nested <a>
        title = None
        job_url = None
        
        # Approach 1: Get title from h2.job-title element (text is in h2, not in <a>)
        try:
            job_title_h2 = card.find_element(By.CSS_SELECTOR, 'h2.job-title')
            title = job_title_h2.text.strip()
            
            # Get URL from the link inside h2
            title_link = job_title_h2.find_element(By.TAG_NAME, 'a')
            job_url = title_link.get_attribute('href')
        except Exception as e:
            logger.debug(f"Failed to extract from h2.job-title: {e}")
        
        # Approach 2: Find any link with /job/ and get text from its parent/card
        if not (title and job_url):
            try:
                job_link = card.find_element(By.CSS_SELECTOR, 'a[href*="/job/"]')
                job_url = job_link.get_attribute('href')
                
                # Try to get title from h2 or h3 within card
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, 'h2, h3')
                    title = title_elem.text.strip()
                except:
                    # Fallback: get all card text and extract first line
                    card_text = card.text.strip()
                    if card_text:
                        # Title is usually the first non-empty line
                        lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                        if lines:
                            title = lines[0]
            except Exception as e:
                logger.debug(f"Failed to extract from link approach: {e}")
        
        if not title or not job_url:
            logger.warning(f"❌ Could not find title or URL in Jora card - Title: '{title}', URL: '{job_url}'")
            # Try to see what's in the card
            try:
                card_text = card.text[:100]
                logger.warning(f"   Card preview: {card_text}")
            except:
                pass
            return None
        
        # TIER 1: Title filtering (before extracting other fields)
        should_scrape, reason = optimizer.tier1_should_scrape_title(title)
        if not should_scrape:
            logger.info(f"⛔ TIER 1 FILTERED: '{title}' - Reason: {reason}")
            return {'_filtered_tier1': True}
        
        logger.info(f"✅ TIER 1 PASSED: '{title}'")
        
        # Extract company - Jora shows company in specific elements
        logger.info(f"📌 Extracting company for: '{title}'")
        company = "Unknown"
        company_selectors = [
            'div.job-company',          # Jora-specific class
            'span.job-company',
            'div[class*="company"]',
            'span[class*="company"]',
            'a[class*="company"]',
        ]
        
        for selector in company_selectors:
            try:
                company_elem = card.find_element(By.CSS_SELECTOR, selector)
                company_text = company_elem.text.strip()
                if company_text and len(company_text) > 1:
                    company = company_text
                    logger.info(f"📌 Company found: '{company}'")
                    break
            except:
                continue
        
        logger.info(f"📌 Company result: '{company}'")
        
        # TIER 2: Deduplication check (before fetching description)
        logger.info(f"📌 Starting TIER 2 check for: '{title}'")
        job_hash = f"{title.lower()}_{company.lower()}_{job_url}"
        
        try:
            # Note: Pass empty list [] as 4th positional argument (not all_jobs=)
            is_duplicate, reason = optimizer.tier2_is_duplicate(job_url, title, company, [])
            logger.info(f"📌 TIER 2 check completed - duplicate: {is_duplicate}")
        except Exception as tier2_error:
            logger.error(f"❌ TIER 2 ERROR for '{title}': {tier2_error}")
            logger.error(f"   Exception type: {type(tier2_error).__name__}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return None
        
        if is_duplicate:
            logger.info(f"⛔ TIER 2 DUPLICATE: '{title}' at {company} - {reason}")
            return {'_filtered_tier2': True}
        
        logger.info(f"✅ TIER 2 PASSED: '{title}' (unique job)")
        
        # Extract location - Jora shows location in specific elements
        location = "Australia"
        location_selectors = [
            'span.job-location',        # Jora-specific class
            'div.job-location',
            'div[class*="location"]',
            'span[class*="location"]',
        ]
        
        for selector in location_selectors:
            try:
                loc_elem = card.find_element(By.CSS_SELECTOR, selector)
                loc_text = loc_elem.text.strip()
                if loc_text and len(loc_text) > 1:
                    location = loc_text
                    break
            except:
                continue
        
        # Fetch full description from job detail page
        description = fetch_jora_job_description(card, driver, job_url)
        
        if not description:
            logger.warning(f"⚠️ No description for: {title}")
            description = ""
        
        # TIER 3: Description quality check
        has_quality, reason = optimizer.tier3_has_quality_description(description)
        if not has_quality:
            logger.info(f"⛔ TIER 3 FILTERED: '{title}' - {reason} (desc length: {len(description)})")
            return {'_filtered_tier3': True}
        
        logger.info(f"✅ TIER 3 PASSED: '{title}' (desc length: {len(description)})")
        
        # Build job dict
        job = {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'url': job_url,
            'posted_date': None,
            'source': 'jora',
            'region': search_config.get('region', 'australia') if search_config else 'australia',
            'source_search_id': search_config.get('search_id') if search_config else None,
            'search_keyword': search_config.get('keyword') if search_config else None
        }
        
        return job
        
    except Exception as e:
        logger.debug(f"Error extracting job from Jora card: {e}")
        return None


def fetch_jora_job_description(card, driver, job_url):
    """
    Fetch full job description by opening job in new tab
    
    Args:
        card: Job card element (not used, for API consistency)
        driver: Selenium WebDriver instance
        job_url: URL of job detail page
    
    Returns:
        Full description text or empty string
    """
    original_window = driver.current_window_handle
    
    try:
        # Open new tab
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        
        # Navigate to job detail page
        driver.get(job_url)
        time.sleep(2)  # Wait for load
        
        # Try multiple selectors for description
        description_selectors = [
            'div[class*="description"]',
            'div[class*="job-detail"]',
            'div[class*="job_detail"]',
            'div[id*="description"]',
            'section[class*="description"]',
            'article[class*="description"]'
        ]
        
        description = ""
        for selector in description_selectors:
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                description = desc_elem.text.strip()
                if description and len(description) > 200:
                    break
            except:
                continue
        
        # If no structured description, try getting all text from main content
        if not description or len(description) < 200:
            try:
                main_elem = driver.find_element(By.TAG_NAME, 'main')
                description = main_elem.text.strip()
            except:
                pass
        
        # Close tab and switch back
        driver.close()
        driver.switch_to.window(original_window)
        
        return description
        
    except Exception as e:
        logger.debug(f"Error fetching Jora description from {job_url}: {e}")
        # Make sure we're back on original window
        try:
            driver.close()
        except:
            pass
        driver.switch_to.window(original_window)
        return ""


def click_next_page_jora(driver):
    """
    Click next page button on Jora (the "Next" link)
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        True if next page clicked, False if no more pages
    """
    try:
        # Scroll to bottom to ensure pagination is visible
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Find all links and look for "Next" text
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        
        for link in all_links:
            link_text = link.text.strip()
            if link_text in ['Next', 'next', '>', '›', '»']:
                # Found a next button - check if it's disabled
                href = link.get_attribute('href')
                classes = link.get_attribute('class') or ''
                
                # Check for disabled state
                if 'disabled' in classes.lower() or not href or href == '#':
                    logger.info("⚠️ Next button is disabled (last page)")
                    return False
                
                # Click the link
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", link)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", link)
                    logger.info(f"✅ Clicked 'Next' button -> {href[:80]}")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to click next link: {e}")
                    continue
        
        logger.info("⚠️ No next page button found (reached end)")
        return False
        
    except Exception as e:
        logger.error(f"Error clicking next page: {e}")
        return False


if __name__ == '__main__':
    # Test the scraper
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    test_url = "https://au.jora.com/j?sp=search&trigger_source=serp&a=7d&q=graduate%20artificial%20intelligence%20engineer&l=Australia"
    
    print("\n" + "="*70)
    print("🧪 TESTING JORA SCRAPER (SELENIUM)")
    print("="*70 + "\n")
    
    jobs = scrape_jora_jobs(
        url=test_url,
        max_pages=3,
        search_config={
            'id': 'test_jora',
            'keyword': 'Graduate Artificial Intelligence Engineer',
            'location': 'Australia',
            'region': 'australia',
            'search_id': 'jora_graduate_ai_engineer_australia'
        }
    )
    
    print(f"\n✅ Test complete: {len(jobs)} jobs scraped")
    
    if jobs:
        print("\n📋 Sample jobs:")
        for job in jobs[:5]:
            print(f"   • {job['title']} - {job['company']}")
            print(f"     Description: {len(job['description'])} chars")
