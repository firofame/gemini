from google import genai

client = genai.Client()

print("Models with generateContent:\n")
for m in client.models.list():
    if m.supported_actions and 'generateContent' in m.supported_actions:
        print(f"{m.name}")