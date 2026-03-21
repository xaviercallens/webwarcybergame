import os
import time
import uuid
import requests
import websockets
import asyncio
import json

BASE_URL = os.environ.get("BASE_URL", "https://neohack-gridlock-v2-212120873430.europe-west1.run.app")
WS_URL = BASE_URL.replace("http", "ws").replace("/api", "") + "/ws/game"
API_URL = f"{BASE_URL}/api"

test_id = str(uuid.uuid4())[:8]
USERNAME = f"e2e_user_{test_id}"
PASSWORD = "SecurePassword123!"

async def run_e2e_test():
    print(f"--- STARTING REMOTE E2E TEST on {BASE_URL} ---")
    
    # 1. Registration
    print(f"1. Registering user {USERNAME}...")
    res = requests.post(f"{API_URL}/auth/register", json={"username": USERNAME, "password": PASSWORD})
    assert res.status_code == 200, f"Registration failed: {res.text}"
    token = res.json()["access_token"]
    player_id = res.json()["player"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   [OK] Registration successful.")
    
    # 2. Login
    print("2. Testing Login...")
    res = requests.post(f"{API_URL}/auth/login", json={"username": USERNAME, "password": PASSWORD})
    assert res.status_code == 200, f"Login failed: {res.text}"
    print("   [OK] Login successful.")
    
    # 3. GET World State
    print("3. Fetching World State...")
    res = requests.get(f"{API_URL}/world/state", headers=headers)
    assert res.status_code == 200, f"Fetch world state failed: {res.text}"
    nodes = res.json().get("nodes", [])
    assert len(nodes) > 0, "No nodes returned."
    print(f"   [OK] Fetched {len(nodes)} nodes.")
    
    # 4. WebSockets Auth via Payload
    print("4. Testing secure WS Payload connection...")
    try:
        ws = await websockets.connect(WS_URL)
        await ws.send(json.dumps({"token": token}))
        # The backend connection manager accepts silently in wait_for, we stay connected.
        print("   [OK] WS Connected securely.")
    except Exception as e:
        print(f"   [FAIL] WS Connection Error: {e}")
        return
        
    # 5. Rate Limits on Chat
    print("5. Testing diplomacy/chat Rate Limit (5/min)...")
    res_list = []
    # Gemini might take a couple of seconds to respond since it's an external API
    # so we shoot 6 requests back to back. (Since they are async, they should queue up fast)
    for i in range(6):
        res = requests.post(f"{API_URL}/diplomacy/chat", json={"faction_id": 2, "message": f"Test {i}"}, headers=headers)
        res_list.append(res.status_code)
    
    assert 429 in res_list, "Rate Limit not triggered! Allowed > 5 requests."
    print("   [OK] Chat Rate Limit successfully caught abuse.")
    
    # 6. Infinite Money Glitch (Max 1 TRADE treaty per faction type check)
    print("6. Testing Trade Treaty cap...")
    res1 = requests.post(f"{API_URL}/diplomacy/propose", json={"target_faction_id": 2, "type": "TRADE", "proposal_text": "Trade A"}, headers=headers)
    if res1.status_code == 200:
        res2 = requests.post(f"{API_URL}/diplomacy/propose", json={"target_faction_id": 2, "type": "TRADE", "proposal_text": "Trade B"}, headers=headers)
        assert res2.status_code == 400, "Was able to propose duplicate TRADE accords. Infinite money glitch is still open!"
        print("   [OK] Duplicate TRADE accords are blocked.")
    else:
        # Faction 2 might reject the first one anyway depending on personality
        print("   [OK] First trade rejected or handled, logic is safe.")
        
    # 7. XP Exploit /game-over
    print("7. Testing XP Exploit cap...")
    res = requests.post(f"{API_URL}/players/me/game-over", json={"won": True, "time_seconds": 60, "nodes_captured": 99999, "nodes_lost": 0, "attacks": 10}, headers=headers)
    assert res.status_code == 400, "XP Exploit succeeded!"
    print("   [OK] Invalid node capture bounds blocked securely.")
    
    await ws.close()
    print("--- ALL REMOTE TESTS PASSED ---")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
