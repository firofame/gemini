#!/usr/bin/env python3
"""Text-to-Speech converter using Google Docs and Camoufox."""

import os
import sys
import base64
import asyncio
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from cloakbrowser import launch_persistent_context_async

# Configuration
CONFIG = {
    'doc_url': 'https://docs.google.com/document/d/1WVxgs-UywesdGppo1zLFR-YA57TQiwEpXDjKoq9EfyM/edit?usp=sharing',
    'max_chunk_length': 20_000,
    'insert_chunk_size': 4000,
    'timeout': 120_000,
    'retry_attempts': 3,
    'retry_delay_seconds': 5,
    'profile_dir': Path.home() / '.cloakbrowser-profile',
    'login_window_size': (1100, 700),
    'debug': True,
    'headless': False,
}

SELECTORS = {
    'tts_button': '#textToSpeechToolbarButton',
    'editor': '.kix-appview-editor',
    'player_audio': '.kixAudioPlayerView [data-media-url][data-media-type="audio"]',
    'player_max_time': '.docsUiWizAudioSliderMaxTime',
    'player_close': '.kixAudioPlayerPaletteCloseButton[aria-label="Close"]',
}


@dataclass
class Args:
    """Command line arguments."""
    input_path: Path | None
    output_path: Path | None
    login_only: bool = False


def parse_args() -> Args:
    """Parse command line arguments."""
    args = sys.argv[1:]

    if '--debug' in args:
        CONFIG['debug'] = True
        args.remove('--debug')

    if '--headless' in args:
        CONFIG['headless'] = True
        args.remove('--headless')

    if not args:
        print(
            'Usage: python tts.py [--debug] [--headless] --login | input.txt [output.mp3|output_dir]',
            file=sys.stderr,
        )
        sys.exit(1)

    if args[0] == '--login':
        return Args(input_path=None, output_path=None, login_only=True)

    input_path = Path(args[0]).resolve()

    if len(args) > 1:
        output_path = Path(args[1]).resolve()
    else:
        output_path = input_path.with_suffix('.mp3')

    return Args(input_path=input_path, output_path=output_path)



def split_text(text: str) -> list[str]:
    """Split text into chunks that fit within maxChunkLength."""
    chunks = []
    current = ''

    for line in text.split('\n'):

        if current and len(current) + len(line) + 1 > CONFIG['max_chunk_length']:
            chunks.append(current)
            current = ''
        current += ('\n' if current else '') + line

    if current:
        chunks.append(current)

    return chunks


def suffix_path(file_path: Path, suffix: str) -> Path:
    """Add suffix to filename before extension."""
    return file_path.with_name(f"{file_path.stem}{suffix}{file_path.suffix}")


def normalize_lines(text: str, num_lines: int = 1) -> str:
    """Normalize the first N lines of a chunk for Google Docs TTS.

    Google Docs TTS often fails to process the very first sentence.
    Fix: replace all breakable punctuation with periods on the first N lines,
    or append a period if a line has no punctuation at all.
    On retries, num_lines is increased to normalize deeper into the text.
    """
    punctuation_marks = ',;:?!،؛؟'
    lines = text.split('\n')
    limit = min(num_lines, len(lines))

    for i in range(limit):
        line = lines[i]
        has_punctuation = any(m in line for m in punctuation_marks)
        if has_punctuation:
            for mark in punctuation_marks:
                line = line.replace(mark, '.')
        elif not line.rstrip().endswith('.'):
            line = line.rstrip() + '.'
        lines[i] = line

    return '\n'.join(lines)



async def click(page: Any, selector: str):
    """Click first matching element."""
    await page.locator(selector).first.click(timeout=CONFIG['timeout'])


