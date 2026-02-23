"""
Writer Agent — Claude API integration.

Takes a Strategy Brief and generates Google Ads RSA content:
- 15 unique headlines (≤ 30 chars each)
- 4 unique descriptions (≤ 90 chars each)
- 2 display URL paths (≤ 15 chars each)

Validates output against character limits and compliance rules.
"""

from __future__ import annotations

import json
import re

import anthropic

from poc.config.settings import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    KNOWLEDGE_BASE_DIR,
    RSA_DESCRIPTION_COUNT,
    RSA_DESCRIPTION_MAX_CHARS,
    RSA_DISPLAY_PATH_COUNT,
    RSA_DISPLAY_PATH_MAX_CHARS,
    RSA_HEADLINE_COUNT,
    RSA_HEADLINE_MAX_CHARS,
)
from poc.validation.compliance_scanner import ComplianceScanner
from poc.validation.content_validator import ContentValidator


def _build_system_prompt(brief: dict) -> str:
    """Build Writer Agent system prompt with brief and platform specs."""
    google_ads_spec = (KNOWLEDGE_BASE_DIR / "platform-specs" / "google-ads.md").read_text()

    # Extract key info from brief
    compliance = brief.get("compliance_checklist", {})
    salary_required = False
    if isinstance(compliance, dict):
        salary_required = compliance.get("salary_disclosure") == "REQUIRED"

    # Extract critical facts to anchor the model
    job_title = brief.get("job_title", "")
    compensation = brief.get("compensation", "")
    primary_keywords = brief.get("primary_keywords", [])
    kw_list = "\n".join(f"  - {kw}" for kw in primary_keywords[:10])

    return f"""You are the Writer Agent for Aquent's AI-powered recruitment advertising system.

Your job is to generate Google Ads Responsive Search Ad (RSA) content based on the Strategy Brief provided.

## CRITICAL FACTS — Use these EXACTLY as given, do NOT change or invent alternatives

- **Exact Job Title**: {job_title}
- **Exact Compensation**: {compensation}
- **Primary Keywords (must appear in 4+ headlines)**:
{kw_list}

You MUST use the exact job title "{job_title}" in your headlines — do NOT substitute synonyms like "Manager" for "Designer" or change the title in any way. When you include salary/compensation, use the EXACT figures from the brief ({compensation}) — do NOT invent different numbers.

## Google Ads RSA Specifications

{google_ads_spec}

## Output Format

You MUST output ONLY valid JSON with this exact structure:
{{
  "headlines": ["headline1", "headline2", ... ],
  "descriptions": ["desc1", "desc2", ... ],
  "display_paths": ["path1", "path2"]
}}

## Hard Constraints (MUST be followed exactly)

1. Exactly {RSA_HEADLINE_COUNT} headlines, each MAXIMUM {RSA_HEADLINE_MAX_CHARS} characters
2. Exactly {RSA_DESCRIPTION_COUNT} descriptions, each MAXIMUM {RSA_DESCRIPTION_MAX_CHARS} characters
3. Exactly {RSA_DISPLAY_PATH_COUNT} display URL paths, each MAXIMUM {RSA_DISPLAY_PATH_MAX_CHARS} characters
4. ALL headlines must be unique (no duplicates, case-insensitive)
5. ALL descriptions must be unique (no duplicates, case-insensitive)
6. No excessive capitalization (max 2 consecutive ALL-CAPS words)
7. No excessive punctuation (no !! or ??)
8. No emoji characters
9. No discriminatory language (age, gender, race, religion, disability)

## Content Guidelines

1. Include primary keywords naturally in at least 4 headlines — this is critical for ad relevance and Quality Score
2. Use the EXACT job title "{job_title}" in at least 5 headlines (with variations like adding location, salary, or CTA around it)
3. Each description should work independently with any headline combination
4. Include at least 2 headlines with a call-to-action (Apply Now, Learn More, etc.)
5. {"Include the EXACT salary range ({}) in at least 1 headline and 1 description — this is LEGALLY REQUIRED for this job location".format(compensation) if salary_required else "Salary inclusion is optional"}
6. If client is marked CONFIDENTIAL, do NOT include the client name in any ad content
7. Vary messaging angles across headlines: job-title-focused, benefit-focused, CTA-focused, salary/comp, location-focused
8. Front-load key information in descriptions (candidates decide in 14 seconds)

## Character Counting

Count EVERY character including spaces and punctuation.
- Headlines: {RSA_HEADLINE_MAX_CHARS} chars MAX (this is strict — 31 chars = FAIL)
- Descriptions: {RSA_DESCRIPTION_MAX_CHARS} chars MAX
- Display paths: {RSA_DISPLAY_PATH_MAX_CHARS} chars MAX

Double-check your character counts before outputting.

Output ONLY the JSON object, no code fences or commentary."""


