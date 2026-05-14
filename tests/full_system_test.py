import requests
import time
import os

# --- Configuration ---
API_BASE_URL = "http://localhost:8000"
API_KEY = "gau_master_secure_2026"  # The one we set in api.py
HEADERS = {"x-api-key": API_KEY}

def test_full_system():
    print("\n--- GenAudius Engine v1.0: Full System Test ---")
    
    # 1. Check Credits / Health
    try:
        print("\n[1/4] Checking Health/Credits...")
        r = requests.get(f"{API_BASE_URL}/api/v1/chat/credit", headers=HEADERS)
        r.raise_for_status()
        print(f"Success: {r.json()}")
    except Exception as e:
        print(f"Error: {e}")
        return

    # 2. List Models
    try:
        print("\n[2/4] Listing Models...")
        r = requests.get(f"{API_BASE_URL}/api/models", headers=HEADERS)
        r.raise_for_status()
        print(f"Success: {r.json()}")
    except Exception as e:
        print(f"Error: {e}")
        return

    # 3. Test Security (Unauthorized Request)
    try:
        print("\n[3/4] Testing Security Shield (expecting 403)...")
        r = requests.get(f"{API_BASE_URL}/api/models", headers={"x-api-key": "wrong_key"})
        print(f"Status Code: {r.status_code}")
        if r.status_code == 403:
            print("Shield is ACTIVE! ✅")
        else:
            print("Shield FAILED! ❌")
    except Exception as e:
        print(f"Error: {e}")

    # 4. Mock Generation Task
    try:
        print("\n[4/4] Testing Generation Endpoint...")
        payload = {
            "prompt": "bachata moderna romántica",
            "version": "MusicGAU-V1"
        }
        r = requests.post(f"{API_BASE_URL}/api/v1/generate", json=payload, headers=HEADERS)
        r.raise_for_status()
        print(f"Success: {r.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- TEST COMPLETE ---")

if __name__ == "__main__":
    test_full_system()
