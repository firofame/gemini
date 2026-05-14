import os
import re
import time
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # pymupdf — renders PDF pages as images
from google import genai
from google.genai import types

# --- Configuration ---
PDF_PATH = "Fazail-e-Sadaqat.pdf"
OUTPUT_FILE = "Fazail-e-Sadaqat_OCR.md"
PROMPT_FILE = "prompt.txt"
# MODEL = "gemini-3.1-flash-lite"
MODEL = "gemma-4-31b-it"

# Set this to True if you want to limit how many pages are processed in one run
LIMIT_PROCESSING = True
# How many pages to process before stopping
MAX_PAGES_TO_PROCESS = 100
# How many PDF pages to send per API request (1 = safest, 2 = halves requests)
PAGES_PER_BATCH = 1
# Number of parallel API requests (tune to your RPM limit)
MAX_WORKERS = 10
# Seconds to wait between API requests (0 for unlimited RPD models like Gemma)
REQUEST_DELAY = 0
# ---------------------

client = genai.Client()

def get_processed_pages(filename):
    """Parses the output file to find which pages are already completed using regex.
    Catches variations like '## Page 49', '# Page 49', 'Page 49:', etc."""
    processed = set()
    if not os.path.exists(filename):
        return processed
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    matches = re.findall(r'^#*\s*Page\s+(\d+)', content, re.MULTILINE | re.IGNORECASE)
    for m in matches:
        processed.add(int(m))
    return processed

def get_last_page_text(filename):
    """Reads the output file and returns the text of the very last processed page."""
    if not os.path.exists(filename):
        return ""
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    # Split by the page headers and grab the last section's text
    parts = content.split("## Page ")
    if len(parts) < 2:
        return ""
    last_section = parts[-1]
    # Remove the page number line and trailing separator
    lines = last_section.split("\n", 1)
    if len(lines) > 1:
        text = lines[1].replace("---", "").strip()
        return text
    return ""


