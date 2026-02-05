"""
Jora Job Scraper

Scrapes job listings from Jora (au.jora.com)
- Uses Selenium with stealth mode to bypass Cloudflare
- URL pattern: https://au.jora.com/j?sp=search&trigger_source=serp&a=24h&q={keyword}&l={location}
"""

import time
import random
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

try:
    from optimization import OptimizationManager
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning("Optimization module not available - running without 3-tier optimization")
    OPTIMIZATION_AVAILABLE = False


class JoraScraper:
    """Scraper for Jora job board using Selenium"""
    
    BASE_URL = "https://au.jora.com"
    SEARCH_URL = "https://au.jora.com/j"
    
    def __init__(self, delay_range=(2, 5), headless=True):
        """
        Initialize Jora scraper with Selenium
        
        Args:
            delay_range: Tuple of (min, max) seconds to wait between requests
            headless: Run browser in headless mode (no GUI)
        """
        self.delay_range = delay_range
        self.logger = logging.getLogger(__name__)
        self.headless = headless
        self.driver = None
        
        # Initialize optimizer
        self.optimizer = None
        if OPTIMIZATION_AVAILABLE:
            try:
                self.optimizer = OptimizationManager()
                self.logger.info("3-Tier Optimization enabled for Jora")
            except Exception as e:
                self.logger.warning(f"Could not initialize optimizer: {e}")
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with stealth mode to bypass Cloudflare"""
        if self.driver:
            return
        
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Apply stealth mode
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="MacIntel",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            self.logger.info("Chrome WebDriver initialized with stealth mode")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def _delay(self):
        """Random delay between requests"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("WebDriver closed")
    
    def __enter__(self):
        """Context manager entry"""
        self._init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def search_jobs(self, keyword, location="Perth WA", time_filter="24h", max_results=50):
        """
        Search for jobs on Jora using Selenium
        
        Args:
            keyword: Search keyword (e.g., "junior ai engineer")
            location: Location filter (e.g., "Perth WA", "Melbourne VIC")
            time_filter: Time filter - "24h", "3d", "7d", "14d" (default: "24h")
            max_results: Maximum number of jobs to fetch (default: 50)
        
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        try:
            # Initialize driver if not already done
            self._init_driver()
            
            # Build URL with query parameters
            from urllib.parse import urlencode
            params = {
                'sp': 'search',
                'trigger_source': 'serp',
                'a': time_filter,
                'q': keyword,
                'l': location
            }
            url = f"{self.SEARCH_URL}?{urlencode(params)}"
            
            self.logger.info(f"Searching Jora: '{keyword}' in {location}")
            self.logger.info(f"URL: {url}")
            print(f"🔷 JORA: Processing URL: {url}")
            
            # Load page
            self.driver.get(url)
            
            # Wait longer for JavaScript to render (Jora uses React)
            time.sleep(8)  # Initial load
            
            # Wait for job listings to load - try multiple selectors
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: len(d.find_elements(By.TAG_NAME, "article")) > 0 or
                              len(d.find_elements(By.CSS_SELECTOR, "[class*='job']")) > 5 or
                              len(d.find_elements(By.TAG_NAME, "h2")) > 3
                )
                time.sleep(3)  # Extra wait for all content
            except Exception as e:
                self.logger.warning(f"Timeout waiting for jobs to load: {e}")
            
            # Try multiple selectors to find job cards
            job_elements = []
            
            # Try 1: <article> tags (most common for job cards)
            articles = self.driver.find_elements(By.TAG_NAME, "article")
            if articles and len(articles) > 3:
                job_elements = articles
                self.logger.info(f"Found {len(articles)} <article> elements")
            
            # Try 2: h2 or h3 tags (job titles)
            if not job_elements:
                headers = self.driver.find_elements(By.CSS_SELECTOR, "h2 a, h3 a")
                if headers:
                    job_elements = headers
                    self.logger.info(f"Found {len(headers)} <h2>/<h3> link elements")
            
            # Try 3: job card containers (common class patterns)
            if not job_elements:
                cards = self.driver.find_elements(By.CSS_SELECTOR, "[class*='job-card'], [class*='job_card'], [class*='jobcard']")
                if cards:
                    job_elements = cards
                    self.logger.info(f"Found {len(cards)} job-card elements")
            
            # Try 4: data attributes
            if not job_elements:
                data_elems = self.driver.find_elements(By.CSS_SELECTOR, "[data-job-id], [data-jobid], [data-jid]")
                if data_elems:
                    job_elements = data_elems
                    self.logger.info(f"Found {len(data_elems)} elements with job data attributes")
            
            # Try 5: Links with /job/ in href (last resort)
            if not job_elements:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                job_links = [l for l in all_links if l.get_attribute('href') and '/job/' in l.get_attribute('href')]
                if job_links:
                    job_elements = job_links[:max_results]
                    self.logger.info(f"Found {len(job_links)} links with '/job/' in href")
            
            if not job_elements:
                self.logger.warning("No job elements found with any selector!")
                # Save page source for debugging
                with open('jora_debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                self.logger.info("Saved page source to jora_debug_page.html for inspection")
                return jobs
            
            # Limit to max_results but ensure we process enough
            elements_to_process = job_elements[:min(len(job_elements), max_results)]
            self.logger.info(f"Processing {len(elements_to_process)} job elements")
            
            # 3-Tier Optimization Metrics
            total_cards = len(elements_to_process)
            tier1_filtered = 0
            tier2_skipped = 0
            tier3_filtered = 0
            
            for elem in elements_to_process:
                try:
                    job = self._parse_job_element(elem)
                    if not job:
                        continue
                    
                    # TIER 1: Title filtering (before fetching full description)
                    if self.optimizer:
                        should_scrape, reason = self.optimizer.tier1_should_scrape_title(job['title'])
                        if not should_scrape:
                            tier1_filtered += 1
                            continue
                    
                    # TIER 2: Deduplication check (before fetching full description)
                    if self.optimizer:
                        is_duplicate, reason = self.optimizer.tier2_is_duplicate(job['url'], job['title'], job['company'], [])
                        if is_duplicate:
                            tier2_skipped += 1
                            continue
                    
                    # Fetch full description from detail page (only if not filtered)
                    try:
                        description = self.get_job_details(job['url'])
                        if description:
                            job['description'] = description
                        else:
                            # Use summary/snippet if full description fetch fails
                            job['description'] = job.get('snippet', '')
                    except Exception as e:
                        self.logger.warning(f"Failed to get description for {job['title']}: {e}")
                        job['description'] = job.get('snippet', '')
                        
                        # TIER 3: Description quality check (before AI scoring)
                        if self.optimizer:
                            has_quality, reason = self.optimizer.tier3_has_quality_description(description)
                            if not has_quality:
                                tier3_filtered += 1
                                continue
                    
                    print(f"   📋 Found job: {job['title']} at {job['company']}")
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.debug(f"Error parsing job element: {e}")
                    continue
            
            # Log optimization metrics
            if self.optimizer:
                self.logger.info(f"""
