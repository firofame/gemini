# Gemini Tools

Small utility scripts for Gemini model listing and Modal-hosted ComfyUI.

The book OCR/translation pipeline was moved to:

```text
/home/firoz/Desktop/gemini-book-pipeline
```

The Google Docs TTS tool was moved to:

```text
/home/firoz/Desktop/google-docs-tts
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

## ComfyUI On Modal

`comfi.py` defines a Modal app that launches ComfyUI with preloaded models:

```bash
uv run modal serve comfi.py
```
