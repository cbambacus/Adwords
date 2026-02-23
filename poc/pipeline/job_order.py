"""
Job order parser and validator.

Parses JSON job orders from Cloudwall and validates them using Pydantic models.
Extracts classification signals (seniority, role type, urgency, geo tier).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class Salary(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "USD"
    type: str = "annual"

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"annual", "hourly"}
        if v.lower() not in allowed:
            raise ValueError(f"salary type must be one of {allowed}")
        return v.lower()


class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "USA"


class JobOrder(BaseModel):
    """Validated job order from Cloudwall."""

    job_id: str
    job_title: str = Field(min_length=1)
    job_description: str = Field(min_length=1)
    salary: Optional[Salary] = None
    location: Location
    work_arrangement: str
    client: Optional[str] = None
    employment_type: Optional[str] = None
    duration_months: Optional[int] = None
    start_date: Optional[str] = None
    additional_notes: Optional[str] = None

    @field_validator("work_arrangement")
    @classmethod
    def validate_work_arrangement(cls, v: str) -> str:
        allowed = {"remote", "hybrid", "onsite"}
        if v.lower() not in allowed:
            raise ValueError(f"work_arrangement must be one of {allowed}")
        return v.lower()

    @model_validator(mode="after")
    def validate_location_for_arrangement(self):
        if self.work_arrangement in ("hybrid", "onsite"):
            if not self.location.city and not self.location.state:
                raise ValueError(
                    f"city or state required for {self.work_arrangement} roles"
                )
        return self


# --- Signal Extraction ---

SENIORITY_EXECUTIVE_PATTERNS = [
    r"\bvp\b", r"\bvice president\b", r"\bdirector\b", r"\bhead of\b",
    r"\bchief\b", r"\bc[a-z]o\b", r"\bgeneral manager\b",
    r"\b15\+?\s*years?\b", r"\b20\+?\s*years?\b",
]

SENIORITY_SENIOR_PATTERNS = [
    r"\bsenior\b", r"\bsr\.?\b", r"\blead\b", r"\bprincipal\b",
    r"\bstaff\b", r"\b(?:5|6|7|8|9|10)\+?\s*years?\b",
]

SENIORITY_MID_PATTERNS = [
    r"\bmid[- ]?level\b", r"\bmanager\b",
    r"\b(?:3|4|5)\+?\s*years?\b",
]

SENIORITY_ENTRY_PATTERNS = [
    r"\bjunior\b", r"\bjr\.?\b", r"\bassociate\b", r"\bentry[- ]?level\b",
    r"\b(?:0|1|2)\+?\s*years?\b", r"\bintern\b", r"\bcoordinator\b",
]

ROLE_TYPE_CREATIVE_KEYWORDS = {
    "designer", "design", "art director", "copywriter", "ux", "ui",
    "creative director", "video", "motion", "graphic", "illustrator",
    "animator", "visual",
}

ROLE_TYPE_TECHNICAL_KEYWORDS = {
    "developer", "engineer", "architect", "data scientist", "devops",
    "qa", "programmer", "software", "backend", "frontend", "full stack",
    "fullstack", "python", "java", "javascript", "react", "node",
    "cloud", "sre", "infrastructure", "machine learning", "ml", "ai",
}

ROLE_TYPE_MARKETING_KEYWORDS = {
    "marketing", "seo", "ppc", "content", "social media", "brand",
    "digital marketing", "growth", "demand generation", "communications",
}

ROLE_TYPE_CORPORATE_KEYWORDS = {
    "hr", "human resources", "finance", "legal", "operations",
    "project manager", "admin", "administrative", "accounting",
    "coordinator", "analyst", "office manager", "recruiter",
}

ROLE_TYPE_EXECUTIVE_KEYWORDS = {
    "c-suite", "ceo", "cto", "cfo", "coo", "cmo", "cio",
    "vp", "vice president", "general manager", "president",
}


def classify_seniority(job: JobOrder) -> str:
    """Classify the seniority level: executive, senior, mid, or entry."""
    text = f"{job.job_title} {job.job_description}".lower()

    # Check executive first (highest priority)
    for pattern in SENIORITY_EXECUTIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            # Confirm it's not just mentioning exec in passing
            if re.search(pattern, job.job_title.lower(), re.IGNORECASE):
                return "executive"

    # Check senior
    for pattern in SENIORITY_SENIOR_PATTERNS:
        if re.search(pattern, job.job_title.lower(), re.IGNORECASE):
            return "senior"

    # Check entry in title (before mid, because "0-2 years" should be entry)
    for pattern in SENIORITY_ENTRY_PATTERNS:
        if re.search(pattern, job.job_title.lower(), re.IGNORECASE):
            return "entry"

    # Check entry in description (e.g., "entry-level", "0-2 years")
    entry_desc_patterns = [
        r"\bentry[- ]?level\b", r"\b0-2\s*years?\b",
        r"\b(?:0|1|2)\s*years?\s*(?:of\s+)?experience\b",
    ]
    for pattern in entry_desc_patterns:
        if re.search(pattern, job.job_description.lower(), re.IGNORECASE):
            return "entry"

    # Check mid patterns in description if title didn't match
    for pattern in SENIORITY_MID_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "mid"

    # Default based on years in description
    years_match = re.findall(r"(\d+)\+?\s*years?", text)
    if years_match:
        max_years = max(int(y) for y in years_match)
        if max_years >= 15:
            return "executive"
        if max_years >= 5:
            return "senior"
        if max_years >= 3:
            return "mid"
        return "entry"

    return "mid"  # default


def classify_role_type(job: JobOrder) -> str:
    """Classify the role type: creative, technical, marketing, corporate, or executive."""
    text = f"{job.job_title} {job.job_description}".lower()

    # Check executive first (VP, C-suite) — use word boundaries
    title_lower = job.job_title.lower()
    for kw in ROLE_TYPE_EXECUTIVE_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, title_lower):
            return "executive"

    # Score each category
    scores = {}
    for category, keywords in [
        ("creative", ROLE_TYPE_CREATIVE_KEYWORDS),
        ("technical", ROLE_TYPE_TECHNICAL_KEYWORDS),
        ("marketing", ROLE_TYPE_MARKETING_KEYWORDS),
        ("corporate", ROLE_TYPE_CORPORATE_KEYWORDS),
    ]:
        score = sum(1 for kw in keywords if kw in text)
        # Weight title matches higher
        score += sum(2 for kw in keywords if kw in job.job_title.lower())
        scores[category] = score

    if not any(scores.values()):
        return "corporate"  # default

    return max(scores, key=scores.get)


def classify_urgency(job: JobOrder) -> str:
    """Classify urgency: critical, high, standard, or passive."""
    notes = (job.additional_notes or "").lower()
    desc = job.job_description.lower()
    text = f"{notes} {desc}"

    # Check high first (urgent/urgent fill) — if "urgent" is present, it's high
    has_urgent = any(kw in text for kw in ["urgent", "urgently", "urgent fill"])

    # Critical: "ASAP", "immediate start", "immediate need"
    # "immediately" alone (e.g., "interviewing immediately") is high, not critical
    critical_patterns = [
        r"\basap\b",
        r"\bimmediate\s+(?:start|need|hire|opening)\b",
    ]
    has_critical = any(re.search(p, text) for p in critical_patterns)

    if has_critical:
        return "critical"
    if has_urgent:
        return "high"
    if any(kw in text for kw in ["evergreen", "ongoing need", "pipeline"]):
        return "passive"
    return "standard"


def classify_geo_tier(job: JobOrder) -> str:
    """Classify geographic tier: tier1, tier2, tier3, or remote."""
    from poc.config.settings import TIER1_CITIES, TIER2_CITIES

    if job.work_arrangement == "remote":
        return "remote"

    city = (job.location.city or "").lower().strip()
    if city in TIER1_CITIES:
        return "tier1"
    if city in TIER2_CITIES:
        return "tier2"
    return "tier3"


def is_salary_required(job: JobOrder) -> bool:
    """Check if salary disclosure is required based on job location."""
    from poc.config.settings import SALARY_REQUIRED_STATES

    state = (job.location.state or "").upper().strip()

    # Remote US jobs must comply with strictest state rules
    if job.work_arrangement == "remote" and (job.location.country or "").upper() in ("USA", "US"):
        return True

    return state in SALARY_REQUIRED_STATES


def is_client_confidential(job: JobOrder) -> bool:
    """Check if the client name should be suppressed."""
    client = (job.client or "").lower().strip()
    if not client:
        return True
    confidential_indicators = [
        "confidential", "anonymous", "undisclosed", "leading",
        "a leading", "top", "major",
    ]
    return any(ind in client for ind in confidential_indicators)


def extract_signals(job: JobOrder) -> dict:
    """Extract all classification signals from a job order."""
    return {
        "seniority": classify_seniority(job),
        "role_type": classify_role_type(job),
        "urgency": classify_urgency(job),
        "geo_tier": classify_geo_tier(job),
        "salary_required": is_salary_required(job),
        "client_confidential": is_client_confidential(job),
        "has_salary": job.salary is not None and job.salary.min is not None,
    }


def parse_job_order(filepath: str | Path) -> JobOrder:
    """Parse a job order JSON file into a validated JobOrder model."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Job order file not found: {filepath}")

    with open(filepath) as f:
        data = json.load(f)

    return JobOrder(**data)


def parse_job_order_string(json_string: str) -> JobOrder:
    """Parse a job order from a JSON string."""
    data = json.loads(json_string)
    return JobOrder(**data)
