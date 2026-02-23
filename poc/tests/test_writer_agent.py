"""
Category C tests: Writer Agent output validation.

Tests character limits, counts, uniqueness, compliance scanning,
and content quality. Uses fixture data rather than live API calls.
"""

from __future__ import annotations

import pytest

from poc.validation.content_validator import ContentValidator
from poc.validation.compliance_scanner import ComplianceScanner


# --- Sample Writer output fixture (represents valid Claude output) ---

SAMPLE_HEADLINES = [
    "Senior UX Designer - Apply",     # 26 chars
    "UX Design Lead | FinTech",        # 24 chars
    "$130K-$155K UX Designer",         # 23 chars
    "Hybrid UX Designer in SF",        # 24 chars
    "Lead Mobile UX Redesign",         # 23 chars
    "UX Designer - San Francisco",     # 28 chars
    "Senior Figma UX Designer",        # 24 chars
    "Apply: UX Design Lead",           # 21 chars
    "UX Designer | Hybrid Role",       # 25 chars
    "Fintech UX Design Jobs",          # 22 chars
    "Mentor Junior Designers",         # 23 chars
    "UX Designer - Apply Now",         # 23 chars
    "Mobile Banking UX Lead",          # 22 chars
    "Top UX Role in FinTech",          # 22 chars
    "Join Our Design Team Today",      # 26 chars
]

SAMPLE_DESCRIPTIONS = [
    "Lead the redesign of a flagship mobile banking app. $130K-$155K. Hybrid in SF. Apply today!",  # 92 chars — over limit!
    "5+ years UX experience? Join our fintech team as a Senior UX Designer. Hybrid, San Francisco.",  # 95 chars — over limit!
    "Senior UX Designer wanted for mobile banking redesign. Figma, WCAG, B2C experience valued.",  # 91 chars — over limit!
    "Shape the future of fintech UX. Mentor designers, lead research, and create intuitive apps.",  # 91 chars — over limit!
]

# Fixed descriptions within 90 chars
VALID_DESCRIPTIONS = [
    "Lead the redesign of our mobile banking app. $130K-$155K. Hybrid in SF. Apply now!",     # 83
    "5+ years UX? Join our fintech team as Senior UX Designer. Hybrid, San Francisco.",       # 82
    "Senior UX Designer for mobile banking redesign. Figma and WCAG experience valued.",      # 83
    "Shape fintech UX. Mentor designers, lead research, and create intuitive experiences.",   # 86
]

SAMPLE_DISPLAY_PATHS = ["UX-Design", "Apply-Now"]

SAMPLE_PRIMARY_KEYWORDS = [
    "UX designer",
    "UX design lead",
    "senior UX designer",
]


class TestCharacterLimits:
    """C-01 through C-04: Character limit validation."""

    def test_all_headlines_within_limit(self):
        for i, h in enumerate(SAMPLE_HEADLINES):
            assert len(h) <= 30, f"Headline {i+1} exceeds 30 chars: '{h}' ({len(h)} chars)"

    def test_headline_over_limit_caught(self):
        bad_headlines = SAMPLE_HEADLINES[:14] + ["This Headline Is Way Too Long For RSA"]
        validator = ContentValidator()
        result = validator.validate_headlines(bad_headlines)
        assert not result.passed

    def test_valid_descriptions_within_limit(self):
        for i, d in enumerate(VALID_DESCRIPTIONS):
            assert len(d) <= 90, f"Desc {i+1} exceeds 90 chars: '{d}' ({len(d)} chars)"

    def test_description_over_limit_caught(self):
        validator = ContentValidator()
        result = validator.validate_descriptions(SAMPLE_DESCRIPTIONS)
        # Original samples are over limit
        over_limit = [d for d in SAMPLE_DESCRIPTIONS if len(d) > 90]
        assert len(over_limit) > 0, "Test fixture should have over-limit descriptions"
        assert not result.passed

    def test_display_paths_within_limit(self):
        for p in SAMPLE_DISPLAY_PATHS:
            assert len(p) <= 15, f"Display path exceeds 15 chars: '{p}' ({len(p)} chars)"


class TestCounts:
    """C-05 through C-07: Required count validation."""

    def test_exact_15_headlines(self):
        validator = ContentValidator()
        result = validator.validate_headlines(SAMPLE_HEADLINES)
        assert result.passed
        assert len(SAMPLE_HEADLINES) == 15

    def test_too_few_headlines(self):
        validator = ContentValidator()
        result = validator.validate_headlines(SAMPLE_HEADLINES[:10])
        assert not result.passed

    def test_exact_4_descriptions(self):
        validator = ContentValidator()
        result = validator.validate_descriptions(VALID_DESCRIPTIONS)
        assert result.passed
        assert len(VALID_DESCRIPTIONS) == 4

    def test_too_few_descriptions(self):
        validator = ContentValidator()
        result = validator.validate_descriptions(VALID_DESCRIPTIONS[:2])
        assert not result.passed

    def test_exact_2_display_paths(self):
        validator = ContentValidator()
        result = validator.validate_display_paths(SAMPLE_DISPLAY_PATHS)
        assert result.passed


