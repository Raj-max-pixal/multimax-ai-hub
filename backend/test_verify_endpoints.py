"""Verify /api/coding/assist and /api/research/search return 200."""
import json
import requests

BASE = "http://localhost:8004"
results = {}

# 1. Test /api/coding/assist
try:
    r = requests.post(
        f"{BASE}/api/coding/assist",
        json={
            "task": "explain",
            "prompt": "Write a Python function to add two numbers",
            "language": "python",
        },
        timeout=600,
    )
    results["coding/assist"] = {
        "status": r.status_code,
        "ok": r.status_code == 200,
        "body_preview": r.text[:400],
    }
except Exception as e:
    results["coding/assist"] = {"status": "EXCEPTION", "error": str(e)}

# 2. Test /api/research/search
try:
    r = requests.post(
        f"{BASE}/api/research/search",
        json={
            "query": "Python programming language",
            "mode": "web",
            "max_sources": 2,
        },
        timeout=600,
    )
    results["research/search"] = {
        "status": r.status_code,
        "ok": r.status_code == 200,
        "body_preview": r.text[:400],
    }
except Exception as e:
    results["research/search"] = {"status": "EXCEPTION", "error": str(e)}

print(json.dumps(results, indent=2))

with open("verify_results.json", "w") as f:
    json.dump(results, f, indent=2)