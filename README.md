# Gemini Book Toolkit

A Python toolkit for converting Malayalam text into audiobooks using Gemini AI and Google Docs TTS.

## Scripts

| Script | Description |
|--------|-------------|
| `auth.py` | Google account authentication via Camoufox browser |
| `tts.py` | Text-to-Speech converter using Google Docs and Playwright |
| `audiobook_script.py` | Converts Malayalam text to TTS-optimized audiobook script using Gemini |
| `archive_upload.py` | Uploads text and audio files to Internet Archive |
| `list.py` | Lists Gemini models that support `generateContent` |
| `sample.py` | Simple Gemini API test script |

## Prerequisites

- Python 3.8+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey) (set as `GEMINI_API_KEY` env var)
- Google Account (for TTS via Google Docs)
- [Playwright](https://playwright.dev/python/docs/intro) with Firefox
- [Camoufox](https://camoufox.com/) (anti-detect browser for auth)
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

4. Install Playwright browsers:
   ```bash
   playwright install firefox
   ```

## Workflow

### 1. Authenticate with Google

```bash
python auth.py
```

Opens a browser for Google sign-in. Saves session to `auth.json`.

### 2. Convert Text to Audiobook Script

```bash
python audiobook_script.py input.txt [output.txt]
```

Uses Gemini to optimize Malayalam text for TTS by expanding Islamic honorifics, converting numerals, and adding natural pauses.

### 3. Generate Audio (MP3)

```bash
python tts.py input.txt [output.mp3]
```

Inserts text into Google Docs and uses its TTS engine to generate MP3 audio.

### 4. Upload to Internet Archive

Edit `identifier` and `source_files` in `archive_upload.py`, then:

```bash
python archive_upload.py
```

## Configuration

- **`tts.py`**: Update `CONFIG['doc_url']` to a Google Doc you have edit access to.
- **`audiobook_script.py`**: Customize `SYSTEM_PROMPT` to change the conversion style.

## License

[MIT License](LICENSE)
