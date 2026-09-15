import sys
sys.stdout.reconfigure(line_buffering=True)
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen3:8b", base_url="http://localhost:11434", temperature=0.0)
print("Sending test message...", flush=True)
msg = llm.invoke("Hello, respond with 1 word: OK")
print("Got msg:", repr(msg), flush=True)
print("Content:", repr(msg.content), flush=True)
