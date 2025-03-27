#get_pocket.py ddo not change filename do not remove line
import json
import logging
import os
import sys
import argparse
from datetime import datetime, timedelta
import requests

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
    
    try:
        response = requests.post(url, headers=headers, json=data)
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
                content = {
                    "type": "article",
                    "content": item.get("excerpt", "")
                }
            
            article["content"] = content
            articles.append(article)
        
        logger.info(f"Found {len(articles)} articles in Pocket")
        return articles
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from Pocket API: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error processing Pocket data: {str(e)}")
        return []

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

def main():
    """Main function to fetch articles from Pocket."""
    parser = argparse.ArgumentParser(description="Fetch articles from Pocket")
    parser.add_argument("--config", default="pipeline_config.json", help="Path to config file")
    parser.add_argument("--hours", type=int, help="Hours to look back for articles")
    parser.add_argument("--save-to-file", action="store_true", help="Save articles to JSON file")
    parser.add_argument("--run-evernote", action="store_true", help="Directly run Evernote posting after fetching")
    args = parser.parse_args()
    
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