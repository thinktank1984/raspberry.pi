# Pocket to Evernote Pipeline

This project allows you to fetch articles from your Pocket account and optionally sync them to Evernote notebooks.

## Features

- Fetches recent articles from your Pocket account
- Saves articles to JSON files with timestamps
- Optionally posts articles to a designated Evernote notebook
- Handles YouTube videos and regular articles differently
- Preserves tags from Pocket
- Avoids creating duplicate notes
- Configurable time window for article retrieval

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pocket-evernote-pipeline.git
   cd pocket-evernote-pipeline
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

The first time you run the pipeline, it will create a configuration file called `pipeline_config.json`. You can edit this file to set your preferences:

```json
{
  "pocket": {
    "consumer_key": "YOUR-POCKET-CONSUMER-KEY",
    "access_token": "YOUR-POCKET-ACCESS-TOKEN",
    "hours_lookback": 24
  },
  "evernote": {
    "enabled": false,
    "auth_token": "YOUR-EVERNOTE-AUTH-TOKEN",
    "notebook_name": "Pocket Articles",
    "sandbox": false
  },
  "output": {
    "save_json": true,
    "json_folder": "pocket_articles"
  }
}
```

### Setting Up Evernote

If you want to use the Evernote sync feature:

1. Go to the [Evernote Developer Portal](https://dev.evernote.com/)
2. Create a new API key (or use an existing one)
3. Generate a developer token for your account
4. Update the `auth_token` value in the configuration file
5. Set `enabled` to `true`

## Usage

### Running the Complete Pipeline

```
python main_pipeline.py
```

### Command Line Options

You can customize the behavior with command line arguments:

```
python main_pipeline.py --hours 48 --evernote True
```

Available options:
- `--hours`: Number of hours to look back for articles
- `--evernote`: Enable or disable Evernote sync (True/False)
- `--config`: Path to a custom config file

### Running Individual Components

You can also run the components separately:

1. Just fetch Pocket articles:
   ```
   python pocket_pipeline.py 24
   ```

2. Just sync to Evernote (requires setup):
   ```
   python pocket_to_evernote.py
   ```

## Files

- `get_pocket.py`: Core functionality for fetching articles from Pocket
- `pocket_pipeline.py`: Pipeline for fetching and saving articles as JSON
- `pocket_to_evernote.py`: Syncs Pocket articles to Evernote
- `main_pipeline.py`: Combined pipeline that orchestrates all tasks
- `requirements.txt`: Required Python packages

## Notes

- The Evernote API has rate limits. If you have many articles, the sync might be throttled.
- For YouTube videos, a thumbnail and link are created instead of embedding the full content.
- Regular articles are cleaned and formatted to comply with Evernote's ENML format.

## Troubleshooting

If you encounter rate limits with the Evernote API, the script will automatically pause and retry. However, if you're syncing a large number of articles, you might want to increase the delay between note creations.

## License

MIT