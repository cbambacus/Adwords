"""
Strategy Agent — Claude API integration.

Analyzes a job order, extracts signals, and generates a Strategy Brief (YAML)
that guides the Writer Agent.

Uses the Strategy Agent Rulebook as its system prompt context.
"""

from __future__ import annotations

import yaml
from pathlib import Path

import anthropic

from poc.config.settings import (
    ANTHROPIC_API_KEY,
    ARCHITECTURE_DIR,
    BASE_DAILY_BUDGET,
    CLAUDE_MODEL,
    GEO_ADJUSTMENT,
    KNOWLEDGE_BASE_DIR,
    SALARY_REQUIRED_STATES,
    URGENCY_MULTIPLIER,
)
from poc.pipeline.job_order import JobOrder, extract_signals
from poc.validation.brief_validator import parse_strategy_brief, validate_brief


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _build_system_prompt() -> str:
    """Build the Strategy Agent system prompt from the rulebook and knowledge base."""
    rulebook = _load_text(ARCHITECTURE_DIR / "strategy-agent-rulebook.md")
    google_ads_spec = _load_text(KNOWLEDGE_BASE_DIR / "platform-specs" / "google-ads.md")
    candidate_psych = _load_text(KNOWLEDGE_BASE_DIR / "candidate-psychology" / "by-seniority.md")
    compliance_eeoc = _load_text(KNOWLEDGE_BASE_DIR / "compliance" / "eeoc-guidelines.md")
    compliance_salary = _load_text(KNOWLEDGE_BASE_DIR / "compliance" / "salary-transparency.md")
    benchmarks = _load_text(KNOWLEDGE_BASE_DIR / "benchmarks" / "recruitment-benchmarks.md")

    return f"""You are the Strategy Agent for the company's AI-powered recruitment advertising system.

Your job is to analyze a job order and produce a Strategy Brief in YAML format that will guide the Writer Agent in creating Google Ads Responsive Search Ads (RSAs).

## Your Rulebook

{rulebook}

## Google Ads Platform Specifications

{google_ads_spec}

## Candidate Psychology by Seniority

{candidate_psych}

## EEOC Compliance Guidelines

{compliance_eeoc}

## Salary Transparency Requirements

{compliance_salary}

## Recruitment Benchmarks

{benchmarks}

## Output Requirements

You MUST output ONLY valid YAML (no markdown code fences, no commentary before or after).
The YAML must follow the Writer Agent Guidance Template structure from Section 5 of the rulebook.

For the POC, only Google Search is enabled. Set all other platforms to enabled: false.

Key rules:
1. Set headlines_needed: 15, descriptions_needed: 4, headline_max_chars: 30, description_max_chars: 90
2. Generate 5-10 primary keywords and 10-20 secondary keywords
3. Include negative keywords (universal + role-specific)
4. Set compliance_checklist with salary_disclosure based on job location state
5. Calculate daily budget using: Base * Urgency Multiplier * Geographic Adjustment
6. If client is "Confidential" or contains "leading"/"a leading", mark client as CONFIDENTIAL
7. For remote US jobs, salary_disclosure must be REQUIRED (strictest state rules apply)
"""


def _build_user_prompt(job: JobOrder, signals: dict) -> str:
    """Build the user prompt with job order data and pre-computed signals."""
    salary_info = "Not provided"
    if job.salary and job.salary.min is not None:
        salary_info = f"${job.salary.min:,.0f} - ${job.salary.max:,.0f} {job.salary.currency}/{job.salary.type}"

    location_info = job.work_arrangement.capitalize()
    if job.location.city:
        location_info = f"{job.location.city}, {job.location.state} ({job.work_arrangement})"
    elif job.location.state:
        location_info = f"{job.location.state} ({job.work_arrangement})"

    budget_base = BASE_DAILY_BUDGET.get(signals["seniority"], 112)
    urgency_mult = URGENCY_MULTIPLIER.get(signals["urgency"], 1.0)
    geo_adj = GEO_ADJUSTMENT.get(signals["geo_tier"], 1.0)
    calculated_budget = round(budget_base * urgency_mult * geo_adj)

    return f"""Analyze this job order and generate a Strategy Brief in YAML format.

## Job Order

- Job ID: {job.job_id}
- Job Title: {job.job_title}
- Client: {job.client or "Not specified"}
- Location: {location_info}
- Work Arrangement: {job.work_arrangement}
- Salary: {salary_info}
- Employment Type: {job.employment_type or "Not specified"}
- Duration: {f"{job.duration_months} months" if job.duration_months else "Permanent"}
- Start Date: {job.start_date or "Not specified"}
- Additional Notes: {job.additional_notes or "None"}

## Job Description

{job.job_description}

## Pre-computed Signals (use these in your brief)

- Seniority: {signals["seniority"]}
- Role Type: {signals["role_type"]}
- Urgency: {signals["urgency"]}
- Geographic Tier: {signals["geo_tier"]}
- Salary Required: {signals["salary_required"]}
- Client Confidential: {signals["client_confidential"]}
- Has Salary Data: {signals["has_salary"]}

## Budget Calculation

- Base daily budget ({signals["seniority"]}): ${budget_base}
- Urgency multiplier ({signals["urgency"]}): {urgency_mult}x
- Geographic adjustment ({signals["geo_tier"]}): {geo_adj}x
- Calculated daily budget: ${calculated_budget}

Generate the YAML Strategy Brief now. Output ONLY the YAML content, no code fences or extra text."""


def run_strategy_agent(
    job: JobOrder,
    signals: dict = None,
    max_retries: int = 2,
) -> dict:
    """
    Run the Strategy Agent to generate a Strategy Brief.

    Args:
        job: Validated job order
        signals: Pre-computed signals (computed if not provided)
        max_retries: Number of retries on validation failure

    Returns:
        dict with keys:
            - brief: parsed Strategy Brief dict
            - brief_yaml: raw YAML string
            - validation: BriefValidationResult
            - signals: the signals dict used
    """
    if signals is None:
        signals = extract_signals(job)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(job, signals)

    for attempt in range(1, max_retries + 2):
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_yaml = message.content[0].text.strip()

        # Strip code fences if Claude included them despite instructions
        if raw_yaml.startswith("```"):
            lines = raw_yaml.split("\n")
            lines = [l for l in lines[1:] if l.strip() != "```"]
            raw_yaml = "\n".join(lines)

        try:
            brief = parse_strategy_brief(raw_yaml)
        except yaml.YAMLError:
            if attempt <= max_retries:
                user_prompt = (
                    f"Your previous response was not valid YAML. Please try again.\n\n"
                    f"The YAML parse error was:\n{raw_yaml[:500]}\n\n"
                    f"Generate ONLY valid YAML, no code fences or extra text."
                )
                continue
            raise

        validation = validate_brief(brief)

        if validation.passed or attempt > max_retries:
            return {
                "brief": brief,
                "brief_yaml": raw_yaml,
                "validation": validation,
                "signals": signals,
            }

        # Retry with validation errors
        error_list = "\n".join(f"- {e.path}: {e.issue}" for e in validation.errors)
        user_prompt = (
            f"Your Strategy Brief had validation errors:\n{error_list}\n\n"
            f"Please regenerate the complete YAML brief fixing these errors. "
            f"Output ONLY valid YAML."
        )

    # Should not reach here
    return {
        "brief": brief,
        "brief_yaml": raw_yaml,
        "validation": validation,
        "signals": signals,
    }
