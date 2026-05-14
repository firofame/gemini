from google import genai

client = genai.Client()
for model in client.models.list():
    print(f"Model: {model.name}")
