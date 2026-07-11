import httpx
import json

# Test backend chat endpoint
r = httpx.post('http://localhost:8000/api/chat', json={
    'model': 'phi3:latest',
    'messages': [{'role': 'user', 'content': 'Say hello in one word'}]
})
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:1000]}")