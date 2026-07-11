import httpx
import json

# Test direct Ollama connection
r = httpx.post('http://localhost:11434/api/chat', 
    json={'model': 'phi3:latest', 'messages': [{'role': 'user', 'content': 'Hello'}], 'stream': False}, 
    timeout=30)
print("Status:", r.status_code)
print("Response:", json.dumps(r.json(), indent=2))