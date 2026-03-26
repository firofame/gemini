from google import genai

client = genai.Client()

print("List of models that support generateContent:\n")
for m in client.models.list():
    print(m.name)