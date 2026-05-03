from camoufox.async_api import AsyncCamoufox
import asyncio
from pathlib import Path

async def main():
    # Configuration from tts.py for consistency
    profile_dir = Path(__file__).resolve().parent / '.camoufox-profile'
    window_size = (1100, 700)
    
    url = "https://www.amazon.in/Panasonic-DustBuster-Convertible-CS-CU-SU18BKY3W/dp/B0GHQVNMKQ"
    
    async with AsyncCamoufox(
        headless=False,
        persistent_context=True,
        user_data_dir=str(profile_dir),
        window=window_size,
        firefox_user_prefs={'media.volume_scale': '0.0'}
    ) as context:
        page = await context.new_page()
        print(f"Opening {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        
        # Wait for and click the product image to open gallery
        image_selector = "#landingImage"
        print(f"Waiting for product image ({image_selector})...")
        gallery_opened = False
        try:
            await page.wait_for_selector(image_selector, timeout=20000)
            print("Clicking product image to open gallery...")
            await page.click(image_selector)
            gallery_opened = True
        except Exception as e:
            print(f"Could not click image: {e}")
            try:
                print("Trying fallback image selector...")
                await page.click("#imgTagWrapperId img")
                gallery_opened = True
            except Exception:
                print("Fallback also failed.")

        if gallery_opened:
            print("Gallery opened. Starting download...")
            output_dir = Path(__file__).resolve().parent / 'images'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Robust wait for gallery: try multiple common Amazon gallery selectors
                gallery_selectors = ["#ivContainer", ".a-popover-content", "#unified-gallery", "#imageBlock"]
                found_selector = None
                for selector in gallery_selectors:
                    try:
                        print(f"Checking for gallery selector: {selector}...")
                        await page.wait_for_selector(selector, timeout=5000)
                        found_selector = selector
                        print(f"Found gallery via: {found_selector}")
                        break
                    except Exception:
                        continue
                
                if not found_selector:
                    print("Could not find a recognized gallery container. Trying to proceed with general search...")

                # Robust thumbnail search: Wait for thumbnails to actually load
                thumb_selectors = [
                    "#ivThumbs .ivThumb", 
                    ".ivThumbs .ivThumb",
                    "#ivThumbs .ivRow .ivThumb",
                    ".ivThumb", 
                    "#altImages .a-button-thumbnail", 
                ]
                
                thumb_selector = None
                thumb_count = 0
                print("Waiting for thumbnails to load...")
                # Give the gallery a moment to stabilize
                await asyncio.sleep(2)
                
                for t_selector in thumb_selectors:
                    try:
                        # Wait for at least one thumbnail to appear
                        await page.wait_for_selector(t_selector, timeout=3000)
                        elements = await page.query_selector_all(t_selector)
                        # Filter out placeholders
                        valid_elements = []
                        for el in elements:
                            is_placeholder = await el.evaluate("el => el.classList.contains('placeholder')")
                            if not is_placeholder:
                                valid_elements.append(el)
                                
                        if valid_elements:
                            thumb_selector = t_selector
                            thumb_count = len(valid_elements)
                            print(f"Found {thumb_count} valid thumbnails using selector: {thumb_selector}")
                            break
                    except Exception:
                        continue
                
                if not thumb_selector:
                    print("No thumbnails found. Attempting to extract images directly from the page...")
                    thumb_selector = f"{found_selector or 'body'} img"
                
                print(f"Processing up to 10 images...")
                downloaded_urls = set()
                download_count = 0
                
                # Use locator for the entire loop for consistency
                loc = page.locator(thumb_selector)
                total_found = await loc.count()
                
                for i in range(min(20, total_found)):
                    if download_count >= 10:
                        break
                        
                    try:
                        thumb_locator = loc.nth(i)
                        
                        # Skip placeholders
                        is_placeholder = await thumb_locator.evaluate("el => el.classList.contains('placeholder')")
                        if is_placeholder:
                            continue

                        # Attempt to make it visible and click
                        try:
                            await thumb_locator.scroll_into_view_if_needed(timeout=1000)
                            await thumb_locator.click(timeout=2000, force=True)
                            await asyncio.sleep(1.5) # Increased wait for gallery update
                        except Exception:
                            try:
                                await thumb_locator.hover(timeout=1000, force=True)
                                await asyncio.sleep(1)
                            except Exception:
                                pass
                        
                        # Robust high-res image detection
                        img_selectors = ["#ivLargeImage img", ".a-stretch-vertical", ".a-dynamic-image", "#main-image"]
                        img_url = None
                        for img_sel in img_selectors:
                            try:
                                el = page.locator(img_sel).first
                                if await el.is_visible(timeout=800):
                                    img_url = await el.get_attribute("src")
                                    if img_url and "base64" not in img_url and "sprite" not in img_url:
                                        break
                            except Exception:
                                continue
                        
                        if img_url:
                            import re
                            original_url = re.sub(r'\._AC_.*_\.', '.', img_url)
                            if original_url != img_url:
                                img_url = original_url

                            if img_url in downloaded_urls:
                                continue
                            
                            downloaded_urls.add(img_url)
                            download_count += 1
                            
                            print(f"[{download_count}] Downloading: {img_url}")
                            img_response = await page.request.get(img_url)
                            if img_response.status == 200:
                                img_data = await img_response.body()
                                
                                ext = "jpg"
                                if ".png" in img_url.lower(): ext = "png"
                                elif ".webp" in img_url.lower(): ext = "webp"
                                
                                file_path = output_dir / f"product_image_{download_count}.{ext}"
                                file_path.write_bytes(img_data)
                                print(f"    ✅ Saved to {file_path.name}")
                            else:
                                print(f"    ❌ Failed (Status {img_response.status})")
                    except Exception as item_err:
                        print(f"    ❌ Error on item {i+1}: {item_err}")
            except Exception as gallery_err:
                print(f"Error accessing gallery: {gallery_err}")

        print("\nProcess complete. Browser is open for inspection.")
        print("Press Ctrl+C to exit.")
        
        try:
            while True:
                await asyncio.sleep(1)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClosing browser...")
