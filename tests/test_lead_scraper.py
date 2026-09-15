"""
Tests for lead_scraper package components:
- Schemas & serialization
- URL validation and filtering
- CSV exporter
- Graph configuration builder
- Pipeline error isolation
"""

import csv
import os
import tempfile
from pathlib import Path
import pytest

from lead_scraper.config import get_graph_config, load_environment
from lead_scraper.exporter import CSV_FIELDNAMES, export_leads_to_csv
from lead_scraper.schemas import LeadInfo, LeadList
from lead_scraper.scraper import LeadScraperPipeline
from lead_scraper.utils import filter_valid_urls, validate_and_normalize_url


def test_lead_info_schema():
    """Test LeadInfo model creation and dict conversion."""
    lead = LeadInfo(
        business_name="ScrapeGraphAI Corp",
        contact_name="Marco Vinciguerra",
        email="contact@scrapegraphai.com",
        phone="+1-555-0199",
        website="https://scrapegraphai.com",
        city="San Francisco"
    )

    data = lead.to_dict()
    assert data["business_name"] == "ScrapeGraphAI Corp"
    assert data["contact_name"] == "Marco Vinciguerra"
    assert data["email"] == "contact@scrapegraphai.com"
    assert data["phone"] == "+1-555-0199"
    assert data["website"] == "https://scrapegraphai.com"
    assert data["city"] == "San Francisco"


def test_lead_info_defaults():
    """Test default values for missing fields in LeadInfo."""
    lead = LeadInfo(business_name="Acme Inc")
    data = lead.to_dict()
    assert data["business_name"] == "Acme Inc"
    assert data["contact_name"] == ""
    assert data["email"] == ""
    assert data["phone"] == ""
    assert data["website"] == ""
    assert data["city"] == ""


def test_url_validation():
    """Test URL validator with various valid and invalid formats."""
    # Valid with scheme
    valid, url, _ = validate_and_normalize_url("https://scrapegraphai.com/docs")
    assert valid is True
    assert url == "https://scrapegraphai.com/docs"

    # Valid without scheme (should prepend https://)
    valid, url, _ = validate_and_normalize_url("scrapegraphai.com")
    assert valid is True
    assert url == "https://scrapegraphai.com"

    # Invalid URLs
    valid, _, reason = validate_and_normalize_url("")
    assert valid is False

    valid, _, reason = validate_and_normalize_url("not_a_valid_url")
    assert valid is False


def test_filter_valid_urls():
    """Test filtering a mixed list of valid and invalid URLs."""
    raw_urls = [
        "https://scrapegraphai.com",
        "invalid url here",
        "http://example.com/contact",
        "   ",
    ]
    valid, invalid = filter_valid_urls(raw_urls)
    assert len(valid) == 2
    assert "https://scrapegraphai.com" in valid
    assert "http://example.com/contact" in valid
    assert len(invalid) == 2


def test_csv_export():
    """Test exporting leads to CSV and verify headers and content."""
    leads = [
        LeadInfo(
            business_name="Company Alpha",
            contact_name="Alice Smith",
            email="alice@alpha.com",
            phone="123-456-7890",
            website="https://alpha.com",
            city="New York",
        ),
        LeadInfo(
            business_name="Company Beta",
            contact_name="Bob Jones",
            email="bob@beta.com",
            phone="987-654-3210",
            website="https://beta.com",
            city="Chicago",
        ),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_leads.csv"
        export_leads_to_csv(leads, output_path=csv_path)

        assert csv_path.exists()
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == CSV_FIELDNAMES
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]["business_name"] == "Company Alpha"
            assert rows[0]["city"] == "New York"
            assert rows[1]["business_name"] == "Company Beta"
            assert rows[1]["city"] == "Chicago"


def test_graph_config():
    """Test graph configuration generation with Gemini 2.5 Flash-Lite."""
    config = get_graph_config(
        model_name="google_genai/gemini-2.5-flash-lite",
        headless=True,
        timeout=45,
        api_key="test_api_key_123",
        model_tokens=1000000
    )

    assert config["llm"]["model"] == "google_genai/gemini-2.5-flash-lite"
    assert config["llm"]["api_key"] == "test_api_key_123"
    assert config["llm"]["model_tokens"] == 1000000
    assert config["headless"] is True
    assert config["timeout"] == 45


def test_scrapegraphai_version_check():
    """Test retrieving installed ScrapeGraphAI version."""
    from lead_scraper.config import get_scrapegraphai_version
    version = get_scrapegraphai_version()
    assert version is not None
    assert version != "unknown"



def test_pipeline_resilience_on_empty_and_invalid_urls():
    """Test that pipeline handles empty and invalid URLs gracefully without crashing."""
    pipeline = LeadScraperPipeline(
        config={
            "llm": {"model": "google_genai/gemini-2.5-flash-lite", "api_key": "dummy_key"},
            "headless": True,
            "verbose": False,
        }
    )

    # Empty list
    results = pipeline.scrape_urls([])
    assert results == []

    # Only invalid URLs
    results = pipeline.scrape_urls(["not-a-valid-url-12345", ""])
    assert results == []
