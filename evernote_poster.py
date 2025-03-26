import json
import logging
import os
import time
import hashlib
from datetime import datetime

# Import Evernote SDK
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient
from evernote.edam.error.ttypes import EDAMUserException, EDAMSystemException, EDAMNotFoundException

def load_evernote_config(config_path="evernote_config.json"):
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
                "sandbox": False  # Set to True for development/testing
            }
            # Save default config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Created default Evernote config at {config_path}, please edit with your Evernote auth token")
            return config
    except Exception as e:
        print(f"Error loading Evernote config: {str(e)}")
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

def post_to_evernote(articles_file):
    """Post articles from a JSON file to Evernote."""
    # Load Evernote configuration
    config = load_evernote_config()
    if not config:
        print("Failed to load Evernote configuration.")
        return False
    
    # Check if auth token is still default
    if config["auth_token"] == "your-evernote-auth-token":
        print("ERROR: Please update your Evernote auth token in the config file:")
        print(f"Edit the file: {os.path.abspath('evernote_config.json')}")
        print("and replace 'your-evernote-auth-token' with your actual Evernote developer token")
        return False
    
    # Load articles from JSON file
    try:
        with open(articles_file, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        if not articles:
            print("No articles found in the JSON file.")
            return False
        
        print(f"Loaded {len(articles)} articles from {articles_file}")
    except Exception as e:
        print(f"Error loading articles from {articles_file}: {str(e)}")
        return False
    
    # Connect to Evernote
    note_store = get_note_store(config['auth_token'], config['sandbox'])
    if not note_store:
        print("Failed to connect to Evernote.")
        return False
    
    # Find or create notebook
    notebook = find_or_create_notebook(note_store, config['notebook_name'])
    if not notebook:
        print("Failed to find or create notebook.")
        return False
    
    # Create notes for each article
    created_count = 0
    for article in articles:
        note = create_note_from_article(note_store, article, notebook.guid)
        if note:
            created_count += 1
            # Sleep a bit to avoid hitting rate limits
            time.sleep(1)
    
    print(f"Synced {created_count} of {len(articles)} articles to Evernote notebook '{config['notebook_name']}'")
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python evernote_poster.py path/to/articles.json")
        sys.exit(1)
    
    articles_file = sys.argv[1]
    if not os.path.exists(articles_file):
        print(f"Error: File {articles_file} not found")
        sys.exit(1)
    
    success = post_to_evernote(articles_file)
    
    if success:
        print("Evernote posting completed successfully.")
    else:
        print("Evernote posting encountered errors.")
        sys.exit(1)