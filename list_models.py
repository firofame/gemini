import os
from google import genai

api_key = next(
    (v for k, v in sorted(os.environ.items()) if k.startswith("GEMINI_API_KEY_")),
    os.environ.get("GEMINI_API_KEY")
)

client = genai.Client(api_key=api_key)
for model in client.models.list():
    print(f"Model: {model.name}")

