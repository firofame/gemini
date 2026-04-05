# Gemini Book Toolkit

A Python toolkit for converting Malayalam text into audiobooks using Gemini AI and Google Docs TTS.

## Scripts

| Script | Description |
|--------|-------------|
| `tts.py` | Text-to-Speech converter using Google Docs and a persistent Camoufox profile |
| `archive_upload.py` | Uploads text and audio files to Internet Archive |
| `list.py` | Lists Gemini models that support `generateContent` |
| `sample.py` | Simple Gemini API test script |

## Prerequisites

- Python 3.10+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey) (set as `GEMINI_API_KEY` env var)
- Google Account (for TTS via Google Docs)
- [Camoufox](https://camoufox.com/) (used for auth and TTS automation)
- [Playwright](https://playwright.dev/python/docs/intro) runtime dependency used by Camoufox
- [internetarchive](https://pypi.org/project/internetarchive/) (for archive.org uploads)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gemini
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install google-genai playwright camoufox internetarchive
   ```

4. Install browser dependencies:
   ```bash
   python -m camoufox fetch
   ```

Camoufox is the browser automation library used directly by `tts.py`. It is Playwright-compatible and still depends on Playwright under the hood, so `playwright` remains in the Python dependencies even though the script does not import it directly.

## Workflow

### 1. Generate Audio (MP3)

```bash
python tts.py input.txt [output.mp3]
```

Inserts text into Google Docs and uses its TTS engine to generate MP3 audio.
The first run opens Camoufox and keeps you signed in via `.camoufox-profile/`.

### 2. Upload to Internet Archive

Edit `identifier` and `source_files` in `archive_upload.py`, then:

```bash
python archive_upload.py
```

## Configuration

- **`tts.py`**: Update `CONFIG['doc_url']` to a Google Doc you have edit access to.

## License

[MIT License](LICENSE)
