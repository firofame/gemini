from internetarchive import upload

identifier = "Tadabbur-Quran-English-Audio"
source_directory = "Tadabbur"

def upload_to_archive():
    metadata = {
        'collection': 'opensource_audio',
        'mediatype': 'audio',
        'creator': 'Tadabbur Project',
        'title': 'Tadabbur - The Holy Quran - English Translation - Audio',
        'description': f'Complete English translation of the Holy Quran in audio format from the Tadabbur project.\n\nClear English recitation of the Quranic text. The Tadabbur project aims to make Quranic content accessible through high-quality audio recordings.\n\nNote: This recording contains English translation only. No Arabic recitation is included.',
        'subject': [
            'Quran',
            'Islam',
            'English Translation',
            'Tadabbur',
            'Audio Quran',
            'Holy Quran',
            'Religious Texts',
            'Islamic Audio'
        ],
        'language': 'eng',
        'licenseurl': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'rights': 'Released under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0). For non-commercial, educational use only.',
        'date': '2025-12-30',
        'format': 'WAV',
        'project': 'Tadabbur',
        'audio_type': 'English Translation',
        'recitation_style': 'Clear English Narration'
    }
    
    print(f"\nStarting bulk upload to https://archive.org/details/{identifier}")    
    try:
        upload(identifier, source_directory, metadata=metadata, verbose=True, delete=True, retries=3, retries_sleep=10)
    except Exception as e:
        print(f"\n✗ AN ERROR OCCURRED: {e}")

if __name__ == "__main__":
    upload_to_archive()