async def wait_for_time_display(page: Any):
    """Wait for time display to show valid format."""
    import re

    async def check_time():
        element = await page.query_selector(SELECTORS['player_max_time'])
        if element:
            text = (await element.text_content() or '').strip()
            return bool(re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', text))
        return False

    await page.wait_for_function(
        """() => /^\\d{1,2}:\\d{2}(:\\d{2})?$/.test(document.querySelector('.docsUiWizAudioSliderMaxTime')?.textContent?.trim() || '')""",
        timeout=CONFIG['timeout']
    )


async def get_blob_url(page: Any, prev_url: str = '') -> str:
    """Get blob URL from audio player."""
    result = await page.wait_for_function(
        """() => {
            const url = document.querySelector('.kixAudioPlayerView [data-media-url][data-media-type="audio"]')?.getAttribute('data-media-url') || '';
            return url.startsWith('blob:') ? url : null;
        }""",
        timeout=CONFIG['timeout']
    )
    return await result.json_value()


async def save_blob(page: Any, blob_url: str, output_path: Path):
    """Download blob and save to file."""
    base64_data = await page.evaluate("""async (url) => {
        const res = await fetch(url);
        const blob = await res.blob();
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.readAsDataURL(blob);
        });
    }""", blob_url)

    output_path.write_bytes(base64.b64decode(base64_data))


async def close_player(page: Any):
    """Close audio player if open."""
    try:
        await page.locator(SELECTORS['player_close']).first.click(timeout=3000)
        await asyncio.sleep(0.5)
    except Exception:
        pass  # Already closed


async def clear_editor(page: Any):
    """Clear editor content with retry and verification.

    Ctrl+A intermittently fails in Google Docs, leaving old text behind.
    We retry up to 5 times, checking the page count to verify the clear worked.
    """
    mod = 'Meta' if sys.platform == 'darwin' else 'Control'

    for attempt in range(5):
        # Focus the editor and scroll to top first
        await click(page, SELECTORS['editor'])
        await asyncio.sleep(1)
        await page.keyboard.press(f'{mod}+Home')
        await asyncio.sleep(0.5)

        # Select all and delete - double execution to ensure full clearance
        await page.keyboard.press(f'{mod}+A')
        await asyncio.sleep(0.5)
        await page.keyboard.press(f'{mod}+A')  # Double select to catch everything
        await asyncio.sleep(0.5)
        await page.keyboard.press('Backspace')
        await asyncio.sleep(0.5)
        
        # Second pass just in case
        await page.keyboard.press(f'{mod}+A')
        await asyncio.sleep(0.5)
        await page.keyboard.press('Backspace')
        await asyncio.sleep(1.5)

        # Verify: check if page count is 1 (cleared doc is always 1 page)
        page_count = await page.evaluate(r"""() => {
            const el = document.querySelector('.kix-page-paginator');
            if (!el) return 1;
            const m = (el.textContent || '').match(/(\d+)\s*of\s*(\d+)/i);
            return m ? parseInt(m[2]) : 1;
        }""")

        if page_count <= 1:
            return
        print(f'  Clear attempt {attempt + 1}: still {page_count} pages, retrying...')


async def insert_text(page: Any, text: str):
    """Insert text into document editor."""
    await click(page, SELECTORS['editor'])
    await asyncio.sleep(0.5)
    await clear_editor(page)

    # Insert text in chunks
    normalized = text.replace('\r\n', '\n')
    chunk_size = CONFIG['insert_chunk_size']

    for i in range(0, len(normalized), chunk_size):
        await page.keyboard.insert_text(normalized[i:i + chunk_size])

    # Scroll back to top after inserting
    mod = 'Meta' if sys.platform == 'darwin' else 'Control'
    await page.keyboard.press(f'{mod}+Home')
    await asyncio.sleep(0.5)


async def generate_audio(page: Any, prev_blob_url: str) -> str:
    """Generate audio from document text."""
    # First trigger initializes, second generates
    for i in range(2):
        await click(page, SELECTORS['tts_button'])
        await page.wait_for_selector(SELECTORS['player_max_time'], timeout=CONFIG['timeout'])
        await wait_for_time_display(page)

        if i == 0:
            await close_player(page)

    return await get_blob_url(page, prev_blob_url)


async def process_chunk(page: Any, text: str, output_path: Path, prev_blob_url: str) -> str:
    """Process a single text chunk with retry on failure."""
    attempts = CONFIG['retry_attempts']
    debug_dir = output_path.parent / 'debug'

    async def debug_screenshot(name: str):
        if not CONFIG['debug']:
            return
        debug_dir.mkdir(exist_ok=True)
        path = debug_dir / f'{output_path.stem}_{name}.png'
        await page.screenshot(path=str(path))
        print(f'  📸 {path}')

    for attempt in range(1, attempts + 1):
        try:
            # Normalize more lines on each attempt (1st line, then 2, then 3...)
            normalized = normalize_lines(text, num_lines=attempt)

            print(f'Inserting {len(normalized)} chars...')
            await insert_text(page, normalized)
            await debug_screenshot(f'after_insert_attempt{attempt}')

            print('Generating audio...')
            blob_url = await generate_audio(page, prev_blob_url)
            await debug_screenshot(f'after_audio_attempt{attempt}')

            print('Saving...')
            await save_blob(page, blob_url, output_path)
            print(f'\u2705 {output_path}')

            return blob_url
        except Exception as err:
            await debug_screenshot(f'error_attempt{attempt}')
            await close_player(page)
            if attempt < attempts:
                delay = CONFIG['retry_delay_seconds'] * attempt
                print(f'\u26a0\ufe0f  Chunk failed (attempt {attempt}/{attempts}): {err}')
                print(f'   Normalizing {attempt + 1} lines and retrying in {delay}s...')
                await asyncio.sleep(delay)
            else:
                print(f'\u274c Chunk failed after {attempts} attempts: {err}')
                raise


async def open_tts_page(context):
    """Open a page in the persistent CloakBrowser profile."""
    # Use the default persistent page if it exists, otherwise create a new one
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(CONFIG['doc_url'], wait_until='domcontentloaded')
    await page.wait_for_selector(SELECTORS['editor'], timeout=CONFIG['timeout'])
    return page


async def login_flow(context):
    """Open the document in a visible browser and let the user sign in."""
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto(CONFIG['doc_url'], wait_until='domcontentloaded')
    print(f'Browser profile: {CONFIG["profile_dir"]}')
    print('Log in to Google in the opened browser, then press Enter here to continue.')
    await asyncio.to_thread(input)
    await page.close()



async def main():
    """Main entry point."""
    args = parse_args()

    CONFIG['profile_dir'].mkdir(parents=True, exist_ok=True)

    # Force visible browser for login flow
    is_headless = CONFIG['headless'] if not args.login_only else False

    # Initialize CloakBrowser context
    context = await launch_persistent_context_async(
        user_data_dir=str(CONFIG['profile_dir']),
        headless=is_headless,
        viewport={'width': CONFIG['login_window_size'][0], 'height': CONFIG['login_window_size'][1]},
        args=['--mute-audio']  # Replaces Firefox volume prefs to keep generation silent
    )

    try:
        if args.login_only:
            await login_flow(context)
            print('Login session saved.')
            return

        assert args.input_path is not None
        assert args.output_path is not None

        text = args.input_path.read_text(encoding='utf-8')
        chunks = split_text(text)
        print(f'Processing {len(chunks)} chunk(s)...')

        page = await open_tts_page(context)
        last_blob_url = ''

        try:
            for i, chunk in enumerate(chunks):
                print(f'\n--- Chunk {i + 1}/{len(chunks)} ---')

                if len(chunks) > 1:
                    out = suffix_path(args.output_path, f'-{i + 1}')
                else:
                    out = args.output_path

                # Resume support: skip chunks already on disk
                if out.exists() and out.stat().st_size > 0:
                    print(f'⏭️  {out} already exists, skipping.')
                    continue

                last_blob_url = await process_chunk(page, chunk, out, last_blob_url)
                await close_player(page)

            # Concatenate multiple audio chunks into a single file
            if len(chunks) > 1:
                print('\nConcatenating audio chunks...')
                list_file = args.output_path.parent / 'ffmpeg_concat_list.txt'
                try:
                    with open(list_file, 'w') as f:
                        for i in range(len(chunks)):
                            chunk_path = suffix_path(args.output_path, f'-{i + 1}')
                            f.write(f"file '{chunk_path}'\n")

                    ret = os.system(
                        f"ffmpeg -y -f concat -safe 0 -i '{list_file}' -c copy '{args.output_path}'"
                    )
                    if ret == 0:
                        print(f'✅ Final audiobook saved as {args.output_path}')
                        # Clean up individual chunk files
                        for i in range(len(chunks)):
                            chunk_path = suffix_path(args.output_path, f'-{i + 1}')
                            if chunk_path.exists():
                                chunk_path.unlink()
                        print(f'Cleaned up {len(chunks)} chunk files.')
                    else:
                        print(f'⚠️  ffmpeg concatenation failed (exit code {ret}).')
                        print(f'Individual chunks are preserved as {args.output_path.stem}-N{args.output_path.suffix}')
                finally:
                    if list_file.exists():
                        list_file.unlink()

            print('\nDone!')
        finally:
            await page.close()
    finally:
        await context.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        print(f'Error: {err}', file=sys.stderr)
        sys.exit(1)
