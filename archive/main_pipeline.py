import json
import logging
import sys
import os
import argparse
from datetime import datetime

# Import local modules
from get_pocket import fetch_pocket_articles

# Optional import for Evernote functionality
try:
    from pocket_to_evernote import sync_pocket_to_evernote
    EVERNOTE_AVAILABLE = True
except ImportError:
    EVERNOTE_AVAILABLE = False

def load_config(config_path="pipeline_config.json"):
    """Load configuration from JSON file."""
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
                    "save_json": True,
                    "json_folder": "pocket_articles"
                }
            }
            
            # Ensure output directory exists
            os.makedirs(config["output"]["json_folder"], exist_ok=True)
            
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return config
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return None

def save_articles_to_json(articles, output_folder):
    """Save articles to a JSON file with timestamp."""
    if not articles:
        print("No articles to save")
        return
    
    # Create folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_folder, f'pocket_articles_{timestamp}.json')
    
    # Convert to JSON and save
    json_output = json.dumps(articles, indent=2, ensure_ascii=False)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_output)
    
    print(f"Saved {len(articles)} articles to {output_file}")
    return output_file

def run_pipeline(config, args):
    """Run the complete pocket articles pipeline."""
    # Update config with command line arguments
    if args.hours:
        config["pocket"]["hours_lookback"] = args.hours
    
    if args.evernote is not None:
        config["evernote"]["enabled"] = args.evernote
    
    # Step 1: Fetch articles from Pocket
    print(f"\n--- Fetching articles from Pocket (last {config['pocket']['hours_lookback']} hours) ---")
    articles = fetch_pocket_articles(
        consumer_key=config["pocket"]["consumer_key"],
        access_token=config["pocket"]["access_token"],
        hours_lookback=config["pocket"]["hours_lookback"]
    )
    
    if not articles:
        print("No articles found in Pocket. Pipeline complete.")
        return
    
    # Step 2: Save articles to JSON if enabled
    if config["output"]["save_json"]:
        json_file = save_articles_to_json(articles, config["output"]["json_folder"])
        print(f"JSON file created: {json_file}")
    
    # Step 3: Sync to Evernote if enabled
    if config["evernote"]["enabled"]:
        if not EVERNOTE_AVAILABLE:
            print("\n--- Evernote sync requested but Evernote module not available ---")
            print("Please install the necessary dependencies with:")
            print("pip install evernote")
            return
        
        print("\n--- Syncing articles to Evernote ---")
        evernote_config = {
            "auth_token": config["evernote"]["auth_token"],
            "notebook_name": config["evernote"]["notebook_name"],
            "sandbox": config["evernote"]["sandbox"],
            "pocket": config["pocket"]
        }
        
        # Check if auth token is still default
        if evernote_config["auth_token"] == "your-evernote-auth-token":
            print("ERROR: Please update your Evernote auth token in the config file:")
            print(f"Edit the file: {os.path.abspath('pipeline_config.json')}")
            print("and replace 'your-evernote-auth-token' with your actual Evernote developer token")
            return
        
        sync_pocket_to_evernote(evernote_config, articles)
    
    print("\n--- Pipeline completed successfully ---")

def main():
    """Main entry point with argument parsing."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Pocket Articles Pipeline')
    parser.add_argument('--hours', type=int, help='Hours to look back for articles')
    parser.add_argument('--evernote', type=bool, help='Enable/disable Evernote sync')
    parser.add_argument('--config', default='pipeline_config.json', help='Path to config file')
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        print("Failed to load configuration. Exiting.")
        sys.exit(1)
    
    # Run the pipeline
    run_pipeline(config, args)

if __name__ == "__main__":
    main()