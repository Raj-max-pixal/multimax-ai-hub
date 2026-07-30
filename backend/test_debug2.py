"""
Test the actual endpoint handler code directly to capture the real exception
with full traceback, bypassing FastAPI error handling.
"""
import sys
import os
import traceback
import logging
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)

# Patch the Ollama URL to verify it works first
os.environ["OLLAMA_URL"] = "http://localhost:11434"

# Test Ollama directly first
import httpx
import asyncio

async def test_ollama_direct():
    print("=" * 70)
    print("PRE-TEST: Direct Ollama API call")
    print("=" * 70)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get("http://localhost:11434/api/tags")
            print(f"Ollama /api/tags -> Status: {r.status_code}")
            if r.status_code == 200:
                models = r.json().get("models", [])
                print(f"Models found: {[m['name'] for m in models]}")
            else:
                print(f"Response: {r.text}")
    except Exception as e:
        print(f"Ollama connection failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "qwen3:4b",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say 'OK' and nothing else."},
                    ],
                    "stream": False,
                },
            )
            print(f"\nOllama /api/chat -> Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                content = data.get("message", {}).get("content") or data.get("response") or ""
                print(f"Response content: {content}")
            else:
                print(f"Response: {r.text}")
                return False
    except Exception as e:
        print(f"Ollama chat failed: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False
    
    return True

async def test_coding_assist_direct():
    """Call the actual endpoint logic directly, capturing exceptions."""
    print("\n" + "=" * 70)
    print("TEST 1: Direct call to coding_assist endpoint logic")
    print("=" * 70)
    
    from main import _build_coding_prompt, _ollama_complete, CodingAssistRequest
    
    request = CodingAssistRequest(
        task="explain",
        prompt="What is a Python decorator?",
        language="Python",
        model="qwen3:4b"
    )
    
    try:
        prompt = _build_coding_prompt(request)
        print(f"Built prompt (first 200 chars): {prompt[:200]}")
        
        answer = await _ollama_complete(
            request.model or "qwen3:4b",
            prompt,
            "You are a senior software engineer inside Multimax AI Hub. Prioritize correct, maintainable, secure code.",
        )
        print(f"Answer received! Length: {len(answer)}")
        print(f"Answer (first 300 chars): {answer[:300]}")
        return True
    except Exception as e:
        print(f"EXCEPTION THROWN: {type(e).__name__}: {e}")
        print("FULL TRACEBACK:")
        traceback.print_exc()
        return False

async def test_research_direct():
    """Call the actual research endpoint logic directly, capturing exceptions."""
    print("\n" + "=" * 70)
    print("TEST 2: Direct call to research_search endpoint logic")
    print("=" * 70)
    
    from main import _ollama_complete, ResearchRequest
    
    request = ResearchRequest(
        query="What is machine learning?",
        mode="web",
        model="qwen3:4b",
        max_sources=3
    )
    
    try:
        from main import _search_web
        sources = await _search_web(request.query, request.max_sources)
        print(f"Web search returned {len(sources)} sources")
        for i, s in enumerate(sources):
            print(f"  [{i+1}] {s.title} - {s.url[:60]}...")
        
        source_text = "\n".join(
            f"[{i + 1}] {source.title}\nURL: {source.url}\nSnippet: {source.snippet}"
            for i, source in enumerate(sources)
        )
        prompt = (
            f"Research mode: {request.mode}\n"
            f"Question: {request.query}\n\n"
            f"Sources:\n{source_text}\n\n"
            "Write a helpful answer with: Key answer, Evidence by source number, Uncertainties, and Next searches. "
            "If sources are unavailable, say that clearly and provide a local reasoning-only draft."
        )
        print(f"\nBuilt prompt (first 200 chars): {prompt[:200]}")
        
        summary = await _ollama_complete(
            request.model or "qwen3:4b",
            prompt,
            "You are Multimax Research Engine. Be careful with citations and uncertainty.",
        )
        print(f"\nSummary received! Length: {len(summary)}")
        print(f"Summary (first 300 chars): {summary[:300]}")
        return True
    except Exception as e:
        print(f"EXCEPTION THROWN: {type(e).__name__}: {e}")
        print("FULL TRACEBACK:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("DIRECT ENDPOINT LOGIC TEST - WITH FULL TRACEBACK")
    print("=" * 70)
    
    result = asyncio.run(test_ollama_direct())
    if not result:
        print("\nOllama pre-test FAILED. Aborting.")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("Ollama pre-test PASSED. Now testing endpoint handlers...")
    print("=" * 70)
    
    result1 = asyncio.run(test_coding_assist_direct())
    result2 = asyncio.run(test_research_direct())
    
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"Coding Assist: {'PASSED' if result1 else 'FAILED'}")
    print(f"Research Search: {'PASSED' if result2 else 'FAILED'}")