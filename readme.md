# Pocket to Evernote Sync

This project allows you to sync your saved Pocket articles to Evernote notebooks automatically.

## Features

- Fetches recent articles from your Pocket account
- Posts articles to a designated Evernote notebook
- Handles YouTube videos and regular articles differently
- Preserves tags from Pocket
- Avoids creating duplicate notes
- Configurable time window for article retrieval

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pocket-to-evernote.git
   cd pocket-to-evernote
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

### Evernote API Access

1. Go to the [Evernote Developer Portal](https://dev.evernote.com/)
2. Create a new API key (or use an existing one)
3. Generate a developer token for your account

### Setting Up Configuration

The script will create a configuration file (`evernote_config.json`) on first run, but you'll need to edit it with your Evernote authentication token:

```json
{
  "auth_token": "YOUR-EVERNOTE-AUTH-TOKEN",
  "notebook_name": "Pocket Articles",
  "sandbox": false,
  "pocket": {
    "consumer_key": "YOUR-POCKET-CONSUMER-KEY",
    "access_token": "YOUR-POCKET-ACCESS-TOKEN",
    "hours_lookback": 24
  }
}
```

- `auth_token`: Your Evernote developer token
- `notebook_name`: Name of the Evernote notebook to save articles to (will be created if it doesn't exist)
- `sandbox`: Set to `true` for testing with Evernote's sandbox environment
- `pocket`: Configuration for your Pocket account

## Usage

Run the sync with default settings (articles from the last 24 hours):
```
python pocket_to_evernote.py
```

Specify a different time window (e.g., 48 hours):
```
python pocket_to_evernote.py 48
```

## Files

- `get_pocket.py`: Core functionality for fetching articles from Pocket
- `pocket_pipeline.py`: Pipeline for fetching and saving articles as JSON
- `pocket_to_evernote.py`: Syncs Pocket articles to Evernote
- `requirements.txt`: Required Python packages

## Notes

- The Evernote API has rate limits. If you have many articles, the sync might be throttled.
- For YouTube videos, a thumbnail and link are created instead of embedding the full content.
- Regular articles are cleaned and formatted to comply with Evernote's ENML format.

## Troubleshooting

If you encounter rate limits with the Evernote API, the script will automatically pause and retry. However, if you're syncing a large number of articles, you might want to increase the delay between note creations.

## License

MIT