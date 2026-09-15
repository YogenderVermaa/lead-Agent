import json
import time
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen3:8b",
    base_url="http://localhost:11434",
    format="json",
    temperature=0.0
)

print("Sending test invoke with format='json'...", flush=True)
start = time.time()
res = llm.invoke("Extract business and city as JSON: Acme Corp is based in New York.")
print(f"Elapsed: {time.time() - start:.2f}s", flush=True)
print("Result content:", res.content, flush=True)