def _build_user_prompt(brief: dict) -> str:
    """Build the user prompt from the Strategy Brief."""
    import yaml
    brief_yaml = yaml.dump(brief, default_flow_style=False, sort_keys=False)

    job_title = brief.get("job_title", "")
    compensation = brief.get("compensation", "")
    primary_keywords = brief.get("primary_keywords", [])
    kw_examples = ", ".join(f'"{kw}"' for kw in primary_keywords[:5])

    return f"""Generate RSA ad content based on this Strategy Brief:

{brief_yaml}

## MANDATORY CHECKLIST — verify before outputting:

1. Exactly {RSA_HEADLINE_COUNT} headlines, each ≤{RSA_HEADLINE_MAX_CHARS} chars — COUNT CHARACTERS
2. Exactly {RSA_DESCRIPTION_COUNT} descriptions, each ≤{RSA_DESCRIPTION_MAX_CHARS} chars
3. Exactly {RSA_DISPLAY_PATH_COUNT} display paths, each ≤{RSA_DISPLAY_PATH_MAX_CHARS} chars
4. Job title "{job_title}" appears in at least 5 headlines — do NOT substitute with synonyms
5. Primary keywords appear in at least 4 headlines (e.g., {kw_examples})
6. Salary "{compensation}" is quoted EXACTLY when used — do NOT change the numbers
7. All headlines unique, all descriptions unique
8. No compliance violations

Output ONLY the JSON object."""


def _parse_writer_output(raw: str) -> dict:
    """Parse the Writer Agent's JSON output, handling code fences."""
    text = raw.strip()

    # Strip code fences
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines[1:] if l.strip() != "```"]
        text = "\n".join(lines)

    return json.loads(text)


def run_writer_agent(
    brief: dict,
    max_retries: int = 2,
) -> dict:
    """
    Run the Writer Agent to generate RSA content.

    Args:
        brief: Parsed Strategy Brief dict from Strategy Agent
        max_retries: Number of retries on validation failure

    Returns:
        dict with keys:
            - content: parsed content dict (headlines, descriptions, display_paths)
            - content_json: raw JSON string
            - content_validation: ContentValidationResult
            - compliance_scan: ComplianceScanResult
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system_prompt = _build_system_prompt(brief)
    user_prompt = _build_user_prompt(brief)

    content_validator = ContentValidator()
    compliance_scanner = ComplianceScanner()
    primary_keywords = brief.get("primary_keywords", [])

    for attempt in range(1, max_retries + 2):
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_json = message.content[0].text.strip()

        try:
            content = _parse_writer_output(raw_json)
        except json.JSONDecodeError:
            if attempt <= max_retries:
                user_prompt = (
                    f"Your previous response was not valid JSON. Please try again.\n\n"
                    f"Output ONLY a valid JSON object with headlines, descriptions, and display_paths arrays."
                )
                continue
            raise

        headlines = content.get("headlines", [])
        descriptions = content.get("descriptions", [])
        display_paths = content.get("display_paths", [])

        # Validate content
        content_result = content_validator.validate_all(
            headlines=headlines,
            descriptions=descriptions,
            display_paths=display_paths,
            primary_keywords=primary_keywords,
        )

        # Compliance scan
        compliance_result = compliance_scanner.scan_all_content(
            headlines=headlines,
            descriptions=descriptions,
        )

        all_passed = content_result.passed and compliance_result.passed

        if all_passed or attempt > max_retries:
            return {
                "content": content,
                "content_json": raw_json,
                "content_validation": content_result,
                "compliance_scan": compliance_result,
            }

        # Build retry prompt with specific errors
        issues = []
        for err in content_result.errors:
            issues.append(f"- {err.field}: {err.issue}" + (f" ({err.value})" if err.value else ""))
        for v in compliance_result.violations:
            issues.append(f"- {v.field_name}: {v.category} violation ({v.term})")

        user_prompt = (
            f"Your ad content had these validation errors:\n"
            + "\n".join(issues)
            + f"\n\nPlease regenerate ALL content fixing these errors.\n"
            f"Remember: {RSA_HEADLINE_COUNT} headlines (≤{RSA_HEADLINE_MAX_CHARS} chars), "
            f"{RSA_DESCRIPTION_COUNT} descriptions (≤{RSA_DESCRIPTION_MAX_CHARS} chars), "
            f"{RSA_DISPLAY_PATH_COUNT} display paths (≤{RSA_DISPLAY_PATH_MAX_CHARS} chars).\n"
            f"Output ONLY the JSON object."
        )

    return {
        "content": content,
        "content_json": raw_json,
        "content_validation": content_result,
        "compliance_scan": compliance_result,
    }
