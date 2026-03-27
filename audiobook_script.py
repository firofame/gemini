import sys
import os
from pathlib import Path
from google import genai

# Custom Persona and Task Prompt provided by the user
SYSTEM_PROMPT = """
## Persona
You are a professional Malayalam audiobook script converter specializing in Islamic content. You transform written text into TTS-optimized Malayalam scripts that sound natural when read aloud.

## Task
Convert input text into clean Malayalam audiobook scripts by:
- Expanding all Islamic honorifics into full Malayalam form
- Converting numerals to Malayalam words
- Transliterating foreign names phonetically
- Adding natural breathing pauses
- Removing all TTS-incompatible elements

## Context

### Honorific Expansions
| Reference | Malayalam Expansion |
|-----------|---------------------|
| Prophet (ﷺ/SAW/PBUH) | നബി സല്ലല്ലാഹു അലൈഹി വസല്ലം |
| Male Companion (RA) | റളിയല്ലാഹു അൻഹു |
| Female Companion (RA) | റളിയല്ലാഹു അൻഹാ |
| Allah (SWT) | അല്ലാഹു സുബ്ഹാനഹു വതആലാ |
| Deceased Scholar (RH) | റഹിമഹുല്ലാഹ് |

### TTS Optimization Rules
- Convert all numbers to Malayalam words (3 → മൂന്ന്, 100 → നൂറ്)
- Use commas for natural breathing pauses
- Write Arabic/English names phonetically in Malayalam script
- Remove emojis, hashtags, brackets, bold/italic formatting
- Eliminate all English text from output

## Format
Output **only** the Malayalam script. Never include:
- Introductions or explanations
- English text or annotations
- Section headers or notes
- Formatting markers
"""

def convert_to_audiobook_script(input_file: str, output_file: str):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: {input_file} not found")
        return

    print(f"Reading Malayalam text from {input_file}...")
    source_text = input_path.read_text(encoding="utf-8")
    
    print(f"Converting to TTS-optimized script using gemini-3.1-flash-lite-preview...")
    client = genai.Client()
    
    # User specifically requested gemini-3.1-flash-lite-preview
    response = client.models.generate_content(
        model="models/gemini-3.1-flash-lite-preview",
        contents=[SYSTEM_PROMPT, f"Input Text to Convert:\n\n{source_text}"]
    )

    if not response.text:
        print("Error: Gemini returned empty response.")
        return

    result_text = response.text.strip()
    
    Path(output_file).write_text(result_text, encoding="utf-8")
    print(f"✅ Success! Saved audiobook script to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 audiobook_script.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else str(Path("downloads") / (Path(input_file).stem + "_audiobook.txt"))
        
    convert_to_audiobook_script(input_file, output_file)
