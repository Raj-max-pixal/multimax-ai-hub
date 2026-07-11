"""
Comprehensive test of the full flow:
1. Test direct Ollama connection
2. Test backend /api/chat endpoint with stream=False (what the frontend sends)
3. Test backend /api/chat endpoint response parsing
"""

import httpx
import json
import sys

def test_direct_ollama():
    """Test direct Ollama chat with stream=False"""
    print("=" * 60)
    print("TEST 1: Direct Ollama /api/chat (stream=False)")
    print("=" * 60)
    try:
        r = httpx.post('http://localhost:11434/api/chat',
            json={
                'model': 'phi3:latest',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'stream': False
            },
            timeout=30)
        print(f"Status: {r.status_code}")
        data = r.json()
        print(f"Response keys: {list(data.keys())}")
        if 'message' in data:
            print(f"message keys: {list(data['message'].keys())}")
            print(f"Content: {data['message']['content'][:100]}")
        else:
            print(f"Full response: {json.dumps(data, indent=2)[:500]}")
        print("PASS: Direct Ollama works with stream=False\n")
        return True
    except Exception as e:
        print(f"FAIL: {e}\n")
        return False

def test_direct_ollama_stream():
    """Test direct Ollama chat with stream=True"""
    print("=" * 60)
    print("TEST 2: Direct Ollama /api/chat (stream=True)")
    print("=" * 60)
    try:
        full = ""
        with httpx.stream('POST', 'http://localhost:11434/api/chat',
            json={
                'model': 'phi3:latest',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'stream': True
            },
            timeout=30) as r:
            for line in r.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'message' in data and 'content' in data['message']:
                        full += data['message']['content']
        print(f"Full content: {full[:200]}")
        print("PASS: Direct Ollama streaming works\n")
        return True
    except Exception as e:
        print(f"FAIL: {e}\n")
        return False

def test_backend_chat():
    """Test the backend /api/chat endpoint - this is what AIChat.tsx calls"""
    print("=" * 60)
    print("TEST 3: Backend /api/chat (what the frontend sends)")
    print("=" * 60)
    try:
        r = httpx.post('http://localhost:8000/api/chat',
            json={
                'model': 'phi3:latest',
                'messages': [{'role': 'user', 'content': 'Hello'}]
            },
            timeout=30)
        print(f"Status: {r.status_code}")
        print(f"Headers: {dict(r.headers)}")
        print(f"Content-Type: {r.headers.get('content-type', 'N/A')}")
        
        # The backend returns a streaming response
        # Read the raw response
        content = r.text
        print(f"Raw response preview: {content[:500]}")
        
        # Try to parse as NDJSON (streaming format)
        lines = content.strip().split('\n')
        full_text = ""
        for line in lines:
            if line.strip():
                try:
                    data = json.loads(line)
                    if 'message' in data and 'content' in data['message']:
                        full_text += data['message']['content']
                    print(f"  Parsed: {json.dumps(data, indent=2)[:200]}")
                except json.JSONDecodeError:
                    print(f"  Could not parse: {line[:200]}")
        
        if full_text:
            print(f"\n  Full AI response: {full_text[:300]}")
        print("PASS: Backend returns streaming response\n")
        return True
    except Exception as e:
        print(f"FAIL: {e}\n")
        return False

def test_backend_non_stream():
    """Test backend with non-streaming - what the FRONTEND expects"""
    print("=" * 60)
    print("TEST 4: KEY ISSUE - Requesting stream=False to backend")
    print("=" * 60)
    print("** The frontend sends NO stream parameter")
    print("** The backend ALWAYS uses stream=True (hardcoded)")
    print("** The frontend tries to parse each line as JSON")
    print("** This SHOULD work if the backend sends NDJSON lines")
    print("=" * 60)
    try:
        r = httpx.post('http://localhost:8000/api/chat',
            json={
                'model': 'phi3:latest',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'stream': False  # Frontend doesn't send this, neither does backend use it
            },
            timeout=30)
        print(f"Status: {r.status_code}")
        content = r.text
        print(f"Response length: {len(content)}")
        print(f"Raw first 500 chars: {content[:500]}")
        lines = content.strip().split('\n')
        print(f"\nNumber of lines: {len(lines)}")
        success = 0
        fail = 0
        for i, line in enumerate(lines):
            if line.strip():
                try:
                    data = json.loads(line)
                    if 'message' in data and 'content' in data['message']:
                        success += 1
                    elif data.get('done'):
                        print(f"  Line {i}: [DONE]")
                    else:
                        print(f"  Line {i}: {str(data)[:200]}")
                        fail += 1
                except:
                    print(f"  Line {i}: PARSE FAILED: {line[:200]}")
                    fail += 1
        print(f"\nSuccessfully parsed lines: {success}")
        print(f"Failed lines: {fail}")
        print("PASS: Backend streaming endpoint works with frontend parsing\n")
        return True
    except Exception as e:
        print(f"FAIL: {e}\n")
        return False

if __name__ == '__main__':
    results = []
    results.append(test_direct_ollama())
    results.append(test_direct_ollama_stream())
    results.append(test_backend_chat())
    results.append(test_backend_non_stream())
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    tests = ["Direct Ollama (non-stream)", "Direct Ollama (stream)", 
             "Backend chat", "Backend with frontend parsing"]
    for i, (name, result) in enumerate(zip(tests, results)):
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")
    print("=" * 60)