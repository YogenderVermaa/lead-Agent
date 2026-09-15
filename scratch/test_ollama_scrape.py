import sys
sys.stdout.reconfigure(line_buffering=True)
import time
from scrapegraphai.graphs import SmartScraperGraph
from lead_scraper.config import get_graph_config
from lead_scraper.schemas import LeadInfo

config = get_graph_config(
    model_name="ollama/qwen3:8b",
    base_url="http://localhost:11434",
    headless=True,
    verbose=True,
)

print("Graph config:", config, flush=True)

prompt = (
    "Extract the business details from the website. "
    "Fields: business_name, contact_name, email, phone, website, city. "
    "If not found, use null or empty string."
)

url = "https://example.com"
print(f"\n[*] Scraping {url} with Ollama (qwen3:8b)...", flush=True)
t0 = time.time()
graph = SmartScraperGraph(
    prompt=prompt,
    source=url,
    config=config,
    schema=LeadInfo,
)
result = graph.run()
t1 = time.time()
print(f"[+] Scraping finished in {t1 - t0:.2f}s", flush=True)
print("[+] Extracted Result:", result, flush=True)
