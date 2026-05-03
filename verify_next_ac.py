import json
import subprocess
import sys
import time
from pathlib import Path

def process_one_ac():
    json_path = Path("ac_list.json")
    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        return False

    # 1. Load the list
    with open(json_path, "r") as f:
        try:
            ac_list = json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Failed to decode {json_path}")
            return False

    # 2. Find the next unverified item
    target_ac = None
    for ac in ac_list:
        if "verified_data" not in ac:
            target_ac = ac
            break

    if not target_ac:
        print("\n🎉 ALL ITEMS VERIFIED! No more unverified items found.")
        return False

    print(f"\n{'='*60}")
    print(f"🚀 PROCESSING: {target_ac.get('title')[:70]}...")
    print(f"🔗 URL: {target_ac['url']}")
    print(f"{'='*60}\n")

    # 3. Clear previous images to avoid mixing data
    image_dir = Path("images")
    if image_dir.exists():
        for img in image_dir.glob("product_image_*.*"):
            img.unlink()
    else:
        image_dir.mkdir(exist_ok=True)

    # 4. Execute Download
    print("📥 Running amazon_image_downloader.py...")
    try:
        subprocess.run([sys.executable, "amazon_image_downloader.py", target_ac["url"]], check=True)
    except subprocess.CalledProcessError:
        print(f"❌ Download failed for {target_ac['asin']}. Skipping to next.")
        # Mark as tried or just continue
        return True
    except Exception as e:
        print(f"❌ Unexpected error during download: {e}")
        return True

    # 5. Execute Extraction
    print("\n🔍 Running extract_label_data.py --json...")
    try:
        result = subprocess.run(
            [sys.executable, "extract_label_data.py", "--json"], 
            stdout=subprocess.PIPE, 
            text=True, 
            check=True
        )
        
        output_text = result.stdout.strip()
        if output_text:
            extracted_data = json.loads(output_text)
            
            if "error" not in extracted_data:
                print(f"✅ Successfully extracted data: {extracted_data}")
                
                # Update the entry and save
                target_ac["verified_data"] = extracted_data
                with open(json_path, "w") as f:
                    json.dump(ac_list, f, indent=4)
                
                print(f"\n💾 SUCCESS: Verified data for {target_ac['asin']} saved!")
            else:
                print(f"⚠️ No BEE label found: {extracted_data.get('error')}")
                # We can optionally mark this as "tried" so we don't loop on it forever
                # For now, we just skip it in the next loop iteration if verified_data is still missing.
                # To prevent infinite loops on unparseable items, we could add a "not_found" flag.
                target_ac["verified_data"] = {"error": extracted_data.get('error')}
                with open(json_path, "w") as f:
                    json.dump(ac_list, f, indent=4)
        
    except Exception as e:
        print(f"❌ Extraction failed or crashed: {e}")

    return True

def main():
    print("🤖 Starting Bulk AC Verification Mode...")
    print("Press Ctrl+C at any time to stop.\n")
    
    try:
        while True:
            # Continue as long as there are items to process
            if not process_one_ac():
                break
            
            print("\n⏳ Cooling down for 5 seconds before next item...")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n🛑 Bulk process stopped by user.")
    
    print("\n🏁 Process finished.")

if __name__ == "__main__":
    main()
