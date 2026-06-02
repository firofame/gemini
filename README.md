# Gemini Tools

Small utility scripts for Gemini model listing.

The book OCR/translation pipeline was moved to:

```text
/home/firoz/Desktop/gemini-book-pipeline
```

The Google Docs TTS tool was moved to:

```text
/home/firoz/Desktop/google-docs-tts
```

The Modal-hosted ComfyUI runner was moved to:

```text
/home/firoz/Desktop/comfi
```

The Internet Archive management tool was moved to:

```text
/home/firoz/Desktop/archive
```

## Setup

```bash
uv venv
uv pip install -r requirements.txt
```

## Gemini Models

List available Gemini models for the configured API key:

```bash
export GEMINI_API_KEY="your-key"
uv run list_models.py
```

Numbered Gemini API keys are also supported:

```bash
export GEMINI_API_KEY_1="key1"
export GEMINI_API_KEY_2="key2"
```
