import asyncio
from pathlib import Path
from camoufox.async_api import AsyncCamoufox
from urllib.parse import urljoin

async def main():
    search_url = "https://www.amazon.in/s?i=merchant-items&me=A3K8GDUW67973J&rh=n%3A976442031%2Cn%3A2083423031%2Cn%3A3474656031%2Cn%3A10545602031&dc&ds=v1%3AnQXDNPDe0%2FgUBzxapdHk1JGHevzaiyhv%2BufeCpklQN4&qid=1777639979&rnid=3474656031&ref=sr_nr_n_1"
    
    profile_dir = Path(__file__).resolve().parent / '.camoufox-profile'
    window_size = (1100, 700)
    
    import json
    products = []
    page_count = 1
    
    async with AsyncCamoufox(
        headless=False,
        persistent_context=True,
        user_data_dir=str(profile_dir),
        window=window_size,
    ) as context:
        page = await context.new_page()
        print(f"Opening search page...")
        await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        
        while True:
            print(f"\n--- Scraping Page {page_count} ---")
            try:
                await page.wait_for_selector("[data-component-type='s-search-result']", timeout=15000)
            except Exception:
                print("No results found or timeout.")
                break
                
            results = await page.query_selector_all("[data-component-type='s-search-result']")
            print(f"Extracting data from {len(results)} items...")
            
            for result in results:
                try:
                    # Basic metadata extraction
                    asin = await result.get_attribute("data-asin")
                    
                    # More robust title and URL extraction
                    title_el = await result.query_selector("h2 span, h2")
                    title = await title_el.inner_text() if title_el else "N/A"
                    
                    link_el = await result.query_selector("h2 a, .a-link-normal.s-no-outline")
                    href = await link_el.get_attribute("href") if link_el else None
                    url = urljoin("https://www.amazon.in", href.split("?")[0]) if href else "N/A"
                    
                    price_el = await result.query_selector(".a-price-whole")
                    price = await price_el.inner_text() if price_el else "N/A"
                    
                    rating_el = await result.query_selector("[data-cy='reviews-block'] span")
                    if rating_el:
                        rating = await rating_el.inner_text()
                    else:
                        rating = "N/A"
                    if rating and "out of" in rating: rating = rating.split(" ")[0]
                    
                    reviews_el = await result.query_selector("span.s-underline-text, .a-size-base.s-underline-text")
                    reviews = await reviews_el.inner_text() if reviews_el else "0"
                    
                    # Clean up reviews (e.g. "(2)" -> "2")
                    import re
                    reviews = re.sub(r'[^0-9]', '', reviews) if reviews else "0"
                    if not reviews: reviews = "0"
                    
                    if asin and price != "N/A":
                        products.append({
                            "asin": asin,
                            "title": title.strip(),
                            "price": price.replace(",", "").strip(),
                            "rating": rating,
                            "reviews": reviews.strip("() "),
                            "url": url
                        })
                    else:
                        reason = "ASIN missing" if not asin else "Price missing"
                        print(f"Skipping item: {reason} for '{title[:30]}...'")
                except Exception as e:
                    print(f"Error processing item: {e}")
                    continue
            
            next_button = await page.query_selector(".s-pagination-next:not(.s-pagination-disabled)")
            if next_button:
                print("Navigating to next page...")
                await next_button.click()
                page_count += 1
                await asyncio.sleep(3)
            else:
                print("Last page reached.")
                break
        
        # Deduplicate by ASIN
        unique_products = {p['asin']: p for p in products}.values()
        print(f"\nTotal: Found {len(unique_products)} unique ACs.")
        
        # Save to JSON
        with open("ac_list.json", "w") as f:
            json.dump(list(unique_products), f, indent=4)
        
        print("✅ Saved to ac_list.json")

if __name__ == "__main__":
    asyncio.run(main())
