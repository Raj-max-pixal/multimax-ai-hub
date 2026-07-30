"""
Quick test of the endpoints with short prompts.
Uses asyncio to call the endpoint functions directly 
and captures full traceback.
"""
import sys
import os
import asyncio
import traceback
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    # First, health-check Ollama directly
    print("=== CHECKING OLLAMA DIRECTLY ===")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("http://localhost:11434/api/tags")
            print(f"Ollama /api/tags: {r.status_code}")
            models = [m["name"] for m in r.json().get("models", [])]
            print(f"Models: {models}")
            if "qwen3:4b" not in models:
                print("WARNING: qwen3:4b not found!")
    except Exception as e:
        print(f"Ollama connection ERROR: {type(e).__name__}: {e}")
    
    # Test with a tiny prompt to get quick response
    print("\n=== TEST 1: _ollama_complete (simple) ===")
    from main import _ollama_complete
    try:
        result = await _ollama_complete(
            "qwen3:4b",
            "Say only the word: OK",
            "You are helpful."
        )
        print(f"OK - got {len(result)} chars: {result[:50]}")
    except Exception as e:
        print(f"EXCEPTION in _ollama_complete: {type(e).__name__}: {e}")
        traceback.print_exc()
    
    print("\n=== TEST 2: coding_assist ===")
    from main import coding_assist, CodingAssistRequest
    req = CodingAssistRequest(task="explain", prompt="What is a function?", language="Python", model="qwen3:4b")
    try:
        result = await coding_assist(req)
        print(f"OK - status 200, answer len={len(result.get('answer',''))}")
    except Exception as e:
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"EXCEPTION STR: '{str(e)}'")
        print(f"EXCEPTION ARGS: {e.args}")
        traceback.print_exc()
    
    print("\n=== TEST 3: research_search (no web) ===")
    from main import research_search, ResearchRequest
    from unittest.mock import patch, AsyncMock
    
    with patch('main._search_web', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []
        req2 = ResearchRequest(query="What is AI?", mode="web", model="qwen3:4b", max_sources=2)
        try:
            result = await research_search(req2)
            print(f"OK - status 200, summary len={len(result.get('summary',''))}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP ERROR: {e.response.status_code}: {e.response.text}")
        except HTTPException as e:
            print(f"HTTPException: {e.status_code}: {e.detail}")
        except Exception as e:
            print(f"EXCEPTION TYPE: {type(e).__name__}")
            print(f"EXCEPTION STR: '{str(e)}'")
            traceback.print_exc()
    
    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(main())