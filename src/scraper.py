import logging
import time
import pickle
import random
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

try:
    from optimization import OptimizationManager
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    logger.warning("Optimization module not available - running without 3-tier optimization")
    OPTIMIZATION_AVAILABLE = False

COOKIES_FILE = Path(__file__).parent.parent / 'data' / 'linkedin_cookies.pkl'
COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / 'config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def create_driver(headless=True, use_profile=False):
    config = _load_config()
    selenium_config = config.get('selenium', {})
    chrome_options = Options()
    
    # Option to use a separate Chrome profile for persistent login
    # Note: Can't use main Chrome profile while Chrome is running
    if use_profile:
        import os
        profile_dir = os.path.join(os.getcwd(), 'chrome_profile')
        chrome_options.add_argument(f'--user-data-dir={profile_dir}')
        logger.info(f"Using Chrome profile: {profile_dir}")
    
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(f'--window-size={selenium_config.get("window_size", "1920,1080")}')
    chrome_options.add_argument(f'user-agent={selenium_config.get("user_agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")}')
    
    # Fix for webdriver-manager extraction issue on Mac ARM64
    import os
    driver_path = ChromeDriverManager().install()
    
    # If path ends with wrong file, find the actual chromedriver
    if not driver_path.endswith('chromedriver') or 'THIRD_PARTY' in driver_path:
        driver_dir = os.path.dirname(driver_path)
        # Look for chromedriver executable in the directory
        for file in os.listdir(driver_dir):
            if file == 'chromedriver' or (file.startswith('chromedriver') and not file.endswith('.txt')):
                driver_path = os.path.join(driver_dir, file)
                break
    
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def save_cookies(driver):
    try:
        cookies = driver.get_cookies()
        with open(COOKIES_FILE, 'wb') as f:
            pickle.dump(cookies, f)
        logger.info(f"Saved {len(cookies)} cookies")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies: {e}")
        return False


def load_cookies(driver):
    config = _load_config()
    selenium_config = config.get('selenium', {})
    try:
        if not COOKIES_FILE.exists():
            return False
        with open(COOKIES_FILE, 'rb') as f:
            cookies = pickle.load(f)
        driver.get("https://www.linkedin.com")
        time.sleep(selenium_config.get('load_timeout', 2))
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        logger.info(f"Loaded {len(cookies)} cookies")
        return True
    except Exception as e:
        logger.error(f"Failed to load cookies: {e}")
        return False


def is_logged_in(driver):
    config = _load_config()
    selenium_config = config.get('selenium', {})
    try:
        current_url = driver.current_url
        time.sleep(selenium_config.get('load_timeout', 2))
        
        # Check if we're on login/authwall page
        if '/login' in current_url or '/authwall' in current_url or '/uas/login' in current_url:
            logger.info("Not logged in - on login/auth page")
            return False
        
        # If we're already on a valid LinkedIn page (feed, jobs, etc), we're logged in
        if 'linkedin.com' in current_url and not any(x in current_url for x in ['/login', '/authwall', '/uas']):
            logger.info(f"LinkedIn session active (on {current_url})")
            return True
        
        logger.info("Login verification failed")
        return False
    except Exception as e:
        logger.error(f"Error checking login status: {e}")
        return False


def manual_login_helper():
    logger.info("MANUAL LOGIN REQUIRED")
    driver = create_driver(headless=False)
    try:
        driver.get("https://www.linkedin.com/login")
        print("\nPlease login to LinkedIn in the browser.")
        print("After login, press ENTER here.\n")
        input("Press ENTER after logged in...")
        
        # Navigate to feed to check login
        driver.get("https://www.linkedin.com/feed")
        config = _load_config()
        selenium_config = config.get('selenium', {})
        time.sleep(selenium_config.get('description_fetch_delay', 3))
        
        if is_logged_in(driver):
            save_cookies(driver)
            print("\nLogin successful! Cookies saved.\n")
            return True
        else:
            print("\nLogin failed. Please make sure you completed the login.\n")
            return False
    finally:
        driver.quit()


