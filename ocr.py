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
    parser.add_argument("--model", "-m", type=str, default="gemini-3-pro",
                        help="Gemini model to use. Default: gemini-3-pro")
    parser.add_argument("--dpi", type=int, default=200,
                        help="DPI for rendering. Default: 200")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: <pdf_name>.txt)")
    parser.add_argument("--keep-images", action="store_true",
                        help="Keep rendered images after OCR")
    parser.add_argument("--prompt", type=str,
                        default="Extract all text from this image in Malayalam. Return only the extracted text without any preamble or explanation.")
    args = parser.parse_args()

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

    client = GeminiClient(
        secure_1psid=os.environ.get("SECURE_1PSID"),
        secure_1psidts=os.environ.get("SECURE_1PSIDTS"),
        verbose=False,
    )
    await client.init(timeout=180)

    results = {}
    tmp_dir = Path("/tmp/gemini_ocr")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        for p in sorted(pages):
            page = doc[p - 1]
            pix = page.get_pixmap(dpi=args.dpi)
            img_path = tmp_dir / f"page_{p}.png"
            pix.save(img_path)
            print(f"OCR page {p}/{total}...", file=sys.stderr)

            text = await ocr_page(client, str(img_path), args.model, args.prompt)
            results[p] = text

            if not args.keep_images:
                img_path.unlink(missing_ok=True)
    finally:
        doc.close()
        await client.close()

    output = "\n".join(results[p] for p in sorted(results))

    out_path = args.output or args.pdf.with_suffix(".txt")
    out_path.write_text(output, encoding="utf-8")
    print(f"Saved to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
