import os
from google import genai
from google.genai import types

INPUT_TEXT = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
SYSTEM_INSTRUCTION = 'translate to malayalam for a muslim audience. return only the translated text'

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
response = client.models.generate_content(model='gemini-3-flash-preview', contents=INPUT_TEXT, config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION))
print(response.text)
client.close()