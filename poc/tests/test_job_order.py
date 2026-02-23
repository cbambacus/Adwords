"""
Category A tests: Input validation and signal extraction.

Tests job order parsing, validation, and classification signals.
"""

import json
import pytest
from pathlib import Path

from poc.pipeline.job_order import (
    JobOrder,
    Salary,
    Location,
    parse_job_order,
    classify_seniority,
    classify_role_type,
    classify_urgency,
    classify_geo_tier,
    is_salary_required,
    is_client_confidential,
    extract_signals,
)

TEST_ORDERS_DIR = Path(__file__).parent.parent.parent / "Tests" / "test-job-orders"


# --- Parsing Tests ---

class TestJobOrderParsing:
    """A-01 through A-05: Valid job orders parse without errors."""

    def test_parse_test_001(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        assert job.job_id == "TEST-001"
        assert job.job_title == "Senior UX Designer"
        assert job.salary.min == 130000
        assert job.salary.max == 155000
        assert job.location.city == "San Francisco"
        assert job.location.state == "CA"
        assert job.work_arrangement == "hybrid"
        assert job.client == "FinTech Innovations Inc."

    def test_parse_test_002(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-002-marketing-coordinator.json")
        assert job.job_id == "TEST-002"
        assert job.job_title == "Marketing Coordinator"
        assert job.work_arrangement == "onsite"
        assert job.salary.min == 45000

    def test_parse_test_003(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-003-python-developer.json")
        assert job.job_id == "TEST-003"
        assert job.salary is None
        assert job.work_arrangement == "remote"
        assert job.location.city is None

    def test_parse_test_004(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-004-junior-graphic-designer.json")
        assert job.job_id == "TEST-004"
        assert job.client == "Confidential"
        assert job.location.state == "CO"

    def test_parse_test_005(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-005-vp-engineering.json")
        assert job.job_id == "TEST-005"
        assert job.job_title == "VP of Engineering"
        assert job.salary.min == 280000
        assert job.salary.max == 350000

    def test_all_test_orders_parse(self):
        """All 5 test orders parse without errors."""
        for f in sorted(TEST_ORDERS_DIR.glob("test-*.json")):
            job = parse_job_order(f)
            assert job.job_id.startswith("TEST-")


class TestJobOrderValidation:
    """A-06 through A-14: Invalid inputs are caught."""

    def test_missing_job_title(self):
        with pytest.raises(Exception):
            JobOrder(
                job_id="BAD-001",
                job_title="",
                job_description="Some description",
                location=Location(country="USA"),
                work_arrangement="remote",
            )

    def test_missing_job_description(self):
        with pytest.raises(Exception):
            JobOrder(
                job_id="BAD-002",
                job_title="Test Role",
                job_description="",
                location=Location(country="USA"),
                work_arrangement="remote",
            )

    def test_invalid_work_arrangement(self):
        with pytest.raises(Exception):
            JobOrder(
                job_id="BAD-003",
                job_title="Test Role",
                job_description="Some description here.",
                location=Location(city="NYC", state="NY", country="USA"),
                work_arrangement="telecommute",
            )

    def test_hybrid_requires_location(self):
        with pytest.raises(Exception):
            JobOrder(
                job_id="BAD-004",
                job_title="Test Role",
                job_description="Some description here.",
                location=Location(country="USA"),
                work_arrangement="hybrid",
            )

    def test_onsite_requires_location(self):
        with pytest.raises(Exception):
            JobOrder(
                job_id="BAD-005",
                job_title="Test Role",
                job_description="Some description here.",
                location=Location(country="USA"),
                work_arrangement="onsite",
            )

    def test_remote_without_city_is_valid(self):
        job = JobOrder(
            job_id="OK-001",
            job_title="Test Role",
            job_description="Some description here.",
            location=Location(country="USA"),
            work_arrangement="remote",
        )
        assert job.work_arrangement == "remote"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_job_order("/nonexistent/path.json")

    def test_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json {{{")
        with pytest.raises(json.JSONDecodeError):
            parse_job_order(bad_file)


# --- Signal Extraction Tests ---

class TestSeniorityClassification:
    """B-03 through B-05: Seniority classification."""

    def test_senior_ux_designer(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        assert classify_seniority(job) == "senior"

    def test_marketing_coordinator_entry(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-002-marketing-coordinator.json")
        assert classify_seniority(job) == "entry"

    def test_python_developer_mid(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-003-python-developer.json")
        assert classify_seniority(job) == "mid"

    def test_junior_graphic_designer_entry(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-004-junior-graphic-designer.json")
        assert classify_seniority(job) == "entry"

    def test_vp_engineering_executive(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-005-vp-engineering.json")
        assert classify_seniority(job) == "executive"


class TestRoleTypeClassification:
    """B-06 through B-08: Role type classification."""

    def test_ux_designer_creative(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        assert classify_role_type(job) == "creative"

    def test_marketing_coordinator(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-002-marketing-coordinator.json")
        role = classify_role_type(job)
        assert role in ("marketing", "corporate")

    def test_python_developer_technical(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-003-python-developer.json")
        assert classify_role_type(job) == "technical"

    def test_graphic_designer_creative(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-004-junior-graphic-designer.json")
        assert classify_role_type(job) == "creative"

    def test_vp_engineering_executive(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-005-vp-engineering.json")
        assert classify_role_type(job) == "executive"


class TestUrgencyClassification:
    """Urgency classification from notes and description."""

    def test_urgent_fill(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        assert classify_urgency(job) == "high"

    def test_standard(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-002-marketing-coordinator.json")
        assert classify_urgency(job) == "standard"

    def test_asap_critical(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-005-vp-engineering.json")
        assert classify_urgency(job) == "critical"


class TestGeoTierClassification:

    def test_sf_tier1(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        assert classify_geo_tier(job) == "tier1"

    def test_austin_tier2(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-002-marketing-coordinator.json")
        assert classify_geo_tier(job) == "tier2"

    def test_remote(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-003-python-developer.json")
        assert classify_geo_tier(job) == "remote"

    def test_denver_tier2(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-004-junior-graphic-designer.json")
        assert classify_geo_tier(job) == "tier2"

    def test_nyc_tier1(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-005-vp-engineering.json")
        assert classify_geo_tier(job) == "tier1"


class TestSalaryRequirement:

    def test_ca_requires_salary(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        assert is_salary_required(job) is True

    def test_tx_no_salary_required(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-002-marketing-coordinator.json")
        assert is_salary_required(job) is False

    def test_remote_requires_salary(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-003-python-developer.json")
        assert is_salary_required(job) is True

    def test_co_requires_salary(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-004-junior-graphic-designer.json")
        assert is_salary_required(job) is True

    def test_ny_requires_salary(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-005-vp-engineering.json")
        assert is_salary_required(job) is True


class TestClientConfidentiality:

    def test_named_client(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        assert is_client_confidential(job) is False

    def test_confidential_client(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-004-junior-graphic-designer.json")
        assert is_client_confidential(job) is True

    def test_leading_firm_confidential(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-005-vp-engineering.json")
        assert is_client_confidential(job) is True


class TestExtractSignals:
    """Full signal extraction produces expected dict."""

    def test_test_001_signals(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-001-senior-ux-designer.json")
        signals = extract_signals(job)
        assert signals["seniority"] == "senior"
        assert signals["role_type"] == "creative"
        assert signals["urgency"] == "high"
        assert signals["geo_tier"] == "tier1"
        assert signals["salary_required"] is True
        assert signals["client_confidential"] is False
        assert signals["has_salary"] is True

    def test_test_003_signals(self):
        job = parse_job_order(TEST_ORDERS_DIR / "test-003-python-developer.json")
        signals = extract_signals(job)
        assert signals["seniority"] == "mid"
        assert signals["role_type"] == "technical"
        assert signals["geo_tier"] == "remote"
        assert signals["has_salary"] is False
        assert signals["salary_required"] is True  # remote = strictest state
