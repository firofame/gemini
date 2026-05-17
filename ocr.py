import argparse
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # pymupdf — renders PDF pages as images
from google import genai
from google.genai import types

import itertools
import threading

API_KEYS = [v for k, v in sorted(os.environ.items()) if k.startswith("GEMINI_API_KEY_")]
if not API_KEYS:
    key = os.environ.get("GEMINI_API_KEY", "")
    API_KEYS = [key] if key else []
if not API_KEYS:
    raise RuntimeError("No GEMINI_API_KEY or GEMINI_API_KEY_N environment variables found")

_clients = [genai.Client(api_key=k) for k in API_KEYS]
_client_cycle = itertools.cycle(_clients)
_client_lock = threading.Lock()

def get_client():
    with _client_lock:
        return next(_client_cycle)

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


def parse_retry_delay(error_msg):
    """Try to extract the suggested retry delay from a 429 error message."""
    s = str(error_msg)
    # Look for 'retryDelay' field like '49s' or 'retry in 49.938153576s'
    m = re.search(r'retryDelay["\']?:\s*["\']?(\d+)', s)
    if m:
        return int(m.group(1)) + 5  # add 5s buffer
    # Look for 'Please retry in Xs' pattern
    m = re.search(r'retry in (\d+(?:\.\d+)?)s', s, re.IGNORECASE)
    if m:
        return int(float(m.group(1))) + 5
    return None


def process_single_batch(doc, batch_pages, prompt, model, previous_text="", max_retries=2):
    """Process a single batch of pages. Returns (batch_pages, result_text, error).
    This function is thread-safe and called from the thread pool."""

    # Render pages as PNG images
    image_parts = []
    for pn in batch_pages:
        page = doc[pn - 1]  # fitz uses 0-based indexing
        pix = page.get_pixmap(dpi=300)
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
    while attempts < max_retries:
        try:
            response = get_client().models.generate_content(
                model=model,
                contents=image_parts + [context_prompt]
            )
            if response.text is None:
                raise ValueError("Model returned empty response")
            return (batch_pages, response.text.strip(), None)
        except Exception as e:
            attempts += 1
            error_str = str(e)
            # Smart delay: parse 429 retryDelay or use exponential backoff
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                parsed_delay = parse_retry_delay(error_str)
                wait = parsed_delay if parsed_delay else 60
            elif '503' in error_str or 'UNAVAILABLE' in error_str:
                wait = 30 * attempts  # longer waits for overloaded servers
            else:
                wait = attempts * 10
            print(f"  -> Error on Page(s) {page_list}: {e}. Retrying in {wait}s (attempt {attempts}/{max_retries})...")
            time.sleep(wait)

    return (batch_pages, None, f"Failed after {max_retries} attempts for page(s) {page_list}")


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


def ocr_pdf(pdf_path, output_file, prompt_file, model,
            limit=None, pages_per_batch=2,
            max_workers=9, wave_delay=5, max_retries=2):
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    if not os.path.exists(prompt_file):
        print(f"Error: {prompt_file} not found.")
        return

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    processed_pages = get_processed_pages(output_file)
    
    print(f"Total pages in PDF: {total_pages}")
    print(f"Already processed: {len(processed_pages)} pages.")

    # Load context from the last previously processed page (for cross-page continuity)
    previous_text = get_last_page_text(output_file)
    if previous_text:
        print(f"Loaded {len(previous_text)} chars of context from previous run.")

    # Build the list of all batches that need processing
    all_batches = []
    for batch_start in range(1, total_pages + 1, pages_per_batch):
        batch_end = min(batch_start + pages_per_batch - 1, total_pages)
        batch_pages = list(range(batch_start, batch_end + 1))
        if all(pn in processed_pages for pn in batch_pages):
            continue
        all_batches.append(batch_pages)

    if limit is not None:
        limited = []
        count = 0
        for batch in all_batches:
            if count >= limit:
                break
            limited.append(batch)
            count += len(batch)
        all_batches = limited

    print(f"Batches to process: {len(all_batches)} ({sum(len(b) for b in all_batches)} pages)")
    print(f"Parallel workers: {max_workers}")

    pages_processed_this_run = 0

    # Process batches in waves of MAX_WORKERS concurrent requests
    failed_batches = []
    total_batches = len(all_batches)

    for wave_start in range(0, total_batches, max_workers):
        wave = all_batches[wave_start : wave_start + max_workers]
        wave_num = wave_start // max_workers + 1
        total_waves = (total_batches + max_workers - 1) // max_workers
        print(f"\n--- Wave {wave_num}/{total_waves} ---")

        # Submit all batches in this wave concurrently
        # Only the first batch in the wave gets cross-page context
        futures = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i, batch_pages in enumerate(wave):
                label = f"Pages {batch_pages[0]}-{batch_pages[-1]}" if len(batch_pages) > 1 else f"Page {batch_pages[0]}"
                print(f"  Submitting {label}...")
                ctx = previous_text if i == 0 else ""
                future = executor.submit(process_single_batch, doc, batch_pages, prompt, model, ctx)
                futures[future] = ctx

            # Collect results as they complete
            results = {}
            for future in as_completed(futures):
                batch_pages, content, error = future.result()
                ctx = futures[future]
                if error:
                    print(f"  ❌ {error}")
                    failed_batches.append((batch_pages, ctx))
                else:
                    results[batch_pages[0]] = (batch_pages, content)

        # Write results in page order
        for start_page in sorted(results.keys()):
            batch_pages, content = results[start_page]
            text_to_write, context_text, count = format_result(batch_pages, content, processed_pages)

            if text_to_write:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(text_to_write)

            if context_text:
                previous_text = context_text
            pages_processed_this_run += count

            label = f"Pages {batch_pages[0]}-{batch_pages[-1]}" if len(batch_pages) > 1 else f"Page {batch_pages[0]}"
            if count > 0:
                print(f"  ✅ {label}")

        # Rate-limit delay between waves
        if wave_start + max_workers < total_batches:
            print(f"  ⏳ Waiting {wave_delay}s before next wave (rate limit)...")
            time.sleep(wave_delay)

    # --- Retry pass for failed pages (one-at-a-time with generous delays) ---
    if failed_batches:
        print(f"\n{'='*50}")
        print(f"Retrying {len(failed_batches)} failed batch(es) sequentially...")
        print(f"{'='*50}")
        still_failed = []
        for batch_pages, ctx in failed_batches:
            page_list = ", ".join(str(p) for p in batch_pages)
            print(f"  🔄 Retrying page(s) {page_list}...")
            time.sleep(15)  # generous delay before each retry
            batch_pages_result, content, error = process_single_batch(
                doc, batch_pages, prompt, model, ctx, max_retries=5
            )
            if error:
                print(f"  ❌ {error}")
                still_failed.append(batch_pages)
            else:
                text_to_write, _, count = format_result(
                    batch_pages_result, content, processed_pages
                )
                if text_to_write:
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(text_to_write)
                pages_processed_this_run += count
                print(f"  ✅ Page(s) {page_list} recovered!")

        if still_failed:
            failed_pages = [p for b in still_failed for p in b]
            print(f"\n⚠️  Permanently failed pages: {failed_pages}")
            print(f"   Re-run the script to retry these pages.")

    sort_output(output_file)

    print(f"\nFinished. Extracted {pages_processed_this_run} pages. Results saved to {output_file}")


