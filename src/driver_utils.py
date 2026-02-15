"""
Chrome WebDriver Utility - Robust driver creation for all scrapers

Handles:
- M1/M2 Mac ARM64 architecture
- Proper driver path resolution
- Error handling and retries
- Automatic cleanup
- Fallback mechanisms

Author: AI Agent
Created: 2026-02-14
"""

import logging
import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


def _resolve_chromedriver_path():
    """
    Resolve ChromeDriver path with special handling for M1/M2 Macs
    
    Returns:
        str: Path to chromedriver executable
    """
    try:
        # Install ChromeDriver using webdriver-manager
        driver_path = ChromeDriverManager().install()
        logger.info(f"ChromeDriver path from manager: {driver_path}")
        
        # Fix for M1/M2 Mac ARM64 architecture
        # Sometimes webdriver-manager returns the wrong path
        if not driver_path.endswith('chromedriver') or 'THIRD_PARTY' in driver_path:
            driver_dir = os.path.dirname(driver_path)
            logger.info(f"Searching for chromedriver in: {driver_dir}")
            
            # Look for chromedriver executable in the directory
            # Prioritize exact match 'chromedriver' first
            exact_match = os.path.join(driver_dir, 'chromedriver')
            if os.path.isfile(exact_match):
                driver_path = exact_match
                # Make it executable if it isn't
                os.chmod(driver_path, 0o755)
                logger.info(f"Found chromedriver: {driver_path}")
            else:
                # Fallback: look for any chromedriver file
                for file in os.listdir(driver_dir):
                    if file.startswith('chromedriver') and not file.endswith('.txt') and file != 'chromedriver':
                        potential_path = os.path.join(driver_dir, file)
                        if os.path.isfile(potential_path) and os.access(potential_path, os.X_OK):
                            driver_path = potential_path
                            logger.info(f"Found alternative chromedriver: {driver_path}")
                            break
        
        # Make sure it's executable (important on Unix)
        if os.path.isfile(driver_path):
            os.chmod(driver_path, 0o755)
            logger.info(f"✅ ChromeDriver ready: {driver_path}")
        else:
            raise FileNotFoundError(f"ChromeDriver not found at {driver_path}")
        
        return driver_path
        
    except Exception as e:
        logger.error(f"Failed to resolve ChromeDriver path: {e}")
        raise


def create_chrome_driver(headless=True, stealth_mode=False, user_profile=False, max_retries=3):
    """
    Create Chrome WebDriver with robust error handling
    
    Args:
        headless: Run in headless mode (default: True)
        stealth_mode: Enable selenium-stealth for anti-detection (default: False)
        user_profile: Use a persistent Chrome profile (default: False)
        max_retries: Maximum retry attempts (default: 3)
    
    Returns:
        Selenium WebDriver instance
        
    Raises:
        Exception: If driver creation fails after all retries
    """
    # Load config
    try:
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path, 'r') as f:
            import json
            config = json.load(f)
        selenium_config = config.get('selenium', {})
    except Exception as e:
        logger.warning(f"Could not load config, using defaults: {e}")
        selenium_config = {}
    
    # Attempt to create driver with retries
    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to create Chrome driver (attempt {attempt + 1}/{max_retries})...")
            
            # Setup Chrome options
            chrome_options = Options()
            
            # User profile (optional, for persistent login)
            if user_profile:
                profile_dir = os.path.join(os.getcwd(), 'chrome_profile')
                chrome_options.add_argument(f'--user-data-dir={profile_dir}')
                logger.info(f"Using Chrome profile: {profile_dir}")
            
            # Headless mode
            if headless:
                chrome_options.add_argument('--headless=new')
                logger.info("Running in headless mode")
            
            # Anti-detection measures
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Window size and user agent
            window_size = selenium_config.get('window_size', '1920,1080')
            user_agent = selenium_config.get('user_agent', 
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            chrome_options.add_argument(f'--window-size={window_size}')
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            # Resolve driver path
            driver_path = _resolve_chromedriver_path()
            
            # Create service
            service = Service(driver_path)
            
            # Create driver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Additional anti-detection: mask webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Apply selenium-stealth if requested
            if stealth_mode:
                try:
                    from selenium_stealth import stealth
                    stealth(driver,
                        languages=["en-AU", "en"],
                        vendor="Google Inc.",
                        platform="MacIntel",
                        webgl_vendor="Intel Inc.",
                        renderer="Intel Iris OpenGL Engine",
                        fix_hairline=True,
                    )
                    logger.info("✅ Stealth mode enabled")
                except ImportError:
                    logger.warning("selenium-stealth not available, skipping")
            
            # Test driver is working
            driver.set_page_load_timeout(30)
            
            logger.info("✅ Chrome driver created successfully")
            return driver
            
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            
            # Try to cleanup if driver was partially created
            try:
                if 'driver' in locals():
                    driver.quit()
            except:
                pass
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            
    # All retries failed
    error_msg = f"Failed to create Chrome driver after {max_retries} attempts. Last error: {last_error}"
    logger.error(error_msg)
    raise Exception(error_msg)


def safe_quit_driver(driver):
    """
    Safely quit driver with error handling
    
    Args:
        driver: Selenium WebDriver instance
    """
    if driver is None:
        return
    
    try:
        driver.quit()
        logger.info("✅ Driver cleaned up successfully")
    except Exception as e:
        logger.warning(f"Error during driver cleanup: {e}")
        # Force kill if normal quit fails
        try:
            driver.service.process.kill()
        except:
            pass


def test_driver_health(driver, test_url="https://www.google.com", timeout=10):
    """
    Test if driver is healthy and responsive
    
    Args:
        driver: Selenium WebDriver instance
        test_url: URL to test (default: Google)
        timeout: Timeout in seconds
        
    Returns:
        bool: True if driver is healthy, False otherwise
    """
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(test_url)
        # Check if page loaded
        return len(driver.page_source) > 0
    except Exception as e:
        logger.error(f"Driver health check failed: {e}")
        return False
