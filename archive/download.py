from internetarchive import get_item, download
from pathlib import Path
import os

# Configuration
identifier = "Fazail-e-Sadqaat-Malayalam-Audio"
dest_dir = Path("./Fazail-e-Sadaqat")

def download_from_archive():
    print(f"\n📥 DOWNLOAD OPERATION")
    print(f"   Source: https://archive.org/details/{identifier}")
    print(f"   Target: {dest_dir.resolve()}\n")

    try:
        # Fetch the item metadata to list files
        item = get_item(identifier)
        all_files = list(item.get_files())

        # Filter for files inside Malayalam_Chapters ending with .md or .txt
        files_to_download = [
            f.name for f in all_files 
            if f.name.startswith("Malayalam_Chapters/") and (f.name.endswith(".md") or f.name.endswith(".txt"))
        ]

        if not files_to_download:
            print("✗ No text/markdown files found in Malayalam_Chapters folder.")
            return

        print(f"Found {len(files_to_download)} text/markdown file(s) to download:")
        for name in files_to_download:
            print(f"   - {name}")

        # Ensure destination directory exists
        dest_dir.mkdir(parents=True, exist_ok=True)

        print("\nStarting download...")
        # internetarchive download preserves the folder structure (e.g. Malayalam_Chapters/filename.md)
        # under the destdir inside a subfolder named after the identifier
        download(
            identifier,
            files=files_to_download,
            destdir=str(dest_dir),
            verbose=True,
            retries=3,
        )

        # Move files to their final clean location and clean up the item-id named directory
        item_dir = dest_dir / identifier
        src_malayalam_dir = item_dir / "Malayalam_Chapters"
        final_malayalam_dir = dest_dir / "Malayalam_Chapters"

        if src_malayalam_dir.exists():
            final_malayalam_dir.mkdir(parents=True, exist_ok=True)
            for f in src_malayalam_dir.iterdir():
                dest_file = final_malayalam_dir / f.name
                # Move/Overwrite if already exists
                if dest_file.exists():
                    dest_file.unlink()
                f.rename(dest_file)
            
            # Clean up empty source directories
            src_malayalam_dir.rmdir()
            if item_dir.exists():
                item_dir.rmdir()

        print(f"\n✓ DOWNLOAD COMPLETED")
        print(f"  Files saved in: {final_malayalam_dir.resolve()}")
    except Exception as error:
        print(f"\n✗ ERROR OCCURRED: {error}")

if __name__ == "__main__":
    download_from_archive()
