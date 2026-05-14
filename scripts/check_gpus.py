import requests, json

RUNPOD_API_KEY = "rpa_P9EYBZEY9I4FIP8BVQTWKDDSUMVX36G7MCGTLNDFpuzy5aPI"
GRAPHQL_URL = f"https://api.runpod.io/graphql?api_key={RUNPOD_API_KEY}"

# First, check account info
r = requests.post(GRAPHQL_URL, headers={"Content-Type": "application/json"},
    json={"query": "{ myself { id email creditBalance } }"},
    timeout=30)
print("ACCOUNT CHECK:")
print(json.dumps(r.json(), indent=2))

# Check GPU types
r2 = requests.post(GRAPHQL_URL, headers={"Content-Type": "application/json"},
    json={"query": "{ gpuTypes { id displayName memoryInGb securePrice secureCloud } }"},
    timeout=30)
print("\nGPU TYPES:")
print(json.dumps(r2.json(), indent=2)[:3000])
