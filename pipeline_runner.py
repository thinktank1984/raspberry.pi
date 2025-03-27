#pipeline_runner.py do not change do not remove
import os
import sys
import json
import argparse
import logging
from datetime import datetime

from get_pocket import fetch_pocket_articles
from evernote_poster import post_to_evernote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pipeline_runner")

def load_pipeline_config(config_path="pipeline_config.json"):
    """Load pipeline configuration from JSON file."""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default config
            config = {
                "pocket": {
                    "consumer_key": "114205-4f640a16a3fd75d1b69798d",
                    "access_token": "0c67ad2b-95d3-a656-d9bd-eb08b7",
                    "hours_lookback": 24
                },
                "evernote": {
                    "enabled": False,
                    "auth_token": "your-evernote-auth-token",
                    "notebook_name": "Pocket Articles",
                    "sandbox": False
                },
                "output": {
                    "save_json": False,
                    "json_folder": "pocket_articles"
                }
            }
            
            # Ensure output directory exists
            os.makedirs(config["output"]["json_folder"], exist_ok=True)
            
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Created default pipeline config at {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading pipeline config: {str(e)}")
        return None

def fetch_pocket_and_save(config, hours_lookback=None, save_to_file=False):
    """
    Fetch articles from Pocket and optionally save to file.
    
    Args:
        config: Pipeline configuration
        hours_lookback: Number of hours to look back for articles
        save_to_file: Whether to save articles to JSON file
        
    Returns:
        Tuple of (articles, json_file_path)
        articles: List of article dictionaries
        json_file_path: Path to saved JSON file (or None if not saved)
    """
    # Determine hours lookback
    if hours_lookback is None:
        hours_lookback = config['pocket']['hours_lookback']
    
    logger.info(f"Fetching articles from Pocket (last {hours_lookback} hours)")
    
    try:
        # Fetch the articles
        articles = fetch_pocket_articles(
            consumer_key=config['pocket']['consumer_key'],
            access_token=config['pocket']['access_token'],
            hours_lookback=hours_lookback
        )
        
        if not articles:
            logger.warning("No articles found.")
            return None, None
        
        json_file = None
        # Save to file only if explicitly requested
        if save_to_file:
            # Create the output directory if it doesn't exist
            os.makedirs(config['output']['json_folder'], exist_ok=True)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = os.path.join(config['output']['json_folder'], f'pocket_articles_{timestamp}.json')
            
            # Save to a JSON file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(articles)} articles to {json_file}")
        else:
            logger.info(f"Found {len(articles)} articles (not saved to file)")
        
        return articles, json_file
    
    except Exception as e:
        logger.error(f"Error fetching Pocket articles: {e}")
        return None, None

def main():
    """Main function to run the entire pipeline."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Pocket to Evernote Pipeline Runner')
    parser.add_argument('--hours', type=int, help='Hours to look back for articles')
    parser.add_argument('--evernote', action='store_true', help='Enable Evernote sync')
    parser.add_argument('--config', default='pipeline_config.json', help='Path to config file')
    parser.add_argument('--json', help='Path to existing JSON file to use (skips Pocket step)')
    parser.add_argument('--save-to-file', action='store_true', help='Save articles to JSON file')
    args = parser.parse_args()
    
    # Load configuration
    config = load_pipeline_config(args.config)
    if not config:
        logger.error("Failed to load pipeline configuration. Exiting.")
        sys.exit(1)
    
    # Determine hours lookback
    hours_lookback = args.hours if args.hours is not None else config['pocket']['hours_lookback']
    
    # Determine if Evernote sync is enabled
    evernote_enabled = args.evernote or config.get('evernote', {}).get('enabled', False)
    
    # Override save_to_file based on command line flag
    save_to_file = args.save_to_file or config.get('output', {}).get('save_json', False)
    
    logger.info("\n===== Pocket to Evernote Pipeline =====\n")
    
    # Step 1: Get articles (either from Pocket or from provided JSON file)
    articles = None
    json_file = args.json
    
    if json_file:
        logger.info(f"Using provided JSON file: {json_file}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            logger.info(f"Loaded {len(articles)} articles from {json_file}")
        except Exception as e:
            logger.error(f"Error loading articles from {json_file}: {e}")
            sys.exit(1)
    else:
        logger.info("Step 1: Fetching articles from Pocket")
        articles, json_file = fetch_pocket_and_save(config, hours_lookback, save_to_file)
        if not articles:
            logger.error("Failed to fetch articles from Pocket. Pipeline aborted.")
            sys.exit(1)
        logger.info("Step 1 complete: Articles fetched from Pocket")
    
    # Step 2: Post to Evernote if enabled
    if evernote_enabled:
        logger.info("\nStep 2: Posting articles directly to Evernote")
        success = post_to_evernote(articles, config_path=args.config)
        if success:
            logger.info("Step 2 complete: Articles posted to Evernote")
        else:
            logger.error("Step 2 failed: Error posting to Evernote")
            sys.exit(1)
    else:
        logger.info("\nStep 2 skipped: Evernote sync not enabled")
    
    logger.info("\n===== Pipeline completed successfully =====")

if __name__ == "__main__":
    main()