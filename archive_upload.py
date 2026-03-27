from internetarchive import upload
from pathlib import Path


identifier = "Akabir-Ka-Ramazan-Hazrat-Sheikh-ul-Hadith-Maulana-Zakariya-Rahimahullah"
source_files = [
    "Akabir-Ka-Ramazan-Urdu_Hazrat-Sheikh-ul-Hadith_Maulana-Zakariya-Rahimahullah.txt",
    "malayalam-audio-അക്കാബിരീങ്ങളുടെ-റമദാൻ-Sheikh-ul-Hadith_Maulana-Zakariya-Rahimahullah.mp3",
]


def upload_to_archive():
    missing_files = [file_name for file_name in source_files if not Path(file_name).is_file()]
    if missing_files:
        print("\n✗ FILES NOT FOUND:")
        for file_name in missing_files:
            print(f"  - {file_name}")
        return

    metadata = {
        "collection": "opensource",
        "mediatype": "audio",
        "creator": "Hazrat Sheikh ul Hadith Maulana Zakariya Rahimahullah",
        "title": "Akabir Ka Ramazan - Urdu Text and Malayalam Audio",
        "description": (
            'Archive upload containing the Urdu text file "Akabir Ka Ramazan" '
            "and its Malayalam audio version, attributed to Hazrat Sheikh ul "
            "Hadith Maulana Zakariya Rahimahullah."
        ),
        "subject": [
            "Islamic Literature",
            "Ramazan",
            "Ramadan",
            "Akabir Ka Ramazan",
            "Maulana Zakariya",
            "Urdu",
            "Malayalam",
            "Audio Lecture",
            "Text Archive",
        ],
        "language": "urd;mal",
    }

    print(f"\nStarting file upload to https://archive.org/details/{identifier}")
    print("Files to upload:")
    for file_name in source_files:
        print(f"  - {file_name}")

    try:
        upload(
            identifier,
            source_files,
            metadata=metadata,
            verbose=True,
            delete=False,
            retries=3,
            retries_sleep=10,
            checksum=True,
        )
        print(f"\n✓ UPLOAD SUCCESSFUL! View at: https://archive.org/details/{identifier}")
    except Exception as error:
        print(f"\n✗ AN ERROR OCCURRED: {error}")


if __name__ == "__main__":
    upload_to_archive()
