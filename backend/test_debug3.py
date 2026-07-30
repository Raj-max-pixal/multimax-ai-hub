"""
Bypass FastAPI error handling - directly call endpoint handler functions
with mocked Ollama to capture the exact exception.
"""
import sys
import os
import traceback
import logging
import asyncio
from unittest.mock import patch, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)

async def test_coding_assist():
    """Directly call the coding_assist handler with mocked Ollama."""
    from main import coding_assist, CodingAssistRequest
    
    request = CodingAssistRequest(
        task="explain",
        prompt="What is a Python decorator?",
        language="Python",
        model="qwen3:4b"
    )
    
    # Set up mock to make _ollama_complete return quickly if it's called
    with patch('main._ollama_complete', new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = "Mock answer"
        
        try:
            result = await coding_assist(request)
            print(f"SUCCESS: {result}")
            return True
        except Exception as e:
            print(f"EXCEPTION TYPE: {type(e).__name__}")
            print(f"EXCEPTION ARGS: {e.args}")
            print(f"EXCEPTION STR: {str(e)}")
            print("\nFULL TRACEBACK:")
            traceback.print_exc()
            return False

async def test_research_search():
    """Directly call the research_search handler with mocked Ollama."""
    from main import research_search, ResearchRequest, _search_web, _extract_duckduckgo_results
    
    request = ResearchRequest(
        query="What is machine learning?",
        mode="web",
        model="qwen3:4b",
        max_sources=3
    )
    
    # Set up mock for both Ollama and web search
    with patch('main._ollama_complete', new_callable=AsyncMock) as mock_ollama:
        mock_ollama.return_value = "Mock research summary"
        
        with patch('main._search_web', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            
            try:
                result = await research_search(request)
                print(f"SUCCESS: {result}")
                return True
            except Exception as e:
                print(f"EXCEPTION TYPE: {type(e).__name__}")
                print(f"EXCEPTION ARGS: {e.args}")
                print(f"EXCEPTION STR: {str(e)}")
                print("\nFULL TRACEBACK:")
                traceback.print_exc()
                return False

async def test_coding_assist_no_mock():
    """Call with actual Ollama - will be slow but real."""
    from main import coding_assist, CodingAssistRequest
    
    request = CodingAssistRequest(
        task="explain",
        prompt="What is a Python decorator?",
        language="Python",
        model="qwen3:4b"
    )
    
    print(f"Calling coding_assist with model={request.model}...")
    try:
        result = await coding_assist(request)
        print(f"SUCCESS: Status 200")
        print(f"Answer length: {len(result.get('answer', ''))}")
        return True
    except Exception as e:
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"EXCEPTION ARGS: {e.args}")
        print(f"EXCEPTION STR: '{str(e)}'")
        print("\nFULL TRACEBACK:")
        traceback.print_exc()
        return False

async def test_research_no_mock():
    """Call with actual Ollama - will be slow but real."""
    from main import research_search, ResearchRequest
    
    request = ResearchRequest(
        query="What is machine learning?",
        mode="web",
        model="qwen3:4b",
        max_sources=2
    )
    
    print(f"Calling research_search with model={request.model}...")
    try:
        result = await research_search(request)
        print(f"SUCCESS: Status 200")
        print(f"Summary length: {len(result.get('summary', ''))}")
        print(f"Sources: {len(result.get('sources', []))}")
        return True
    except Exception as e:
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"EXCEPTION ARGS: {e.args}")
        print(f"EXCEPTION STR: '{str(e)}'")
        print("\nFULL TRACEBACK:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("TEST 1: coding_assist with MOCKED Ollama (fast)")
    print("=" * 70)
    r1 = asyncio.run(test_coding_assist())
    
    print("\n" + "=" * 70)
    print("TEST 2: research_search with MOCKED Ollama (fast)")
    print("=" * 70)
    r2 = asyncio.run(test_research_search())
    
    if r1 and r2:
        print("\n" + "=" * 70)
        print("Mock tests passed. Now trying REAL Ollama calls...")
        print("=" * 70)
        r3 = asyncio.run(test_coding_assist_no_mock())
        r4 = asyncio.run(test_research_no_mock())
        
        print("\n" + "=" * 70)
        print("FINAL RESULTS")
        print("=" * 70)
        print(f"Coding Assist (mock): {'PASS' if r1 else 'FAIL'}")
        print(f"Research Search (mock): {'PASS' if r2 else 'FAIL'}")
        print(f"Coding Assist (real): {'PASS' if r3 else 'FAIL'}")
        print(f"Research Search (real): {'PASS' if r4 else 'FAIL'}")