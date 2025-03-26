import os
import sys
import json
import argparse
import logging
from datetime import datetime
import subprocess

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
                    "enabled": False
                },
                "output": {
                    "json_folder": "pocket_articles"
                }
            }
            
            # Ensure output directory exists
            os.makedirs(config["output"]["json_folder"], exist_ok=True)
            
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Created default pipeline config at {config_path}")
            return config
    except Exception as e:
        print(f"Error loading pipeline config: {str(e)}")
        return None

def run_pocket_direct(config, hours_lookback=None):
    """Run the get_pocket module directly to extract articles."""
    from get_pocket import fetch_pocket_articles
    
    # Determine hours lookback
    if hours_lookback is None:
        hours_lookback = config['pocket']['hours_lookback']
    
    print(f"Fetching articles from Pocket (last {hours_lookback} hours)")
    
    try:
        # Fetch the articles
        articles = fetch_pocket_articles(
            consumer_key=config['pocket']['consumer_key'],
            access_token=config['pocket']['access_token'],
            hours_lookback=hours_lookback
        )
        
        if not articles:
            print("No articles found.")
            return None
        
        # Create the output directory if it doesn't exist
        os.makedirs(config['output']['json_folder'], exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = os.path.join(config['output']['json_folder'], f'pocket_articles_{timestamp}.json')
        
        # Save to a JSON file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(articles)} articles to {json_file}")
        return json_file
    
    except Exception as e:
        print(f"Error fetching Pocket articles: {e}")
        return None

def run_evernote_poster(json_file):
    """Run the Evernote poster with the specified JSON file."""
    if not os.path.exists(json_file):
        print(f"Error: JSON file {json_file} does not exist.")
        return False
    
    # Try to import and run directly first
    try:
        from evernote_poster import post_to_evernote
        print("Running Evernote poster directly...")
        return post_to_evernote(json_file)
    except ImportError:
        # Fall back to subprocess if import fails
        try:
            cmd = ["python", "evernote_poster.py", json_file]
            print(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(result.stdout)
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"Error running evernote_poster.py: {e}")
            print(f"Output: {e.stdout}")
            print(f"Error: {e.stderr}")
            return False

def main():
    """Main function to run the entire pipeline."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Pocket to Evernote Pipeline Runner')
    parser.add_argument('--hours', type=int, help='Hours to look back for articles')
    parser.add_argument('--evernote', action='store_true', help='Enable Evernote sync')
    parser.add_argument('--config', default='pipeline_config.json', help='Path to config file')
    parser.add_argument('--json', help='Path to existing JSON file to use (skips Pocket step)')
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Load configuration
    config = load_pipeline_config(args.config)
    if not config:
        print("Failed to load pipeline configuration. Exiting.")
        sys.exit(1)
    
    # Determine hours lookback
    hours_lookback = args.hours if args.hours is not None else config['pocket']['hours_lookback']
    
    # Determine if Evernote sync is enabled
    evernote_enabled = args.evernote or config['evernote']['enabled']
    
    print("\n===== Pocket to Evernote Pipeline =====\n")
    
    # Step 1: Run Pocket pipeline to get articles (unless JSON file is provided)
    json_file = args.json
    if not json_file:
        print("Step 1: Fetching articles from Pocket")
        json_file = run_pocket_direct(config, hours_lookback)
        if not json_file:
            print("Failed to fetch articles from Pocket. Pipeline aborted.")
            sys.exit(1)
        print(f"Step 1 complete: Articles saved to {json_file}")
    else:
        print(f"Using provided JSON file: {json_file}")
    
    # Step 2: Post to Evernote if enabled
    if evernote_enabled:
        print("\nStep 2: Posting articles to Evernote")
        success = run_evernote_poster(json_file)
        if success:
            print("Step 2 complete: Articles posted to Evernote")
        else:
            print("Step 2 failed: Error posting to Evernote")
            sys.exit(1)
    else:
        print("\nStep 2 skipped: Evernote sync not enabled")
    
    print("\n===== Pipeline completed successfully =====")

if __name__ == "__main__":
    main()