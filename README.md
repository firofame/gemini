# Gemini Book Toolkit

A comprehensive Python toolkit for automating the process of OCR, translating PDF books into Malayalam, and generating audio versions (MP3) using Gemini and Google Docs.

## Features

- **PDF to Malayalam Translation**: Leverages Google Gemini for high-quality OCR and translation.
- **Context-Aware Processing**: Maintains story/topic context between PDF chunks for coherent translations.
- **Text-to-Speech (TTS)**: Uses Google Docs' natural-sounding voices via Playwright automation.
- **Internet Archive Integration**: Automatically uploads text and audio files to archive.org with full metadata.
- **Instagram Audio Downloader**: Utility to download audio from Instagram Reels for reference or inclusion.
- **Resume Support**: Automatically saves progress and allows resuming from where the script left off.

## Prerequisites

- Python 3.8+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- Google Account (for TTS/Google Docs access)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (for audio downloads)
- [Playwright](https://playwright.dev/python/docs/intro)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd gemini-book-toolkit
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # If requirements.txt doesn't exist, install these:
   pip install google-genai pypdf playwright internetarchive camoufox
   ```

4. Install Playwright browsers:
   ```bash
   playwright install firefox
   ```

## Usage

### 1. Authentication
Before running the TTS or translation scripts that interact with Google services, you need to authenticate:
```bash
python auth.py
```
This will open a browser for you to sign in. The session will be saved to `auth.json`.

### 2. Translate a Book
To translate a PDF book to Malayalam:
```bash
python translate_book.py path/to/your/book.pdf --output translated_book.md
```
- `--pages`: Number of pages per chunk (default: 10).
- `--model`: Gemini model to use (default: gemini-2.5-pro).
- `--prompt`: Custom prompt file (default: prompt.txt).

### 3. Generate Audio (TTS)
To convert the translated text into MP3 audio:
```bash
python tts.py translated_book.md output.mp3
```
Note: This script requires `auth.json` and a valid `doc_url` configured in `tts.py`.

### 4. Upload to Internet Archive
To upload your results to archive.org:
1. Configure the `identifier` and `source_files` in `archive_upload.py`.
2. Run the script:
```bash
python archive_upload.py
```

### 5. Download Instagram Audio
To download audio from an Instagram Reel:
```bash
python download_audio.py <reel-url>
```

## Configuration

- **`prompt.txt`**: The system prompt used for Gemini OCR/Translation. You can customize this to change the translation style or target language.
- **`tts.py`**: Update `CONFIG['doc_url']` to a Google Doc you have edit access to.

## License

[MIT License](LICENSE)
