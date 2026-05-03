import os
from pathlib import Path
from google import genai
from google.genai import types
import time

def main():
    client = genai.Client()
    model_id = "gemini-3.1-flash-lite-preview" 
    
    image_dir = Path("images")
    if not image_dir.exists():
        print("Error: images/ directory not found.")
        return

    # Filter for images where check_labels.py might have found something
    image_files = sorted(list(image_dir.glob("product_image_*.*")))
    if not image_files:
        print("No images found.")
        return

    print("Extracting BEE Label data from images...\n")

    prompt = """
    This image contains an Indian BEE 'POWER SAVINGS GUIDE' sticker.
    Please extract the following technical specifications from the label:
    1. Star Rating (e.g., 3 Star, 5 Star)
    2. ISEER (e.g., 4.75)
    3. Cooling Capacity (100%) (e.g., 5000 W)
    4. Electricity Consumption (kWh/year) (e.g., 850.5)
    5. Model Name/Year (if visible)

    Respond in a clean format. If you cannot find a label in a specific image, respond with 'NO_LABEL_VISIBLE'.
    """

    for img_path in image_files:
        try:
            print(f"--- Analyzing {img_path.name} ---")
            
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            mime_type = "image/jpeg"
            if img_path.suffix.lower() == ".png": mime_type = "image/png"
            elif img_path.suffix.lower() == ".webp": mime_type = "image/webp"

            response = client.models.generate_content(
                model=model_id,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=img_data, mime_type=mime_type)
                ]
            )
            
            result = response.text.strip()
            if "NO_LABEL_VISIBLE" not in result:
                print(result)
                print("-" * 30)
                # If we found a good label and extracted data, we can stop or continue
                # Typically, image_1 or image_2 are the best ones.
            else:
                print("No label detected in this image.")
            
            time.sleep(2) # Cooldown
            
        except Exception as e:
            print(f"Error analyzing {img_path.name}: {e}")

if __name__ == "__main__":
    main()