def sort_output(output_file):
    """Reads the markdown file, sorts sections by page number, and writes back."""
    if not os.path.exists(output_file):
        return

    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()

    parts = re.split(r'^(#*\s*Page\s+(\d+))', content, flags=re.MULTILINE | re.IGNORECASE)

    if len(parts) < 4:
        return

    pre_text = parts[0]
    pages = []

    for i in range(1, len(parts), 3):
        header = parts[i]
        page_num = int(parts[i+1])
        body = parts[i+2] if (i+2) < len(parts) else ""
        pages.append((page_num, header, body))

    pages.sort(key=lambda x: x[0])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pre_text)
        for _, header, body in pages:
            f.write(header + body)

    print(f"\n  -> Sorted output file '{os.path.basename(output_file)}' numerically by page number.")


def clean_output(input_file):
    """Strip page markers and formatting, producing a clean plain-text version."""
    output_file = input_file.replace(".md", "_Clean.txt")

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    text = re.sub(r'^## Page \d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^---\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*<!-- SKIPPED:.*?-->\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text.strip())

    print(f"Cleaned text saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OCR and translate a PDF using Gemini models."
    )
    parser.add_argument(
        "pdf", nargs="?", default="Malfoozat-Maulana-Ilyas.pdf",
        help="Path to the PDF file (default: Malfoozat-Maulana-Ilyas.pdf)"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output markdown file (default: <pdf_name>_OCR.md)"
    )
    parser.add_argument(
        "-p", "--prompt", default="prompt_urdu_ocr.txt",
        help="Prompt file (default: prompt_urdu_ocr.txt)"
    )
    parser.add_argument(
        "-m", "--model", default="gemini-3.1-flash-lite",
        help="Gemini model name (default: gemini-3.1-flash-lite)"
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=None,
        help="Limit processing to N pages"
    )
    parser.add_argument(
        "--pages-per-batch", type=int, default=1,
        help="Pages per API batch request (default: 1)"
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=12,
        help="Max parallel API workers (default: 12)"
    )
    parser.add_argument(
        "--wave-delay", type=int, default=2,
        help="Seconds delay between waves (default: 2)"
    )
    parser.add_argument(
        "-r", "--retries", type=int, default=2,
        help="Max retries per batch (default: 2)"
    )
    parser.add_argument(
        "--no-clean", action="store_true",
        help="Skip generating the cleaned plain-text output"
    )
    args = parser.parse_args()

    output_file = args.output or args.pdf.replace(".pdf", "_OCR.md")

    ocr_pdf(
        pdf_path=args.pdf,
        output_file=output_file,
        prompt_file=args.prompt,
        model=args.model,
        limit=args.limit,
        pages_per_batch=args.pages_per_batch,
        max_workers=args.workers,
        wave_delay=args.wave_delay,
        max_retries=args.retries,
    )

    if not args.no_clean and os.path.exists(output_file):
        clean_output(output_file)