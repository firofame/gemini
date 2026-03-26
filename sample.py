from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.1-flash-lite-preview",
    contents="Tell me a joke about AI."
)

print(f"Model ID: gemini-3.1-flash-lite-preview")
print(f"Response: {response.text}")