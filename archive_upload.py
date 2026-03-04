from internetarchive import upload
from pathlib import Path

# Archive item identifier
identifier = "Umm-ul-Amraz-Hazrat-Sheikh-ul-Hadith-Maulana-Zakariya-Rahimahullah"
source_file = "Umm-ul-Amraz_Hazrat-Sheikh-ul-Hadith_Maulana-Zakariya-Rahimahullah.txt"

def upload_to_archive():
    if not Path(source_file).is_file():
        print(f"\n✗ FILE NOT FOUND: {source_file}")
        return

    metadata = {
        'collection': 'opensource',
        'mediatype': 'texts',
        'creator': 'Hazrat Sheikh ul Hadith Maulana Zakariya Rahimahullah',
        'title': 'Umm ul Amraz (ام الامراض)',
        'description': (
            'Text upload of "Umm ul Amraz" (ام الامراض), attributed to '
            'Hazrat Sheikh ul Hadith Maulana Zakariya Rahimahullah.\n\n'
            'This item contains a plain text file for reading and archival access.'
        ),
        'subject': [
            'Islamic Literature',
            'Umm ul Amraz',
            'Maulana Zakariya',
            'Urdu',
            'Arabic Script'
        ],
        'language': 'urd',
        'format': 'txt'
    }
    
    print(f"\nStarting file upload to https://archive.org/details/{identifier}")
    
    try:
        upload(
            identifier, 
            source_file,
            metadata=metadata, 
            verbose=True, 
            delete=False,
            retries=3, 
            retries_sleep=10,
            checksum=True
        )
        print(f"\n✓ UPLOAD SUCCESSFUL! View at: https://archive.org/details/{identifier}")
    except Exception as e:
        print(f"\n✗ AN ERROR OCCURRED: {e}")

if __name__ == "__main__":
    upload_to_archive()
