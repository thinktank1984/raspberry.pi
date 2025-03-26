import json
import logging
import sys
import os
from datetime import datetime

# Import the get_pocket module
from get_pocket import fetch_pocket_articles

def load_config(config_path="pocket_config.json"):
    """Load configuration from JSON file."""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default config
            config = {
                "consumer_key": "114205-4f640a16a3fd75d1b69798d",
                "access_token": "0c67ad2b-95d3-a656-d9bd-eb08b7",
                "hours_lookback": 24
            }
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return config
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return None

def main():
    """Main function to run the pipeline."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    config = load_config()
    if not config:
        print("Failed to load configuration. Exiting.")
        sys.exit(1)
    
    # Process command line arguments for hours lookback
    if len(sys.argv) > 1:
        try:
            config["hours_lookback"] = int(sys.argv[1])
            print(f"Using hours lookback: {config['hours_lookback']}")
        except ValueError:
            print(f"Invalid hours value: {sys.argv[1]}. Using default: {config['hours_lookback']}")
    
    # Fetch and process articles using the imported function
    articles = fetch_pocket_articles(
        consumer_key=config["consumer_key"],
        access_token=config["access_token"],
        hours_lookback=config["hours_lookback"]
    )
    
    # Convert to JSON and print
    json_output = json.dumps(articles, indent=2, ensure_ascii=False)
    print(json_output)
    
    # Save to a file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'pocket_articles_{timestamp}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_output)
    
    print(f"Saved {len(articles)} articles to {output_file}")

if __name__ == "__main__":
    main()