def extract_job_from_card(card, search_config, driver, optimizer=None):
    try:
        # Try multiple title selectors
        title = None
        title_selectors = [
            "h3.base-search-card__title",
            "a.job-card-list__title",
            "span.job-card-list__title",
            ".job-card-container__link",
            "a[data-tracking-control-name*='job']"
        ]
        for selector in title_selectors:
            try:
                title = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                if title:
                    break
            except:
                continue
        
        if not title:
            logger.debug("Could not extract title from card")
            return None
        
        # TIER 1: Title Pre-Filtering (before clicking/scraping)
        if optimizer:
            should_scrape, reason = optimizer.tier1_should_scrape_title(title)
            if not should_scrape:
                logger.debug(f"Tier 1 filtered: {title} - {reason}")
                return {'filtered': 'tier1', 'reason': reason, 'title': title}
        
        # Try multiple company selectors
        company = "Unknown"
        company_selectors = [
            "h4.base-search-card__subtitle",
            "span.job-card-container__company-name",
            ".job-card-container__primary-description",
            "div.artdeco-entity-lockup__subtitle"
        ]
        for selector in company_selectors:
            try:
                company = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                if company:
                    break
            except:
                continue
        
        # Try multiple location selectors
        location = "Unknown"
        location_selectors = [
            "span.job-search-card__location",
            ".job-card-container__metadata-item",
            "span.job-card-container__metadata-wrapper"
        ]
        for selector in location_selectors:
            try:
                location = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                if location and location != company:
                    break
            except:
                continue
        
        # Try multiple link selectors
        url = None
        link_selectors = [
            "a.base-card__full-link",
            "a.job-card-list__title",
            "a.job-card-container__link",
            "a[href*='/jobs/view/']",
            "a",  # Fallback: any link
        ]
        for selector in link_selectors:
            try:
                links = card.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/jobs/view/' in href:
                        url = href.split('?')[0]
                        break
                if url:
                    break
            except:
                continue
        
        if not url:
            logger.warning(f"Could not extract URL for job: {title}")
            # Try getting job ID from card attributes
            try:
                job_id = card.get_attribute('data-job-id') or card.get_attribute('data-entity-urn')
                if job_id:
                    url = f"https://www.linkedin.com/jobs/view/{job_id}"
                    logger.info(f"Constructed URL from job ID: {url}")
            except:
                pass
            
            if not url:
                logger.error(f"Failed to get URL for: {title} - skipping")
                return None
        
        # Get posted date/age from card
        posted_date = ""
        job_age = ""
        try:
            # Try time element first
            time_elem = card.find_element(By.CSS_SELECTOR, "time")
            posted_date = time_elem.get_attribute('datetime') or ""
            job_age = time_elem.text.strip()
        except:
            # Try to find "Posted X days ago" text
            try:
                card_text = card.text.lower()
                if 'hour' in card_text or 'day' in card_text or 'week' in card_text or 'month' in card_text:
                    lines = card_text.split('\n')
                    for line in lines:
                        if any(word in line for word in ['hour', 'day', 'week', 'month', 'ago']):
                            job_age = line.strip()
                            break
            except:
                pass
        
        # Click the job card to load details in the side panel
        config = _load_config()
        selenium_config = config.get('selenium', {})
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", card)
            time.sleep(selenium_config.get('click_delay', 0.5))
            
            # Try clicking with JavaScript if regular click fails
            try:
                card.click()
            except:
                driver.execute_script("arguments[0].click();", card)
            
            # Wait longer for details panel to load
            min_delay = selenium_config.get('load_timeout', 2)
            max_delay = selenium_config.get('description_fetch_delay', 3)
            time.sleep(random.uniform(min_delay, max_delay))
            
            # Extra wait for description to load (LinkedIn lazy loads this)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-description-content__text, div.jobs-box__html-content, div.jobs-description__content"))
                )
            except:
                logger.debug("Description element took longer to load")
                time.sleep(selenium_config.get('load_timeout', 2))  # Extra fallback wait
            
            # Extract full job details from the details panel
            description = ""
            requirement_text = ""
            skills = []
            seniority = ""
            employment_type = ""
            job_function = ""
            industries = ""
            
            try:
                # Find the job details panel
                details_panel = driver.find_element(By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card, div.jobs-details, div.jobs-unified-top-card")
                
                # Get full description - try multiple times if needed
                desc_element = None
                logger.info(f"📌 Fetching full description for: '{title}'")
                max_attempts = selenium_config.get('description_retry_attempts', 3)
                for attempt in range(max_attempts):
                    try:
                        desc_element = driver.find_element(By.CSS_SELECTOR, "div.jobs-description-content__text, div.jobs-box__html-content, div.jobs-description__content")
                        if desc_element and desc_element.text.strip():
                            logger.info(f"✅ Found description on attempt {attempt + 1}: {len(desc_element.text.strip())} chars")
                            break
                        else:
                            logger.warning(f"⚠️ Description element found but empty on attempt {attempt + 1}")
                        time.sleep(selenium_config.get('retry_delay', 1))  # Wait and retry
                    except Exception as e:
                        logger.warning(f"⚠️ Description not found on attempt {attempt + 1}: {e}")
                        if attempt < max_attempts - 1:
                            time.sleep(selenium_config.get('retry_delay', 1))
                        continue
                
                if desc_element:
                    try:
                        full_text = desc_element.text.strip()
                        logger.info(f"✅ Description extracted: {len(full_text)} chars")
                        
                        # Try to separate requirements section
                        # LinkedIn often has "Requirements added by the job poster" or similar headings
                        requirement_indicators = [
                            "Requirements added by the job poster",
                            "Requirements:",
                            "Required Qualifications",
                            "Minimum Qualifications",
                            "Basic Qualifications",
                            "Must Have"
                        ]
                        
                        requirement_split = None
                        for indicator in requirement_indicators:
                            if indicator in full_text:
                                parts = full_text.split(indicator, 1)
                                if len(parts) == 2:
                                    description = parts[0].strip()
                                    requirement_text = f"{indicator}\n{parts[1].strip()}"
                                    requirement_split = True
                                    logger.debug(f"Found requirements section: {len(requirement_text)} chars")
                                    break
                        
                        # If no split found, use full text as description
                        if not requirement_split:
                            description = full_text
                            # Try to extract requirements from structured elements
                            try:
                                req_elements = desc_element.find_elements(By.XPATH, ".//h3[contains(translate(text(),'REQUIREMENTS','requirements'),'requirements')]/following-sibling::*")
                                if req_elements:
                                    requirement_text = "\n".join([elem.text.strip() for elem in req_elements if elem.text.strip()])
                                    logger.debug(f"Found requirements from structured elements: {len(requirement_text)} chars")
                            except:
                                pass
                        
                        logger.debug(f"Found description: {len(description)} chars")
                    except Exception as e:
                        logger.error(f"Could not extract description text: {e}")
                else:
                    logger.error(f"❌ No description element found after 3 retries for: {title}")
                
                # Get job criteria (seniority, employment type, function, industries)
                # Try multiple selectors for LinkedIn's changing HTML
                try:
                    criteria_items = driver.find_elements(By.CSS_SELECTOR, "li.jobs-unified-top-card__job-insight, ul.jobs-unified-top-card__job-insight-view-model-secondary li")
                    if not criteria_items:
                        # Try alternative structure - look for any list items in top card area
                        criteria_items = driver.find_elements(By.CSS_SELECTOR, "div.job-details-jobs-unified-top-card li, div.jobs-unified-top-card li")
                    
                    logger.debug(f"Found {len(criteria_items)} criteria items")
                    
                    for item in criteria_items:
                        text = item.text.strip()
                        logger.debug(f"Criteria item text: {text}")
                        
                        # Check for seniority
                        if any(word in text for word in ["Seniority level", "Entry level", "Mid-Senior", "Associate", "Internship"]):
                            seniority = text.replace("Seniority level", "").strip()
                        # Check for employment type
                        elif any(word in text for word in ["Employment type", "Full-time", "Part-time", "Contract", "Temporary", "Freelance"]):
                            employment_type = text.replace("Employment type", "").strip()
                        # Check for job function
                        elif "Job function" in text:
                            job_function = text.replace("Job function", "").strip()
                        # Check for industries
                        elif "Industries" in text or "Industry" in text:
                            industries = text.replace("Industries", "").replace("Industry", "").strip()
                except Exception as e:
                    logger.debug(f"Could not find criteria: {e}")
                
                # Get skills if available - try multiple selectors
                try:
                    skill_elements = driver.find_elements(By.CSS_SELECTOR, "span.job-details-skill-match-status-list__skill, span.job-details-skill-match-status-list__text, span[data-tracking-control-name='job_details_skill']")
                    if not skill_elements:
                        # Try alternative - look in any skills section
                        skill_elements = driver.find_elements(By.CSS_SELECTOR, "div.job-details-skill-match-status-list span.artdeco-tag__text")
                    
                    logger.debug(f"Found {len(skill_elements)} skill elements")
                    skills = [s.text.strip() for s in skill_elements if s.text.strip()][:10]
                except Exception as e:
                    logger.debug(f"Could not find skills: {e}")
                
                # If we still don't have seniority/employment from criteria, try to extract from the full page text
                if not seniority or not employment_type or not job_function or not industries:
                    try:
                        # LinkedIn sometimes shows these at the end of the job details or in the right panel
                        # Get all text from the entire right panel/details area
                        try:
                            full_panel = driver.find_element(By.CSS_SELECTOR, "div.jobs-details, div.job-view-layout")
                            full_text = full_panel.text
                        except:
                            # Fallback to getting all visible text
                            full_text = driver.find_element(By.TAG_NAME, "body").text
                        
                        full_text_lower = full_text.lower()
                        
                        # Look for explicit labels
                        if "seniority level:" in full_text_lower or "seniority:" in full_text_lower:
                            # Extract the line after "seniority level:"
                            lines = full_text.split('\n')
                            for i, line in enumerate(lines):
                                if 'seniority level' in line.lower() or ('seniority:' in line.lower() and 'level' not in line.lower()):
                                    if i + 1 < len(lines):
                                        potential_seniority = lines[i + 1].strip()
                                        # Filter out false matches
                                        if len(potential_seniority) < 50 and not any(skip in potential_seniority.lower() for skip in ['benefits', 'salary', 'compensation', 'pay', 'hours']):
                                            seniority = potential_seniority
                                    break
                        elif not seniority:
                            # Fallback to keywords
                            if "entry level" in full_text_lower or ("internship" in full_text_lower and "program" in full_text_lower):
                                seniority = "Entry level"
                            elif "mid-senior" in full_text_lower or "senior level" in full_text_lower:
                                seniority = "Mid-Senior level"
                            elif "associate" in full_text_lower and "degree" not in full_text_lower:
                                seniority = "Associate"
                                
                        if "employment type:" in full_text_lower:
                            lines = full_text.split('\n')
                            for i, line in enumerate(lines):
                                if 'employment type' in line.lower():
                                    if i + 1 < len(lines):
                                        employment_type = lines[i + 1].strip()
                                    break
                        elif not employment_type:
                            # Fallback to keywords
                            if "full-time" in full_text_lower or "full time" in full_text_lower:
                                employment_type = "Full-time"
                            elif "contract" in full_text_lower:
                                employment_type = "Contract"
                            elif "part-time" in full_text_lower or "part time" in full_text_lower:
                                employment_type = "Part-time"
                                
                        # Try to extract job function and industries similarly
                        if "job function:" in full_text_lower and not job_function:
                            lines = full_text.split('\n')
                            for i, line in enumerate(lines):
                                if 'job function' in line.lower():
                                    if i + 1 < len(lines):
                                        job_function = lines[i + 1].strip()
                                    break
                                    
                        if ("industries:" in full_text_lower or "industry:" in full_text_lower) and not industries:
                            lines = full_text.split('\n')
                            for i, line in enumerate(lines):
                                if 'industries' in line.lower() or 'industry:' in line.lower():
                                    if i + 1 < len(lines):
                                        industries = lines[i + 1].strip()
                                    break
                    except Exception as e:
                        logger.debug(f"Text extraction fallback failed: {e}")
                    
            except Exception as e:
                logger.debug(f"Could not extract detailed info: {e}")
        
        except Exception as e:
            logger.debug(f"Could not click job card for details: {e}")
        
        logger.info(f"Extracted: {title} at {company} ({job_age})")
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'requirement_text': requirement_text,
            'url': url,
            'posted_date': posted_date,
            'job_age': job_age,
            'seniority_level': seniority,
            'employment_type': employment_type,
            'job_function': job_function,
            'industries': industries,
            'skills': ', '.join(skills) if skills else "",
            'source_search_id': search_config['id'],
            'region': search_config.get('region', 'australia')
        }
    except Exception as e:
        logger.debug(f"Error extracting job card: {e}")
        return None


