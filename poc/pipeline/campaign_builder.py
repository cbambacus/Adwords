"""
Campaign Builder — Maps Strategy Brief + Writer content to Google Ads campaign structure.

Builds a campaign JSON structure compatible with Google Ads API,
organized by ad groups with intent-based segmentation.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from poc.config.settings import (
    BASE_DAILY_BUDGET,
    GEO_ADJUSTMENT,
    URGENCY_MULTIPLIER,
)


def _calculate_daily_budget(signals: dict) -> int:
    """Calculate daily budget from signals."""
    base = BASE_DAILY_BUDGET.get(signals["seniority"], 112)
    mult = URGENCY_MULTIPLIER.get(signals["urgency"], 1.0)
    adj = GEO_ADJUSTMENT.get(signals["geo_tier"], 1.0)
    return round(base * mult * adj)


def _build_location_targeting(brief: dict, signals: dict) -> dict:
    """Build location targeting from brief."""
    work_arr = brief.get("work_arrangement", "remote")
    location = brief.get("location", "")

    if work_arr == "remote":
        return {
            "target_type": "national",
            "country": "US",
            "radius": None,
        }

    # Extract city/state from location string
    city = ""
    state = ""
    if "," in location:
        parts = location.split(",")
        city = parts[0].strip()
        # State might have arrangement info in parens
        state_part = parts[1].strip()
        state = re.sub(r"\s*\(.*\)", "", state_part).strip()

    radius_miles = 50 if work_arr == "hybrid" else 25

    return {
        "target_type": "radius",
        "city": city,
        "state": state,
        "country": "US",
        "radius_miles": radius_miles,
    }


def _segment_keywords(brief: dict) -> List[Dict[str, Any]]:
    """
    Segment keywords into intent-based ad groups:
    - Intent-RoleSeeking: Job title + "jobs" variations
    - Intent-SkillBased: Skills and tool-based keywords
    - Intent-LocationBased: Location-specific keywords
    """
    primary = brief.get("primary_keywords", [])
    secondary = brief.get("secondary_keywords", [])
    all_keywords = primary + secondary
    negatives = brief.get("negative_keywords", [])

    role_seeking = []
    skill_based = []
    location_based = []

    location = (brief.get("location", "") or "").lower()
    city = ""
    if "," in location:
        city = location.split(",")[0].strip().lower()

    for kw in all_keywords:
        kw_lower = kw.lower()
        if city and city in kw_lower:
            location_based.append(kw)
        elif any(term in kw_lower for term in ["jobs", "role", "position", "hiring", "openings", "career"]):
            role_seeking.append(kw)
        elif any(term in kw_lower for term in [
            "designer", "developer", "engineer", "manager", "lead",
            "director", "coordinator", "analyst", "architect",
        ]):
            role_seeking.append(kw)
        else:
            skill_based.append(kw)

    # Ensure each group has at least some keywords
    if not location_based and city:
        # Pull location-relevant ones from role_seeking
        for kw in list(role_seeking):
            if city in kw.lower():
                location_based.append(kw)
                role_seeking.remove(kw)

    # If still empty, add a constructed location keyword
    if not location_based and city:
        title = brief.get("job_title", "jobs")
        location_based.append(f"{title} {city}")

    # Distribute negatives across groups
    role_negatives = [n for n in negatives if any(
        t in n.lower() for t in ["course", "training", "bootcamp", "salary", "resume", "cover letter"]
    )]
    skill_negatives = [n for n in negatives if any(
        t in n.lower() for t in ["template", "free", "diy", "tutorial"]
    )]
    location_negatives = [n for n in negatives if any(
        t in n.lower() for t in ["freelance", "intern", "junior", "entry"]
    )]

    # Ensure universals in each group
    universal_negatives = [n for n in negatives if n.lower() in {
        "course", "training", "certification", "freelance",
        "interview questions", "resume template",
    }]

    return [
        {
            "name": "Intent-RoleSeeking",
            "keywords": role_seeking or primary[:5],
            "negative_keywords": list(set(role_negatives + universal_negatives)),
        },
        {
            "name": "Intent-SkillBased",
            "keywords": skill_based or secondary[:5],
            "negative_keywords": list(set(skill_negatives + universal_negatives)),
        },
        {
            "name": "Intent-LocationBased",
            "keywords": location_based or [brief.get("job_title", "job") + " near me"],
            "negative_keywords": list(set(location_negatives + universal_negatives)),
        },
    ]


def build_campaign(
    brief: dict,
    content: dict,
    signals: dict,
) -> dict:
    """
    Build a Google Ads campaign structure from Strategy Brief and Writer content.

    Args:
        brief: Strategy Agent output (parsed YAML)
        content: Writer Agent output (headlines, descriptions, display_paths)
        signals: Pre-computed job signals

    Returns:
        Campaign structure dict ready for Google Ads API or JSON serialization.
    """
    job_title = brief.get("job_title", "Unknown")
    job_id = brief.get("job_id", signals.get("job_id", "UNKNOWN"))

    # Campaign name
    sanitized_title = re.sub(r"[^a-zA-Z0-9 -]", "", job_title).replace(" ", "-")
    campaign_name = f"{job_id}-{sanitized_title}"

    daily_budget = _calculate_daily_budget(signals)
    location_targeting = _build_location_targeting(brief, signals)
    ad_groups_config = _segment_keywords(brief)

    headlines = content.get("headlines", [])
    descriptions = content.get("descriptions", [])
    display_paths = content.get("display_paths", [])

    # Build ad groups with RSAs
    ad_groups = []
    for ag_config in ad_groups_config:
        ad_group = {
            "name": ag_config["name"],
            "keywords": [
                {"text": kw, "match_type": "PHRASE"}
                for kw in ag_config["keywords"]
            ],
            "negative_keywords": [
                {"text": nk, "match_type": "PHRASE"}
                for nk in ag_config["negative_keywords"]
            ],
            "ads": [
                {
                    "type": "RESPONSIVE_SEARCH_AD",
                    "headlines": [
                        {"text": h, "position": None}
                        for h in headlines
                    ],
                    "descriptions": [
                        {"text": d, "position": None}
                        for d in descriptions
                    ],
                    "display_paths": display_paths,
                    "final_url": f"https://aquent.com/find-work/{job_id.lower()}",
                }
            ],
        }
        ad_groups.append(ad_group)

    campaign = {
        "campaign_name": campaign_name,
        "status": "PAUSED",
        "budget": {
            "amount_micros": daily_budget * 1_000_000,
            "daily_budget_dollars": daily_budget,
            "delivery_method": "STANDARD",
        },
        "bidding_strategy": "MAXIMIZE_CONVERSIONS",
        "network_settings": {
            "target_google_search": True,
            "target_search_network": True,
            "target_content_network": False,
        },
        "location_targeting": location_targeting,
        "ad_groups": ad_groups,
        "metadata": {
            "job_id": job_id,
            "job_title": job_title,
            "seniority": signals.get("seniority", ""),
            "role_type": signals.get("role_type", ""),
            "urgency": signals.get("urgency", ""),
            "geo_tier": signals.get("geo_tier", ""),
            "created_at": datetime.utcnow().isoformat() + "Z",
        },
    }

    return campaign


def get_campaign_summary(campaign: dict) -> dict:
    """Extract a summary of the campaign for display."""
    ad_groups = campaign.get("ad_groups", [])

    ag_summaries = []
    for ag in ad_groups:
        kw_count = len(ag.get("keywords", []))
        neg_count = len(ag.get("negative_keywords", []))
        ads = ag.get("ads", [])
        headline_count = len(ads[0]["headlines"]) if ads else 0
        desc_count = len(ads[0]["descriptions"]) if ads else 0
        ag_summaries.append({
            "name": ag["name"],
            "keyword_count": kw_count,
            "negative_keyword_count": neg_count,
            "rsa_summary": f"{headline_count}h + {desc_count}d",
        })

    return {
        "campaign_name": campaign["campaign_name"],
        "status": campaign["status"],
        "daily_budget": campaign["budget"]["daily_budget_dollars"],
        "bidding_strategy": campaign["bidding_strategy"],
        "location": campaign["location_targeting"],
        "ad_groups": ag_summaries,
        "total_keywords": sum(ag["keyword_count"] for ag in ag_summaries),
        "total_negatives": sum(ag["negative_keyword_count"] for ag in ag_summaries),
    }
