import os
import sys
import asyncio
import argparse
from pathlib import Path
import fitz
from gemini_webapi import GeminiClient


async def ocr_page(client: GeminiClient, image_path: str, model: str, prompt: str) -> str:
    response = await client.generate_content(prompt, files=[image_path], model=model)
    return response.text


async def main():
    parser = argparse.ArgumentParser(description="OCR PDF pages using Gemini")
    parser.add_argument("pdf", type=Path, help="Path to the PDF file")
    parser.add_argument("--pages", "-p", type=str, default="1",
                        help="Pages to OCR (e.g. 1, 1-5, 1,3,5). Default: 1")
    parser.add_argument("--model", "-m", type=str, default="gemini-3-flash",
                        help="Gemini model to use. Default: gemini-3-flash")
    parser.add_argument("--dpi", type=int, default=200,
                        help="DPI for rendering. Default: 200")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: <pdf_name>.txt)")
    parser.add_argument("--keep-images", action="store_true",
                        help="Keep rendered images after OCR")
    parser.add_argument("--delay", type=int, default=15,
                        help="Delay in seconds between pages. Default: 15")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last completed page")
    parser.add_argument("--prompt", type=str, default="prompt.txt",
                        help="Prompt text or path to prompt file. Default: prompt.txt")
    args = parser.parse_args()

    prompt_path = Path(args.prompt)
    if prompt_path.is_file():
        args.prompt = prompt_path.read_text(encoding="utf-8")

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

    doc = fitz.open(args.pdf)
    total = len(doc)
    pages = {p for p in pages if 1 <= p <= total}
    if not pages:
        print(f"Error: no valid pages (1-{total}).", file=sys.stderr)
        doc.close()
        sys.exit(1)

    out_path = args.output or args.pdf.with_suffix(".txt")
    state_path = out_path.with_suffix(".state")

    completed = set()
    if args.resume:
        if state_path.is_file():
            with state_path.open() as f:
                completed = {int(line.strip()) for line in f if line.strip().isdigit()}
        elif out_path.is_file():
            print(f"Resuming: appending to existing {out_path}", file=sys.stderr)

    to_process = sorted(pages - completed)
    if not to_process:
        print(f"All requested pages already done.", file=sys.stderr)
        doc.close()
        return

    print(f"Processing {len(to_process)} page(s) ({len(completed)} already done)...", file=sys.stderr)

    client = GeminiClient(
        secure_1psid=os.environ.get("SECURE_1PSID"),
        secure_1psidts=os.environ.get("SECURE_1PSIDTS"),
        verbose=False,
        auto_refresh=False,
    )
    await client.init(timeout=180)

    tmp_dir = Path("/tmp/gemini_ocr")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        for i, p in enumerate(to_process):
            page = doc[p - 1]
            pix = page.get_pixmap(dpi=args.dpi)
            img_path = tmp_dir / f"page_{p}.png"
            pix.save(img_path)
            print(f"OCR page {p}/{total}...", file=sys.stderr)

            text = await ocr_page(client, str(img_path), args.model, args.prompt)

            with out_path.open("a" if (completed or i > 0) else "w", encoding="utf-8") as f:
                f.write(text + "\n")

            with state_path.open("a") as f:
                f.write(f"{p}\n")

            if not args.keep_images:
                img_path.unlink(missing_ok=True)

            if i < len(to_process) - 1:
                await asyncio.sleep(args.delay)
    finally:
        doc.close()
        await client.close()

    print(f"Saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
