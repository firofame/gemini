import os
import subprocess
import json
import argparse
import sys
import re
from pathlib import Path

def get_audio_from_url(url: str) -> Path:
    """Downloads audio from a URL using yt-dlp."""
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)
    
    # Create a safe filename from the URL
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url.split('/')[-1] or "audio")
    output_template = str(downloads_dir / f"{safe_name}.%(ext)s")
    
    print(f"Downloading audio from {url}...")
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "-o", output_template,
        url
    ]
    
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Error downloading audio: {proc.stderr}")
        sys.exit(1)
        
    # Find the downloaded file (it might have an extra extension)
    # yt-dlp with -x --audio-format mp3 should result in .mp3
    downloaded_file = downloads_dir / f"{safe_name}.mp3"
    if not downloaded_file.exists():
        # Fallback to searching for the file if exact match fails
        files = list(downloads_dir.glob(f"{safe_name}.*"))
        if files:
            downloaded_file = files[0]
        else:
            print(f"Could not find downloaded file for {safe_name}")
            sys.exit(1)
            
    return downloaded_file

def transcribe(audio_path: Path, language: str = None) -> dict:
    """Sends the audio file to Cloudflare Workers AI using curl and JSON/Base64."""
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    
    if not account_id or not api_token:
        return {"error": "Cloudflare credentials (CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN) not found in your environment."}
    
    if not audio_path.exists():
        return {"error": f"File not found: {audio_path}"}

    # Using the more robust turbo model
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/openai/whisper-large-v3-turbo"
    
    import base64
    import tempfile
    
    print(f"Loading and encoding {audio_path.name}...")
    with open(audio_path, 'rb') as f:
        audio_b64 = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {"audio": audio_b64}
    if language:
        payload["language"] = language
    
    # Use a temp file for the JSON payload to avoid command line length limits
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
        json.dump(payload, tf)
        tmp_json_path = tf.name
        
    try:
        print(f"Calling Cloudflare Workers AI (whisper-large-v3-turbo)...")
        cmd = [
            "curl", "-X", "POST", url,
            "-H", f"Authorization: Bearer {api_token}",
            "-H", "Content-Type: application/json",
            "-d", f"@{tmp_json_path}",
            "--silent"
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True)
        
        if proc.returncode != 0:
            return {"error": f"curl failed: {proc.stderr}"}
            
        try:
            response = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {"error": f"Failed to parse Cloudflare response: {proc.stdout}"}

    finally:
        if os.path.exists(tmp_json_path):
            os.remove(tmp_json_path)

    if not response.get("success"):
        errors = response.get("errors", [])
        return {"error": f"Cloudflare API error: {errors}"}
        
    result = response["result"]
    return {"text": result.get("text", ""), "language": language or "auto"}

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio using Cloudflare Workers AI Whisper.")
    parser.add_argument("--audio-file", required=True, help="Path to the audio file or a URL")
    parser.add_argument("--output-file", help="Path to save the transcript")
    parser.add_argument("--language", help="Optional language code (e.g., 'en', 'ml')")
    parser.add_argument("--keep-audio", action="store_true", help="Keep the downloaded audio file")
    
    args = parser.parse_args()
    
    is_url = args.audio_file.startswith(("http://", "https://"))
    
    # Handle URLs
    if is_url:
        audio_path = get_audio_from_url(args.audio_file)
        # Default output file if not specified
        if not args.output_file:
            args.output_file = f"{audio_path.stem}_transcript.txt"
    else:
        audio_path = Path(args.audio_file)
        if not audio_path.exists():
            # Check in downloads folder as a convenience
            if not args.audio_file.startswith("downloads/") and (Path("downloads") / args.audio_file).exists():
                audio_path = Path("downloads") / args.audio_file
            else:
                print(f"Error: {args.audio_file} not found")
                sys.exit(1)
        if not args.output_file:
            args.output_file = "transcript.txt"

    print(f"Processing {audio_path}...")
    result = transcribe(audio_path, language=args.language)
    
    if "error" in result:
        print(f"Transcription failed: {result['error']}")
        sys.exit(1)

    # Cleanup downloaded file if requested
    if is_url and not args.keep_audio:
        print(f"Cleaning up {audio_path}...")
        audio_path.unlink()

    Path(args.output_file).write_text(result["text"], encoding="utf-8")
    print(f"\n--- TRANSCRIPT START ---\n")
    print(result["text"])
    print(f"\n--- TRANSCRIPT END ---\n")
    print(f"Saved transcript to {args.output_file}")
    print(f"View transcript: open '{args.output_file}'")

if __name__ == "__main__":
    main()