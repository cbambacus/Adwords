"""
Configuration settings for the POC pipeline.

API keys and account IDs are loaded from environment variables.
Google Ads credentials are loaded from config/google-ads.yaml (gitignored).
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
REPO_ROOT = PROJECT_ROOT.parent
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUT_DIR = PROJECT_ROOT / "output"
TESTS_DIR = REPO_ROOT / "Tests"
TEST_JOB_ORDERS_DIR = TESTS_DIR / "test-job-orders"
COMPLIANCE_WORDLISTS_DIR = TESTS_DIR / "compliance-wordlists"
KNOWLEDGE_BASE_DIR = REPO_ROOT / "Knowledge-Base"
ARCHITECTURE_DIR = REPO_ROOT / "Architecture"

# Claude API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Google Ads - TEST ACCOUNT ONLY
# These must be set in config/google-ads.yaml (gitignored)
# Switching to production requires changing these values here,
# not via a CLI flag (prevents accidental production publish).
GOOGLE_ADS_YAML_PATH = CONFIG_DIR / "google-ads.yaml"
GOOGLE_ADS_USE_TEST_ACCOUNT = True  # Safety: always True for POC

# Google Ads RSA constraints
RSA_HEADLINE_COUNT = 15
RSA_HEADLINE_MAX_CHARS = 30
RSA_DESCRIPTION_COUNT = 4
RSA_DESCRIPTION_MAX_CHARS = 90
RSA_DISPLAY_PATH_MAX_CHARS = 15
RSA_DISPLAY_PATH_COUNT = 2

# Budget guardrails
MAX_CAMPAIGN_TOTAL_BUDGET = 10000
MAX_DAILY_BUDGET = 750
HUMAN_APPROVAL_CAMPAIGN_TOTAL = 5000
HUMAN_APPROVAL_DAILY_BUDGET = 500

# Seniority base daily budgets (midpoint of range)
BASE_DAILY_BUDGET = {
    "executive": 350,
    "senior": 175,
    "mid": 112,
    "entry": 75,
}

# Urgency multipliers
URGENCY_MULTIPLIER = {
    "critical": 2.0,
    "high": 1.5,
    "standard": 1.0,
    "passive": 0.7,
}

# Geographic adjustment factors
GEO_ADJUSTMENT = {
    "tier1": 1.4,   # SF, NYC, Boston, Seattle
    "tier2": 1.2,   # Austin, Denver, Chicago
    "tier3": 1.0,   # Other metros / suburban
    "remote": 0.9,  # Remote / national
}

# Tier 1 metro cities
TIER1_CITIES = {
    "san francisco", "new york", "boston", "seattle", "los angeles",
    "washington", "chicago",
}

# Tier 2 metro cities
TIER2_CITIES = {
    "austin", "denver", "portland", "atlanta", "dallas", "houston",
    "phoenix", "minneapolis", "san diego", "miami", "philadelphia",
    "raleigh", "nashville",
}

# Salary transparency required states
SALARY_REQUIRED_STATES = {"CA", "CO", "NY", "WA", "HI"}
