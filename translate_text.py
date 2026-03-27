import sys
from pathlib import Path
from google import genai

def translate_text(input_file: str, output_file: str, target_language: str = "Malayalam"):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: {input_file} not found")
        return

    print(f"Reading {input_file}...")
    source_text = input_path.read_text(encoding="utf-8")
    
    # Using the same prompt style as translate_book.py
    prompt = f"Translate the following text into {target_language}. Output only the translated text, with no commentary.\n\n{source_text}"

    print(f"Translating to {target_language} using Gemini...")
    client = genai.Client()
    # Using gemini-2.5-flash which is available in your environment
    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=[prompt]
    )

    if not response.text:
        print("Error: Gemini returned empty response.")
        return

    Path(output_file).write_text(response.text, encoding="utf-8")
    print(f"Saved translated text to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 translate_text.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else Path(input_file).with_suffix("").name + "_ml.txt"
    if len(sys.argv) <= 2:
        output_file = str(Path("downloads") / (Path(input_file).stem + "_ml.txt"))
        
    translate_text(input_file, output_file)
