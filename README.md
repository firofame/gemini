# Gemini Book Toolkit

A Python toolkit for converting Malayalam text into audiobooks using Gemini AI and Google Docs TTS.

## Scripts

| Script | Description |
|--------|-------------|
| `tts.py` | Text-to-Speech converter using Google Docs and a persistent Camoufox profile |
| `archive_upload.py` | Uploads text and audio files to Internet Archive |
| `list_models.py` | Lists available Gemini models for your account |
| `sample.py` | Gemini API test script using `gemini_webapi` |
| `ocr.py` | OCR PDF pages via Gemini (renders pages as images, extracts text) |
| `comfi.py` | Modal app for running ComfyUI with Qwen-Image-Edit models |

## Prerequisites

- Python 3.10+
- Google Account signed in at [gemini.google.com](https://gemini.google.com)
- `__Secure-1PSID` and `__Secure-1PSIDTS` cookies from gemini.google.com (set as `SECURE_1PSID` / `SECURE_1PSIDTS` env vars, or use `browser-cookie3` for auto-detection)
- [Camoufox](https://camoufox.com/) (used for auth and TTS automation)
- [internetarchive](https://pypi.org/project/internetarchive/) (for archive.org uploads)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gemini
   ```

2. Create and activate a virtual environment with `uv`:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   uv pip install gemini_webapi camoufox internetarchive
   uv pip install "gemini_webapi[browser]"  # optional: auto-detect cookies from browser
   ```

4. Install browser dependencies:
   ```bash
   python -m camoufox fetch
   ```

## Authentication

`gemini_webapi` uses your Google account cookies instead of an API key. Export your cookies from [gemini.google.com](https://gemini.google.com):

```bash
export SECURE_1PSID="your-value"
export SECURE_1PSIDTS="your-value"
export GEMINI_COOKIE_PATH="$HOME/.cache/gemini_cookies"  # for auto-refresh persistence
```

Or install `gemini_webapi[browser]` to auto-detect cookies from your logged-in browser.

## Workflow

### 1. Login Once

```bash
uv run tts.py --login
```

Opens Camoufox with the persistent profile at `~/.camoufox-profile` so you can sign in to Google once and reuse that session later.

### 2. Generate Audio (MP3)

```bash
uv run tts.py input.txt [output.mp3]
```

Inserts text into Google Docs and uses its TTS engine to generate MP3 audio.
Uses the saved Google session from `.camoufox-profile/`.

### 3. Upload to Internet Archive

Edit `identifier` and `source_files` in `archive_upload.py`, then:

```bash
uv run archive_upload.py
```

## Configuration

- **`tts.py`**: Update `CONFIG['doc_url']` to a Google Doc you have edit access to.

## Related Projects

- **[AC Scraper](file:///home/firoz/Desktop/ac-scraper)**: An automated pipeline for extracting technical AC data from Amazon. (Moved to separate repository).

## License

[MIT License](LICENSE)
