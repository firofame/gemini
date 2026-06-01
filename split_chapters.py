#!/usr/bin/env python3
"""Split a translated/OCR'd text file into individual chapter files.

Usage examples:
  # Split Malayalam translation by chapter transitions (default pattern)
  python split_chapters.py Volume_2_Malayalam_Clean.txt -o Malayalam_Chapters

  # Split Arabic OCR by باب headers
  python split_chapters.py Volume_1_OCR_Clean.txt --pattern '^#{1,3}\\s*الْبَابُ'

  # Preview what would be split without writing files
  python split_chapters.py input.txt --dry-run
"""

import argparse
import os
import re
import sys


def clean_text(text):
    """Strip leftover markers from the translation/OCR pipeline."""
    # Page markers: ## Page 1, ## Page 2, etc.
    text = re.sub(r'^#*\s*Page\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    # Part markers: ## Part 1, ## Part 2, etc.
    text = re.sub(r'^#*\s*Part\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    # Horizontal rules
    text = re.sub(r'^---\s*$', '', text, flags=re.MULTILINE)
    # HTML comments (SKIPPED pages, etc.)
    text = re.sub(r'^\s*<!--.*?-->\s*$', '', text, flags=re.MULTILINE)
    # Collapse excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _sanitize_filename(name):
    """Remove characters that are unsafe in filenames."""
    # Keep letters (any script), digits, spaces, hyphens, underscores
    name = re.sub(r'[^\w\s\-]', '', name, flags=re.UNICODE)
    # Collapse whitespace to single underscore
    name = re.sub(r'\s+', '_', name.strip())
    return name or "Untitled"


def _extract_title(section, index, has_intro):
    """Extract chapter title from === CHAPTER: ... === marker, or default."""
    if index == 0 and has_intro:
        return "ആമുഖം"
    match = re.search(r'^=== CHAPTER:\s*(.+?)\s*===', section, re.MULTILINE)
    if match:
        return _sanitize_filename(match.group(1))
    return f"Chapter_{index:02d}"


def split_chapters(input_file, output_dir, pattern, dry_run=False, no_clean=False):
    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found.")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    if not no_clean:
        text = clean_text(text)

    # Split on the pattern using lookahead so the delimiter stays with the section
    sections = re.split(f'(?={pattern})', text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    if len(sections) == 0:
        print("No sections found. Check your --pattern.")
        sys.exit(1)

    # If the first section doesn't match the pattern, treat it as intro/preamble
    has_intro = not re.match(pattern, sections[0], re.MULTILINE)

    print(f"Input:    {input_file}")
    print(f"Pattern:  {pattern}")
    print(f"Sections: {len(sections)} ({'1 intro + ' + str(len(sections) - 1) + ' chapters' if has_intro else str(len(sections)) + ' chapters'})")
    print()

    if dry_run:
        for i, section in enumerate(sections):
            title = _extract_title(section, i, has_intro)
            label = f"{i:02d}_{title}"
            first_line = section.split('\n', 1)[0][:80]
            print(f"  [{label}] {len(section):,} chars — {first_line}")
        print(f"\nDry run complete. Use without --dry-run to write files.")
        return

    os.makedirs(output_dir, exist_ok=True)

    for i, section in enumerate(sections):
        title = _extract_title(section, i, has_intro)
        fname = f"{i:02d}_{title}.txt"

        # Strip the chapter marker line itself — it was only needed for splitting
        section_clean = re.sub(r'^=== CHAPTER:.*===\s*\n?', '', section, flags=re.MULTILINE).strip()

        path = os.path.join(output_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(section_clean + "\n")

        print(f"  Created {fname} ({len(section_clean.splitlines()):,} lines)")

    print(f"\nDone. {len(sections)} files written to {output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split a text file into chapter files by a regex pattern.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "input", help="Input text file to split"
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="Output directory for chapter files (default: <input_dir>/Chapters)"
    )
    parser.add_argument(
        "-p", "--pattern",
        default=r'^=== CHAPTER:.*===\s*$',
        help="Regex pattern to split on (default: === CHAPTER: ... === markers)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview sections without writing files"
    )
    parser.add_argument(
        "--no-clean", action="store_true",
        help="Skip stripping Page/Part markers before splitting"
    )
    args = parser.parse_args()

    output_dir = args.output_dir or os.path.join(os.path.dirname(args.input) or ".", "Chapters")

    split_chapters(
        input_file=args.input,
        output_dir=output_dir,
        pattern=args.pattern,
        dry_run=args.dry_run,
        no_clean=args.no_clean,
    )