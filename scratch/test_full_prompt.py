import sys
sys.stdout.reconfigure(line_buffering=True)
import json
import requests
import time

prompt = """You are a website scraper and you have just scraped the following content from a website converted in markdown format.
You are now asked to answer a user question about the content you have scraped.

OUTPUT INSTRUCTIONS: The output should be formatted as a JSON instance that conforms to the JSON schema below.
{"properties": {"business_name": {"title": "Business Name", "type": "string"}, "contact_name": {"title": "Contact Name", "type": "string"}, "email": {"title": "Email", "type": "string"}, "phone": {"title": "Phone", "type": "string"}, "website": {"title": "Website", "type": "string"}, "city": {"title": "City", "type": "string"}}, "required": ["business_name", "contact_name", "email", "phone", "website", "city"]}

USER QUESTION: Extract business_name, contact_name, email, phone, website, city from the website.
WEBSITE CONTENT: # Example Domain\n\nThis domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission.\n\n[More information...](https://www.iana.org/domains/example)
"""

print("Sending prompt to Ollama /api/chat...", flush=True)
t0 = time.time()
resp = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen3:8b",
        "messages": [{"role": "user", "content": prompt}],
        "format": "json",
        "stream": True,
        "options": {
            "temperature": 0.0,
        }
    },
    stream=True
)

full_content = ""
for line in resp.iter_lines():
    if line:
        data = json.loads(line)
        msg = data.get("message", {}).get("content", "")
        full_content += msg
        print(msg, end="", flush=True)
        if data.get("done"):
            print(f"\nDone! Time: {time.time()-t0:.2f}s", flush=True)

print("\nResult received:", full_content)
