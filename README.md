# Gemini Book Toolkit

A comprehensive Python toolkit for automating the process of OCR, translating PDF books into Malayalam, and generating audio versions (MP3) using Gemini and Google Docs.

## Features

- **Audio/Video Transcription**: Uses OpenAI Whisper on Modal to transcribe media files into text with automatic language detection.
- **PDF to Malayalam Translation**: Leverages Google Gemini for high-quality OCR and translation of books.
- **Context-Aware Processing**: Maintains story/topic context between PDF chunks for coherent translations.
- **TTS optimization**: Converts Malayalam text into professional audiobook scripts with honorific expansions and natural pauses.
- **Text-to-Speech (TTS)**: Uses Google Docs' natural-sounding voices via Playwright automation.
- **Internet Archive Integration**: Automatically uploads text and audio files to archive.org with full metadata.
- **Instagram Audio Downloader**: Utility to download audio from Instagram Reels for reference or inclusion.

## Prerequisites

- Python 3.8+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- Google Account (for TTS/Google Docs access)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (for audio downloads)
- [Playwright](https://playwright.dev/python/docs/intro)
- [Modal](https://modal.com/) (for Whisper GPU transcription)

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
   pip install google-genai pypdf playwright internetarchive camoufox modal
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

1. **Transcribe source audio**:
   ```bash
   modal run transcribe.py --audio-file downloads/audio.mp3
   ```
   *Note: Language defaults to English or auto-detected. Use `--language ar` for Arabic.*

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

#### Download Instagram Audio
To download audio from an Instagram Reel:
```bash
python download_audio.py <reel-url>
```

## Configuration

- **`prompt.txt`**: The system prompt used for Gemini OCR/Translation. You can customize this to change the translation style or target language.
- **`tts.py`**: Update `CONFIG['doc_url']` to a Google Doc you have edit access to.

## License

[MIT License](LICENSE)
