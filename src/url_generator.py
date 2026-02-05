"""
URL Generator for Multi-Source Job Scraping

Reads jobs.txt configuration and generates search URLs for:
- LinkedIn
- Seek  
- Jora

Replaces hardcoded job_searches.json with dynamic generation.
"""

import json
import logging
import re
from pathlib import Path


class URLGenerator:
    """Generate search URLs for all job boards from jobs.txt"""
    
    # Seek URL templates  
    SEEK_TEMPLATE = "https://www.seek.com.au/{keyword_formatted}-jobs/in-{location_formatted}?daterange={days}"
    
    # Jora URL template (uses query params)
    JORA_BASE = "https://au.jora.com/j"
    
    def __init__(self, jobs_file="jobs.txt"):
        """
        Initialize URL generator
        
        Args:
            jobs_file: Path to jobs.txt configuration file
        """
        self.jobs_file = Path(jobs_file)
        self.logger = logging.getLogger(__name__)
        
        if not self.jobs_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {jobs_file}")
        
        # Parse configuration
        self.config = self._parse_jobs_file()
    
    def _parse_jobs_file(self):
        """Parse jobs.txt and extract configuration"""
        with open(self.jobs_file, 'r') as f:
            content = f.read()
        
        config = {
            'job_titles': [],
            'locations': [],
            'job_boards': ['linkedin'],  # Default
            'max_job_age_hours': 24,
            'regions': ['australia']
        }
        
        # Extract job titles (first non-comment, non-empty line after header)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            # Skip comments and section markers
            if line.startswith('#') or line.startswith('[') or not line:
                continue
            # First substantial line should be job titles
            if ',' in line and not ':' in line:
                config['job_titles'] = [title.strip() for title in line.split(',')]
                break
        
        # Extract preferences section
        prefs_section = re.search(r'\[PREFERENCES\](.*?)(?:\[|$)', content, re.DOTALL)
        if prefs_section:
            prefs_text = prefs_section.group(1)
            
            # Locations
            loc_match = re.search(r'locations:\s*(.+)', prefs_text)
            if loc_match:
                config['locations'] = [loc.strip() for loc in loc_match.group(1).split(',')]
            
            # Job boards
            boards_match = re.search(r'job_boards:\s*(.+)', prefs_text)
            if boards_match:
                config['job_boards'] = [board.strip() for board in boards_match.group(1).split(',')]
            
            # Max job age
            age_match = re.search(r'max_job_age_hours:\s*(\d+)', prefs_text)
            if age_match:
                config['max_job_age_hours'] = int(age_match.group(1))
            
            # Regions
            region_match = re.search(r'regions:\s*(.+)', prefs_text)
            if region_match:
                config['regions'] = [r.strip() for r in region_match.group(1).split(',')]
        
        self.logger.info(f"Parsed {len(config['job_titles'])} job titles")
        self.logger.info(f"Locations: {config['locations']}")
        self.logger.info(f"Job boards: {config['job_boards']}")
        
        return config
    
    def _format_keyword_linkedin(self, keyword):
        """Format keyword for LinkedIn URL"""
        return keyword.strip()
    
    def _format_keyword_seek(self, keyword):
        """Format keyword for Seek URL (lowercase, hyphens)"""
        return keyword.lower().strip().replace(' ', '-').replace('/', '-')
    
    def _format_location_linkedin(self, location):
        """Format location for LinkedIn"""
        # LinkedIn location format examples:
        # Perth, Western Australia, Australia
        # Melbourne, Victoria, Australia
        # Australia (for nationwide)
        # Worldwide (for remote)
        
        location_map = {
            'perth': 'Perth, Western Australia, Australia',
            'melbourne': 'Melbourne, Victoria, Australia',
            'sydney': 'Sydney, New South Wales, Australia',
            'brisbane': 'Brisbane, Queensland, Australia',
            'adelaide': 'Adelaide, South Australia, Australia',
            'canberra': 'Canberra, Australian Capital Territory, Australia',
            'remote': 'Australia',  # Remote within Australia
            'australia': 'Australia',
            'all australia': 'Australia',
            'us': 'United States',
            'uk': 'United Kingdom',
            'singapore': 'Singapore',
        }
        
        location_lower = location.lower().strip()
        return location_map.get(location_lower, location)
    
    def _format_location_seek(self, location):
        """Format location for Seek URL"""
        # Seek uses: All-Perth-WA, All-Melbourne-VIC, etc.
        location_map = {
            'perth': 'All-Perth-WA',
            'melbourne': 'All-Melbourne-VIC',
            'sydney': 'All-Sydney-NSW',
            'brisbane': 'All-Brisbane-QLD',
            'adelaide': 'All-Adelaide-SA',
            'canberra': 'All-Canberra-ACT',
            'remote': 'All-Australia',
            'australia': 'All-Australia',
            'all australia': 'All-Australia',
        }
        
        location_lower = location.lower().strip()
        return location_map.get(location_lower, 'All-Australia')
    
    def _format_location_jora(self, location):
        """Format location for Jora URL (uses natural format like 'Perth WA')"""
        location_map = {
            'perth': 'Perth WA',
            'melbourne': 'Melbourne VIC',
            'sydney': 'Sydney NSW',
            'brisbane': 'Brisbane QLD',
            'adelaide': 'Adelaide SA',
            'canberra': 'Canberra ACT',
            'remote': 'Australia',
            'australia': 'Australia',
            'all australia': 'Australia',
        }
        
        location_lower = location.lower().strip()
        return location_map.get(location_lower, 'Australia')
    
    def generate_linkedin_urls(self):
        """Generate LinkedIn search URLs"""
        urls = []
        
        hours = self.config['max_job_age_hours']
        # LinkedIn f_TPR format: r{followed by number in some unit}
        # For 24h: r86400, for 1 week (168h): r604800, etc.
        time_param = str(hours * 3600)  # Convert hours to seconds
        
        # LinkedIn locations with different work type filters
        linkedin_locations = [
            {'name': 'Australia', 'geoId': '101452733', 'work_type': None},  # All work types (onsite, hybrid, remote)
            {'name': 'US', 'geoId': '103644278', 'work_type': '2'}  # Remote only
        ]
        
        for title in self.config['job_titles']:
            for loc in linkedin_locations:
                # Build URL parameters
                params = [
                    f"keywords={self._format_keyword_linkedin(title)}",
                    f"f_TPR=r{time_param}",
                    f"geoId={loc['geoId']}"
                ]
                
                # Add work type filter only for US (remote only)
                if loc['work_type']:
                    params.append(f"f_WT={loc['work_type']}")
                
                url = f"https://www.linkedin.com/jobs/search/?{'&'.join(params)}"
                
                urls.append({
                    'url': url,
                    'source': 'linkedin',
                    'keyword': title,
                    'location': loc['name'],
                    'search_id': f"linkedin_{title.lower().replace(' ', '_')}_{loc['name'].lower()}"
                })
        
        return urls
    
    def generate_seek_urls(self):
        """Generate Seek search URLs"""
        urls = []
        
        # Seek only works for Australia
        if 'australia' not in [r.lower() for r in self.config['regions']]:
            return urls
        
        # Convert hours to days for Seek
        hours = self.config['max_job_age_hours']
        days = max(1, hours // 24)
        
        for title in self.config['job_titles']:
            # Only Australia-wide for Seek
            url = self.SEEK_TEMPLATE.format(
                keyword_formatted=self._format_keyword_seek(title),
                location_formatted='All-Australia',
                days=days
            )
            
            urls.append({
                'url': url,
                'source': 'seek',
                'keyword': title,
                'location': 'Australia',
                'search_id': f"seek_{title.lower().replace(' ', '_')}_australia"
            })
        
        return urls
    
    def generate_jora_urls(self):
        """Generate Jora search URLs"""
        urls = []
        
        # Jora only works for Australia
        if 'australia' not in [r.lower() for r in self.config['regions']]:
            return urls
        
        hours = self.config['max_job_age_hours']
        # Jora uses 'a' parameter: 24h, 7d, 30d, etc.
        if hours <= 24:
            time_param = '24h'
        elif hours <= 168:  # 1 week
            time_param = '7d'
        elif hours <= 720:  # 30 days
            time_param = '30d'
        else:
            time_param = '30d'  # max 30 days
        
        for title in self.config['job_titles']:
            # Only Australia-wide for Jora
            # Build URL with query parameters
            from urllib.parse import urlencode
            params = {
                'sp': 'search',
                'trigger_source': 'serp',
                'a': time_param,
                'q': title.lower(),  # Keep natural format with spaces
                'l': 'Australia'
            }
            url = f"{self.JORA_BASE}?{urlencode(params)}"
            
            urls.append({
                'url': url,
                'source': 'jora',
                'keyword': title,
                'location': 'Australia',
                'search_id': f"jora_{title.lower().replace(' ', '_')}_australia"
            })
        
        return urls
    
    def generate_all_urls(self, output_file=None):
        """
        Generate all search URLs based on configuration
        
        Args:
            output_file: Optional path to save URLs as JSON
        
        Returns:
            Dictionary with URLs for each source
        """
        all_urls = {
            'linkedin': [],
            'seek': [],
            'jora': []
        }
        
        # Generate URLs based on configured job boards
        job_boards = [board.lower().strip() for board in self.config['job_boards']]
        
        if 'linkedin' in job_boards:
            all_urls['linkedin'] = self.generate_linkedin_urls()
        
        if 'seek' in job_boards:
            all_urls['seek'] = self.generate_seek_urls()
        
        if 'jora' in job_boards:
            all_urls['jora'] = self.generate_jora_urls()
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(all_urls, f, indent=2)
            self.logger.info(f"Saved URLs to {output_file}")
        
        # Log statistics
        total_urls = sum(len(urls) for urls in all_urls.values())
        self.logger.info(f"Generated {total_urls} total search URLs:")
        for source, urls in all_urls.items():
            if urls:
                self.logger.info(f"  {source}: {len(urls)} URLs")
        
        return all_urls


def main():
    """Test URL generator"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Generate URLs
    generator = URLGenerator('jobs.txt')
    all_urls = generator.generate_all_urls(output_file='generated_search_urls.json')
    
    print(f"\n{'='*80}")
    print("Generated Search URLs")
    print(f"{'='*80}\n")
    
    for source, urls in all_urls.items():
        if urls:
            print(f"\n{source.upper()} ({len(urls)} URLs):")
            print("-" * 80)
            for i, url_data in enumerate(urls[:3], 1):  # Show first 3
                print(f"{i}. {url_data['keyword']} in {url_data['location']}")
                print(f"   {url_data['url']}")
            if len(urls) > 3:
                print(f"   ... and {len(urls) - 3} more")


if __name__ == '__main__':
    main()
