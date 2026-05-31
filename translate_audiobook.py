import argparse
import os
import re
import time
import glob
from google import genai
from google.genai import types
import itertools
import threading
import concurrent.futures

# --- THREAD LOCKS ---
_client_lock = threading.Lock()
_print_lock = threading.Lock()  # Keeps terminal output clean during parallel processing

def safe_print(message):
    """Thread-safe print so terminal output doesn't get scrambled."""
    with _print_lock:
        print(message)

# --- API KEY SETUP ---
# Automatically loads GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, etc.
API_KEYS = [v for k, v in sorted(os.environ.items()) if k.startswith("GEMINI_API_KEY_")]
if not API_KEYS:
    key = os.environ.get("GEMINI_API_KEY", "")
    API_KEYS = [key] if key else []
if not API_KEYS:
    raise RuntimeError("No GEMINI_API_KEY or GEMINI_API_KEY_N environment variables found")

safe_print(f"Loaded {len(API_KEYS)} API keys. Ready for rotation.")

_clients = [genai.Client(api_key=k) for k in API_KEYS]
_client_cycle = itertools.cycle(_clients)

def get_client():
    with _client_lock:
        return next(_client_cycle)

# --- UTILITY FUNCTIONS ---
def get_processed_parts(filename):
    if not os.path.exists(filename):
        return 0
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    matches = re.findall(r'^## Part (\d+)', content, re.MULTILINE | re.IGNORECASE)
    if not matches:
        return 0
    return max(int(m) for m in matches)

def get_last_context(filename):
    if not os.path.exists(filename):
        return ""
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    parts = re.split(r'^## Part \d+\s*$', content, flags=re.MULTILINE | re.IGNORECASE)
    if len(parts) > 1:
        return parts[-1].strip()
    return ""

def parse_retry_delay(error_msg):
    s = str(error_msg)
    m = re.search(r'retryDelay["\']?:\s*["\']?(\d+)', s)
    if m:
        return int(m.group(1)) + 5
    m = re.search(r'retry in (\d+(?:\.\d+)?)s', s, re.IGNORECASE)
    if m:
        return int(float(m.group(1))) + 5
    return None

def chunk_text(text, max_chars=15000):
    paragraphs = re.split(r'\n\n+', text.strip())
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if not p.strip():
            continue
        if len(current_chunk) + len(p) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
        else:
            current_chunk += p + "\n\n"
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

# --- CORE TRANSLATION LOGIC ---
def translate_single_chunk(filename_base, part_num, chunk_text, prompt, model, previous_malayalam="", max_retries=6):
    context_instruction = ""
    if previous_malayalam:
        context_instruction = (
            f"\n\n[CRITICAL CONTEXT: Here is the ending of the PREVIOUS translated part. "
            f"Use this to understand the current flow and pronoun references. "
            f"DO NOT TRANSLATE THIS AGAIN, ONLY TRANSLATE THE NEW TEXT PROVIDED BELOW.]\n"
            f"--- PREVIOUS MALAYALAM CONTEXT ---\n"
            f"...{previous_malayalam[-500:]}\n"
            f"-----------------------------------\n"
        )
    
    full_prompt = (
        f"{prompt}\n"
        f"{context_instruction}\n"
        f"--- NEW URDU TEXT TO TRANSLATE NOW ---\n"
        f"{chunk_text}\n"
    )

    attempts = 0
    while attempts < max_retries:
        try:
            response = get_client().models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                    ]
                )
            )
            if response.text is None:
                raise ValueError("Model returned empty response (likely Safety Filter block)")
            return response.text.strip(), None
        
        except Exception as e:
            attempts += 1
            error_str = str(e)
            
            # Smart delay handling
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                parsed_delay = parse_retry_delay(error_str)
                wait = parsed_delay if parsed_delay else 60
            elif '503' in error_str or 'UNAVAILABLE' in error_str:
                wait = 30 * attempts
            else:
                wait = attempts * 10
                
            safe_print(f"  [⚠️ Rate Limit/Error] {filename_base} (Part {part_num}): {error_str.splitlines()[0]}. Retrying in {wait}s (Attempt {attempts}/{max_retries})...")
            time.sleep(wait)

    return None, f"Failed after {max_retries} attempts for Part {part_num}"

