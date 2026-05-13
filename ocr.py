import os
import sys
import asyncio
import argparse
from pathlib import Path
import fitz
from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model


async def ocr_page(client: GeminiClient, image_path: str, model: str, prompt: str) -> str:
    response = await client.generate_content(prompt, files=[image_path], model=model)
    return response.text


async def ocr_page_with_retry(client: GeminiClient, image_path: str, model: str,
                              prompt: str, retries: int, base_delay: int) -> str:
    last_error = None
    for attempt in range(retries):
        try:
            return await ocr_page(client, image_path, model, prompt)
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                wait = base_delay * (2 ** attempt)
                print(f"  Retry {attempt+1}/{retries} in {wait}s: {e}", file=sys.stderr)
                await asyncio.sleep(wait)
    raise last_error


def _sorted_parts(parts_dir: Path) -> list[int]:
    return sorted(
        int(p.stem.replace("page_", ""))
        for p in parts_dir.glob("page_*.txt")
    )


def rebuild_output(parts_dir: Path, out_path: Path, pages: set[int]) -> None:
    wanted = [p for p in _sorted_parts(parts_dir) if p in pages]
    with out_path.open("w", encoding="utf-8") as f:
        for p in wanted:
            f.write((parts_dir / f"page_{p}.txt").read_text(encoding="utf-8") + "\n")


async def main():
    parser = argparse.ArgumentParser(description="OCR PDF pages using Gemini")
    parser.add_argument("pdf", type=Path, help="Path to the PDF file")
    parser.add_argument("--pages", "-p", type=str, default="1",
                        help="Pages to OCR (e.g. 1, 1-5, 1,3,5). Default: 1")
    parser.add_argument("--model", "-m", type=str, default=Model.PLUS_THINKING,
                        help="Gemini model to use. Default: Model.PLUS_THINKING")
    parser.add_argument("--dpi", type=int, default=200,
                        help="DPI for rendering. Default: 200")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: <pdf_name>.txt)")
    parser.add_argument("--keep-images", action="store_true",
                        help="Keep rendered images after OCR")
    parser.add_argument("--delay", type=int, default=15,
                        help="Delay in seconds between pages (sequential mode). Default: 15")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last completed page")
    parser.add_argument("--prompt", type=str, default="prompt.txt",
                        help="Prompt text or path to prompt file. Default: prompt.txt")
    parser.add_argument("--workers", "-w", type=int, default=2,
                        help="Number of concurrent pages. Default: 2")
    parser.add_argument("--retries", "-r", type=int, default=1,
                        help="Retry attempts per page on failure. Default: 1")
    args = parser.parse_args()

    if args.retries < 1:
        parser.error("--retries must be >= 1")
    if args.workers < 1:
        parser.error("--workers must be >= 1")
    if args.dpi < 1:
        parser.error("--dpi must be > 0")
    if args.delay < 0:
        parser.error("--delay must be >= 0")

    prompt_path = Path(args.prompt)
    if prompt_path.is_file():
        args.prompt = prompt_path.read_text(encoding="utf-8")
    elif args.prompt == "prompt.txt":
        print("Error: default prompt file 'prompt.txt' not found.", file=sys.stderr)
        sys.exit(1)

    if not args.pdf.is_file():
        print(f"Error: {args.pdf} not found.", file=sys.stderr)
        sys.exit(1)

    pages = set()
    for part in args.pages.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))

    doc = None
    client = None
    try:
        doc = fitz.open(args.pdf)
        total = len(doc)
        pages = {p for p in pages if 1 <= p <= total}
        if not pages:
            print(f"Error: no valid pages (1-{total}).", file=sys.stderr)
            return

        out_path = args.output or args.pdf.with_suffix(".txt")
        parts_dir = out_path.parent / f".{out_path.stem}_parts"
        parts_dir.mkdir(parents=True, exist_ok=True)

        completed = set(_sorted_parts(parts_dir)) & pages
        to_process = sorted(pages - completed)

        if not to_process:
            rebuild_output(parts_dir, out_path, pages)
            print("All requested pages already done.", file=sys.stderr)
            return

        print(f"Processing {len(to_process)} page(s) ({len(completed)} already done)...",
              file=sys.stderr)

        client = GeminiClient(
            secure_1psid=os.environ.get("SECURE_1PSID"),
            secure_1psidts=os.environ.get("SECURE_1PSIDTS"),
            verbose=False,
            auto_refresh=False,
        )
        await client.init(timeout=180)

        tmp_dir = Path("/tmp/gemini_ocr")
        tmp_dir.mkdir(parents=True, exist_ok=True)

        if args.workers > 1:
            sem = asyncio.Semaphore(args.workers)
            lock = asyncio.Lock()
            done = 0
            total_todo = len(to_process)

            async def process_page(p: int) -> None:
                nonlocal done
                img_path = tmp_dir / f"page_{p}.png"

                async with sem:
                    page = doc[p - 1]
                    pix = page.get_pixmap(dpi=args.dpi)
                    pix.save(img_path)
                    text = await ocr_page_with_retry(
                        client, str(img_path), args.model, args.prompt,
                        args.retries, 5
                    )

                (parts_dir / f"page_{p}.txt").write_text(text, encoding="utf-8")

                async with lock:
                    done += 1
                    pct = done * 100 // total_todo
                    print(f"OCR page {p}/{total} [{done}/{total_todo} {pct}%] done",
                          file=sys.stderr)

                if not args.keep_images:
                    img_path.unlink(missing_ok=True)

            tasks = [process_page(p) for p in to_process]
            await asyncio.gather(*tasks)

        else:
            for i, p in enumerate(to_process):
                page = doc[p - 1]
                pix = page.get_pixmap(dpi=args.dpi)
                img_path = tmp_dir / f"page_{p}.png"
                pix.save(img_path)
                pct = (i + 1) * 100 // len(to_process)
                print(f"OCR page {p}/{total} [{i+1}/{len(to_process)} {pct}%]...",
                      file=sys.stderr)

                text = await ocr_page_with_retry(
                    client, str(img_path), args.model, args.prompt, args.retries, 5
                )

                (parts_dir / f"page_{p}.txt").write_text(text, encoding="utf-8")

                if not args.keep_images:
                    img_path.unlink(missing_ok=True)

                if i < len(to_process) - 1:
                    await asyncio.sleep(args.delay)

        rebuild_output(parts_dir, out_path, pages)

    finally:
        if doc is not None:
            doc.close()
        if client is not None:
            await client.close()

    print(f"Saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
