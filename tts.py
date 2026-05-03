#!/usr/bin/env python3
"""Text-to-Speech converter using Google Docs and Camoufox."""

import sys
import base64
import asyncio
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from camoufox.async_api import AsyncCamoufox

# Configuration
CONFIG = {
    'doc_url': 'https://docs.google.com/document/d/1WVxgs-UywesdGppo1zLFR-YA57TQiwEpXDjKoq9EfyM/edit?usp=sharing',
    'max_chunk_length': 20_000,
    'insert_chunk_size': 4000,
    'timeout': 120_000,
    'retry_attempts': 3,
    'retry_delay_seconds': 5,
    'profile_dir': Path(__file__).resolve().parent / '.camoufox-profile',
    'login_window_size': (1100, 700),
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

    if not args:
        print(
            'Usage: python tts.py --login | input.txt [output.mp3|output_dir]',
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
        line = normalize_long_lead_sentence(line)

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


def normalize_long_lead_sentence(text: str) -> str:
    """Break very long leading clauses to avoid Google Docs TTS issues."""
    punctuation_marks = ',;:?!،؛؟'

    while len(text) > 300:
        positions = [text.index(mark) for mark in punctuation_marks if mark in text]
        if not positions:
            break

        idx = min(positions)
        text = text[:idx] + '.' + text[idx + 1:]
    return text



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
    """Clear the editor and verify the previous content is gone."""
    mod = 'Meta' if sys.platform == 'darwin' else 'Control'

    for attempt in range(3):
        await click(page, SELECTORS['editor'])
        await asyncio.sleep(0.7)
        await page.keyboard.press(f'{mod}+A')
        await asyncio.sleep(0.5)
        await page.keyboard.press('Backspace')
        await asyncio.sleep(1.2)

        is_empty = await page.evaluate("""() => {
            const editor = document.querySelector('.kix-appview-editor');
            if (!editor) return false;

            const text = (editor.innerText || editor.textContent || '')
                .replace(/[\\u200b\\u200c\\u200d\\ufeff\\u00a0]/g, '')
                .replace(/\\s+/g, '');
            return text.length === 0;
        }""")
        if is_empty:
            return True

        print(f'Editor not empty after clear attempt {attempt + 1}, retrying...')

    # Leave the document selected so the first inserted chunk replaces any
    # leftover whitespace or stale content that Docs still reports internally.
    await click(page, SELECTORS['editor'])
    await asyncio.sleep(0.7)
    await page.keyboard.press(f'{mod}+A')
    await asyncio.sleep(0.5)
    print('Proceeding with select-all replacement despite non-empty editor check...')
    return False


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
    """Process a single text chunk."""
    print(f'Inserting {len(text)} chars...')
    await insert_text(page, text)

    print('Generating audio...')
    blob_url = await generate_audio(page, prev_blob_url)

    print('Saving...')
    await save_blob(page, blob_url, output_path)
    print(f'✅ {output_path}')

    return blob_url


async def open_tts_page(context):
    """Open a page in the persistent Camoufox profile."""
    page = await context.new_page()
    await page.goto(CONFIG['doc_url'], wait_until='domcontentloaded')
    await page.wait_for_selector(SELECTORS['editor'], timeout=CONFIG['timeout'])
    return page


async def login_flow(context):
    """Open the document in a visible browser and let the user sign in."""
    page = await context.new_page()
    await page.goto(CONFIG['doc_url'], wait_until='domcontentloaded')
    print(f'Browser profile: {CONFIG["profile_dir"]}')
    print('Log in to Google in the opened browser, then press Enter here to continue.')
    await asyncio.to_thread(input)
    await page.close()



async def main():
    """Main entry point."""
    args = parse_args()

    CONFIG['profile_dir'].mkdir(parents=True, exist_ok=True)

    async with AsyncCamoufox(
        headless=False,
        persistent_context=True,
        user_data_dir=str(CONFIG['profile_dir']),
        window=CONFIG['login_window_size'],
        firefox_user_prefs={'media.volume_scale': '0.0'}
    ) as context:
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

                last_blob_url = await process_chunk(page, chunk, out, last_blob_url)
                await close_player(page)

            print('\nDone!')
        finally:
            await page.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        print(f'Error: {err}', file=sys.stderr)
        sys.exit(1)
