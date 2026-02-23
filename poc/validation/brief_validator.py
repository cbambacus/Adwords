"""
Strategy Brief YAML validator.

Validates that the Strategy Agent's YAML output contains all required sections
and follows the expected structure from the rulebook.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml


REQUIRED_TOP_LEVEL_KEYS = [
    "job_title",
    "client",
    "location",
    "work_arrangement",
    "compensation",
    "audience",
    "key_selling_points",
    "tone_guidelines",
    "platforms",
    "primary_keywords",
    "secondary_keywords",
    "compliance_checklist",
]

REQUIRED_AUDIENCE_KEYS = [
    "seniority_level",
    "candidate_mindset",
    "primary_motivations",
]

REQUIRED_PLATFORM_KEYS = [
    "google_search",
]

REQUIRED_GOOGLE_SEARCH_KEYS = [
    "enabled",
    "headlines_needed",
    "descriptions_needed",
    "headline_max_chars",
    "description_max_chars",
]

REQUIRED_COMPLIANCE_KEYS = [
    "no_discriminatory_language",
    "salary_disclosure",
    "equal_opportunity_mention",
    "platform_policy_compliant",
]


@dataclass
class BriefValidationIssue:
    path: str        # e.g., "audience.seniority_level"
    issue: str       # description
    severity: str    # "error" or "warning"


@dataclass
class BriefValidationResult:
    issues: list[BriefValidationIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> list[BriefValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def add(self, issue: BriefValidationIssue):
        self.issues.append(issue)


def parse_strategy_brief(yaml_text: str) -> dict:
    """Parse YAML strategy brief text into a dict."""
    # Strip markdown code fences if present
    text = yaml_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```yaml or ```) and last line (```)
        lines = [l for l in lines[1:] if l.strip() != "```"]
        text = "\n".join(lines)

    return yaml.safe_load(text)


def validate_brief(brief: dict) -> BriefValidationResult:
    """Validate a parsed strategy brief dictionary."""
    result = BriefValidationResult()

    if not isinstance(brief, dict):
        result.add(BriefValidationIssue(
            path="root",
            issue="Brief must be a YAML mapping",
            severity="error",
        ))
        return result

    # Top-level keys
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in brief:
            result.add(BriefValidationIssue(
                path=key,
                issue=f"Missing required key: {key}",
                severity="error",
            ))

    # Audience section
    audience = brief.get("audience", {})
    if isinstance(audience, dict):
        for key in REQUIRED_AUDIENCE_KEYS:
            if key not in audience:
                result.add(BriefValidationIssue(
                    path=f"audience.{key}",
                    issue=f"Missing required audience key: {key}",
                    severity="error",
                ))

        # Validate seniority level value
        seniority = audience.get("seniority_level", "")
        valid_seniority = {"entry", "mid", "senior", "executive",
                          "entry-level", "mid-level", "senior-level"}
        if seniority and str(seniority).lower().replace("_", "-") not in valid_seniority:
            result.add(BriefValidationIssue(
                path="audience.seniority_level",
                issue=f"Invalid seniority: {seniority}",
                severity="warning",
            ))

        # Validate candidate mindset
        mindset = audience.get("candidate_mindset", "")
        valid_mindsets = {"active", "passive", "mixed",
                         "active_seeker", "passive_candidate"}
        if mindset and str(mindset).lower().replace(" ", "_") not in valid_mindsets:
            result.add(BriefValidationIssue(
                path="audience.candidate_mindset",
                issue=f"Invalid mindset: {mindset}",
                severity="warning",
            ))
    else:
        result.add(BriefValidationIssue(
            path="audience",
            issue="audience must be a mapping",
            severity="error",
        ))

    # Platforms section
    platforms = brief.get("platforms", {})
    if isinstance(platforms, dict):
        for key in REQUIRED_PLATFORM_KEYS:
            if key not in platforms:
                result.add(BriefValidationIssue(
                    path=f"platforms.{key}",
                    issue=f"Missing required platform: {key}",
                    severity="error",
                ))

        # Google Search specifics
        gs = platforms.get("google_search", {})
        if isinstance(gs, dict):
            for key in REQUIRED_GOOGLE_SEARCH_KEYS:
                if key not in gs:
                    result.add(BriefValidationIssue(
                        path=f"platforms.google_search.{key}",
                        issue=f"Missing: {key}",
                        severity="error",
                    ))

            # Validate values
            if gs.get("headlines_needed") != 15:
                result.add(BriefValidationIssue(
                    path="platforms.google_search.headlines_needed",
                    issue=f"Must be 15, got {gs.get('headlines_needed')}",
                    severity="error",
                ))
            if gs.get("descriptions_needed") != 4:
                result.add(BriefValidationIssue(
                    path="platforms.google_search.descriptions_needed",
                    issue=f"Must be 4, got {gs.get('descriptions_needed')}",
                    severity="error",
                ))
            if gs.get("headline_max_chars") != 30:
                result.add(BriefValidationIssue(
                    path="platforms.google_search.headline_max_chars",
                    issue=f"Must be 30, got {gs.get('headline_max_chars')}",
                    severity="error",
                ))
            if gs.get("description_max_chars") != 90:
                result.add(BriefValidationIssue(
                    path="platforms.google_search.description_max_chars",
                    issue=f"Must be 90, got {gs.get('description_max_chars')}",
                    severity="error",
                ))
    else:
        result.add(BriefValidationIssue(
            path="platforms",
            issue="platforms must be a mapping",
            severity="error",
        ))

    # Keywords
    primary_kw = brief.get("primary_keywords", [])
    if isinstance(primary_kw, list):
        if len(primary_kw) < 5:
            result.add(BriefValidationIssue(
                path="primary_keywords",
                issue=f"Expected 5-10 primary keywords, got {len(primary_kw)}",
                severity="warning",
            ))
    else:
        result.add(BriefValidationIssue(
            path="primary_keywords",
            issue="primary_keywords must be a list",
            severity="error",
        ))

    secondary_kw = brief.get("secondary_keywords", [])
    if isinstance(secondary_kw, list):
        if len(secondary_kw) < 10:
            result.add(BriefValidationIssue(
                path="secondary_keywords",
                issue=f"Expected 10-20 secondary keywords, got {len(secondary_kw)}",
                severity="warning",
            ))
    else:
        result.add(BriefValidationIssue(
            path="secondary_keywords",
            issue="secondary_keywords must be a list",
            severity="error",
        ))

    # Compliance checklist
    compliance = brief.get("compliance_checklist", {})
    if isinstance(compliance, dict):
        for key in REQUIRED_COMPLIANCE_KEYS:
            if key not in compliance:
                result.add(BriefValidationIssue(
                    path=f"compliance_checklist.{key}",
                    issue=f"Missing: {key}",
                    severity="error",
                ))
    elif isinstance(compliance, list):
        # Accept list format too (e.g., list of dicts)
        pass
    else:
        result.add(BriefValidationIssue(
            path="compliance_checklist",
            issue="compliance_checklist must be a mapping or list",
            severity="error",
        ))

    # Tone guidelines
    tone = brief.get("tone_guidelines", {})
    if isinstance(tone, dict):
        if "overall_tone" not in tone:
            result.add(BriefValidationIssue(
                path="tone_guidelines.overall_tone",
                issue="Missing overall_tone",
                severity="warning",
            ))
        if "formality_level" not in tone:
            result.add(BriefValidationIssue(
                path="tone_guidelines.formality_level",
                issue="Missing formality_level",
                severity="warning",
            ))

    return result


def validate_brief_yaml(yaml_text: str) -> BriefValidationResult:
    """Parse and validate a YAML strategy brief string."""
    try:
        brief = parse_strategy_brief(yaml_text)
    except yaml.YAMLError as e:
        result = BriefValidationResult()
        result.add(BriefValidationIssue(
            path="root",
            issue=f"Invalid YAML: {e}",
            severity="error",
        ))
        return result

    return validate_brief(brief)