def process_single_batch(doc, batch_pages, prompt, previous_text=""):
    """Process a single batch of pages. Returns (batch_pages, result_text, error).
    This function is thread-safe and called from the thread pool."""
    # Render pages as PNG images
    image_parts = []
    for pn in batch_pages:
        page = doc[pn - 1]  # fitz uses 0-based indexing
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        image_parts.append(
            types.Part.from_bytes(data=img_bytes, mime_type='image/png')
        )

    # Build prompt with strict header enforcement
    page_list = " and ".join(str(p) for p in batch_pages)
    valid_headers = " and ".join(f"'## Page {p}'" for p in batch_pages)

    context_prompt = prompt + (
        f"\n\nFORMATTING INSTRUCTIONS FOR THIS BATCH:\n"
        f"You are receiving PDF page(s) {page_list}. "
        f"The ONLY valid headers you are allowed to output are {valid_headers}. "
        f"Do NOT output any other page numbers you see printed on the image. "
        f"If a page is just an index/blank, write 'SKIP_PAGE' under its specific header."
    )
    if previous_text:
        context_prompt += (
            f"\n\nContext from the previous page (do not repeat this, "
            f"but use it to seamlessly continue any split sentences):\n"
            f"{previous_text[-500:]}"
        )

    attempts = 0
    while attempts < 3:
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=image_parts + [context_prompt]
            )
            if response.text is None:
                raise ValueError("Model returned empty response")
            return (batch_pages, response.text.strip(), None)
        except Exception as e:
            attempts += 1
            wait = attempts * 10
            print(f"  -> Error on Page(s) {page_list}: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    return (batch_pages, None, f"Failed after 3 attempts for page(s) {page_list}")


def format_result(batch_pages, content, processed_pages):
    """Format the model's response into markdown. Returns (text_to_write, context_text, pages_count)."""
    # If the entire response is just SKIP_PAGE (all pages skipped)
    stripped = content
    for token in ["SKIP_PAGE", "#", "Page"] + [str(p) for p in batch_pages]:
        stripped = stripped.replace(token, "")
    if stripped.strip() == "":
        text = ""
        for pn in batch_pages:
            if pn not in processed_pages:
                text += f"\n\n## Page {pn}\n\n<!-- SKIPPED: Index/Blank page -->\n\n---\n"
        label = f"Pages {batch_pages[0]}-{batch_pages[-1]}" if len(batch_pages) > 1 else f"Page {batch_pages[0]}"
        print(f"  -> {label} skipped (Index/Blank).")
        return (text, "", 0)

    # Ensure first page header exists
    if not re.search(rf'^#*\s*Page\s+{batch_pages[0]}\b', content, re.IGNORECASE | re.MULTILINE):
        content = f"## Page {batch_pages[0]}\n\n{content}"

    # Mark any individually skipped pages
    for pn in batch_pages:
        section_marker = f"## Page {pn}"
        if section_marker in content:
            idx = content.index(section_marker)
            next_marker = f"## Page {pn + 1}"
            if next_marker in content:
                section_text = content[idx:content.index(next_marker)]
            else:
                section_text = content[idx:]

            if "SKIP_PAGE" in section_text:
                content = content.replace(
                    section_text,
                    f"## Page {pn}\n\n<!-- SKIPPED: Index/Blank page -->\n"
                )
                print(f"  -> Page {pn} skipped (Index/Blank).")

    text_to_write = f"\n\n{content}\n\n---\n"

    # Extract context from the last real content section
    context_text = ""
    parts = content.split("## Page ")
    for part in reversed(parts[1:]):
        part_text = part.split("\n", 1)[-1].strip()
        if "SKIPPED" not in part_text and part_text:
            context_text = part_text
            break

    return (text_to_write, context_text, len(batch_pages))


def ocr_pdf():
    if not os.path.exists(PDF_PATH):
        print(f"Error: {PDF_PATH} not found.")
        return

    if not os.path.exists(PROMPT_FILE):
        print(f"Error: {PROMPT_FILE} not found.")
        return

    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    processed_pages = get_processed_pages(OUTPUT_FILE)
    
    print(f"Total pages in PDF: {total_pages}")
    print(f"Already processed: {len(processed_pages)} pages.")

    # Load context from the last previously processed page (for cross-page continuity)
    previous_text = get_last_page_text(OUTPUT_FILE)
    if previous_text:
        print(f"Loaded {len(previous_text)} chars of context from previous run.")

    # Build the list of all batches that need processing
    all_batches = []
    for batch_start in range(1, total_pages + 1, PAGES_PER_BATCH):
        batch_end = min(batch_start + PAGES_PER_BATCH - 1, total_pages)
        batch_pages = list(range(batch_start, batch_end + 1))
        if all(pn in processed_pages for pn in batch_pages):
            continue
        all_batches.append(batch_pages)

    if LIMIT_PROCESSING:
        # Limit batches so total pages don't exceed MAX_PAGES_TO_PROCESS
        limited = []
        count = 0
        for batch in all_batches:
            if count >= MAX_PAGES_TO_PROCESS:
                break
            limited.append(batch)
            count += len(batch)
        all_batches = limited

    print(f"Batches to process: {len(all_batches)} ({sum(len(b) for b in all_batches)} pages)")
    print(f"Parallel workers: {MAX_WORKERS}")

    pages_processed_this_run = 0

    # Process batches in waves of MAX_WORKERS concurrent requests
    for wave_start in range(0, len(all_batches), MAX_WORKERS):
        wave = all_batches[wave_start : wave_start + MAX_WORKERS]

        # Submit all batches in this wave concurrently
        # Only the first batch in the wave gets cross-page context
        futures = {}
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for i, batch_pages in enumerate(wave):
                label = f"Pages {batch_pages[0]}-{batch_pages[-1]}" if len(batch_pages) > 1 else f"Page {batch_pages[0]}"
                print(f"  Submitting {label}...")
                ctx = previous_text if i == 0 else ""
                future = executor.submit(process_single_batch, doc, batch_pages, prompt, ctx)
                futures[future] = batch_pages

            # Collect results as they complete
            results = {}
            for future in as_completed(futures):
                batch_pages, content, error = future.result()
                if error:
                    print(f"  ❌ {error}")
                else:
                    results[batch_pages[0]] = (batch_pages, content)

        # Write results in page order
        for start_page in sorted(results.keys()):
            batch_pages, content = results[start_page]
            text_to_write, context_text, count = format_result(batch_pages, content, processed_pages)

            if text_to_write:
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(text_to_write)

            if context_text:
                previous_text = context_text
            pages_processed_this_run += count

            label = f"Pages {batch_pages[0]}-{batch_pages[-1]}" if len(batch_pages) > 1 else f"Page {batch_pages[0]}"
            if count > 0:
                print(f"  ✅ {label}")

        if REQUEST_DELAY > 0:
            time.sleep(REQUEST_DELAY)

    print(f"Finished. Extracted {pages_processed_this_run} pages. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    ocr_pdf()