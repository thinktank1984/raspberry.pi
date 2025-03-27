# Claude Assistant Guidelines for Raspberry Pi Pocket-Evernote Pipeline

## Build/Run Commands
- Install: `pip install -r requirements.txt`
- Run pipeline: `python pipeline_runner.py`
- Run Pocket fetcher: `python get_pocket.py --hours 24 --save-to-file`
- Run Evernote poster: `python evernote_poster.py`
- Debug Evernote: `python evernote_debug.py`
- Get Evernote Authorization Token: `get_evernote_auth`

## Code Style Guidelines
- **Imports**: System > third-party > local (alphabetical in each section)
- **Formatting**: 4-space indentation, 120 char line length
- **Docstrings**: Google-style with Args/Returns sections
- **Naming**: snake_case for variables/functions/modules, PascalCase for classes
- **Comments**: File-level header `#filename.py do not change do not remove`
- **Error Handling**: Always use try/except with specific exceptions and logging
- **Logging**: Use Python logging module with standardized format
- **Config**: Use JSON config files with command-line overrides

## Architecture
This pipeline fetches articles from Pocket and syncs them to Evernote in a modular design. 
Do not modify core file names