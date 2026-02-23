"""
Category D tests: Campaign Builder output validation.

Tests campaign structure, budget, targeting, ad group organization,
and RSA content mapping.
"""

from __future__ import annotations

import pytest

from poc.pipeline.campaign_builder import build_campaign, get_campaign_summary


# --- Fixtures ---

SAMPLE_BRIEF = {
    "job_title": "Senior UX Designer",
    "job_id": "TEST-001",
    "client": "FinTech Innovations Inc.",
    "location": "San Francisco, CA (hybrid)",
    "work_arrangement": "hybrid",
    "compensation": "$130,000 - $155,000/yr",
    "audience": {
        "seniority_level": "senior",
        "candidate_mindset": "mixed",
        "primary_motivations": ["Career growth", "Impact", "Compensation"],
    },
    "primary_keywords": [
        "senior UX designer jobs",
        "UX designer San Francisco",
        "senior UX designer hybrid",
        "UX design lead jobs",
        "senior product designer jobs",
        "UX designer fintech",
        "senior UX designer salary",
        "UX designer contract to hire",
    ],
    "secondary_keywords": [
        "Figma designer jobs",
        "mobile app UX designer",
        "banking UX designer",
        "user research jobs SF",
        "UX wireframe designer",
        "product design lead",
        "design system jobs",
        "WCAG accessibility designer",
        "UX mentor role",
        "hybrid UX designer",
        "B2C UX designer",
        "interaction designer SF",
        "senior UI UX designer",
        "design lead fintech",
        "UX portfolio required",
    ],
    "negative_keywords": [
        "course", "training", "certification", "tutorial", "bootcamp",
        "salary survey", "freelance", "intern", "junior", "entry level",
        "template", "free download", "DIY", "resume template", "cover letter",
        "interview questions",
    ],
    "compliance_checklist": {
        "salary_disclosure": "REQUIRED",
        "no_discriminatory_language": "REQUIRED",
    },
}

SAMPLE_CONTENT = {
    "headlines": [
        "Senior UX Designer - Apply",
        "UX Design Lead | FinTech",
        "$130K-$155K UX Designer",
        "Hybrid UX Designer in SF",
        "Lead Mobile UX Redesign",
        "UX Designer - San Francisco",
        "Senior Figma UX Designer",
        "Apply: UX Design Lead",
        "UX Designer | Hybrid Role",
        "Fintech UX Design Jobs",
        "Mentor Junior Designers",
        "UX Designer - Apply Now",
        "Mobile Banking UX Lead",
        "Top UX Role in FinTech",
        "Join Our Design Team Today",
    ],
    "descriptions": [
        "Lead the redesign of our mobile banking app. $130K-$155K. Hybrid in SF. Apply now!",
        "5+ years UX? Join our fintech team as Senior UX Designer. Hybrid, San Francisco.",
        "Senior UX Designer for mobile banking redesign. Figma and WCAG experience valued.",
        "Shape fintech UX. Mentor designers, lead research, and create intuitive experiences.",
    ],
    "display_paths": ["UX-Design", "Apply-Now"],
}

SAMPLE_SIGNALS = {
    "seniority": "senior",
    "role_type": "creative",
    "urgency": "high",
    "geo_tier": "tier1",
    "salary_required": True,
    "client_confidential": False,
    "has_salary": True,
    "job_id": "TEST-001",
}


