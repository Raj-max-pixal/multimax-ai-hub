"""
Simplified test to reproduce the exact failure in /api/coding/assist and /api/research/search
with full traceback capture.
"""
import sys
import os
import traceback
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)

# Import the main app
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("=" * 70)
print("TEST 1: POST /api/coding/assist - Expect HTTP 500 with empty error")
print("=" * 70)

try:
    payload = {
        "task": "explain",
        "prompt": "What is a Python decorator?",
        "language": "Python",
        "model": "qwen3:4b"
    }
    print(f"Request payload: {payload}")
    r = client.post("/api/coding/assist", json=payload)
    print(f"Response status: {r.status_code}")
    print(f"Response body: {r.text}")
    print(f"Response headers: {dict(r.headers)}")
except Exception as e:
    print(f"CLIENT EXCEPTION: {type(e).__name__}: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST 2: POST /api/research/search")
print("=" * 70)

try:
    payload = {
        "query": "What is machine learning?",
        "mode": "web",
        "model": "qwen3:4b",
        "max_sources": 3
    }
    print(f"Request payload: {payload}")
    r = client.post("/api/research/search", json=payload)
    print(f"Response status: {r.status_code}")
    print(f"Response body: {r.text}")
    print(f"Response headers: {dict(r.headers)}")
except Exception as e:
    print(f"CLIENT EXCEPTION: {type(e).__name__}: {e}")
    traceback.print_exc()

print("\nDone.")