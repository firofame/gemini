# Gemini PDF Toolkit

OCR, translate, polish, and generate TTS audiobooks from PDFs using Google Gemini models.

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

Set at least one API key:

```bash
export GEMINI_API_KEY="your-key"
# Or for key rotation:
export GEMINI_API_KEY_1="key1"
export GEMINI_API_KEY_2="key2"
```

## Usage

### translate.py — OCR & Translation

Extract and translate a PDF page-by-page using Gemini vision models. Supports resuming interrupted runs and configurable concurrency.

```bash
uv run translate.py document.pdf -p prompt_translate.txt -o output.md
```

**Options:**

| Flag | Default | Description |
| :--- | :--- | :--- |
| `pdf` | `Fazail-e-Sadqaat.pdf` | Input PDF path |
| `-o, --output` | `<pdf>_OCR.md` | Output markdown file |
| `-p, --prompt` | `prompt_translate.txt` | Prompt template file |
| `-m, --model` | `gemini-3.1-flash-lite` | Gemini model name |
| `-l, --limit` | _(none)_ | Process only N pages then stop |
| `--pages-per-batch` | `2` | PDF pages per API request |
| `-w, --workers` | `9` | Parallel API workers |
| `--wave-delay` | `5` | Seconds between worker waves |
| `-r, --retries` | `2` | Retries per failed batch |
| `--no-clean` | _(off)_ | Skip auto-generating `_Clean.txt` |

After translation, a cleaned plain-text version is automatically written to `<output>_Clean.txt` (strips page markers, separators, and skipped pages). Pass `--no-clean` to skip.

### tts.py — Text-to-Speech

Generates audio from a markdown file using Google Docs TTS via Camoufox.

```bash
uv run tts.py --login          # One-time login (headed)
uv run tts.py output.md        # Generate audio chunks + concatenated MP3
```

### archive_upload.py — Archive.org Upload

Upload generated files to Internet Archive.

```bash
export IA_ACCESS_KEY="your-key"
export IA_SECRET_KEY="your-secret"
uv run archive_upload.py
```

### list_models.py

List available Gemini models for your API key.

```bash
uv run list_models.py
```

## Prompt Files

| File | Purpose |
| :--- | :--- |
| `prompt_translate.txt` | Prompt for OCR + translation pass |
| `prompt_polish.txt` | Prompt for post-translation polishing pass |

Both contain formatting rules, honorific expansions, and TTS-optimization instructions tailored for Malayalam output. Edit them to suit your target language or domain.

## Project Files

| File | Description |
| :--- | :--- |
| `translate.py` | Main OCR, translation, and polishing pipeline |
| `tts.py` | Google Docs TTS via Camoufox automation |
| `archive_upload.py` | Internet Archive uploader |
| `list_models.py` | Lists available Gemini models |
| `comfi.py` | ComfyUI image generation via Modal |
