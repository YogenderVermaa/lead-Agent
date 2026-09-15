"""
Lead exporter module.
Handles writing extracted lead records to CSV format.
"""

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

from .schemas import LeadInfo

logger = logging.getLogger("lead_scraper.exporter")

CSV_FIELDNAMES = [
    "business_name",
    "contact_name",
    "email",
    "phone",
    "website",
    "city",
]


def export_leads_to_csv(
    leads: List[Union[LeadInfo, Dict[str, Any]]],
    output_path: Union[str, Path] = "leads.csv",
    append: bool = False,
) -> Path:
    """
    Export a collection of extracted leads to a CSV file.

    Args:
        leads: List of LeadInfo models or dictionary records.
        output_path: Destination file path for leads.csv.
        append: If True, appends to existing CSV without repeating headers.

    Returns:
        Path: Path to the generated CSV file.
    """
    dest = Path(output_path).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    file_exists = dest.exists() and dest.stat().st_size > 0
    mode = "a" if append else "w"

    normalized_rows = []
    for lead in leads:
        if isinstance(lead, LeadInfo):
            normalized_rows.append(lead.to_dict())
        elif isinstance(lead, dict):
            # Normalize dictionary keys to match CSV fields
            row = {
                "business_name": lead.get("business_name") or lead.get("business name") or lead.get("name") or "",
                "contact_name": lead.get("contact_name") or lead.get("contact name") or lead.get("contact") or "",
                "email": lead.get("email") or "",
                "phone": lead.get("phone") or lead.get("phone_number") or lead.get("telephone") or "",
                "website": lead.get("website") or lead.get("url") or "",
                "city": lead.get("city") or lead.get("location") or "",
            }
            normalized_rows.append(row)

    with open(dest, mode=mode, newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)
        if not append or not file_exists:
            writer.writeheader()
        writer.writerows(normalized_rows)

    logger.info(f"Successfully wrote {len(normalized_rows)} lead record(s) to {dest}")
    return dest
