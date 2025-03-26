import json
import logging
import time
import requests
from datetime import datetime, timedelta
from pocket import Pocket, PocketException
from bs4 import BeautifulSoup
import re
import urllib.parse

# Configuration
HOURS_LOOKBACK = 24  # Number of hours to look back for articles

logging.basicConfig(level=logging.DEBUG)

def get_full_content(url):
    """Extract the full content from a URL based on its type."""
    try:
        if 'youtube.com' in url or 'youtu.be' in url:
            return get_youtube_content(url)
        else:
            return get_article_content(url)
    except Exception as e:
        logging.error(f"Error extracting content from {url}: {str(e)}")
        return "Content extraction failed"

def get_youtube_content(url):
    """For YouTube videos, just return basic info without scraping."""
    try:
        # Extract video ID from URL
        video_id = None
        if 'v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
        
        if not video_id:
            return "Could not extract YouTube video ID"
        
        # Format as JSON-friendly data structure
        return {
            "type": "youtube",
            "video_id": video_id,
            "url": url
        }
    except Exception as e:
        logging.error(f"YouTube content extraction error: {str(e)}")
        return "YouTube content extraction failed"

def get_article_content(url):
    """Extract the full content from a regular article URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        
        # Try to find the main article content
        article_content = None
        
        # Try to find article by common article tags
        for selector in ['article', 'main', '.article', '.post-content', '.entry-content', '#content', '.content']:
            if article_content:
                break
            article_content = soup.select_one(selector)
        
        # If no article container found, use the body
        if not article_content:
            article_content = soup.body
        
        # Get text and clean it up
        text = article_content.get_text(separator='\n')
        
        # Clean up empty lines and excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        cleaned_text = '\n\n'.join(lines)
        
        return {
            "type": "article",
            "content": cleaned_text,
            "url": url
        }
    except Exception as e:
        logging.error(f"Article content extraction error: {str(e)}")
        return "Article content extraction failed"

p = Pocket(
    consumer_key='114205-4f640a16a3fd75d1b69798d',
    access_token='0c67ad2b-95d3-a656-d9bd-eb08b7'
)

# Calculate timestamp for the lookback period
lookback_time = int((datetime.now() - timedelta(hours=HOURS_LOOKBACK)).timestamp())

try:
    # Fetch recent articles
    response = p.get(state='all', since=lookback_time)
    
    # Process the articles into the format you need
    articles = []
    
    if response and response[0] and 'list' in response[0]:
        for item_id, item in response[0]['list'].items():
            # Extract tags as a list
            tags_list = []
            if 'tags' in item and item['tags']:
                tags_list = list(item['tags'].keys())
            
            url = item.get('resolved_url', '')
            
            # Get content details based on URL type
            content_details = get_full_content(url)
            
            # Create article object with appropriate structure
            article = {
                'title': item.get('resolved_title', 'No title'),
                'excerpt': item.get('excerpt', ''),
                'content': content_details,
                'tags': tags_list,
                'url': url,
                'time_added': datetime.fromtimestamp(int(item.get('time_added', 0))).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            articles.append(article)
    
    # Output the results
    print(f"Found {len(articles)} items from the last {HOURS_LOOKBACK} hour(s)")
    
    # Convert to JSON and print
    json_output = json.dumps(articles, indent=2, ensure_ascii=False)
    print(json_output)
    
    # Save to a file
    with open('pocket_articles.json', 'w', encoding='utf-8') as f:
        f.write(json_output)
    
except PocketException as e:
    print(f"Pocket API Error: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")