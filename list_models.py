import requests

API_KEY = "123456"
BASE_URL = "http://localhost:7860"

url = f"{BASE_URL}/v1/models"
headers = {
    "Authorization": f"Bearer {API_KEY}",
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    print("Status:", response.status_code)
    print(response.text)
except requests.exceptions.ConnectionError:
    print("Could not connect to localhost:7860. Start the server first.")
