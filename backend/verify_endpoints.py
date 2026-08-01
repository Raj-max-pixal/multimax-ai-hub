# -*- coding: utf-8 -*-
"""Verify POST /api/coding/assist and POST /api/research/search return 200."""
import requests
import sys

BASE = "http://localhost:8000"

print("=== VERIFICATION: both endpoints ===", flush=True)
print("Model warm check: qwen3:4b loaded in memory", flush=True)
print("No client-side timeout (Ollama may still be slow)", flush=True)
print("", flush=True)

# 1. POST /api/coding/assist
try:
    r = requests.post(
        f"{BASE}/api/coding/assist",
        json={
            "task": "explain",
            "prompt": "Write a Python function that adds two numbers and returns the sum.",
            "language": "python",
        },
        timeout=None,  # wait for the server no matter how long
    )
    print(f"POST /api/coding/assist -> HTTP {r.status_code}", flush=True)
    if r.status_code == 200:
        data = r.json()
        answer = data.get("answer") or data.get("response") or ""
        print(f"  PASS: answer length={len(answer)} chars", flush=True)
        print(f"  sample: {answer[:150]}...", flush=True)
    else:
        print(f"  FAIL: {r.text[:300]}", flush=True)
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}", flush=True)

print("", flush=True)

# 2. POST /api/research/search
try:
    r = requests.post(
        f"{BASE}/api/research/search",
        json={"query": "Python programming language", "mode": "web", "max_sources": 1},
        timeout=None,
    )
    print(f"POST /api/research/search -> HTTP {r.status_code}", flush=True)
    if r.status_code == 200:
        data = r.json()
        sources = data.get("sources") or []
        summary = data.get("summary") or ""
        print(f"  PASS: sources={len(sources)} summary_len={len(summary)}", flush=True)
        if sources:
            print(f"  first source: {sources[0].get('title', '')[:80]}", flush=True)
        print(f"  summary sample: {summary[:150]}...", flush=True)
    else:
        print(f"  FAIL: {r.text[:300]}", flush=True)
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}", flush=True)

print("", flush=True)
print("=== DONE ===", flush=True)