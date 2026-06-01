# https://archive.org/developers/internetarchive/internetarchive.html

from internetarchive import upload
from pathlib import Path
import os
import datetime

# Configuration
identifier = "Hayat-us-Sahabah-Malayalam-Audio"
search_dir = Path("./Hayat al-Sahaba")

def safe_component(name, max_bytes=225):
    """Truncate a path component so its UTF-8 encoding doesn't exceed max_bytes."""
    encoded = name.encode('utf-8')
    if len(encoded) <= max_bytes:
        return name
    
    if '.' in name:
        base, ext = name.rsplit('.', 1)
        ext_bytes = ('.' + ext).encode('utf-8')
        max_base_bytes = max_bytes - len(ext_bytes)
    else:
        base, ext = name, None
        max_base_bytes = max_bytes
        
    encoded_base = base.encode('utf-8')
    valid_len = max_base_bytes
    while valid_len > 0:
        try:
            encoded_base[:valid_len].decode('utf-8')
            break
        except UnicodeDecodeError:
            valid_len -= 1
            
    truncated = encoded_base[:valid_len].decode('utf-8')
    if ext is not None:
        return truncated + '.' + ext
    return truncated

def get_source_files():
    """Returns a map of {remote_filename: local_filepath} for all files in search_dir."""
    if not search_dir.is_dir():
        return {}
    
    file_map = {}
    for f in search_dir.glob("**/*"):
        if f.is_file() and "debug" not in f.parts:
            # Create a safe key by truncating path components that are too long (Archive.org limit is 230 bytes)
            rel_path = f.relative_to(search_dir)
            safe_parts = [safe_component(part) for part in rel_path.parts]
            remote_key = "/".join(safe_parts)
            file_map[remote_key] = str(f)
            
    return file_map

def upload_to_archive():
    source_files_map = get_source_files()
    if not source_files_map:
        print(f"\n✗ DIRECTORY NOT FOUND: {search_dir}")
        return

    # Authentication - prioritize environment variables
    access_key = os.environ.get("IA_ACCESS_KEY")
    secret_key = os.environ.get("IA_SECRET_KEY")

    metadata = {
        "collection": "opensource_audio",
        "mediatype": "audio",
        "creator": "Maulana Muhammad Yusuf Khandalwi",
        "title": "Hayat us-Sahabah (Malayalam Audio & Texts)",
        "description": (
            "Hayat us-Sahabah (The Lives of the Sahabah) by Maulana Muhammad Yusuf Khandalwi "
            "with Malayalam audio chapters, Malayalam & Arabic text chapters, and the full PDFs."
        ),
        "subject": [
            "Islam",
            "Hayat us-Sahabah",
            "Hayat al-Sahaba",
            "Maulana Muhammad Yusuf Khandalwi",
            "Malayalam",
            "Audio",
            "Sahabah",
        ],
        "language": "mal",
        "date": str(datetime.datetime.now().year),
    }

    print(f"\nStarting upload to https://archive.org/details/{identifier}")
    print(f"Total files found in {search_dir}: {len(source_files_map)}")
    
    if access_key and secret_key:
        print("✓ Using authentication keys from environment variables.")
    else:
        print("! No keys in environment variables. Falling back to local configuration ('ia configure').")

    try:
        upload(
            identifier,
            source_files_map,
            metadata=metadata,
            access_key=access_key,
            secret_key=secret_key,
            verbose=True,
            delete=True,
            retries=3,
            retries_sleep=10,
            checksum=True,
            request_kwargs={"timeout": 600},
        )
        print(f"\n✓ UPLOAD SUCCESSFUL! View at: https://archive.org/details/{identifier}")
    except Exception as error:
        print(f"\n✗ AN ERROR OCCURRED: {error}")

if __name__ == "__main__":
    upload_to_archive()
