import json
import logging
import time
from datetime import datetime, timedelta
from pocket import Pocket, PocketException

logging.basicConfig(level=logging.DEBUG)

p = Pocket(
    consumer_key='114205-4f640a16a3fd75d1b69798d',
    access_token='0c67ad2b-95d3-a656-d9bd-eb08b7'
)

# Calculate timestamp for 1 hour ago
one_hour_ago = int((datetime.now() - timedelta(hours=1)).timestamp())

try:
    # Fetch recent articles
    response = p.get(state='all', since=one_hour_ago)
    
    # Process the articles into the format you need
    articles = []
    
    if response and response[0] and 'list' in response[0]:
        for item_id, item in response[0]['list'].items():
            # Extract tags as a list
            tags_list = []
            if 'tags' in item and item['tags']:
                tags_list = list(item['tags'].keys())
            
            article = {
                'title': item.get('resolved_title', 'No title'),
                'body': item.get('excerpt', ''),
                'tags': tags_list,
                'url': item.get('resolved_url', ''),
                'time_added': datetime.fromtimestamp(int(item.get('time_added', 0))).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            articles.append(article)
    
    # Output the results
    print(f"Found {len(articles)} items from the last hour")
    
    # Convert to JSON and print
    json_output = json.dumps(articles, indent=2)
    print(json_output)
    
    # Optionally save to a file
    with open('pocket_articles.json', 'w') as f:
        f.write(json_output)
    
except PocketException as e:
    print(f"Pocket API Error: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")