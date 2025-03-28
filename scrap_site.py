#scrap_site.py do not change filename do not remove line
import logging
import os
import random
import time
from datetime import datetime

# Lazy import of playwright to avoid startup overhead if not needed
playwright_available = False
try:
    from playwright.sync_api import sync_playwright
    playwright_available = True
except ImportError:
    logging.warning("Playwright not installed. Web scraping will not function properly.")
    logging.warning("Install with: pip install playwright pyee greenlet typing-extensions websockets && playwright install chromium")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("scrap_site")

def scrape_website(url, timeout=30000, screenshot_dir="debug_screenshots"):
    """Scrape content from a web page using Playwright.
    
    Args:
        url: The URL to scrape
        timeout: Maximum time to wait for page load in milliseconds
        screenshot_dir: Directory to save debug screenshots
        
    Returns:
        String with article content or None if scraping failed
    """
    if not url:
        return None
        
    if not playwright_available:
        logger.error("Playwright not available. Cannot scrape web content.")
        return None
        
    logger.info(f"Using Playwright to scrape content from: {url}")
    
    try:
        # Check if URL is valid
        if not url.startswith(('http://', 'https://')):
            logger.error(f"Invalid URL format: {url}")
            return None
            
        # Use retry logic
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    retry_wait = retry_delay * (2 ** (attempt - 1)) + random.uniform(0.1, 0.5)
                    logger.info(f"Retry attempt {attempt+1}/{max_retries} for {url}, waiting {retry_wait:.1f}s")
                    time.sleep(retry_wait)
                
                with sync_playwright() as p:
                    # Launch browser in headless mode with appropriate options
                    browser_type = p.chromium
                    
                    # Configure browser launch options
                    browser_args = []
                    
                    # Add arguments to handle SSL errors
                    browser_args.extend([
                        '--ignore-certificate-errors',
                        '--ignore-ssl-errors',
                        '--disable-web-security'
                    ])
                    
                    browser = browser_type.launch(
                        headless=True,
                        args=browser_args
                    )
                    
                    # Configure context with realistic browser profile
                    context = browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        locale="en-US",
                        timezone_id="America/New_York",
                        permissions=["geolocation"]
                    )
                    
                    # Open new page with timeout
                    page = context.new_page()
                    page.set_default_timeout(timeout)
                    
                    # Add extra headers to avoid being detected as a bot
                    page.set_extra_http_headers({
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Referer": "https://www.google.com/",
                        "DNT": "1",
                        "Upgrade-Insecure-Requests": "1"
                    })
                    
                    # Only block media files but allow CSS and other resources for better SPA support
                    page.route("**/*.{png,jpg,jpeg,gif,svg,pdf,mp4,webm,ogg,mp3,wav,ico}", 
                              lambda route: route.abort())
                    
                    try:
                        # Handle hash-based SPAs better
                        is_hash_based_spa = "#" in url
                        
                        if is_hash_based_spa:
                            # For hash-based SPAs, first load the base URL
                            base_url = url.split("#")[0]
                            hash_fragment = url.split("#")[1]
                            
                            logger.info(f"Detected hash-based SPA. First loading base URL: {base_url}")
                            response = page.goto(base_url, wait_until="domcontentloaded", timeout=timeout)
                            
                            # Wait longer for SPA to initialize
                            page.wait_for_timeout(5000)
                            
                            # Then navigate to the specific hash route
                            logger.info(f"Setting hash fragment: #{hash_fragment}")
                            page.evaluate(f"() => {{ window.location.hash = '#{hash_fragment}'; }}")
                            
                            # Wait for route change to fully load
                            page.wait_for_timeout(8000)
                        else:
                            # Standard navigation
                            logger.info(f"Navigating to: {url}")
                            response = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                        
                        # Check if we got a valid response
                        if not response or response.status >= 400:
                            logger.warning(f"Received HTTP status {response.status if response else 'unknown'} for {url}")
                            if attempt == max_retries - 1:
                                # Last attempt, try to get content anyway
                                pass
                            else:
                                # Not last attempt, try again
                                browser.close()
                                continue
                    except Exception as e:
                        logger.warning(f"Error navigating to {url}: {e}")
                        if "ERR_CERT" in str(e) or "SSL" in str(e) or "certificate" in str(e).lower():
                            # Handle SSL errors by continuing and trying to get content anyway
                            logger.warning(f"SSL certificate error, continuing anyway: {e}")
                            pass
                        elif attempt == max_retries - 1:
                            # Last attempt, try to get content anyway
                            pass
                        else:
                            # Not last attempt, try again
                            browser.close()
                            continue
                    
                    # For SPAs, wait extra time for JavaScript to render
                    page.wait_for_timeout(5000)
                    
                    # Special handling for sites with strict security
                    if "hunyuan.tencent.com" in url:
                        logger.info("Detected site with strict security measures, using special handling")
                        # Try to avoid bot detection by simulating user interaction
                        try:
                            # Move mouse randomly
                            page.mouse.move(100, 100)
                            page.wait_for_timeout(500)
                            page.mouse.move(200, 300)
                            
                            # Scroll down to trigger lazy loading
                            page.evaluate("window.scrollTo(0, 300)")
                            page.wait_for_timeout(2000)
                            page.evaluate("window.scrollTo(0, 600)")
                            page.wait_for_timeout(2000)
                            
                            # Wait longer for content to appear
                            page.wait_for_timeout(10000)
                        except Exception as e:
                            logger.warning(f"Error during special site handling: {e}")
                            pass
                    
                    # Try to detect and handle cookie/GDPR consent dialogs
                    for consent_btn in ["accept", "agree", "cookie", "consent", "gdpr"]:
                        try:
                            # Try to find and click buttons with consent-related text
                            page.click(f"button:has-text('{consent_btn}')", timeout=1000, force=True)
                        except:
                            pass
                    
                    # Extract content using common article selectors
                    content = None
                    selectors = [
                        "article", "main", ".article", ".post", ".content", "#content", 
                        ".article-content", ".post-content", "[itemprop='articleBody']",
                        ".entry-content", ".main-content", ".post-body", "#article-body",
                        ".story-body", ".story-content", ".news-content", ".document-content",
                        ".blog-post", ".blog-content", ".cms-content", ".page-content"
                    ]
                    
                    # Enhanced SPA content extraction - try to get meaningful text elements
                    try:
                        logger.info("Attempting enhanced content extraction")
                        content = page.evaluate("""() => {
                            return Array.from(document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, article, .article, .content'))
                                .map(el => el.textContent)
                                .filter(text => text && text.trim().length > 10)
                                .join('\\n\\n');
                        }""")
                    except Exception as e:
                        logger.warning(f"Enhanced extraction failed: {e}")
                    
                    # If enhanced extraction didn't yield much, try standard selectors
                    if not content or len(content.strip()) < 200:
                        # Try each selector
                        for selector in selectors:
                            try:
                                # Check if selector exists
                                if page.query_selector(selector):
                                    # Get text content from the selector
                                    content = page.eval_on_selector(
                                        selector,
                                        "el => el.textContent"
                                    )
                                    if content and len(content.strip()) > 200:  # Only accept if substantial content
                                        break
                            except Exception:
                                continue
                    
                    # If still no content found with selectors, get entire body text
                    if not content or len(content.strip()) < 200:
                        try:
                            content = page.eval_on_selector("body", "el => el.textContent")
                        except Exception as e:
                            logger.error(f"Error extracting body content: {e}")
                            content = None
                    
                    # Take a screenshot for debugging if no content found
                    if not content or len(content.strip()) < 50:
                        try:
                            os.makedirs(screenshot_dir, exist_ok=True)
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            domain = url.split("//")[-1].split("/")[0].replace(".", "_")
                            screenshot_path = os.path.join(screenshot_dir, f"{domain}_{timestamp}.png")
                            page.screenshot(path=screenshot_path)
                            logger.warning(f"Saved debug screenshot to {screenshot_path}")
                        except Exception as e:
                            logger.error(f"Failed to save debug screenshot: {e}")
                    
                    # Close browser
                    browser.close()
                    
                    # Process and clean the content
                    if content:
                        # Clean the content
                        content = ' '.join(content.split())  # Normalize whitespace
                        
                        # Remove excessive whitespace
                        import re
                        content = re.sub(r'\s+', ' ', content).strip()
                        
                        # Limit content length
                        max_length = 5000
                        if len(content) > max_length:
                            content = content[:max_length] + "... (content truncated)"
                        
                        logger.info(f"Successfully scraped {len(content)} characters from {url}")
                        return content
                    else:
                        logger.warning(f"No content found on page: {url}")
                        return None
                        
            except Exception as e:
                logger.error(f"Playwright error scraping {url} (attempt {attempt+1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All retry attempts failed for {url}")
                    return None
        
        return None
        
    except Exception as e:
        logger.error(f"Unhandled error scraping {url}: {str(e)}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        content = scrape_website(url)
        if content:
            print(f"Successfully scraped {len(content)} characters")
            print(content[:500] + "..." if len(content) > 500 else content)
        else:
            print(f"Failed to scrape content from {url}")
    else:
        print("Usage: python scrap_site.py <url>")