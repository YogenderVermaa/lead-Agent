import sys
sys.stdout.reconfigure(line_buffering=True)
import json
import requests

print("Connecting to Ollama streaming...", flush=True)
resp = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen3:8b",
        "prompt": "Respond with JSON only: {'status': 'ok'}",
        "stream": True,
        "format": "json"
    },
    stream=True
)

for line in resp.iter_lines():
    if line:
        data = json.loads(line)
        response_text = data.get("response", "")
        print(response_text, end="", flush=True)
        if data.get("done"):
            print(f"\nDone! Total duration: {data.get('total_duration', 0)/1e9:.2f}s", flush=True)
