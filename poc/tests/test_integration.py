"""
Category G tests: End-to-end integration (offline).

Tests the full pipeline flow from job order through campaign building,
using fixture data (no live API calls).
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from poc.pipeline.job_order import parse_job_order, extract_signals
from poc.pipeline.campaign_builder import build_campaign, get_campaign_summary
from poc.validation.brief_validator import parse_strategy_brief, validate_brief
from poc.validation.content_validator import ContentValidator
from poc.validation.compliance_scanner import ComplianceScanner

TEST_ORDERS_DIR = Path(__file__).parent.parent.parent / "Tests" / "test-job-orders"


# --- Sample fixtures for offline integration ---

SAMPLE_BRIEF_YAML = """
job_title: Senior UX Designer
job_id: TEST-001
client: FinTech Innovations Inc.
location: San Francisco, CA (hybrid)
work_arrangement: hybrid
compensation: $130,000 - $155,000/yr
audience:
  seniority_level: senior
  candidate_mindset: mixed
  primary_motivations:
    - Career growth
    - Impact
    - Compensation
tone_guidelines:
  overall_tone: Inspirational
  formality_level: 2
platforms:
  google_search:
    enabled: true
    headlines_needed: 15
    descriptions_needed: 4
    headline_max_chars: 30
    description_max_chars: 90
key_selling_points:
  primary:
    point: Lead mobile banking redesign
    rationale: Ownership and impact
primary_keywords:
  - senior UX designer jobs
  - UX designer San Francisco
  - senior UX designer hybrid
  - UX design lead jobs
  - senior product designer
  - UX designer fintech
  - UX designer salary
  - UX designer contract
secondary_keywords:
  - Figma designer jobs
  - mobile UX designer
  - banking UX designer
  - user research SF
  - UX wireframe designer
  - product design lead
  - design system jobs
  - WCAG designer
  - UX mentor role
  - hybrid UX designer
  - B2C UX designer
  - interaction designer
negative_keywords:
  - course
  - training
  - certification
  - tutorial
  - bootcamp
  - salary survey
  - freelance
  - intern
  - junior
  - entry level
  - template
  - free download
  - DIY
  - resume template
  - cover letter
  - interview questions
compliance_checklist:
  no_discriminatory_language: REQUIRED
  salary_disclosure: REQUIRED
  equal_opportunity_mention: REQUIRED
  platform_policy_compliant: REQUIRED
"""

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


class TestEndToEndOffline:
    """Full pipeline from parse → strategy → writer → campaign (offline)."""

    @pytest.mark.parametrize("filename", [
        "test-001-senior-ux-designer.json",
        "test-002-marketing-coordinator.json",
        "test-003-python-developer.json",
        "test-004-junior-graphic-designer.json",
        "test-005-vp-engineering.json",
    ])
    def test_parse_and_classify_all_orders(self, filename):
        """All 5 test orders parse and produce valid signals."""
        job = parse_job_order(TEST_ORDERS_DIR / filename)
        signals = extract_signals(job)

        assert signals["seniority"] in ("entry", "mid", "senior", "executive")
        assert signals["role_type"] in ("creative", "technical", "marketing", "corporate", "executive")
        assert signals["urgency"] in ("critical", "high", "standard", "passive")
        assert signals["geo_tier"] in ("tier1", "tier2", "tier3", "remote")
        assert isinstance(signals["salary_required"], bool)
        assert isinstance(signals["client_confidential"], bool)

    def test_strategy_to_campaign_flow(self):
        """Strategy Brief + Writer Content → valid Campaign structure."""
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)

        # Validate brief
        brief_validation = validate_brief(brief)
        assert brief_validation.passed

        # Build campaign
        signals = {
            "seniority": "senior",
            "role_type": "creative",
            "urgency": "high",
            "geo_tier": "tier1",
            "salary_required": True,
            "client_confidential": False,
            "has_salary": True,
            "job_id": "TEST-001",
        }

        campaign = build_campaign(brief, SAMPLE_CONTENT, signals)

        # Validate campaign structure
        assert campaign["status"] == "PAUSED"
        assert campaign["budget"]["daily_budget_dollars"] > 0
        assert len(campaign["ad_groups"]) == 3

        for ag in campaign["ad_groups"]:
            assert len(ag["keywords"]) > 0
            assert len(ag["ads"]) == 1
            rsa = ag["ads"][0]
            assert rsa["type"] == "RESPONSIVE_SEARCH_AD"
            assert len(rsa["headlines"]) == 15
            assert len(rsa["descriptions"]) == 4

    def test_content_validation_in_pipeline(self):
        """Writer content passes both content and compliance validation."""
        validator = ContentValidator()
        scanner = ComplianceScanner()

        content_result = validator.validate_all(
            headlines=SAMPLE_CONTENT["headlines"],
            descriptions=SAMPLE_CONTENT["descriptions"],
            display_paths=SAMPLE_CONTENT["display_paths"],
        )
        compliance_result = scanner.scan_all_content(
            SAMPLE_CONTENT["headlines"],
            SAMPLE_CONTENT["descriptions"],
        )

        assert content_result.passed
        assert compliance_result.passed

    def test_campaign_serializable(self):
        """Campaign structure can be serialized to JSON."""
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        signals = {
            "seniority": "senior", "role_type": "creative", "urgency": "high",
            "geo_tier": "tier1", "salary_required": True, "client_confidential": False,
            "has_salary": True, "job_id": "TEST-001",
        }

        campaign = build_campaign(brief, SAMPLE_CONTENT, signals)
        json_str = json.dumps(campaign, indent=2, default=str)
        assert len(json_str) > 100

        # Round-trip
        parsed = json.loads(json_str)
        assert parsed["campaign_name"] == campaign["campaign_name"]

    def test_campaign_summary_extractable(self):
        """Campaign summary can be extracted for display."""
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        signals = {
            "seniority": "senior", "role_type": "creative", "urgency": "high",
            "geo_tier": "tier1", "salary_required": True, "client_confidential": False,
            "has_salary": True, "job_id": "TEST-001",
        }

        campaign = build_campaign(brief, SAMPLE_CONTENT, signals)
        summary = get_campaign_summary(campaign)

        assert summary["campaign_name"]
        assert summary["daily_budget"] > 0
        assert len(summary["ad_groups"]) == 3
        assert summary["total_keywords"] > 0