def fetch_jobs_from_url(url, search_config, driver, max_pages=None):
    """
    Fetch jobs from LinkedIn with pagination support and 3-tier optimization
    max_pages: Number of pages to scrape (None = unlimited, reads from config)
    LinkedIn shows ~25 jobs per page, uses &start=0, &start=25, &start=50, etc.
    """
    all_jobs = []
    
    print(f"🔵 LINKEDIN: Processing URL: {url}")
    
    # Initialize optimizer
    optimizer = None
    if OPTIMIZATION_AVAILABLE:
        try:
            optimizer = OptimizationManager()
            logger.info("3-Tier Optimization enabled")
        except Exception as e:
            logger.warning(f"Could not initialize optimizer: {e}")
    
    for page_num in range(max_pages):
        start_index = page_num * 25  # LinkedIn pagination: 25 jobs per page
        
        # Build paginated URL
        if '&start=' in url:
            # Replace existing start parameter
            import re
            paginated_url = re.sub(r'&start=\d+', f'&start={start_index}', url)
        else:
            # Add start parameter
            separator = '&' if '?' in url else '?'
            paginated_url = f"{url}{separator}start={start_index}"
        
        logger.info(f"Fetching page {page_num + 1}/{max_pages}: {paginated_url[:80]}...")
        
        try:
            driver.get(paginated_url)
            
            # Check for auth wall
            if '/authwall' in driver.current_url or '/login' in driver.current_url:
                logger.error("Session expired - redirected to login")
                return all_jobs
            
            # Wait longer for React app to render
            logger.info("Waiting for page to load...")
            time.sleep(random.uniform(7, 10))
            
            # Wait for job results list to be present
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
                )
                logger.info("Job results list loaded")
            except:
                logger.warning("Job results list did not load with expected selector - trying fallback methods")
            
            # Scroll aggressively to trigger lazy loading
            logger.info("Scrolling to load job cards...")
            for i in range(8):  # Increased from 5 to 8
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1.5)  # Increased delay
            
            # Extra wait for lazy-loaded job cards
            time.sleep(3)
            
            # Find ALL job cards first
            all_job_cards = []
            job_card_selectors = [
                "ul.jobs-search__results-list > li",  # Updated: direct children of results list
                "li.jobs-search-results__list-item",
                "li.scaffold-layout__list-item",
                "div.job-card-container",
                "div.jobs-search-results__list-item"
            ]
            
            for selector in job_card_selectors:
                all_job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if all_job_cards:
                    logger.info(f"Found {len(all_job_cards)} total job cards with selector: {selector}")
                    break
            
            if not all_job_cards:
                logger.warning("No job cards found with any selector, trying alternative approach...")
                # Try finding by partial class match
                all_job_cards = driver.find_elements(By.CSS_SELECTOR, "li[class*='job']")
                if all_job_cards:
                    logger.info(f"Found {len(all_job_cards)} cards with fallback selector")
            
            if not all_job_cards:
                logger.warning("No job cards found in search results")
                logger.error("No job listings found")
                with open('/tmp/linkedin_page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                logger.info("Saved page source to /tmp/linkedin_page_debug.html")
                driver.save_screenshot('/tmp/linkedin_debug.png')
                logger.info("Saved screenshot to /tmp/linkedin_debug.png")
                continue
            
            # Filter out recommendation sections
            job_cards = []
            for card in all_job_cards:
                try:
                    # Get the card's parent containers to check section type
                    card_html = card.get_attribute("outerHTML").lower()
                    
                    # Skip if in recommendation sections
                    skip_keywords = ["top-pick", "recommended", "discover", "similar", "might"]
                    is_recommendation = any(keyword in card_html for keyword in skip_keywords)
                    
                    if not is_recommendation:
                        job_cards.append(card)
                except:
                    job_cards.append(card)
            
            logger.info(f"After filtering: {len(job_cards)} search result jobs (removed {len(all_job_cards) - len(job_cards)} recommendations)")
            
            if not job_cards:
                logger.warning(f"No job listings found on page {page_num + 1}")
                # If no jobs on this page, stop pagination
                break
            
            page_jobs = []
            page_tier1_filtered = 0
            page_tier2_skipped = 0
            page_tier3_filtered = 0
            
            for card in job_cards:
                job = extract_job_from_card(card, search_config, driver, optimizer)
                if job:
                    # Check if filtered by any tier
                    if job.get('filtered') == 'tier1':
                        page_tier1_filtered += 1
                        continue
                    elif job.get('filtered') == 'tier2':
                        page_tier2_skipped += 1
                        continue
                    elif job.get('filtered') == 'tier3':
                        page_tier3_filtered += 1
                        continue
                    
                    print(f"   📋 Found job: {job['title']} at {job['company']}")
                    page_jobs.append(job)
                time.sleep(random.uniform(0.3, 0.6))
            
            logger.info(f"Page {page_num + 1}: Extracted {len(page_jobs)} jobs | Filtered: T1={page_tier1_filtered} T2={page_tier2_skipped} T3={page_tier3_filtered}")
            all_jobs.extend(page_jobs)
            
            # Only stop if we got ZERO jobs (instead of < 5)
            # This allows continuation even with heavy filtering
            if len(page_jobs) == 0 and len(job_cards) > 0:
                logger.info(f"Got 0 jobs despite {len(job_cards)} cards - all filtered, trying next page")
                # Don't break - continue to next page
            elif len(job_cards) < 10:
                logger.info(f"Only {len(job_cards)} cards found, likely last page")
                break
            
            # Delay between pages to avoid detection
            if page_num < max_pages - 1:  # Don't delay after last page
                delay = random.uniform(8, 12)
                logger.info(f"Waiting {delay:.1f}s before next page...")
                time.sleep(delay)
        
        except Exception as e:
            logger.error(f"Error fetching page {page_num + 1}: {e}")
            # Continue to next page on error
            continue
    
    # Print optimization metrics (Jora-style) - Set final count first
    if optimizer:
        # CRITICAL: Set the final jobs_scraped count
        optimizer.metrics['jobs_scraped'] = len(all_jobs)
        
        metrics = optimizer.get_metrics_summary()
        total = metrics['total_cards_seen']
        t1 = metrics['tier1_title_filtered']
        t2 = metrics['tier2_duplicates_skipped']
        t3 = metrics['tier3_quality_filtered']
        final = metrics['jobs_scraped']
        
        logger.info(f"")
        logger.info(f"🎯 LINKEDIN FINAL METRICS:")
        logger.info(f"   Total cards seen: {total}")
        logger.info(f"   Tier 1 (Title filter): {t1} filtered ({t1/total*100:.1f}%)")
        logger.info(f"   Tier 2 (Deduplication): {t2} skipped ({t2/total*100:.1f}%)")
        logger.info(f"   Tier 3 (Quality filter): {t3} filtered ({t3/total*100:.1f}%)")
        logger.info(f"   ✓ Jobs scraped: {final} ({final/total*100:.1f}%)")
        logger.info(f"   Total filtered: {metrics['total_filtered']} ({metrics['efficiency_gain']})")
        
        print(f"\n🎯 LINKEDIN FINAL METRICS:")
        print(f"   Total cards seen: {total}")
        print(f"   Tier 1 (Title filter): {t1} filtered ({t1/total*100:.1f}%)")
        print(f"   Tier 2 (Deduplication): {t2} skipped ({t2/total*100:.1f}%)")
        print(f"   Tier 3 (Quality filter): {t3} filtered ({t3/total*100:.1f}%)")
        print(f"   ✓ Jobs scraped: {final} ({final/total*100:.1f}%)")
        print(f"   Total filtered: {metrics['total_filtered']} ({metrics['efficiency_gain']})")
    
    logger.info(f"Total extracted: {len(all_jobs)} jobs across {page_num + 1} page(s)")
    return all_jobs


def fetch_all_jobs(searches, api_key=None, headless=True, max_pages=None, config=None):
    """
    Fetch jobs from all search configurations with pagination
    max_pages: Number of pages to scrape per search (None = read from config)
    config: Configuration dict (for max_pages setting)
    """
    all_jobs = []
    strategy_stats = {'Selenium': 0, 'Failed': 0}
    
    # Get max_pages from config if not specified
    if max_pages is None and config:
        max_pages = config.get('linkedin_max_pages', 3)
    elif max_pages is None:
        max_pages = 3  # Fallback default
    
    if not COOKIES_FILE.exists():
        logger.warning("No LinkedIn session. Run: python src/scraper.py --login")
        return [], {'Failed': len([s for s in searches if s.get('enabled', True)])}
    
    driver = None
    try:
        driver = create_driver(headless=headless)
        load_cookies(driver)
        
        if not is_logged_in(driver):
            logger.error("Session expired. Run: python src/scraper.py --login")
            return [], {'Failed': len([s for s in searches if s.get('enabled', True)])}
        
        enabled_searches = [s for s in searches if s.get('enabled', True)]
        total_searches = len(enabled_searches)
        
        for idx, search in enumerate(enabled_searches, 1):
            url = search.get('url')
            if not url:
                strategy_stats['Failed'] += 1
                continue
            
            # Progress header
            region_flag = "🇦🇺" if search.get('region') == 'australia' else "🇺🇸"
            print(f"\n{'=' * 70}")
            print(f"{region_flag} [{idx}/{total_searches}] {search['name']}")
            print(f"{'=' * 70}")
            
            start_time = time.time()
            jobs = fetch_jobs_from_url(url, search, driver, max_pages=max_pages)
            elapsed = time.time() - start_time
            
            if jobs:
                all_jobs.extend(jobs)
                strategy_stats['Selenium'] += 1
                print(f"✅ Found {len(jobs)} jobs in {elapsed:.1f}s")
                logger.info(f"{search['name']}: {len(jobs)} jobs")
            else:
                strategy_stats['Failed'] += 1
                print(f"❌ No jobs found")
            
            # Progress summary
            completed = idx
            remaining = total_searches - idx
            avg_time_per_search = (time.time() - start_time) / idx if idx > 0 else 90
            eta_minutes = (remaining * avg_time_per_search) / 60
            
            print(f"📊 Progress: {completed}/{total_searches} | Jobs so far: {len(all_jobs)} | ETA: {eta_minutes:.0f}m")
            
            time.sleep(random.uniform(5, 10))
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        if driver:
            # If visible mode, pause before closing
            if not headless:
                print(f"\n✓ Finished scraping! Found {len(all_jobs)} total jobs.")
                print("Browser will close in 8 seconds...")
                time.sleep(8)
            driver.quit()
    
    return all_jobs, strategy_stats


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if '--login' in sys.argv:
        manual_login_helper()
    else:
        print("Usage: python src/scraper.py --login")