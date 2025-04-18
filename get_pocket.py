#get_pocket.py ddo not change filename do not remove line
import json
import logging
import os
import sys
import argparse
import random
import time
import asyncio
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException, SSLError, ConnectionError, Timeout

# Import scraping module (will be lazy-loaded when needed)
try:
    from scrap_site import scrape_website
    scraping_available = True
except ImportError:
    logging.warning("scrap_site module not found. Web scraping will not function properly.")
    scraping_available = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("get_pocket")

def load_config(config_path="pipeline_config.json"):
    """Load configuration from JSON file."""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            logger.error(f"Config file not found: {config_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return None

def fetch_pocket_articles(consumer_key, access_token, hours_lookback=24):
    """Fetch articles from Pocket API.
    
    Args:
        consumer_key: Pocket API consumer key
        access_token: Pocket API access token
        hours_lookback: Number of hours to look back for articles
        
    Returns:
        List of article dictionaries
    """
    logger.info(f"Fetching articles from Pocket (last {hours_lookback} hours)...")
    
    # Calculate the unix timestamp for hours_lookback
    since = int((datetime.now() - timedelta(hours=hours_lookback)).timestamp())
    
    # Prepare API request
    url = "https://getpocket.com/v3/get"
    headers = {"Content-Type": "application/json; charset=UTF-8", "X-Accept": "application/json"}
    data = {
        "consumer_key": consumer_key,
        "access_token": access_token,
        "state": "all",  # all, unread, archive
        "sort": "newest",  # newest, oldest, title, site
        "detailType": "complete",  # simple, complete
        "since": since
    }
    
    # Maximum retries for Pocket API calls
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            # Add small delay between retries
            if attempt > 0:
                retry_wait = retry_delay * (2 ** (attempt - 1))
                logger.info(f"Retrying Pocket API call (attempt {attempt+1}/{max_retries}) after {retry_wait:.1f}s")
                time.sleep(retry_wait)
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()  # Raise exception for 4XX/5XX status codes
            
            result = response.json()
            
            # Check if we have any items
            if "list" not in result or not result["list"]:
                logger.info("No articles found in Pocket for the given time range.")
                return []
            
            # Process the items into a more usable format
            articles = []
            for item_id, item in result["list"].items():
                # Basic article info
                article = {
                    "item_id": item_id,
                    "title": item.get("resolved_title") or item.get("given_title") or "Untitled",
                    "url": item.get("resolved_url") or item.get("given_url"),
                    "excerpt": item.get("excerpt", ""),
                    "time_added": datetime.fromtimestamp(int(item.get("time_added", 0))).strftime('%Y-%m-%d %H:%M:%S'),
                    "time_updated": datetime.fromtimestamp(int(item.get("time_updated", 0))).strftime('%Y-%m-%d %H:%M:%S'),
                    "word_count": item.get("word_count", 0),
                    "tags": list(item.get("tags", {}).keys())
                }
                
                # Add content info based on type
                content = {}
                if item.get("has_video") == "2" and item.get("videos"):
                    # YouTube content
                    for vid in item.get("videos", {}).values():
                        if vid.get("src").lower().find("youtube") >= 0:
                            content = {
                                "type": "youtube",
                                "video_id": vid.get("vid")
                            }
                            break
                elif item.get("has_image") == "1" and item.get("images"):
                    # Image content
                    content = {
                        "type": "image",
                        "image_url": next(iter(item.get("images", {}).values()), {}).get("src", "")
                    }
                else:
                    # Article content
                    excerpt = item.get("excerpt", "")
                    if not excerpt or len(excerpt.strip()) < 100:  # If no excerpt or very short excerpt
                        # Try to scrape content
                        url = item.get("resolved_url") or item.get("given_url")
                        scraped_content = scrape_article_content(url)
                        content = {
                            "type": "article",
                            "content": scraped_content if scraped_content else excerpt,
                            "scraped": scraped_content is not None
                        }
                    else:
                        content = {
                            "type": "article",
                            "content": excerpt,
                            "scraped": False
                        }
                
                article["content"] = content
                articles.append(article)
            
            logger.info(f"Found {len(articles)} articles in Pocket")
            return articles
            
        except requests.exceptions.HTTPError as e:
            # Handle specific HTTP errors
            status_code = e.response.status_code if hasattr(e, 'response') else None
            logger.error(f"HTTP error {status_code} when fetching from Pocket API: {str(e)}")
            
            # If we get rate limited or server error, retry
            if status_code and (status_code == 429 or status_code >= 500):
                if attempt < max_retries - 1:
                    continue
            
            # For other HTTP errors, no need to retry
            return []
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            logger.error(f"Network error when fetching from Pocket API (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                continue
            return []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error when fetching from Pocket API: {str(e)}")
            if attempt < max_retries - 1:
                continue
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response from Pocket API: {str(e)}")
            return []
            
        except Exception as e:
            logger.error(f"Unexpected error processing Pocket data: {str(e)}")
            return []
    
    # If we reach here, all retries failed
    logger.error(f"Failed to fetch articles from Pocket API after {max_retries} attempts")
    return []

def fetch_with_retry(url, max_retries=3, backoff_factor=0.5):
    """Fetches a URL with retry logic using requests.
    Only used for API calls that don't require full browser rendering.
    
    Args:
        url: The URL to fetch
        max_retries: Maximum number of retry attempts
        backoff_factor: Factor to determine wait time between retries
        
    Returns:
        Response object or None if all retries failed
    """
    # Add headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    }
    
    for attempt in range(max_retries):
        try:
            # Add rate limiting to avoid being blocked
            if attempt > 0:
                # Randomize wait time between retries
                wait_time = backoff_factor * (2 ** attempt) + random.uniform(0.1, 0.5)
                logger.warning(f"Retry attempt {attempt+1}/{max_retries} for {url}, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
            else:
                # Small random delay even on first attempt
                time.sleep(random.uniform(0.2, 0.7))
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response
            
        except SSLError as e:
            logger.warning(f"SSL Error on attempt {attempt+1}/{max_retries} for {url}: {e}")
            if attempt == max_retries - 1:
                # Last attempt, try without SSL verification
                try:
                    logger.warning(f"Trying final attempt without SSL verification for {url}")
                    response = requests.get(url, headers=headers, timeout=15, verify=False)
                    response.raise_for_status()
                    return response
                except Exception as inner_e:
                    logger.error(f"Final attempt failed for {url}: {inner_e}")
                    return None
                    
        except ConnectionError as e:
            logger.warning(f"Connection Error on attempt {attempt+1}/{max_retries} for {url}: {e}")
            if attempt == max_retries - 1:
                logger.error(f"All connection attempts failed for {url}")
                return None
                
        except Timeout as e:
            logger.warning(f"Timeout on attempt {attempt+1}/{max_retries} for {url}: {e}")
            if attempt == max_retries - 1:
                logger.error(f"All attempts timed out for {url}")
                return None
                
        except RequestException as e:
            logger.warning(f"Request Exception on attempt {attempt+1}/{max_retries} for {url}: {e}")
            if attempt == max_retries - 1:
                logger.error(f"All retry attempts failed for {url}")
                return None
    
    return None

def scrape_article_content(url, timeout=30000):
    """Scrape content from a web page.
    
    Args:
        url: The URL to scrape
        timeout: Maximum time to wait for page load in milliseconds
        
    Returns:
        String with article content or None if scraping failed
    """
    if not url:
        return None
        
    if not scraping_available:
        logger.error("Scraping module not available. Cannot scrape web content.")
        return None
    
    # Use the dedicated scraping module
    return scrape_website(url, timeout=timeout)


def save_articles_to_json(articles, output_folder="pocket_articles"):
    """Save articles to a JSON file with timestamp.
    
    Args:
        articles: List of article dictionaries
        output_folder: Folder to save JSON file in
        
    Returns:
        Path to the saved JSON file
    """
    if not articles:
        logger.warning("No articles to save.")
        return None
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pocket_articles_{timestamp}.json"
    filepath = os.path.join(output_folder, filename)
    
    # Save articles to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(articles)} articles to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving articles to file: {str(e)}")
        return None

def check_playwright_installation():
    """Check if Playwright is installed and offer to install it if not."""
    if not playwright_available:
        logger.warning("Playwright is not installed. JavaScript-heavy sites may not scrape properly.")
        try:
            user_input = input("Would you like to install Playwright now? (y/n): ")
            if user_input.lower() in ['y', 'yes']:
                logger.info("Installing Playwright...")
                os.system("pip install playwright")
                logger.info("Installing Playwright browsers...")
                os.system("playwright install chromium")
                logger.info("Playwright installation complete. Please restart the script.")
                return True
        except Exception as e:
            logger.error(f"Error during Playwright installation: {e}")
    return False

def main():
    """Main function to fetch articles from Pocket."""
    parser = argparse.ArgumentParser(description="Fetch articles from Pocket")
    parser.add_argument("--config", default="pipeline_config.json", help="Path to config file")
    parser.add_argument("--hours", type=int, help="Hours to look back for articles")
    parser.add_argument("--save-to-file", action="store_true", help="Save articles to JSON file")
    parser.add_argument("--run-evernote", action="store_true", help="Directly run Evernote posting after fetching")
    parser.add_argument("--install-playwright", action="store_true", help="Install Playwright for better scraping of JavaScript-heavy sites")
    args = parser.parse_args()
    
    # Check if we need to install Playwright
    if args.install_playwright:
        installed = check_playwright_installation()
        if installed:
            logger.info("Playwright installed. Please restart the script.")
            sys.exit(0)
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.error("Failed to load configuration. Exiting.")
        sys.exit(1)
    
    # Get Pocket configuration
    pocket_config = config.get("pocket", {})
    
    # Override hours_lookback if specified in command line
    hours_lookback = args.hours if args.hours is not None else pocket_config.get("hours_lookback", 24)
    
    # Fetch articles from Pocket
    articles = fetch_pocket_articles(
        consumer_key=pocket_config.get("consumer_key"),
        access_token=pocket_config.get("access_token"),
        hours_lookback=hours_lookback
    )
    
    if not articles:
        logger.warning("No articles found to process.")
        sys.exit(0)
    
    # Save to JSON file if requested
    json_file = None
    if args.save_to_file or config.get("output", {}).get("save_json", False):
        json_folder = config.get("output", {}).get("json_folder", "pocket_articles")
        json_file = save_articles_to_json(articles, json_folder)
    
    # Run Evernote posting if requested
    if args.run_evernote:
        # Import evernote_poster only when needed
        try:
            from evernote_poster import post_to_evernote
            logger.info("Directly posting articles to Evernote...")
            success = post_to_evernote(articles, config_path=args.config)
            if success:
                logger.info("Evernote posting completed successfully.")
            else:
                logger.error("Evernote posting encountered errors.")
                sys.exit(1)
        except ImportError:
            logger.error("Failed to import evernote_poster module. Make sure it's in the same directory.")
            sys.exit(1)
    
    logger.info("Pocket article fetching completed.")

if __name__ == "__main__":
    main()