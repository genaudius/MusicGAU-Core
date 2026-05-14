"""
RunPod GPU Pod Deployer via GraphQL API
Deploys a new training Pod with the GenAudius Engine image.
"""
import requests
import json
import time
import sys

RUNPOD_API_KEY = "rpa_P9EYBZEY9I4FIP8BVQTWKDDSUMVX36G7MCGTLNDFpuzy5aPI"
GRAPHQL_URL = f"https://api.runpod.io/graphql?api_key={RUNPOD_API_KEY}"
HEADERS = {"Content-Type": "application/json"}

DOCKER_IMAGE = "genaudius/musicgau-core:latest"
GAU_API_KEY = "gau_master_secure_2026"

def gql(query: str, variables: dict = None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    r = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload, timeout=30)
    return r.json()

def list_pods():
    print("--- Checking existing pods ---")
    result = gql("{ myself { pods { id name desiredStatus runtime { gpus { id gpuUtilPercent memoryUtilPercent } } } } }")
    pods = result.get("data", {}).get("myself", {}).get("pods", [])
    for pod in pods:
        print(f"  Pod: {pod['id']} | Name: {pod['name']} | Status: {pod['desiredStatus']}")
    return pods

def get_available_gpus():
    print("\n--- Checking GPU Availability ---")
    # Try A100, then 4090, then 3090 in order of preference
    gpu_types = ["NVIDIA A100-SXM4-80GB", "NVIDIA GeForce RTX 4090", "NVIDIA RTX A6000", "NVIDIA GeForce RTX 3090"]
    
    query = """
    query gpuTypes {
      gpuTypes {
        id
        displayName
        memoryInGb
        lowestPrice { minimumBidPrice stockStatus }
        securePrice
      }
    }
    """
    result = gql(query)
    gpu_data = result.get("data", {}).get("gpuTypes", [])
    
    available = []
    for gpu in gpu_data:
        price_data = gpu.get("lowestPrice") or {}
        status = price_data.get("stockStatus", "UNAVAILABLE")
        if status != "UNAVAILABLE":
            available.append(gpu)
            print(f"  AVAILABLE: {gpu['displayName']} | VRAM: {gpu['memoryInGb']}GB | Price: ${gpu.get('securePrice', 'N/A')}/hr")
    
    return available

def deploy_pod():
    print("\n--- Deploying GenAudius Training Pod ---")
    
    # Create the pod mutation
    mutation = """
    mutation podFindAndDeployOnDemand($input: PodFindAndDeployOnDemandInput!) {
      podFindAndDeployOnDemand(input: $input) {
        id
        imageName
        desiredStatus
      }
    }
    """
    
    variables = {
        "input": {
            "cloudType": "SECURE",
            "gpuCount": 1,
            "volumeInGb": 100,
            "containerDiskInGb": 20,
            "minVcpuCount": 8,
            "minMemoryInGb": 24,
            "gpuTypeId": "NVIDIA GeForce RTX 4090",  # Start with 4090
            "name": "genaudius-training",
            "imageName": DOCKER_IMAGE,
            "dockerArgs": "",
            "ports": "8000/http",
            "volumeMountPath": "/workspace/data",
            "env": [
                {"key": "GAU_API_KEY", "value": GAU_API_KEY},
                {"key": "RUNPOD_SERVERLESS", "value": "false"}
            ],
            "startJupyter": False,
            "startSsh": True,
        }
    }
    
    # Try 4090 first, then A100
    gpu_priority = [
        "NVIDIA GeForce RTX 4090",
        "NVIDIA A100-SXM4-80GB",
        "NVIDIA RTX A6000",
        "NVIDIA GeForce RTX 3090",
    ]
    
    for gpu_type in gpu_priority:
        print(f"\nTrying GPU: {gpu_type}...")
        variables["input"]["gpuTypeId"] = gpu_type
        result = gql(mutation, variables)
        
        errors = result.get("errors")
        pod_data = result.get("data", {}).get("podFindAndDeployOnDemand")
        
        if pod_data:
            pod_id = pod_data["id"]
            print(f"\nPod deployed successfully!")
            print(f"Pod ID: {pod_id}")
            print(f"Image: {pod_data['imageName']}")
            print(f"Status: {pod_data['desiredStatus']}")
            return pod_id
        elif errors:
            err_msg = errors[0].get("message", "Unknown error")
            print(f"  Failed ({err_msg}). Trying next GPU...")
    
    print("\nNo GPU available at the moment. Try again later or use Serverless.")
    return None


if __name__ == "__main__":
    print("=== GenAudius RunPod Deployer ===\n")
    pods = list_pods()
    gpus = get_available_gpus()
    pod_id = deploy_pod()
    
    if pod_id:
        print(f"\nAccess your pod at: https://console.runpod.io/pods/{pod_id}")
        print("Next: SSH in and run: cd /workspace/GenAudius_V1 && ./scripts/runpod_train.sh")
