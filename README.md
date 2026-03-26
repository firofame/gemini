# Gemini Book Translator

A powerful Python tool to OCR and translate multi-page PDF books (both digital and scanned) to Malayalam using the Google Gemini 1.5/2.0 API.

## 🚀 Features

- **High-Quality OCR & Translation**: Leverages Gemini's multimodal capabilities to handle scanned images and complex layouts natively.
- **Batch Processing**: Automatically splits large books (e.g., 600+ pages) into manageable chunks to ensure reliability and stay within API limits.
- **Resume Functionality**: Progress is tracked automatically. If interrupted, the script skips already processed chunks upon restart.
- **Context-Awareness**: Maintains consistency in character names, plot, and style by passing summaries from previous batches to the next section.
- **Configurable Prompts**: Easily customize translation instructions via `prompt.txt`.

## 🛠️ Prerequisites

- **Python**: 3.8 or higher.
- **Gemini API Key**: Obtain one from [Google AI Studio](https://aistudio.google.com/).
- **Dependencies**: `google-genai` and `pypdf`.

## 📦 Installation

1. **Clone or download** this repository.
2. **Setup a virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install google-genai pypdf
   ```

## 📖 Usage

1. **Set your API key**:
   ```bash
   export GOOGLE_API_KEY="your-api-key-here"
   ```

2. **Run the translator**:
   ```bash
   python translate_book.py path/to/your_book.pdf --output malayalam_version.md
   ```

### Command Line Options

| Option | Shorthand | Default | Description |
| :--- | :--- | :--- | :--- |
| `--output` | `-o` | `translated_book.md` | Path to the output file. |
| `--pages` | `-p` | `10` | Number of pages per batch. |
| `--model` | `-m` | `gemini-1.5-flash` | The Gemini model to use. |
| `--prompt` | | `prompt.txt` | Path to your custom prompt template. |

## ⚙️ Configuration

You can customize the translation instructions by editing **`prompt.txt`**. The script uses `{target_language}` as a placeholder which it fills dynamically.

## 📝 License

MIT
