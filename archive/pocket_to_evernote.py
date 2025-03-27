import json
import logging
import sys
import os
import hashlib
import binascii
from datetime import datetime
import time

# Import Evernote SDK
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient
from evernote.edam.error.ttypes import EDAMUserException, EDAMSystemException, EDAMNotFoundException

# Import local modules
from get_pocket import fetch_pocket_articles

def load_config(config_path="evernote_config.json"):
    """Load Evernote configuration from JSON file."""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default config
            config = {
                "auth_token": "your-evernote-auth-token",
                "notebook_name": "Pocket Articles",
                "sandbox": False,  # Set to True for development/testing
                "pocket": {
                    "consumer_key": "your-pocket-consumer-key",
                    "access_token": "your-pocket-access-token",
                    "hours_lookback": 24
                }
            }
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Created default config at {config_path}, please edit with your Evernote auth token")
            return config
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return None

def get_note_store(auth_token, sandbox=False):
    """Initialize Evernote client and get note store."""
    try:
        client = EvernoteClient(token=auth_token, sandbox=sandbox)
        return client.get_note_store()
    except Exception as e:
        print(f"Error connecting to Evernote: {str(e)}")
        return None

def find_or_create_notebook(note_store, notebook_name):
    """Find the specified notebook or create it if it doesn't exist."""
    try:
        notebooks = note_store.listNotebooks()
        for notebook in notebooks:
            if notebook.name == notebook_name:
                print(f"Found notebook: {notebook_name}")
                return notebook
        
        # Notebook not found, create it
        print(f"Creating new notebook: {notebook_name}")
        new_notebook = Types.Notebook()
        new_notebook.name = notebook_name
        created_notebook = note_store.createNotebook(new_notebook)
        return created_notebook
    
    except Exception as e:
        print(f"Error finding/creating notebook: {str(e)}")
        return None

def create_note_from_article(note_store, article, notebook_guid):
    """Create a new note in Evernote from a Pocket article."""
    try:
        # Create a unique note title with date prefix
        title = article.get('title', 'Untitled Article')
        
        # Generate a hash of the URL to use as a unique identifier
        url = article.get('url', '')
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Check if a note with this URL already exists (to avoid duplicates)
        filter = Types.NoteFilter()
        filter.notebookGuid = notebook_guid
        filter.words = f"sourceURL:{url}"
        spec = Types.NotesMetadataResultSpec()
        spec.includeTitle = True
        existing_notes = note_store.findNotesMetadata(filter, 0, 1, spec)
        
        if existing_notes.totalNotes > 0:
            print(f"Note already exists for: {title}")
            return None
        
        # Create a new note
        note = Types.Note()
        note.title = title
        note.notebookGuid = notebook_guid
        
        # Set source URL 
        note.attributes = Types.NoteAttributes()
        note.attributes.sourceURL = url
        
        # Create note content
        content_html = '<?xml version="1.0" encoding="UTF-8"?>'
        content_html += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        content_html += '<en-note>'
        
        # Add tags as colored labels
        if article.get('tags'):
            content_html += '<div style="margin-bottom: 10px;">'
            for tag in article.get('tags', []):
                content_html += f'<span style="background-color: #E0E0E0; padding: 2px 5px; margin-right: 5px; border-radius: 3px;">{tag}</span>'
            content_html += '</div>'
        
        # Add article excerpt
        if article.get('excerpt'):
            content_html += f'<div style="font-style: italic; margin-bottom: 10px;">{article.get("excerpt")}</div>'
        
        # Add divider
        content_html += '<hr/>'
        
        # Add content based on type
        content = article.get('content', {})
        content_type = content.get('type', 'unknown')
        
        if content_type == 'youtube':
            video_id = content.get('video_id', '')
            content_html += f'<div><a href="{url}"><h3>YouTube Video</h3></a></div>'
            content_html += f'<div>Video ID: {video_id}</div>'
            content_html += f'<div><a href="{url}"><img src="https://img.youtube.com/vi/{video_id}/0.jpg" alt="YouTube Thumbnail" /></a></div>'
        
        elif content_type == 'article':
            article_content = content.get('content', '')
            # Clean content to fit within ENML restrictions
            article_content = article_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            content_html += f'<div>{article_content}</div>'
        
        else:
            content_html += f'<div><a href="{url}">View Original Content</a></div>'
        
        # Add original link
        content_html += f'<div style="margin-top: 20px;"><a href="{url}">View Original</a></div>'
        
        # Add timestamp
        timestamp = article.get('time_added', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        content_html += f'<div style="font-size: small; margin-top: 10px;">Added to Pocket: {timestamp}</div>'
        
        content_html += '</en-note>'
        
        note.content = content_html
        
        # Create the note in Evernote
        created_note = note_store.createNote(note)
        print(f"Created note: {title}")
        return created_note
    
    except EDAMUserException as e:
        print(f"Evernote user error: {e.errorCode}, {e.parameter}")
        return None
    except EDAMSystemException as e:
        print(f"Evernote system error: {e.errorCode}")
        # Rate limiting might be in effect
        if e.errorCode == 19:  # RATE_LIMIT_REACHED
            print(f"Rate limit exceeded. Retry after {e.rateLimitDuration} seconds")
            time.sleep(e.rateLimitDuration + 1)
            return create_note_from_article(note_store, article, notebook_guid)  # Retry
        return None
    except Exception as e:
        print(f"Error creating note: {str(e)}")
        return None

def sync_pocket_to_evernote(config, articles=None):
    """Sync Pocket articles to Evernote.
    
    Args:
        config: Evernote configuration dictionary
        articles: Optional list of pocket articles. If None, will fetch from Pocket API.
    """
    # Fetch articles from Pocket if not provided
    if articles is None:
        articles = fetch_pocket_articles(
            consumer_key=config['pocket']['consumer_key'],
            access_token=config['pocket']['access_token'],
            hours_lookback=config['pocket']['hours_lookback']
        )
    
    if not articles:
        print("No articles found to sync to Evernote.")
        return
    
    # Connect to Evernote
    note_store = get_note_store(config['auth_token'], config['sandbox'])
    if not note_store:
        print("Failed to connect to Evernote.")
        return
    
    # Find or create notebook
    notebook = find_or_create_notebook(note_store, config['notebook_name'])
    if not notebook:
        print("Failed to find or create notebook.")
        return
    
    # Create notes for each article
    created_count = 0
    for article in articles:
        note = create_note_from_article(note_store, article, notebook.guid)
        if note:
            created_count += 1
            # Sleep a bit to avoid hitting rate limits
            time.sleep(1)
    
    print(f"Synced {created_count} of {len(articles)} articles to Evernote notebook '{config['notebook_name']}'")

def main():
    """Main function to run the Pocket to Evernote sync."""
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
            config["pocket"]["hours_lookback"] = int(sys.argv[1])
            print(f"Using hours lookback: {config['pocket']['hours_lookback']}")
        except ValueError:
            print(f"Invalid hours value: {sys.argv[1]}. Using default: {config['pocket']['hours_lookback']}")
    
    # Run the sync
    sync_pocket_to_evernote(config)

if __name__ == "__main__":
    main()