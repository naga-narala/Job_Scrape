"""
Seek Job Scraper

Scrapes job listings from Seek (seek.com.au)
- Requires cookies/session (like LinkedIn)
- URL pattern: https://www.seek.com.au/{keyword}-jobs/in-All-Perth-WA
- Similar structure to LinkedIn scraper
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import logging
import json
import re

try:
    from optimization import OptimizationManager
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning("Optimization module not available - running without 3-tier optimization")
    OPTIMIZATION_AVAILABLE = False


class SeekScraper:
    """Scraper for Seek job board"""
    
    BASE_URL = "https://www.seek.com.au"
    
    def __init__(self, cookies=None, delay_range=(2, 5)):
        """
        Initialize Seek scraper
        
        Args:
            cookies: Dictionary of cookies from browser session
            delay_range: Tuple of (min, max) seconds to wait between requests
        """
        self.delay_range = delay_range
        self.logger = logging.getLogger(__name__)
        
        # Initialize optimizer
        self.optimizer = None
        if OPTIMIZATION_AVAILABLE:
            try:
                self.optimizer = OptimizationManager()
                self.logger.info("3-Tier Optimization enabled for Seek")
            except Exception as e:
                self.logger.warning(f"Could not initialize optimizer: {e}")
        
        # User agent to match browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        if cookies:
            self.session.cookies.update(cookies)
    
    def _delay(self):
        """Random delay between requests"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def _format_url_part(self, text):
        """Format text for Seek URL"""
        # Seek uses format: "machine-learning-jobs"
        return text.lower().replace(' ', '-').replace('/', '-')
    
    def _format_location(self, location):
        """
        Format location for Seek URL
        Examples:
        - "Perth" -> "All-Perth-WA"
        - "Melbourne" -> "All-Melbourne-VIC"  
        - "Australia" -> "All-Australia"
        """
        location_lower = location.lower()
        
        # Map locations to Seek format
        location_map = {
            'perth': 'All-Perth-WA',
            'melbourne': 'All-Melbourne-VIC',
            'sydney': 'All-Sydney-NSW',
            'brisbane': 'All-Brisbane-QLD',
            'adelaide': 'All-Adelaide-SA',
            'canberra': 'All-Canberra-ACT',
            'australia': 'All-Australia',
            'remote': 'All-Australia'  # Seek doesn't have specific remote filter
        }
        
        for key, value in location_map.items():
            if key in location_lower:
                return value
        
        # Default to All-Australia if not recognized
        return 'All-Australia'
    
    def search_jobs(self, keyword, location="Perth", time_filter="1", page=1):
        """
        Search for jobs on Seek
        
        Args:
            keyword: Search keyword (e.g., "AI Engineer", "Machine Learning")
            location: Location filter (default: "Perth")
            time_filter: Days since posted - "1", "3", "7", "14", "31" (default: "1")
            page: Page number (default: 1)
        
        Returns:
            List of job dictionaries with keys:
            - title: Job title
            - company: Company name  
            - location: Job location
            - description: Job description/snippet
            - url: Full job URL
            - posted_date: Posted date (if available)
            - employment_type: Full-time, Part-time, etc.
            - source: "seek"
        """
        jobs = []
        
        # Format keyword and location
        keyword_formatted = self._format_url_part(keyword)
        location_formatted = self._format_location(location)
        
        # Build URL: https://www.seek.com.au/machine-learning-jobs/in-All-Perth-WA
        search_url = f"{self.BASE_URL}/{keyword_formatted}-jobs/in-{location_formatted}"
        
        # Add query parameters
        params = {
            'daterange': time_filter,  # Days since posted
            'page': page
        }
        
        try:
            self.logger.info(f"Searching Seek: '{keyword}' in {location} (page {page})")
            print(f"🟣 SEEK: Processing URL: {search_url}")
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Seek uses <article> tags with data-testid="job-card"
            job_cards = soup.find_all('article', attrs={'data-testid': 'job-card'})
            
            if not job_cards:
                self.logger.warning(f"No job cards found for '{keyword}'")
                # Try alternate selectors
                job_cards = soup.select('article[data-card-type="JobCard"]')
            
            self.logger.info(f"Found {len(job_cards)} job cards")
            
            # 3-Tier Optimization Metrics
            total_cards = len(job_cards)
            tier1_filtered = 0
            tier2_skipped = 0
            tier3_filtered = 0
            
            for card in job_cards:
                try:
                    # Parse basic job info first
                    job = self._parse_job_card(card)
                    if not job:
                        continue
                    
                    # TIER 1: Title filtering (before full scrape)
                    if self.optimizer:
                        should_scrape, reason = self.optimizer.tier1_should_scrape_title(job['title'])
                        if not should_scrape:
                            tier1_filtered += 1
                            continue
                    
                    # TIER 2: Deduplication check
                    if self.optimizer:
                        is_duplicate, reason = self.optimizer.tier2_is_duplicate(job['url'], job['title'], job['company'], [])
                        if is_duplicate:
                            tier2_skipped += 1
                            continue
                    
                    # TIER 3: Description quality check (before AI scoring)
                    if self.optimizer and job.get('description'):
                        has_quality, reason = self.optimizer.tier3_has_quality_description(job['description'])
                        if not has_quality:
                            tier3_filtered += 1
                            continue
                    
                    print(f"   📋 Found job: {job['title']} at {job['company']}")
                    jobs.append(job)
                    
                except Exception as e:
                    self.logger.error(f"Error parsing job card: {e}")
                    continue
            
            # Log optimization metrics
            if self.optimizer:
                self.logger.info(f"""
3-TIER OPTIMIZATION METRICS (SEEK):
  Total cards seen: {total_cards}
  Tier 1 (Title): {tier1_filtered} filtered ({tier1_filtered/total_cards*100:.1f}%)
  Tier 2 (Dedup): {tier2_skipped} skipped ({tier2_skipped/total_cards*100:.1f}%)
  Tier 3 (Quality): {tier3_filtered} filtered ({tier3_filtered/total_cards*100:.1f}%)
  Jobs scraped: {len(jobs)}
  Total filtered: {tier1_filtered + tier2_skipped + tier3_filtered}
  Efficiency gain: {(tier1_filtered + tier2_skipped + tier3_filtered)/total_cards*100:.1f}%""")
            
            # Delay before next request
            self._delay()
            
        except Exception as e:
            self.logger.error(f"Error searching Seek for '{keyword}': {e}")
        
        return jobs
    
    def _parse_job_card(self, card):
        """
        Parse a single Seek job card
        
        Args:
            card: BeautifulSoup element for job card
        
        Returns:
            Job dictionary or None if parsing fails
        """
        try:
            # Title and URL
            title_elem = card.find('a', attrs={'data-automation': 'jobTitle'})
            if not title_elem:
                title_elem = card.select_one('h1 a, h2 a, h3 a')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            job_url = title_elem.get('href', '')
            
            # Make absolute URL
            if job_url.startswith('/'):
                job_url = f"{self.BASE_URL}{job_url}"
            
            # Company
            company_elem = card.find('a', attrs={'data-automation': 'jobCompany'})
            if not company_elem:
                company_elem = card.select_one('[data-automation="jobAdvertiser"]')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.find('a', attrs={'data-automation': 'jobLocation'})
            if not location_elem:
                location_elem = card.select_one('[data-automation="jobSuburb"]')
            location = location_elem.get_text(strip=True) if location_elem else "Australia"
            
            # Description/Snippet
            desc_elem = card.find('span', attrs={'data-automation': 'jobShortDescription'})
            if not desc_elem:
                desc_elem = card.select_one('[data-automation="jobDescription"]')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Posted date
            date_elem = card.find('span', attrs={'data-automation': 'jobListingDate'})
            posted_date = date_elem.get_text(strip=True) if date_elem else None
            
            # Employment type
            type_elem = card.find('span', attrs={'data-automation': 'jobClassification'})
            if not type_elem:
                type_elem = card.select_one('[data-automation="jobWorkType"]')
            employment_type = type_elem.get_text(strip=True) if type_elem else None
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'requirement_text': '',  # Seek doesn't have separate requirements section
                'url': job_url,
                'posted_date': posted_date,
                'employment_type': employment_type,
                'source': 'seek'
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing job card: {e}")
            return None
    
    def scrape_jobs_from_url(self, url, max_jobs=20):
        """
        Scrape jobs from a Seek URL
        
        Args:
            url: Full Seek search URL
            max_jobs: Maximum number of jobs to scrape
        
        Returns:
            List of job dictionaries
        """
        # Parse URL to extract keyword and location
        # Example: https://www.seek.com.au/graduate-artificial-intelligence-engineer-jobs/in-All-Perth-WA?daterange=1
        import re
        from urllib.parse import urlparse, parse_qs
        
        try:
            # Extract keyword from URL path
            path = urlparse(url).path
            # Path format: /keyword-jobs/in-Location
            match = re.search(r'/(.+)-jobs/in-(.+)', path)
            
            if match:
                keyword = match.group(1).replace('-', ' ')
                location_part = match.group(2)
            else:
                self.logger.warning(f"Could not parse URL: {url}")
                return []
            
            # Extract time filter from query params
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            time_filter = params.get('daterange', ['1'])[0]
            
            # Use search_jobs method
            jobs = self.search_jobs(keyword, location=location_part, time_filter=time_filter, page=1)
            
            # Limit to max_jobs
            return jobs[:max_jobs]
            
        except Exception as e:
            self.logger.error(f"Error scraping from URL {url}: {e}")
            return []
    
    def get_job_details(self, job_url):
        """
        Fetch full job description from Seek job detail page
        
        Args:
            job_url: URL of the job posting
        
        Returns:
            Full job description text or None
        """
        try:
            self.logger.info(f"Fetching job details: {job_url}")
            response = self.session.get(job_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Seek uses <div data-automation="jobAdDetails">
            desc_container = soup.find('div', attrs={'data-automation': 'jobAdDetails'})
            if not desc_container:
                desc_container = soup.select_one('[data-automation="jobDescription"]')
            
            if desc_container:
                return desc_container.get_text(separator='\n', strip=True)
            
            self.logger.warning(f"No description found for {job_url}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching job details from {job_url}: {e}")
            return None


def main():
    """Test the Seek scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Note: For testing, you'd need to provide cookies from your browser
    # Example:
    # cookies = {
    #     'JobseekerSessionId': 'your-session-id',
    #     'JobseekerVisitorId': 'your-visitor-id'
    # }
    
    scraper = SeekScraper()  # No cookies = may get limited results
    
    # Test search
    jobs = scraper.search_jobs("machine learning", location="Perth")
    
    print(f"\n{'='*80}")
    print(f"Seek Scraper Test")
    print(f"Found {len(jobs)} jobs")
    print(f"{'='*80}\n")
    
    for i, job in enumerate(jobs[:3], 1):  # Show first 3
        print(f"{i}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Posted: {job['posted_date']}")
        print(f"   Type: {job['employment_type']}")
        print(f"   URL: {job['url']}")
        print(f"   Snippet: {job['description'][:100]}...")
        print()


if __name__ == '__main__':
    main()
