"""
Core scraper engine wrapping ScrapeGraphAI's SmartScraperMultiGraph.
Provides robust multi-URL lead extraction with per-URL error isolation and resilience.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from scrapegraphai.graphs import SmartScraperGraph, SmartScraperMultiGraph

from .config import get_graph_config
from .schemas import LeadInfo, LeadList
from .utils import filter_valid_urls, validate_and_normalize_url

logger = logging.getLogger("lead_scraper.scraper")

DEFAULT_PROMPT = (
    "Extract the contact and business details from the website. "
    "Specifically extract: "
    "1. business_name: The company or organization name. "
    "2. contact_name: The name of the primary contact person, owner, or executive if mentioned. "
    "3. email: The contact or support email address. "
    "4. phone: The telephone or phone number. "
    "5. website: The official website URL. "
    "6. city: The city or locality where the business is located. "
    "If any field cannot be found on the page, return null or empty string for that field."
)


class LeadScraperPipeline:
    """
    Modular scraping pipeline for extracting business and contact leads from multiple URLs.
    Uses ScrapeGraphAI's SmartScraperMultiGraph and handles invalid or failing URLs gracefully.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        prompt: str = DEFAULT_PROMPT,
        model_name: Optional[str] = None,
        base_url: str = "http://localhost:11434",
        headless: bool = True,
        verbose: bool = False,
        timeout: int = 60,
    ):
        """
        Initialize the LeadScraperPipeline.

        Args:
            config: Optional pre-built ScrapeGraphAI configuration dictionary.
            prompt: Extraction prompt instructing the LLM on target fields.
            model_name: LLM identifier (defaults to auto-detected local Ollama model).
            base_url: Ollama base server URL.
            headless: Whether browser runs headless.
            verbose: Verbose logging flag.
            timeout: Page fetch timeout in seconds.
        """
        self.prompt = prompt
        if config is not None:
            self.config = config
        else:
            self.config = get_graph_config(
                model_name=model_name,
                base_url=base_url,
                headless=headless,
                verbose=verbose,
                timeout=timeout,
            )

    def scrape_single_url(self, url: str) -> Optional[LeadInfo]:
        """
        Scrape a single URL using SmartScraperGraph with full error isolation.

        Args:
            url: Target website URL.

        Returns:
            Optional[LeadInfo]: Extracted lead information, or None if scraping failed.
        """
        is_valid, normalized_url, reason = validate_and_normalize_url(url)
        if not is_valid:
            logger.warning(f"Skipping invalid URL '{url}': {reason}")
            return None

        try:
            logger.info(f"Scraping single URL: {normalized_url}")
            graph = SmartScraperGraph(
                prompt=self.prompt,
                source=normalized_url,
                config=self.config,
                schema=LeadInfo,
            )
            raw_result = graph.run()
            return self._parse_lead_result(raw_result, fallback_url=normalized_url)
        except Exception as exc:
            logger.error(f"Failed to scrape URL '{normalized_url}': {exc}", exc_info=False)
            return None

    def scrape_urls(
        self,
        urls: List[str],
        use_multigraph: bool = True,
        fallback_to_individual: bool = True,
    ) -> List[LeadInfo]:
        """
        Scrape lead information across a list of URLs using SmartScraperMultiGraph.
        Handles failed or invalid URLs without stopping the entire process.

        Args:
            urls: List of target website URLs.
            use_multigraph: If True, uses SmartScraperMultiGraph to batch process URLs.
            fallback_to_individual: If True, falls back to per-URL scraping if multi-graph fails.

        Returns:
            List[LeadInfo]: List of extracted lead records.
        """
        if not urls:
            logger.warning("No URLs provided to scrape.")
            return []

        valid_urls, invalid_urls = filter_valid_urls(urls)

        if not valid_urls:
            logger.warning("No valid URLs remain after filtering invalid entries.")
            return []

        logger.info(f"Starting lead extraction for {len(valid_urls)} valid URL(s) (Skipped {len(invalid_urls)} invalid).")

        extracted_leads: List[LeadInfo] = []

        if use_multigraph and len(valid_urls) > 1:
            try:
                logger.info(f"Executing SmartScraperMultiGraph on {len(valid_urls)} URLs...")
                multi_graph = SmartScraperMultiGraph(
                    prompt=self.prompt,
                    source=valid_urls,
                    config=self.config,
                    schema=LeadList,
                )
                raw_result = multi_graph.run()

                parsed_leads = self._parse_multi_graph_result(raw_result, valid_urls)
                if parsed_leads:
                    extracted_leads.extend(parsed_leads)
                    return extracted_leads
                else:
                    logger.warning("SmartScraperMultiGraph returned empty or unparseable result, attempting individual fallback...")
            except Exception as exc:
                logger.error(
                    f"SmartScraperMultiGraph batch execution encountered error: {exc}. "
                    f"Proceeding with resilient per-URL execution to avoid losing data.",
                    exc_info=False,
                )

        # Fallback / Per-URL sequential processing for maximum error tolerance
        if not extracted_leads and (fallback_to_individual or len(valid_urls) == 1):
            logger.info("Processing URLs with isolated per-URL scraping for maximum fault tolerance...")
            for idx, target_url in enumerate(valid_urls, 1):
                logger.info(f"[{idx}/{len(valid_urls)}] Processing: {target_url}")
                lead = self.scrape_single_url(target_url)
                if lead:
                    extracted_leads.append(lead)
                else:
                    logger.warning(f"[{idx}/{len(valid_urls)}] Extraction failed or returned empty for: {target_url}")

        logger.info(f"Extraction completed. Total leads collected: {len(extracted_leads)}")
        return extracted_leads

    def _parse_lead_result(self, raw_result: Any, fallback_url: str = "") -> Optional[LeadInfo]:
        """Parse raw ScrapeGraphAI output into a LeadInfo object."""
        if not raw_result:
            return None

        if isinstance(raw_result, LeadInfo):
            if not raw_result.website and fallback_url:
                raw_result.website = fallback_url
            return raw_result

        if isinstance(raw_result, dict):
            if "leads" in raw_result and isinstance(raw_result["leads"], list) and raw_result["leads"]:
                return self._parse_lead_result(raw_result["leads"][0], fallback_url)

            data = {
                "business_name": raw_result.get("business_name") or raw_result.get("business name") or raw_result.get("name"),
                "contact_name": raw_result.get("contact_name") or raw_result.get("contact name") or raw_result.get("contact"),
                "email": raw_result.get("email"),
                "phone": raw_result.get("phone") or raw_result.get("phone_number") or raw_result.get("telephone"),
                "website": raw_result.get("website") or raw_result.get("url") or fallback_url,
                "city": raw_result.get("city") or raw_result.get("location"),
            }
            return LeadInfo(**data)

        return None

    def _parse_multi_graph_result(self, raw_result: Any, urls: List[str]) -> List[LeadInfo]:
        """Parse SmartScraperMultiGraph output dictionary into a list of LeadInfo objects."""
        results: List[LeadInfo] = []
        if not raw_result:
            return results

        if isinstance(raw_result, LeadList):
            return raw_result.leads

        if isinstance(raw_result, list):
            for item in raw_result:
                parsed = self._parse_lead_result(item)
                if parsed:
                    results.append(parsed)
            return results

        if isinstance(raw_result, dict):
            if "leads" in raw_result and isinstance(raw_result["leads"], list):
                for item in raw_result["leads"]:
                    parsed = self._parse_lead_result(item)
                    if parsed:
                        results.append(parsed)
                return results

            parsed = self._parse_lead_result(raw_result)
            if parsed:
                results.append(parsed)

        return results
