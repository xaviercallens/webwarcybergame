import requests
import uuid

BASE_URL = "https://neohack-gridlock-v2-212120873430.europe-west1.run.app"
API_URL = f"{BASE_URL}/api"
USERNAME = f"e2e_user_{str(uuid.uuid4())[:8]}"

print(f"Registering {USERNAME}...")
res = requests.post(f"{API_URL}/auth/register", json={"username": USERNAME, "password": "SecurePassword123!"})
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Testing chat endpoint...")
res = requests.post(f"{API_URL}/diplomacy/chat", json={"faction_id": 2, "message": "Give me a status update."}, headers=headers)
print(f"Status Code: {res.status_code}")
print(f"Reply: {res.json().get('reply')}")

print("Testing propose endpoint...")
res = requests.post(f"{API_URL}/diplomacy/propose", json={"target_faction_id": 2, "type": "TRADE", "proposal_text": "Let us trade!"}, headers=headers)
print(f"Status Code: {res.status_code}")
print(f"Reply: {res.json()}")

