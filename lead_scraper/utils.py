"""
Utility functions for URL validation, sanitization, and logging.
"""

import logging
import re
from typing import List, Tuple
from urllib.parse import urlparse

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lead_scraper")

# Basic regex pattern for domain validation
URL_REGEX = re.compile(
    r"^(https?:\/\/)?"  # optional scheme
    r"(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})"  # domain
    r"(:\d+)?"  # optional port
    r"(\/.*)?$",  # optional path
    re.IGNORECASE
)


def validate_and_normalize_url(raw_url: str) -> Tuple[bool, str, str]:
    """
    Validate and normalize a URL string.

    Args:
        raw_url: Raw input URL string.

    Returns:
        Tuple[bool, str, str]: (is_valid, normalized_url, reason_or_error)
    """
    if not raw_url or not isinstance(raw_url, str):
        return False, "", "Empty or non-string URL provided."

    cleaned = raw_url.strip()
    if not cleaned:
        return False, "", "Empty URL after stripping whitespace."

    # Prepend https:// if no scheme is provided
    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned

    try:
        parsed = urlparse(cleaned)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            return False, cleaned, f"Unsupported URL scheme: {parsed.scheme}"
        if not parsed.netloc or "." not in parsed.netloc:
            return False, cleaned, f"Invalid domain structure: {parsed.netloc}"

        return True, cleaned, ""
    except Exception as exc:
        return False, cleaned, f"Malformed URL syntax: {str(exc)}"


def filter_valid_urls(urls: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Separate a list of URLs into valid normalized URLs and invalid URLs with failure reasons.

    Args:
        urls: List of input URLs.

    Returns:
        Tuple[List[str], List[Tuple[str, str]]]:
            - List of valid normalized URLs
            - List of tuples (invalid_url, error_reason)
    """
    valid_urls: List[str] = []
    invalid_urls: List[Tuple[str, str]] = []

    for raw in urls:
        is_valid, normalized, reason = validate_and_normalize_url(raw)
        if is_valid:
            valid_urls.append(normalized)
        else:
            logger.warning(f"Skipping invalid URL '{raw}': {reason}")
            invalid_urls.append((raw, reason))

    return valid_urls, invalid_urls
