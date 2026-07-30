"""Test the /api/coding/assist and /api/research/search endpoints with full traceback."""
import sys
import os
import traceback
import json
import httpx

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check if we can reach the running server or need to use TestClient
import requests

def test_via_requests():
    """Test the endpoints via HTTP if the server is running."""
    base_url = "http://localhost:8000"
    
    # Test health first
    print("=" * 60)
    print("1. Testing /health endpoint...")
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        print(f"   Status: {r.status_code}, Body: {r.json()}")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   Server may not be running. Use TestClient instead.")
        return False
    
    # Test /api/coding/assist
    print("\n" + "=" * 60)
    print("2. Testing POST /api/coding/assist...")
    try:
        payload = {
            "task": "explain",
            "prompt": "What is a Python decorator?",
            "language": "Python",
            "model": "qwen3:4b"
        }
        r = requests.post(f"{base_url}/api/coding/assist", json=payload, timeout=180)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   Task: {data.get('task')}")
            print(f"   Model: {data.get('model')}")
            answer = data.get('answer', '')
            print(f"   Answer (first 200 chars): {answer[:200]}")
        else:
            print(f"   Body: {r.text}")
    except Exception as e:
        print(f"   EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc()
    
    # Test /api/research/search
    print("\n" + "=" * 60)
    print("3. Testing POST /api/research/search...")
    try:
        payload = {
            "query": "What is machine learning?",
            "mode": "web",
            "model": "qwen3:4b",
            "max_sources": 3
        }
        r = requests.post(f"{base_url}/api/research/search", json=payload, timeout=180)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   Query: {data.get('query')}")
            print(f"   Mode: {data.get('mode')}")
            print(f"   Sources count: {len(data.get('sources', []))}")
            summary = data.get('summary', '')
            print(f"   Summary (first 200 chars): {summary[:200]}")
        else:
            print(f"   Body: {r.text}")
    except Exception as e:
        print(f"   EXCEPTION: {type(e).__name__}: {e}")
        traceback.print_exc()
    
    return True

def test_via_testclient():
    """Test endpoints using FastAPI TestClient (no server needed)."""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        print("=" * 60)
        print("1. Testing /health via TestClient...")
        r = client.get("/health")
        print(f"   Status: {r.status_code}, Body: {r.json()}")
        
        # Test /api/coding/assist
        print("\n" + "=" * 60)
        print("2. Testing POST /api/coding/assist via TestClient...")
        try:
            payload = {
                "task": "explain",
                "prompt": "What is a Python decorator?",
                "language": "Python",
                "model": "qwen3:4b"
            }
            r = client.post("/api/coding/assist", json=payload)
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"   Task: {data.get('task')}")
                print(f"   Model: {data.get('model')}")
                answer = data.get('answer', '')
                print(f"   Answer (first 200 chars): {answer[:200]}")
            else:
                print(f"   Body: {r.text}")
        except Exception as e:
            print(f"   EXCEPTION at /api/coding/assist: {type(e).__name__}: {e}")
            traceback.print_exc()
        
        # Test /api/research/search
        print("\n" + "=" * 60)
        print("3. Testing POST /api/research/search via TestClient...")
        try:
            payload = {
                "query": "What is machine learning?",
                "mode": "web",
                "model": "qwen3:4b",
                "max_sources": 3
            }
            r = client.post("/api/research/search", json=payload)
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"   Query: {data.get('query')}")
                print(f"   Mode: {data.get('mode')}")
                print(f"   Sources count: {len(data.get('sources', []))}")
                summary = data.get('summary', '')
                print(f"   Summary (first 200 chars): {summary[:200]}")
            else:
                print(f"   Body: {r.text}")
        except Exception as e:
            print(f"   EXCEPTION at /api/research/search: {type(e).__name__}: {e}")
            traceback.print_exc()
    
    except ImportError as e:
        print(f"Could not import TestClient or main: {e}")
        return False
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING CODING ASSIST AND RESEARCH SEARCH ENDPOINTS")
    print("=" * 60)
    
    # First try HTTP requests (needs server running)
    try:
        print("\n[*] Trying HTTP requests...")
        if test_via_requests():
            print("\n[DONE] HTTP tests completed")
            sys.exit(0)
    except Exception as e:
        print(f"\n[*] HTTP request approach failed: {e}")
    
    # Fall back to TestClient
    print("\n[*] Trying TestClient...")
    test_via_testclient()
    print("\n[DONE] TestClient tests completed")