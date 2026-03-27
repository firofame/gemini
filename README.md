# Gemini Book Toolkit

A comprehensive Python toolkit for automating the process of OCR, translating PDF books into Malayalam, and generating audio versions (MP3) using Gemini and Google Docs.

## Features

- **Audio/Video Transcription**: Uses Cloudflare Workers AI (Whisper-large-v3-turbo) to transcribe local files or URLs (Instagram, YouTube, etc.) directly into text.
- **PDF to Malayalam Translation**: Leverages Google Gemini for high-quality OCR and translation of books.
- **Context-Aware Processing**: Maintains story/topic context between PDF chunks for coherent translations.
- **TTS optimization**: Converts Malayalam text into professional audiobook scripts with honorific expansions and natural pauses.
- **Text-to-Speech (TTS)**: Uses Google Docs' natural-sounding voices via Playwright automation.
- **Internet Archive Integration**: Automatically uploads text and audio files to archive.org with full metadata.
- **URL Transcription**: Supports direct URLs (Instagram, YouTube) by automatically downloading audio via yt-dlp before transcription.

## Prerequisites

- Python 3.8+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- [Cloudflare Account ID & API Token](https://developers.cloudflare.com/workers-ai/)
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
   pip install google-genai pypdf playwright internetarchive camoufox requests
   ```

4. Install Playwright browsers:
   ```bash
   playwright install firefox
   ```

## Workflow Guide

### 1. Authentication
Before running the TTS or translation scripts that interact with Google services, you need to authenticate:
```bash
python auth.py
```
This will open a browser for you to sign in. The session will be saved to `auth.json`.

---

### Workflow A: PDF Book Processing
1. **Translate the Book**:
   ```bash
   python translate_book.py path/to/your/book.pdf --output translated_book.md
   ```
2. **Generate Audio**:
   ```bash
   python tts.py translated_book.md output.mp3
   ```

---

### Workflow B: Audio/Video to Malayalam Audiobook
This workflow transcribes a source audio file, translates the content to Malayalam, and formats it for a high-quality audiobook listening experience.

1. **Transcribe source audio (Local or URL)**:
   ```bash
   # For a local file
   python3 transcribe.py --audio-file downloads/audio.mp3

   # For a URL (Instagram, YouTube, etc.)
   python3 transcribe.py --audio-file https://www.instagram.com/reels/DVXct1kj91A/
   ```
   *Note: Uses Cloudflare Workers AI with specialized support for religious speakers/mixed languages via the turbo model. Use `--language ar` for Arabic.*

2. **Translate transcript to Malayalam**:
   ```bash
   python translate_text.py downloads/audio_transcript.txt
   ```

3. **Format for Audiobook TTS**:
   ```bash
   python audiobook_script.py downloads/audio_transcript_ml.txt
   ```
   *This expands honorifics (S.A.W, R.A) and adds natural breathing pauses.*

4. **Generate Final Audiobook MP3**:
   ```bash
   python tts.py downloads/audio_transcript_ml_audiobook.txt output.mp3
   ```

---

### Other Utilities

#### Upload to Internet Archive
To upload your results to archive.org:
1. Configure the `identifier` and `source_files` in `archive_upload.py`.
2. Run the script:
```bash
python archive_upload.py
```

#### Direct URL Support
You can now pass a URL directly to the transcription script. It will handle the download and transcription in one go:
```bash
python3 transcribe.py --audio-file <reel-url>
```

## Configuration

- **`prompt.txt`**: The system prompt used for Gemini OCR/Translation. You can customize this to change the translation style or target language.
- **`tts.py`**: Update `CONFIG['doc_url']` to a Google Doc you have edit access to.

## License

[MIT License](LICENSE)