# --- CHAPTER PROCESSING LOGIC ---
def process_chapter(input_file, output_file, prompt, model):
    filename_base = os.path.basename(input_file)
    
    with open(input_file, "r", encoding="utf-8") as f:
        source_text = f.read()

    chunks = chunk_text(source_text, max_chars=15000)
    total_parts = len(chunks)
    
    start_part = get_processed_parts(output_file) + 1
    previous_malayalam = get_last_context(output_file)

    if start_part > total_parts:
        safe_print(f"  ✓ [{filename_base}] is already fully translated. Skipping.")
        return True

    if start_part > 1:
        safe_print(f"  -> [{filename_base}] Resuming from Part {start_part}/{total_parts}...")

    for i in range(start_part - 1, total_parts):
        part_num = i + 1
        current_urdu = chunks[i]
        
        safe_print(f"  -> [{filename_base}] Translating Part {part_num}/{total_parts}...")
        
        malayalam_text, error = translate_single_chunk(
            filename_base=filename_base,
            part_num=part_num,
            chunk_text=current_urdu,
            prompt=prompt,
            model=model,
            previous_malayalam=previous_malayalam
        )

        if error:
            safe_print(f"  ❌ FATAL ERROR in {filename_base}: {error}")
            return False

        # Write to disk immediately so progress is saved
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"## Part {part_num}\n\n{malayalam_text}\n\n")
        
        previous_malayalam = malayalam_text
        
        # Short cooldown between parts of the *same* chapter 
        # (parallel threads will keep the overall RPM high)
        time.sleep(3)

    safe_print(f"  ✅ Finished [{filename_base}] successfully!")
    return True

# --- THREAD WRAPPER ---
def _process_file_wrapper(input_file, output_dir, master_prompt, model):
    """Helper function to run a single chapter in a background thread."""
    filename = os.path.basename(input_file)
    out_name = filename.replace(".txt", "_Malayalam.md")
    output_file = os.path.join(output_dir, out_name)
    
    safe_print(f"[STARTING] {filename}...")
    success = process_chapter(input_file, output_file, master_prompt, model)
    return success

# --- MAIN PARALLEL LOOP ---
def translate_all_chapters(input_dir, output_dir, prompt_file, model):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(prompt_file, "r", encoding="utf-8") as f:
        master_prompt = f.read().strip()

    # Get all .txt files, sorted alphabetically
    input_files = sorted(glob.glob(os.path.join(input_dir, "*.txt")))
    
    if not input_files:
        safe_print(f"No .txt files found in directory: {input_dir}")
        return

    safe_print(f"\n{'='*50}")
    safe_print(f" Found {len(input_files)} chapters to translate.")
    safe_print(f"{'='*50}\n")

    # Set to 10 based on your limits: 
    # 10 concurrent files * (1 req / ~30 sec) = ~20 Requests per minute.
    # You have 45 RPM max (15 RPM * 3 keys), so this is extremely safe and fast.
    MAX_CONCURRENT_CHAPTERS = 10 
    
    safe_print(f"Starting parallel processing with {MAX_CONCURRENT_CHAPTERS} concurrent workers...\n")

    # Launch threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CHAPTERS) as executor:
        futures = {executor.submit(_process_file_wrapper, f, output_dir, master_prompt, model): f for f in input_files}
        
        for future in concurrent.futures.as_completed(futures):
            file_path = futures[future]
            try:
                success = future.result()
                if not success:
                    safe_print(f"[ERROR] Failed to complete {os.path.basename(file_path)}")
            except Exception as e:
                safe_print(f"[FATAL EXCEPTION] {os.path.basename(file_path)} generated an exception: {e}")

    safe_print("\n🎉 All Chapters Processing Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate Audiobook Chapters to Malayalam TTS script in parallel.")
    parser.add_argument("-i", "--input-dir", default="Hayat al-Sahaba/Arabic_Chapters", help="Directory containing chapter .txt files")
    parser.add_argument("-o", "--output-dir", default="Malayalam_Chapters", help="Directory to save translated .md files")
    parser.add_argument("-p", "--prompt", default="prompt_tts_malayalam.txt", help="Master prompt file")
    parser.add_argument("-m", "--model", default="gemini-3.1-flash-lite", help="Gemini Model") # Updated to default to the newest flash
    
    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' not found. Please create it and add your split .txt files.")
    elif not os.path.exists(args.prompt):
        print(f"Error: Prompt file '{args.prompt}' not found.")
    else:
        translate_all_chapters(args.input_dir, args.output_dir, args.prompt, args.model)