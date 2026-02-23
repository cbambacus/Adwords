"""
Category B tests: Strategy Agent output validation.

Tests strategy brief structure, classification accuracy, compliance flagging,
keyword generation, and budget calculations.

Uses a sample YAML brief fixture rather than live API calls.
"""

from __future__ import annotations

import pytest
import yaml

from poc.pipeline.job_order import parse_job_order, extract_signals
from poc.validation.brief_validator import (
    validate_brief,
    validate_brief_yaml,
    parse_strategy_brief,
)
from poc.config.settings import (
    BASE_DAILY_BUDGET,
    URGENCY_MULTIPLIER,
    GEO_ADJUSTMENT,
)

from pathlib import Path

TEST_ORDERS_DIR = Path(__file__).parent.parent.parent / "Tests" / "test-job-orders"


# --- Sample Strategy Brief fixture (represents valid Claude output) ---

SAMPLE_BRIEF_YAML = """
job_title: Senior UX Designer
client: FinTech Innovations Inc.
location: San Francisco, CA (hybrid)
work_arrangement: hybrid
compensation: $130,000 - $155,000/yr

audience:
  seniority_level: senior
  years_experience: 5-10
  current_likely_titles:
    - UX Designer
    - Senior Product Designer
    - Lead UX Designer
  candidate_mindset: mixed
  primary_motivations:
    - Career growth into design leadership
    - Working on impactful fintech products
    - Competitive compensation with hybrid flexibility
  pain_points_to_address:
    - Limited growth at current company
    - Want more influence on product decisions

key_selling_points:
  primary:
    point: Lead redesign of flagship mobile banking app
    rationale: Senior designers want ownership and impact
  secondary:
    - point: "$130K-$155K with contract-to-hire path"
      rationale: Salary transparency required in CA, competitive range
    - point: Hybrid 3 days in SF fintech
      rationale: Flexibility matters, SF is a design hub

differentiators:
  - Mentorship opportunity (lead junior designers)
  - Fintech innovation space

avoid_messaging:
  - Generic "fast-paced environment"
  - Overused "rock star" or "ninja"

tone_guidelines:
  overall_tone: Inspirational
  formality_level: 2
  industry_conventions: Design community values craft, portfolio, and impact

platforms:
  google_search:
    enabled: true
    headlines_needed: 15
    descriptions_needed: 4
    headline_max_chars: 30
    description_max_chars: 90
    special_notes: Include salary in at least one headline and one description for CA compliance

  google_display:
    enabled: false
  linkedin:
    enabled: false
  indeed:
    enabled: false

primary_keywords:
  - senior UX designer jobs
  - UX designer San Francisco
  - senior UX designer hybrid
  - UX design lead jobs
  - senior product designer jobs
  - UX designer fintech
  - senior UX designer salary
  - UX designer contract to hire

secondary_keywords:
  - Figma designer jobs
  - mobile app UX designer
  - banking UX designer
  - user research jobs SF
  - UX wireframe designer
  - product design lead
  - design system jobs
  - WCAG accessibility designer
  - UX mentor role
  - hybrid UX designer
  - B2C UX designer
  - interaction designer SF
  - senior UI UX designer
  - design lead fintech
  - UX portfolio required

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
  no_guaranteed_outcomes: REQUIRED
  platform_policy_compliant: REQUIRED

variation_strategy:
  total_variations_needed: 3
  a_b_test_elements:
    - Salary in headline vs. not
    - CTA phrasing (Apply Now vs. Learn More)
"""


