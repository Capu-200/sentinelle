import urllib.request
import json
import uuid

url = "http://127.0.0.1:8000/auth/register"
email = f"test_{uuid.uuid4()}@example.com"
data = {
    "email": email,
    "password": "password123",
    "full_name": "Test User"
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        print("Response:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"Error: {e.code}")
    print("Response:", e.read().decode('utf-8'))
except Exception as e:
    print(f"Exception: {e}")
