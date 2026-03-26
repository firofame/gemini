import argparse
import time
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from google import genai


def split_pdf(input_path, output_dir, pages_per_chunk=10):
    """Split a PDF into smaller chunks and return the chunk paths."""
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    chunk_paths = []

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(0, total_pages, pages_per_chunk):
        writer = PdfWriter()
        chunk_end = min(i + pages_per_chunk, total_pages)

        for page_num in range(i, chunk_end):
            writer.add_page(reader.pages[page_num])

        chunk_filename = f"chunk_{i // pages_per_chunk:03d}_{i+1}-{chunk_end}.pdf"
        chunk_path = output_dir / chunk_filename

        with open(chunk_path, "wb") as f:
            writer.write(f)

        chunk_paths.append(chunk_path)

    return chunk_paths


def translate_chunk(client, model_id, file_path, prompt_template, context=None, target_language="Malayalam"):
    """Upload a chunk and request OCR + translation."""
    print(f"Processing {file_path.name}...")

    uploaded_file = None
    try:
        uploaded_file = client.files.upload(file=file_path)

        while uploaded_file.state.name == "PROCESSING":
            print("File is processing, waiting...")
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise ValueError("File processing failed on the server.")

        prompt = prompt_template.format(target_language=target_language)
        if context:
            prompt = f"Context from previous pages: {context}\n\n{prompt}"

        response = client.models.generate_content(
            model=model_id,
            contents=[uploaded_file, prompt]
        )

        if not response.text:
            raise ValueError("Model returned empty response.")

        # Request a brief summary for the next chunk's context
        summary_prompt = f"Provide a 1-2 sentence summary of the key plot points or terminology in the following translation to use as context for the next section:\n\n{response.text}"
        summary_response = client.models.generate_content(
            model=model_id,
            contents=[summary_prompt]
        )
        context_summary = summary_response.text if summary_response.text else ""

        return response.text, context_summary

    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
                print(f"Cleaned up {uploaded_file.name} from server.")
            except Exception as cleanup_error:
                print(f"Warning: Failed to delete file from server: {cleanup_error}")


def main():
    parser = argparse.ArgumentParser(
        description="OCR and translate a PDF book to Malayalam using Gemini."
    )
    parser.add_argument("input", help="Path to the input PDF file")
    parser.add_argument(
        "--output", "-o",
        default="translated_book.md",
        help="Path to the output markdown/text file"
    )
    parser.add_argument(
        "--pages", "-p",
        type=int,
        default=10,
        help="Pages per chunk (default: 10)"
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini-2.5-pro",
        help="Gemini model to use (default: gemini-2.5-pro)"
    )
    parser.add_argument(
        "--prompt",
        default="prompt.txt",
        help="Path to the prompt template file (default: prompt.txt)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File {args.input} not found.")
        return

    if args.pages <= 0:
        print("Error: --pages must be greater than 0.")
        return

    prompt_path = Path(args.prompt)
    if not prompt_path.exists():
        print(f"Error: Prompt file {args.prompt} not found.")
        return
    prompt_template = prompt_path.read_text(encoding="utf-8").strip()

    client = genai.Client()

    success_count = 0
    failure_count = 0
    resume_file = Path(args.output).with_suffix(".resume")
    last_processed_idx = -1
    if resume_file.exists():
        try:
            last_processed_idx = int(resume_file.read_text().strip())
            print(f"Resuming from chunk index {last_processed_idx + 1}")
        except ValueError:
            pass

    current_context = ""

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        chunk_paths = split_pdf(input_path, temp_dir, args.pages)

        # Open output file in append mode if resuming, else write mode
        mode = "a" if last_processed_idx >= 0 else "w"
        with open(args.output, mode, encoding="utf-8") as out_f:
            if mode == "w":
                out_f.write(f"# Translated Book: {input_path.stem}\n\n")

        for idx, chunk_path in enumerate(chunk_paths):
            if idx <= last_processed_idx:
                continue

            try:
                translated_text, next_context = translate_chunk(
                    client, args.model, chunk_path, prompt_template, current_context, "Malayalam"
                )
                current_context = next_context

                with open(args.output, "a", encoding="utf-8") as out_f:
                    out_f.write(translated_text)
                    out_f.write("\n\n----- (Page Break) -----\n\n")

                print(f"Successfully processed {chunk_path.name}")
                success_count += 1
                
                # Update resume file
                resume_file.write_text(str(idx))

                time.sleep(5)

            except Exception as e:
                print(f"Error processing {chunk_path.name}: {e}\n")
                failure_count += 1
                break # Stop on error to allow resuming later

    if failure_count == 0:
        if resume_file.exists():
            resume_file.unlink()
        print(f"\nDone! Translated book saved to: {args.output}")
    else:
        print(f"\nScript stopped due to an error. You can resume by running the script again.")
    
    print(f"Total chunks processed successfully: {success_count}")
    print(f"Total chunks failed: {failure_count}")


if __name__ == "__main__":
    main()