class TestUniqueness:
    """C-08, C-09: No duplicate headlines or descriptions."""

    def test_no_duplicate_headlines(self):
        validator = ContentValidator()
        result = validator.validate_headlines(SAMPLE_HEADLINES)
        assert result.passed

    def test_duplicate_headline_caught(self):
        duped = SAMPLE_HEADLINES[:14] + [SAMPLE_HEADLINES[0]]
        validator = ContentValidator()
        result = validator.validate_headlines(duped)
        assert not result.passed

    def test_no_duplicate_descriptions(self):
        validator = ContentValidator()
        result = validator.validate_descriptions(VALID_DESCRIPTIONS)
        assert result.passed

    def test_duplicate_description_caught(self):
        duped = VALID_DESCRIPTIONS[:3] + [VALID_DESCRIPTIONS[0]]
        validator = ContentValidator()
        result = validator.validate_descriptions(duped)
        assert not result.passed


class TestKeywordIntegration:
    """C-10: Primary keywords appear in headlines."""

    def test_primary_keywords_in_headlines(self):
        """At least 3 headlines should contain a primary keyword."""
        kw_count = 0
        for h in SAMPLE_HEADLINES:
            h_lower = h.lower()
            if any(kw.lower() in h_lower for kw in SAMPLE_PRIMARY_KEYWORDS):
                kw_count += 1
        assert kw_count >= 3, f"Only {kw_count}/3 headlines contain primary keywords"

    def test_validator_warns_on_low_keyword_count(self):
        no_kw_headlines = [f"Generic Headline {i}" for i in range(15)]
        validator = ContentValidator()
        result = validator.validate_headlines(no_kw_headlines, SAMPLE_PRIMARY_KEYWORDS)
        # Should have a warning about low keyword count
        kw_warnings = [w for w in result.warnings if "keyword" in w.issue.lower()]
        assert len(kw_warnings) > 0


class TestComplianceScanning:
    """C-11 through C-15: EEOC and editorial compliance."""

    def test_clean_content_passes(self):
        scanner = ComplianceScanner()
        result = scanner.scan_all_content(SAMPLE_HEADLINES, VALID_DESCRIPTIONS)
        assert result.passed, f"Violations: {[(v.category, v.term) for v in result.violations]}"

    def test_age_discrimination_caught(self):
        scanner = ComplianceScanner()
        result = scanner.scan_text("Looking for young digital native professionals")
        assert not result.passed
        categories = {v.category for v in result.violations}
        assert "age_discrimination" in categories

    def test_gender_discrimination_caught(self):
        scanner = ComplianceScanner()
        result = scanner.scan_text("He will manage the sales team as chairman")
        assert not result.passed
        categories = {v.category for v in result.violations}
        assert "gender_discrimination" in categories

    def test_excessive_caps_caught(self):
        scanner = ComplianceScanner()
        result = scanner.scan_text("APPLY NOW TODAY FOR THIS ROLE")
        assert not result.passed
        terms = {v.term for v in result.violations}
        assert "excessive_caps" in terms

    def test_excessive_punctuation_caught(self):
        scanner = ComplianceScanner()
        result = scanner.scan_text("Amazing opportunity!! Apply now!!")
        assert not result.passed
        terms = {v.term for v in result.violations}
        assert "excessive_punctuation" in terms

    def test_emoji_caught(self):
        scanner = ComplianceScanner()
        result = scanner.scan_text("Great job opportunity! 🚀")
        assert not result.passed
        terms = {v.term for v in result.violations}
        assert "emoji" in terms

    def test_national_origin_caught(self):
        scanner = ComplianceScanner()
        result = scanner.scan_text("Must be native English speaker with no foreign accents")
        assert not result.passed

    def test_coded_language_flagged_as_warning(self):
        scanner = ComplianceScanner()
        result = scanner.scan_text("Great cultural fit for our team")
        assert result.passed  # Warnings don't fail
        assert len(result.warnings) > 0


class TestFullValidation:
    """C-16 through C-19: Full content validation pipeline."""

    def test_valid_content_passes_all(self):
        validator = ContentValidator()
        scanner = ComplianceScanner()

        content_result = validator.validate_all(
            headlines=SAMPLE_HEADLINES,
            descriptions=VALID_DESCRIPTIONS,
            display_paths=SAMPLE_DISPLAY_PATHS,
            primary_keywords=SAMPLE_PRIMARY_KEYWORDS,
        )
        compliance_result = scanner.scan_all_content(SAMPLE_HEADLINES, VALID_DESCRIPTIONS)

        assert content_result.passed, f"Content errors: {[e.issue for e in content_result.errors]}"
        assert compliance_result.passed, f"Compliance violations: {[(v.category, v.term) for v in compliance_result.violations]}"

    def test_empty_headline_caught(self):
        headlines = SAMPLE_HEADLINES[:14] + [""]
        validator = ContentValidator()
        result = validator.validate_headlines(headlines)
        assert not result.passed
