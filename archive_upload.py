from internetarchive import upload
import datetime

# CHANGED: Generic identifier (No branding)
identifier = "The-Holy-Quran-Malayalam-Translation-Audio"
source_directory = "audio"

def upload_to_archive():
    metadata = {
        'collection': 'opensource_audio',
        'mediatype': 'audio',
        'creator': 'GEMINI', 
        'title': 'The Holy Quran - Malayalam Translation - Audio (വിശുദ്ധ ഖുർആൻ മലയാളം പരിഭാഷ)',
        'description': (
            'Complete Malayalam translation of the Holy Quran in audio format.\n\n'
            'This collection contains the audio translation of the Quran in Malayalam (മലയാളം), intended for speakers '
            'in Kerala and the Malayalam-speaking diaspora.\n\n'
            'Original Title: വിശുദ്ധ ഖുർആൻ (The Holy Quran)\n'
            'Language: Malayalam\n\n'
            'This collection aims to make Quranic content accessible through high-quality audio recordings.\n\n'
            'Note: This recording contains Malayalam translation only. No Arabic recitation is included.'
        ),
        'subject': [
            'Quran',
            'Islam',
            'Malayalam Translation',
            'Audio Quran',
            'Holy Quran',
            'Kerala',
            'Malabari',
            'Mappila',
            'South Indian',
            'വിശുദ്ധ ഖുർആൻ', # Quran in Malayalam script
            'മലയാളം'        # Malayalam in Malayalam script
        ],
        'language': 'mal',
        'format': 'mp3',
        'audio_type': 'Malayalam Translation',
        'recitation_style': 'Clear Narration'
    }
    
    print(f"\nStarting bulk upload to https://archive.org/details/{identifier}")    
    
    try:
        upload(
            identifier, 
            source_directory, 
            metadata=metadata, 
            verbose=True, 
            delete=True, 
            retries=3, 
            retries_sleep=10,
            checksum=True
        )
        print(f"\n✓ UPLOAD SUCCESSFUL! View at: https://archive.org/details/{identifier}")
    except Exception as e:
        print(f"\n✗ AN ERROR OCCURRED: {e}")

if __name__ == "__main__":
    upload_to_archive()