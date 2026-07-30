import asyncio
import json
import urllib.request
import urllib.error
import sys

BASE = "http://localhost:8001"

async def test_endpoint(name: str, endpoint: str, payload: dict, timeout: int = 300):
    print(f"\n=== Testing {name} ===")
    try:
        req = urllib.request.Request(
            f"{BASE}{endpoint}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        # Use async-compatible approach via run_in_executor
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: urllib.request.urlopen(req, timeout=timeout)
        )
        status = resp.status
        body = resp.read().decode()
        print(f"Status: {status}")
        if status == 200:
            data = json.loads(body)
            if "answer" in data:
                print(f"Answer length: {len(data['answer'])} chars")
                print(f"Answer preview: {data['answer'][:200]}...")
            elif "summary" in data:
                print(f"Summary length: {len(data['summary'])} chars")
                print(f"Summary preview: {data['summary'][:200]}...")
            return True, data
        else:
            print(f"FAILED: {body[:500]}")
            return False, body
    except Exception as e:
        print(f"EXCEPTION: {type(e).__name__}: {e}")
        return False, str(e)

async def main():
    # Test 1: Health check
    try:
        req = urllib.request.Request(f"{BASE}/health")
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"\nHealth: {resp.status} - {resp.read().decode()}")
    except Exception as e:
        print(f"Health failed: {e}")
        sys.exit(1)

    # Test 2: coding/assist
    success1, _ = await test_endpoint(
        "coding_assist (explain 2+2)",
        "/api/coding/assist",
        {"task": "explain", "prompt": "What is 2+2 in Python?", "language": "Python"},
        timeout=600
    )

    # Test 3: research/search
    success2, _ = await test_endpoint(
        "research_search (simple query)",
        "/api/research/search",
        {"query": "What is Python?", "mode": "web", "max_sources": 3},
        timeout=600
    )

    print(f"\n\n=== RESULTS ===")
    print(f"coding/assist: {'PASS' if success1 else 'FAIL'}")
    print(f"research/search: {'PASS' if success2 else 'FAIL'}")

    if success1 and success2:
        print("\nAll endpoints return 200!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())