from internetarchive import upload

identifier = "Quran-English-SaheehInternational-Audio"
source_directory = "audio"

def upload_to_archive():
    metadata = {
        'collection': 'opensource_audio',
        'mediatype': 'audio',
        'creator': 'kokoro',
        'title': 'The Holy Quran - English Translation (Saheeh International) - TTS Audio',
        'description': 'Complete English translation of the Holy Quran, narrated by Text-to-Speech (TTS) technology. This collection contains all 114 Surahs (chapters), with each Surah in its own directory. Audio files are organized by verse number within each Surah directory (e.g., 001/001.wav, 001/002.wav, etc.).\n\nNote: This recording contains English translation only. No Arabic recitation is included.\n\nThe Saheeh International translation is known for its clear, modern English and precision in conveying Islamic terminology.',
        'subject': [
            'Quran',
            'Islam',
            'English Translation',
            'Saheeh International',
            'TTS',
            'Audio Quran',
            'Holy Quran',
            'Religious Texts'
        ],
        'translator': 'Saheeh International',
        'language': 'eng',
        'licenseurl': 'https://quran.com/license',
        'rights': 'The English translation is © Saheeh International. Used with permission for non-commercial, educational purposes. Audio recording released under Creative Commons BY-NC-SA 4.0.',
        'date': '2025-11-22',
        'files_count': '6236',
        'surahs': '114',
        'format': 'WAV',
        'tts_engine': 'kokoro',
        'tts_voice': 'af_heart',
    }
    print(f"\nStarting bulk upload to https://archive.org/details/{identifier}\n")
    try:
        upload(identifier, source_directory, metadata=metadata, verbose=True, delete=True, retries=3, retries_sleep=10)
    except Exception as e:
        print(f"\n✗ AN ERROR OCCURRED: {e}")

if __name__ == "__main__":
    upload_to_archive()