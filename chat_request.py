import requests

API_KEY = "123456"
BASE_URL = "http://localhost:7860"

url = f"{BASE_URL}/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}
payload = {
    # "model": "gemini-3.1-pro-preview",
    "model": "gemini-3.1-flash-lite-preview",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"},
    ],
    "stream": False,
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print("Status:", response.status_code)
    print(response.text)
except requests.exceptions.ConnectionError:
    print("Could not connect to localhost:7860. Start the server first.")