3-TIER OPTIMIZATION METRICS (JORA):
  Total cards seen: {total_cards}
  Tier 1 (Title): {tier1_filtered} filtered ({tier1_filtered/total_cards*100:.1f}%)
  Tier 2 (Dedup): {tier2_skipped} skipped ({tier2_skipped/total_cards*100:.1f}%)
  Tier 3 (Quality): {tier3_filtered} filtered ({tier3_filtered/total_cards*100:.1f}%)
  Jobs scraped: {len(jobs)}
  Total filtered: {tier1_filtered + tier2_skipped + tier3_filtered}
  Efficiency gain: {(tier1_filtered + tier2_skipped + tier3_filtered)/total_cards*100:.1f}%""")
            
            self.logger.info(f"Successfully parsed {len(jobs)} jobs")
            
            # Delay before next search
            self._delay()
            
        except Exception as e:
            self.logger.error(f"Error searching Jora for '{keyword}': {e}")
        
        return jobs
    
    def _parse_job_element(self, element):
        """Parse a Jora job element using Selenium"""
        try:
            # Try to find title link
            title_elem = None
            url = None
            
            # If element is already a link
            if element.tag_name == 'a':
                title_elem = element
                url = element.get_attribute('href')
            else:
                # Find link within element - prefer job detail links
                links = element.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    # Skip location-only links
                    if href and 'jobs-in-' in href:
                        continue
                    if href and ('job' in href or '/j/' in href):
                        title_elem = link
                        url = href
                        break
                
                # If no job link found, try any link with meaningful text
                if not title_elem:
                    for link in links:
                        text = link.text.strip()
                        href = link.get_attribute('href')
                        if text and len(text) > 3 and href and 'jobs-in-' not in href:
                            title_elem = link
                            url = href
                            break
            
            if not title_elem or not url:
                return None
            
            # Get title text
            title = title_elem.text.strip()
            if not title or len(title) < 3:
                return None
            
            # Skip if title looks like a location
            location_keywords = ['WA', 'VIC', 'NSW', 'QLD', 'SA', 'ACT', 'NT', 'TAS']
            if any(title.endswith(kw) for kw in location_keywords) and len(title.split()) <= 3:
                return None
            
            # Make absolute URL
            if url.startswith('/'):
                url = f"{self.BASE_URL}{url}"
            
            # Clean URL - extract base job URL without tracking parameters
            # Example: https://au.jora.com/job/Engineer-ABC123?sol_key=xyz&tk=123
            # Should become: https://au.jora.com/job/Engineer-ABC123
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            # Keep only the base path, remove query parameters
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            url = clean_url
            
            # Try to find company (look for text near title)
            company = "Unknown"
            try:
                # Look in parent element
                parent = element if element.tag_name != 'a' else element.find_element(By.XPATH, '..')
                text_elements = parent.find_elements(By.XPATH, ".//*[not(self::a)]")
                for text_elem in text_elements:
                    text = text_elem.text.strip()
                    if text and text != title and len(text) > 2 and len(text) < 100:
                        # Skip ratings (numbers with decimals)
                        if text.replace('.', '').isdigit():
                            continue
                        company = text
                        break
            except:
                pass
            
            # Try to find location
            location = "Australia"
            try:
                # Look for common location patterns
                parent = element if element.tag_name != 'a' else element.find_element(By.XPATH, '..')
                text = parent.text
                for loc in ['Perth', 'Melbourne', 'Sydney', 'Brisbane', 'Adelaide', 'Canberra']:
                    if loc in text:
                        location = loc
                        break
            except:
                pass
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': '',
                'requirement_text': '',  # Jora doesn't have separate requirements section
                'url': url,
                'posted_date': None,
                'employment_type': None,
                'source': 'jora'
            }
        except Exception as e:
            self.logger.debug(f"Error parsing Jora element: {e}")
            return None
    
    def get_job_details(self, job_url):
        """
        Fetch full job description from job detail page
        
        Args:
            job_url: URL of the job posting
        
        Returns:
            Full job description text or None
        """
        try:
            self._init_driver()
            
            self.logger.info(f"Fetching job details: {job_url}")
            self.driver.get(job_url)
            
            # Wait for job description to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='description'], div[class*='detail']"))
                )
            except:
                pass
            
            # Try to find description container
            desc_containers = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='description'], div[class*='detail']")
            if desc_containers:
                return desc_containers[0].text
            
            self.logger.warning(f"No description found for {job_url}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching job details from {job_url}: {e}")
            return None


def main():
    """Test the Jora scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*80)
    print("Testing Jora Scraper with Selenium + Stealth")
    print("="*80 + "\n")
    
    # Use context manager to ensure driver cleanup
    with JoraScraper(headless=True) as scraper:
        # Test search
        jobs = scraper.search_jobs("junior ai engineer", "Perth WA")
        
        print(f"Found {len(jobs)} jobs\n")
        
        for i, job in enumerate(jobs[:5], 1):  # Show first 5
            print(f"{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   URL: {job['url'][:80]}...")
            print()


if __name__ == '__main__':
    main()