class TestCampaignStructure:
    """D-01 through D-04: Campaign has correct top-level structure."""

    def test_campaign_has_name(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        assert "TEST-001" in campaign["campaign_name"]
        assert "UX-Designer" in campaign["campaign_name"] or "Senior" in campaign["campaign_name"]

    def test_campaign_paused(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        assert campaign["status"] == "PAUSED"

    def test_campaign_has_budget(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        assert campaign["budget"]["daily_budget_dollars"] > 0
        assert campaign["budget"]["amount_micros"] > 0

    def test_campaign_bidding_strategy(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        assert campaign["bidding_strategy"] == "MAXIMIZE_CONVERSIONS"

    def test_campaign_has_metadata(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        meta = campaign["metadata"]
        assert meta["job_id"] == "TEST-001"
        assert meta["seniority"] == "senior"
        assert meta["urgency"] == "high"


class TestBudget:
    """D-05, D-06: Budget calculation matches signals."""

    def test_budget_for_senior_high_tier1(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        # senior=175, high=1.5x, tier1=1.4x → 175*1.5*1.4 = 367.5 → 368
        budget = campaign["budget"]["daily_budget_dollars"]
        assert 300 <= budget <= 400, f"Expected ~368, got {budget}"

    def test_budget_micros_correct(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        budget = campaign["budget"]["daily_budget_dollars"]
        micros = campaign["budget"]["amount_micros"]
        assert micros == budget * 1_000_000


class TestLocationTargeting:
    """D-07, D-08: Location targeting matches work arrangement."""

    def test_hybrid_radius_targeting(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        loc = campaign["location_targeting"]
        assert loc["target_type"] == "radius"
        assert loc["radius_miles"] == 50  # hybrid = 50mi
        assert loc["city"] == "San Francisco"

    def test_remote_national_targeting(self):
        remote_signals = {**SAMPLE_SIGNALS, "geo_tier": "remote"}
        remote_brief = {**SAMPLE_BRIEF, "work_arrangement": "remote", "location": "Remote, US"}
        campaign = build_campaign(remote_brief, SAMPLE_CONTENT, remote_signals)
        loc = campaign["location_targeting"]
        assert loc["target_type"] == "national"

    def test_onsite_radius_targeting(self):
        onsite_signals = {**SAMPLE_SIGNALS, "geo_tier": "tier2"}
        onsite_brief = {**SAMPLE_BRIEF, "work_arrangement": "onsite"}
        campaign = build_campaign(onsite_brief, SAMPLE_CONTENT, onsite_signals)
        loc = campaign["location_targeting"]
        assert loc["target_type"] == "radius"
        assert loc["radius_miles"] == 25  # onsite = 25mi


class TestAdGroups:
    """D-09 through D-13: Ad group structure and content mapping."""

    def test_three_ad_groups(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        assert len(campaign["ad_groups"]) == 3

    def test_ad_group_names(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        names = [ag["name"] for ag in campaign["ad_groups"]]
        assert "Intent-RoleSeeking" in names
        assert "Intent-SkillBased" in names
        assert "Intent-LocationBased" in names

    def test_each_ad_group_has_keywords(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        for ag in campaign["ad_groups"]:
            assert len(ag["keywords"]) > 0, f"{ag['name']} has no keywords"

    def test_each_ad_group_has_rsa(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        for ag in campaign["ad_groups"]:
            ads = ag["ads"]
            assert len(ads) == 1
            rsa = ads[0]
            assert rsa["type"] == "RESPONSIVE_SEARCH_AD"
            assert len(rsa["headlines"]) == 15
            assert len(rsa["descriptions"]) == 4

    def test_keywords_have_match_type(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        for ag in campaign["ad_groups"]:
            for kw in ag["keywords"]:
                assert "match_type" in kw
                assert kw["match_type"] == "PHRASE"

    def test_negative_keywords_distributed(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        total_negs = sum(len(ag["negative_keywords"]) for ag in campaign["ad_groups"])
        assert total_negs > 0


class TestCampaignSummary:
    """Test the summary extraction for display."""

    def test_summary_has_required_fields(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        summary = get_campaign_summary(campaign)
        assert "campaign_name" in summary
        assert "daily_budget" in summary
        assert "ad_groups" in summary
        assert "total_keywords" in summary

    def test_summary_ad_group_counts(self):
        campaign = build_campaign(SAMPLE_BRIEF, SAMPLE_CONTENT, SAMPLE_SIGNALS)
        summary = get_campaign_summary(campaign)
        for ag in summary["ad_groups"]:
            assert ag["keyword_count"] > 0
            assert "rsa_summary" in ag
