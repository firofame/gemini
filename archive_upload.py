from internetarchive import upload
from pathlib import Path
import os
import datetime

# Configuration
identifier = "Fazail-e-Sadaqat-Malayalam"
search_dir = Path("./Fazail-e-Sadaqat")

def get_source_files():
    """Returns a map of {remote_filename: local_filepath} for all files in search_dir."""
    if not search_dir.is_dir():
        return {}
    
    # Map each file's relative path to its absolute path for a root-level upload
    return {f.relative_to(search_dir).as_posix(): str(f) for f in search_dir.glob("**/*") if f.is_file()}

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
        "creator": "Sheikhul Hadith Maulana Muhammad Zakariyya",
        "title": "Fazail-e-Sadaqat (Malayalam Audio)",
        "description": (
            "Fazail-e-Sadaqat (The Virtues of Charity) with audio chapters in Malayalam, "
            "authored by Sheikhul Hadith Maulana Muhammad Zakariyya. "
            "Includes individual chapter MP3 audio and text files."
        ),
        "subject": [
            "Islam",
            "Hadith",
            "Sadaqat",
            "Charity",
            "Malayalam",
            "Audio",
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
        )
        print(f"\n✓ UPLOAD SUCCESSFUL! View at: https://archive.org/details/{identifier}")
    except Exception as error:
        print(f"\n✗ AN ERROR OCCURRED: {error}")

if __name__ == "__main__":
    upload_to_archive()
