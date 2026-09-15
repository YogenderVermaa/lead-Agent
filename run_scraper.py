"""
Main script for running the ScrapeGraphAI Lead Scraper.
Supports local free Ollama (http://localhost:11434) and cloud models.
Accepts a list of URLs, extracts lead info, and saves output to leads.csv.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from lead_scraper import (
    LeadScraperPipeline,
    export_leads_to_csv,
    get_available_ollama_models,
    load_environment,
)

logger = logging.getLogger("lead_scraper.main")

# Default sample URLs to demonstrate extraction
DEFAULT_URLS = [
    "https://scrapegraphai.com/",
    "https://invalid-nonexistent-domain-test-12345.org/",  # Intentionally invalid to demo error resilience
]


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ScrapeGraphAI Lead Scraper powered by Local Ollama & ScrapeGraphAI."
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        help="List of URLs to scrape for lead information.",
        default=None,
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Path to a text file containing URLs (one per line).",
        default=None,
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="leads.csv",
        help="Output CSV file path (default: leads.csv).",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        help="LLM model identifier (default: auto-detected local Ollama model, e.g. ollama/qwen3:8b).",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434).",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode instead of headless.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output during scraping.",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=300,
        help="Scraping timeout per URL in seconds (default: 300).",
    )

    return parser.parse_args()


def load_urls_from_file(file_path: str) -> List[str]:
    """Read URLs from a text file, ignoring empty lines and comments."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"URLs file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    return urls


def main():
    """Main execution function."""
    args = parse_arguments()

    print("=" * 70)
    print(" ScrapeGraphAI Multi-URL Lead Scraper (Local Ollama Engine)")
    print("=" * 70)

    # Determine model & provider
    target_model = args.model
    if target_model is None or target_model.startswith("ollama"):
        available_models = get_available_ollama_models(args.base_url)
        if available_models:
            if target_model is None:
                target_model = f"ollama/{available_models[0]}"
            print(f"[+] Connected to Local Ollama at {args.base_url}")
            print(f"[+] Available local models: {', '.join(available_models)}")
        else:
            if target_model is None:
                target_model = "ollama/qwen3:8b"
            print(f"[!] Warning: Could not reach Ollama at {args.base_url}, proceeding with default model {target_model}")
    else:
        # Cloud model requested
        api_key = load_environment()
        if api_key:
            masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            print(f"[+] Loaded Cloud API Key from .env: {masked}")

    # Determine URL list
    if args.urls:
        target_urls = args.urls
    elif args.file:
        try:
            target_urls = load_urls_from_file(args.file)
        except Exception as e:
            print(f"[!] Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("[*] No URLs specified via CLI, using demonstration URL list.")
        target_urls = DEFAULT_URLS

    print(f"[+] Target URLs count : {len(target_urls)}")
    for i, u in enumerate(target_urls, 1):
        print(f"    {i}. {u}")

    print(f"[+] LLM Model Engine  : {target_model}")
    print(f"[+] Browser Mode      : {'Headless' if not args.no_headless else 'Visible'}")
    print(f"[+] Output CSV        : {args.output}")
    print("-" * 70)

    # Initialize scraping pipeline
    pipeline = LeadScraperPipeline(
        model_name=target_model,
        base_url=args.base_url,
        headless=not args.no_headless,
        verbose=args.verbose,
        timeout=args.timeout,
    )

    # Run scraping process
    print("[*] Starting extraction process...")
    leads = pipeline.scrape_urls(target_urls)

    print("-" * 70)
    print(f"[+] Scraping finished. Total leads extracted: {len(leads)}")

    # Export results to CSV
    output_file = export_leads_to_csv(leads, output_path=args.output)
    print(f"[+] Successfully saved extracted leads to: {output_file.resolve()}")

    # Display preview table
    if leads:
        print("\n" + "=" * 70)
        print(" Extracted Leads Summary")
        print("=" * 70)
        for idx, lead in enumerate(leads, 1):
            print(f"\n--- Lead #{idx} ---")
            print(f"  Business Name : {lead.business_name or 'N/A'}")
            print(f"  Contact Name  : {lead.contact_name or 'N/A'}")
            print(f"  Email         : {lead.email or 'N/A'}")
            print(f"  Phone         : {lead.phone or 'N/A'}")
            print(f"  Website       : {lead.website or 'N/A'}")
            print(f"  City          : {lead.city or 'N/A'}")
    else:
        print("[!] No lead records were extracted from the provided URLs.")

    print("\n" + "=" * 70)
    print(" Execution Completed Successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
