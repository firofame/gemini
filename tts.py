#!/usr/bin/env python3
"""Text-to-Speech converter using Google Docs and Playwright."""

import sys
import base64
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Page

# Configuration
CONFIG = {
    'doc_url': 'https://docs.google.com/document/d/1WVxgs-UywesdGppo1zLFR-YA57TQiwEpXDjKoq9EfyM/edit?usp=sharing',
    'max_chunk_length': 20_000,
    'insert_chunk_size': 4000,
    'timeout': 120_000,
}

SELECTORS = {
    'tts_button': '#textToSpeechToolbarButton',
    'editor': '.kix-appview-editor',
    'player_audio': '.kixAudioPlayerView [data-media-url][data-media-type="audio"]',
    'player_max_time': '.docsUiWizAudioSliderMaxTime',
    'player_close': '.kixAudioPlayerPaletteCloseButton[aria-label="Close"]',
}


def parse_args():
    """Parse command line arguments."""
    if len(sys.argv) < 2:
        print('Usage: python google_docs_tts.py input.txt [output.mp3]', file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1]).resolve()

    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2]).resolve()
    else:
        output_path = input_path.with_suffix('.mp3')

    return input_path, output_path


def split_text(text: str) -> list[str]:
    """Split text into chunks that fit within maxChunkLength."""
    chunks = []
    current = ''

    for line in text.split('\n'):
        # Break long lines at first comma
        while len(line) > 300 and ',' in line:
            idx = line.index(',')
            line = line[:idx] + '.' + line[idx + 1:]

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


async def click(page: Page, selector: str):
    """Click first matching element."""
    await page.locator(selector).first.click(timeout=CONFIG['timeout'])


async def wait_for_time_display(page: Page):
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


async def get_blob_url(page: Page, prev_url: str = '') -> str:
    """Get blob URL from audio player."""
    result = await page.wait_for_function(
        """() => {
            const url = document.querySelector('.kixAudioPlayerView [data-media-url][data-media-type="audio"]')?.getAttribute('data-media-url') || '';
            return url.startsWith('blob:') ? url : null;
        }""",
        timeout=CONFIG['timeout']
    )
    return await result.json_value()


async def save_blob(page: Page, blob_url: str, output_path: Path):
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


async def close_player(page: Page):
    """Close audio player if open."""
    try:
        await page.locator(SELECTORS['player_close']).first.click(timeout=3000)
        await asyncio.sleep(0.5)
    except Exception:
        pass  # Already closed


async def insert_text(page: Page, text: str):
    """Insert text into document editor."""
    await click(page, SELECTORS['editor'])
    await asyncio.sleep(0.5)

    # Determine modifier key based on platform
    mod = 'Meta' if sys.platform == 'darwin' else 'Control'

    # Clear existing content
    await page.keyboard.press(f'{mod}+A')
    await asyncio.sleep(0.2)
    await page.keyboard.press('Backspace')
    await asyncio.sleep(0.7)

    # Insert text in chunks
    normalized = text.replace('\r\n', '\n')
    chunk_size = CONFIG['insert_chunk_size']

    for i in range(0, len(normalized), chunk_size):
        await page.keyboard.insert_text(normalized[i:i + chunk_size])

    await asyncio.sleep(0.5)


async def generate_audio(page: Page, prev_blob_url: str) -> str:
    """Generate audio from document text."""
    # First trigger initializes, second generates
    for i in range(2):
        await click(page, SELECTORS['tts_button'])
        await page.wait_for_selector(SELECTORS['player_max_time'], timeout=CONFIG['timeout'])
        await wait_for_time_display(page)

        if i == 0:
            await close_player(page)

    return await get_blob_url(page, prev_blob_url)


async def process_chunk(page: Page, text: str, output_path: Path, prev_blob_url: str) -> str:
    """Process a single text chunk."""
    print(f'Inserting {len(text)} chars...')
    await insert_text(page, text)

    print('Generating audio...')
    blob_url = await generate_audio(page, prev_blob_url)

    print('Saving...')
    await save_blob(page, blob_url, output_path)
    print(f'✅ {output_path}')

    return blob_url


async def main():
    """Main entry point."""
    input_path, output_path = parse_args()

    text = input_path.read_text(encoding='utf-8')
    if not text.strip():
        raise ValueError('Empty input file')

    chunks = split_text(text)
    print(f'Processing {len(chunks)} chunk(s)...')

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            headless=False,
            firefox_user_prefs={'media.volume_scale': '0.0'}
        )

        try:
            context = await browser.new_context(storage_state='auth.json')
            page = await context.new_page()

            await page.goto(CONFIG['doc_url'], wait_until='domcontentloaded')
            await page.wait_for_selector(SELECTORS['editor'], timeout=CONFIG['timeout'])

            last_blob_url = ''

            for i, chunk in enumerate(chunks):
                print(f'\n--- Chunk {i + 1}/{len(chunks)} ---')

                if len(chunks) > 1:
                    out = suffix_path(output_path, f'-{i + 1}')
                else:
                    out = output_path

                last_blob_url = await process_chunk(page, chunk, out, last_blob_url)
                await close_player(page)

            print('\nDone!')

        finally:
            await browser.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as err:
        print(f'Error: {err}', file=sys.stderr)
        sys.exit(1)
