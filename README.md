# Gemini Tools

Small utility scripts for Gemini model listing, Internet Archive file management, and Modal-hosted ComfyUI.

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

## Internet Archive

The `archive/` scripts manage Internet Archive items:

```bash
export IA_ACCESS_KEY="your-key"
export IA_SECRET_KEY="your-secret"

uv run archive/upload.py
uv run archive/download.py
uv run archive/delete.py
```

Check each script before running; item identifiers and file paths are script-local configuration.

## ComfyUI On Modal

`comfi.py` defines a Modal app that launches ComfyUI with preloaded models:

```bash
uv run modal serve comfi.py
```
