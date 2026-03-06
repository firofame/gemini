#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_MAX_CHARS = 20_000
DEFAULT_OUTPUT_DIR = "chapters"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split a text file into chapter files without breaking paragraphs."
        )
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="book.txt",
        help="Path to the source text file (default: book.txt)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for chapter files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "-m",
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
        help=f"Maximum characters per chapter (default: {DEFAULT_MAX_CHARS})",
    )
    return parser.parse_args()


def split_paragraphs(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return re.split(r"\n\s*\n+", text)


def build_chapters(paragraphs: list[str], max_chars: int) -> list[str]:
    chapters: list[str] = []
    current: list[str] = []
    current_len = 0

    for index, paragraph in enumerate(paragraphs, start=1):
        paragraph_len = len(paragraph)
        if paragraph_len > max_chars:
            raise ValueError(
                f"Paragraph {index} is {paragraph_len} characters, which exceeds the "
                f"chapter limit of {max_chars}."
            )

        separator_len = 2 if current else 0
        projected_len = current_len + separator_len + paragraph_len

        if current and projected_len > max_chars:
            chapters.append("\n\n".join(current))
            current = [paragraph]
            current_len = paragraph_len
        else:
            current.append(paragraph)
            current_len = projected_len

    if current:
        chapters.append("\n\n".join(current))

    return chapters


def write_chapters(chapters: list[str], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing in output_dir.glob("chapter_*.txt"):
        existing.unlink()

    for number, chapter in enumerate(chapters, start=1):
        path = output_dir / f"chapter_{number:03}.txt"
        path.write_text(chapter, encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_file)
    output_dir = Path(args.output_dir)

    if args.max_chars <= 0:
        raise SystemExit("--max-chars must be greater than 0")

    text = input_path.read_text(encoding="utf-8")
    paragraphs = split_paragraphs(text)
    chapters = build_chapters(paragraphs, args.max_chars)
    write_chapters(chapters, output_dir)

    print(f"Wrote {len(chapters)} chapters to {output_dir}")


if __name__ == "__main__":
    main()
