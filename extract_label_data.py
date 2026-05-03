import os
import sys
from pathlib import Path
from google import genai
from google.genai import types
import time

def main():
    client = genai.Client()
    model_id = "gemma-4-31b-it" 
    
    image_dir = Path("images")
    if not image_dir.exists():
        print("Error: images/ directory not found.", file=sys.stderr)
        return

    image_files = sorted(list(image_dir.glob("product_image_*.*")))
    if not image_files:
        print("No images found in images/ directory.", file=sys.stderr)
        return

    output_json = "--json" in sys.argv
    num_images = len(image_files)

    if output_json:
        print(f"🔍 Extractor: Analyzing {num_images} images...", file=sys.stderr, flush=True)
    else:
        print(f"📦 Found {num_images} images to analyze.\n")
    
    prompt = """
    This image contains an Indian BEE 'POWER SAVINGS GUIDE' sticker.
    Please extract the technical specifications from the label.
    
    Return ONLY a valid JSON object with these exact keys:
    1. "star_rating" (e.g., "3 Star")
    2. "iseer" (e.g., "4.75")
    3. "cooling_capacity" (e.g., "5000")
    4. "consumption" (e.g., "850.5")
    5. "model_year" (e.g., "2025")

    If you cannot find a label, respond with {"error": "NO_LABEL_VISIBLE"}.
    """

    for i, img_path in enumerate(image_files, 1):
        try:
            # Print progress to stderr so it shows up in bulk mode
            print(f"   [{i}/{num_images}] Analyzing {img_path.name}...", file=sys.stderr, flush=True)
            
            if not output_json: print(f"--- Analyzing {img_path.name} ---")
            
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            mime_type = "image/jpeg"
            if img_path.suffix.lower() == ".png": mime_type = "image/png"
            elif img_path.suffix.lower() == ".webp": mime_type = "image/webp"

            response = client.models.generate_content(
                model=model_id,
                contents=[prompt, types.Part.from_bytes(data=img_data, mime_type=mime_type)],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            result_text = response.text.strip()
            try:
                result_data = json.loads(result_text)
                if "error" not in result_data:
                    if output_json:
                        print(json.dumps(result_data))
                        return
                    else:
                        print(json.dumps(result_data, indent=2))
                        print("-" * 30)
                        break
                elif not output_json:
                    print("No label detected in this image.")
            except:
                if not output_json: print(result_text)
            
            time.sleep(1) # Cooldown
            
        except Exception as e:
            if not output_json: print(f"Error analyzing {img_path.name}: {e}")

    # If we reached here, no valid label was found across any images
    if output_json:
        print(json.dumps({"error": "NO_LABEL_FOUND_IN_ANY_IMAGE"}))

if __name__ == "__main__":
    import json
    main()
