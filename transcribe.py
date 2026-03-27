import modal
from pathlib import Path

app = modal.App("whisper-transcribe")

# Use a standard image and install whisper via pip
# This avoids the complex compilation issues of whisper.cpp
image = (
    modal.Image.debian_slim()
    .apt_install("ffmpeg")
    .pip_install("openai-whisper", "torch", "numpy")
)

@app.function(image=image, gpu="T4", timeout=1200)
def transcribe(audio_bytes: bytes, filename: str, language: str = None) -> dict:
    import whisper
    import os
    import tempfile
    
    # Save the audio bytes to a temporary file
    suffix = Path(filename).suffix if filename else ".mp3"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
        
    try:
        print(f"Loading Whisper 'medium' model...")
        model = whisper.load_model("medium")
        print(f"Transcribing {filename} (language: {'auto' if language is None else language})...")
        result = model.transcribe(tmp_path, language=language)
        return {"text": result["text"], "language": result.get("language")}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.local_entrypoint()
def main(audio_file: str, output_file: str = "transcript.txt", language: str = None):
    audio_path = Path(audio_file)
    if not audio_path.exists():
        if not audio_file.startswith("downloads/") and (Path("downloads") / audio_file).exists():
            audio_path = Path("downloads") / audio_file
        else:
            print(f"Error: {audio_file} not found")
            return

    print(f"Processing {audio_path}...")
    result = transcribe.remote(audio_path.read_bytes(), audio_path.name, language)
    
    print(f"Detected language: {result['language']}")
    Path(output_file).write_text(result["text"], encoding="utf-8")
    print(f"Saved transcript to {output_file}")