class TestBriefStructure:
    """B-01, B-02: Strategy Brief has valid YAML structure with all required sections."""

    def test_sample_brief_parses(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        assert isinstance(brief, dict)

    def test_sample_brief_validates(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        result = validate_brief(brief)
        assert result.passed, f"Errors: {[e.issue for e in result.errors]}"

    def test_required_top_level_keys(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        required = [
            "job_title", "client", "location", "work_arrangement",
            "compensation", "audience", "key_selling_points",
            "tone_guidelines", "platforms", "primary_keywords",
            "secondary_keywords", "compliance_checklist",
        ]
        for key in required:
            assert key in brief, f"Missing key: {key}"

    def test_audience_section_structure(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        aud = brief["audience"]
        assert "seniority_level" in aud
        assert "candidate_mindset" in aud
        assert "primary_motivations" in aud
        assert isinstance(aud["primary_motivations"], list)

    def test_platforms_google_search_structure(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        gs = brief["platforms"]["google_search"]
        assert gs["enabled"] is True
        assert gs["headlines_needed"] == 15
        assert gs["descriptions_needed"] == 4
        assert gs["headline_max_chars"] == 30
        assert gs["description_max_chars"] == 90


class TestSeniorityClassification:
    """B-03 through B-05: Correct seniority classification for all test orders."""

    @pytest.mark.parametrize("filename,expected", [
        ("test-001-senior-ux-designer.json", "senior"),
        ("test-002-marketing-coordinator.json", "entry"),
        ("test-003-python-developer.json", "mid"),
        ("test-004-junior-graphic-designer.json", "entry"),
        ("test-005-vp-engineering.json", "executive"),
    ])
    def test_seniority(self, filename, expected):
        job = parse_job_order(TEST_ORDERS_DIR / filename)
        signals = extract_signals(job)
        assert signals["seniority"] == expected


class TestRoleTypeClassification:
    """B-06 through B-08: Correct role type classification."""

    @pytest.mark.parametrize("filename,expected_options", [
        ("test-001-senior-ux-designer.json", ["creative"]),
        ("test-002-marketing-coordinator.json", ["marketing", "corporate"]),
        ("test-003-python-developer.json", ["technical"]),
        ("test-004-junior-graphic-designer.json", ["creative"]),
        ("test-005-vp-engineering.json", ["executive"]),
    ])
    def test_role_type(self, filename, expected_options):
        job = parse_job_order(TEST_ORDERS_DIR / filename)
        signals = extract_signals(job)
        assert signals["role_type"] in expected_options


class TestComplianceFlagging:
    """B-09 through B-13: Salary transparency compliance flags."""

    def test_ca_salary_required(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        signals = extract_signals(job)
        assert signals["salary_required"] is True

    def test_tx_salary_not_required(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-002-marketing-coordinator.json")
        signals = extract_signals(job)
        assert signals["salary_required"] is False

    def test_remote_salary_required(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-003-python-developer.json")
        signals = extract_signals(job)
        assert signals["salary_required"] is True

    def test_co_salary_required(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-004-junior-graphic-designer.json")
        signals = extract_signals(job)
        assert signals["salary_required"] is True

    def test_ny_salary_required(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-005-vp-engineering.json")
        signals = extract_signals(job)
        assert signals["salary_required"] is True

    def test_brief_compliance_salary_required_for_ca(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        assert brief["compliance_checklist"]["salary_disclosure"] == "REQUIRED"


class TestKeywordGeneration:
    """B-14 through B-18: Keyword counts and structure."""

    def test_primary_keyword_count(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        kws = brief["primary_keywords"]
        assert 5 <= len(kws) <= 10, f"Expected 5-10 primary keywords, got {len(kws)}"

    def test_secondary_keyword_count(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        kws = brief["secondary_keywords"]
        assert 10 <= len(kws) <= 20, f"Expected 10-20 secondary keywords, got {len(kws)}"

    def test_negative_keywords_present(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        negs = brief.get("negative_keywords", [])
        assert len(negs) >= 10, f"Expected 10+ negative keywords, got {len(negs)}"

    def test_primary_keywords_include_job_title(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        kws_lower = [kw.lower() for kw in brief["primary_keywords"]]
        # At least one keyword should contain "ux designer"
        assert any("ux designer" in kw for kw in kws_lower)

    def test_negative_keywords_include_universals(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        negs = [n.lower() for n in brief.get("negative_keywords", [])]
        for universal in ["course", "training", "freelance"]:
            assert universal in negs, f"Missing universal negative: {universal}"


class TestBudgetCalculation:
    """B-19 through B-25: Budget calculation from signals."""

    @pytest.mark.parametrize("seniority,urgency,geo,expected_min,expected_max", [
        ("senior", "high", "tier1", 300, 600),
        ("entry", "standard", "tier2", 60, 130),
        ("executive", "critical", "tier1", 700, 1500),
        ("mid", "standard", "remote", 80, 120),
    ])
    def test_budget_range(self, seniority, urgency, geo, expected_min, expected_max):
        base = BASE_DAILY_BUDGET[seniority]
        mult = URGENCY_MULTIPLIER[urgency]
        adj = GEO_ADJUSTMENT[geo]
        budget = round(base * mult * adj)
        assert expected_min <= budget <= expected_max, f"Budget ${budget} outside expected ${expected_min}-${expected_max}"

    def test_test_001_budget(self):
        """TEST-001: Senior + High urgency + Tier1 (SF)"""
        base = BASE_DAILY_BUDGET["senior"]   # 175
        mult = URGENCY_MULTIPLIER["high"]    # 1.5
        adj = GEO_ADJUSTMENT["tier1"]        # 1.4
        budget = round(base * mult * adj)     # 175 * 1.5 * 1.4 = 367.5 → 368
        assert 300 <= budget <= 400

    def test_test_005_budget(self):
        """TEST-005: Executive + Critical + Tier1 (NYC)"""
        base = BASE_DAILY_BUDGET["executive"]  # 350
        mult = URGENCY_MULTIPLIER["critical"]  # 2.0
        adj = GEO_ADJUSTMENT["tier1"]          # 1.4
        budget = round(base * mult * adj)       # 350 * 2.0 * 1.4 = 980
        assert 900 <= budget <= 1100


class TestBriefValidation:
    """Test the brief validator catches structural problems."""

    def test_missing_audience(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        del brief["audience"]
        result = validate_brief(brief)
        assert not result.passed

    def test_missing_platforms(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        del brief["platforms"]
        result = validate_brief(brief)
        assert not result.passed

    def test_wrong_headline_count(self):
        brief = parse_strategy_brief(SAMPLE_BRIEF_YAML)
        brief["platforms"]["google_search"]["headlines_needed"] = 10
        result = validate_brief(brief)
        assert not result.passed

    def test_invalid_yaml(self):
        result = validate_brief_yaml("this: is: not: valid: {yaml")
        # PyYAML may or may not error on this, but invalid structure should fail
        # Test with clearly broken YAML
        result2 = validate_brief_yaml("{{{{")
        assert not result2.passed

    def test_code_fence_stripping(self):
        fenced = "```yaml\n" + SAMPLE_BRIEF_YAML + "\n```"
        brief = parse_strategy_brief(fenced)
        assert brief["job_title"] == "Senior UX Designer"
