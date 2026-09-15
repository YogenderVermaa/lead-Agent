"""
Lead extraction schemas using Pydantic.
Defines the structure for extracting lead information from websites.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LeadInfo(BaseModel):
    """Schema representing contact and business lead information extracted from a website."""

    business_name: Optional[str] = Field(
        default=None,
        description="The official legal or trade name of the business or company."
    )
    contact_name: Optional[str] = Field(
        default=None,
        description="Name of the primary contact person, founder, owner, or executive if available."
    )
    email: Optional[str] = Field(
        default=None,
        description="Official contact or support email address found on the website."
    )
    phone: Optional[str] = Field(
        default=None,
        description="Contact telephone or mobile phone number."
    )
    website: Optional[str] = Field(
        default=None,
        description="The website URL of the business."
    )
    city: Optional[str] = Field(
        default=None,
        description="City or locality where the business is headquartered or located."
    )

    def to_dict(self) -> dict:
        """Convert lead info to a clean dictionary for CSV export."""
        return {
            "business_name": self.business_name or "",
            "contact_name": self.contact_name or "",
            "email": self.email or "",
            "phone": self.phone or "",
            "website": self.website or "",
            "city": self.city or "",
        }


class LeadList(BaseModel):
    """Container schema for multiple leads extracted across pages or directories."""

    leads: List[LeadInfo] = Field(
        default_factory=list,
        description="List of extracted leads from the scraped sources."
    )
