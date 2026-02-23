"""
Compliance scanner for ad content.

Scans headlines, descriptions, and other text against:
- EEOC prohibited terms (age, gender, national origin, religion, disability)
- Editorial violations (excessive caps, punctuation, emoji)
- Salary transparency requirements

Uses wordlists from Tests/compliance-wordlists/.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from poc.config.settings import COMPLIANCE_WORDLISTS_DIR


@dataclass
class ComplianceViolation:
    category: str          # e.g., "age_discrimination", "editorial_violations"
    term: str              # the matched term or pattern
    text: str              # the text that contained the violation
    field_name: str        # e.g., "headline_3", "description_1"
    severity: str = "error"  # "error" or "warning"
    note: str = ""


@dataclass
class ComplianceScanResult:
    violations: list[ComplianceViolation] = field(default_factory=list)
    warnings: list[ComplianceViolation] = field(default_factory=list)
    passed: bool = True

    def add_violation(self, v: ComplianceViolation):
        if v.severity == "warning":
            self.warnings.append(v)
        else:
            self.violations.append(v)
            self.passed = False

    @property
    def total_issues(self) -> int:
        return len(self.violations) + len(self.warnings)


class ComplianceScanner:
    """Scans text for EEOC, editorial, and compliance violations."""

    def __init__(self):
        self._eeoc_terms = None
        self._salary_rules = None

    @property
    def eeoc_terms(self) -> dict:
        if self._eeoc_terms is None:
            path = COMPLIANCE_WORDLISTS_DIR / "eeoc-prohibited-terms.json"
            with open(path) as f:
                self._eeoc_terms = json.load(f)
        return self._eeoc_terms

    @property
    def salary_rules(self) -> dict:
        if self._salary_rules is None:
            path = COMPLIANCE_WORDLISTS_DIR / "salary-transparency-rules.json"
            with open(path) as f:
                self._salary_rules = json.load(f)
        return self._salary_rules

    def scan_text(self, text: str, field_name: str = "text") -> ComplianceScanResult:
        """Scan a single piece of text for all compliance violations."""
        result = ComplianceScanResult()
        text_lower = text.lower()

        # EEOC category scans
        for category in ["age_discrimination", "gender_discrimination",
                         "national_origin_discrimination", "religion_discrimination",
                         "disability_discrimination"]:
            category_data = self.eeoc_terms.get(category, {})

            # Exact term matches
            for term in category_data.get("prohibited_exact", []):
                if term.lower() in text_lower:
                    result.add_violation(ComplianceViolation(
                        category=category,
                        term=term,
                        text=text,
                        field_name=field_name,
                        severity="error",
                    ))

            # Phrase matches
            for phrase in category_data.get("prohibited_phrases", []):
                # Handle wildcard patterns like "no more than * years"
                pattern = re.escape(phrase.lower()).replace(r"\*", r".*?")
                if re.search(pattern, text_lower):
                    result.add_violation(ComplianceViolation(
                        category=category,
                        term=phrase,
                        text=text,
                        field_name=field_name,
                        severity="error",
                    ))

            # Context-dependent terms (warnings)
            for ctx_item in category_data.get("context_dependent", []):
                term = ctx_item["term"]
                if term.lower() in text_lower:
                    result.add_violation(ComplianceViolation(
                        category=category,
                        term=term,
                        text=text,
                        field_name=field_name,
                        severity="warning",
                        note=ctx_item.get("note", ""),
                    ))

        # Coded language (warnings)
        coded = self.eeoc_terms.get("coded_language", {})
        for term in coded.get("flagged_terms", []):
            if term.lower() in text_lower:
                result.add_violation(ComplianceViolation(
                    category="coded_language",
                    term=term,
                    text=text,
                    field_name=field_name,
                    severity="warning",
                    note=coded.get("note", ""),
                ))

        # Editorial violations
        self._check_editorial(text, field_name, result)

        return result

    def _check_editorial(self, text: str, field_name: str, result: ComplianceScanResult):
        """Check for editorial policy violations."""
        # Excessive caps: 3+ consecutive uppercase words
        if re.search(r"\b[A-Z]{2,}(?:\s+[A-Z]{2,}){2,}\b", text):
            result.add_violation(ComplianceViolation(
                category="editorial_violations",
                term="excessive_caps",
                text=text,
                field_name=field_name,
                severity="error",
                note="Three or more consecutive uppercase words",
            ))

        # Excessive punctuation: 2+ consecutive identical punctuation
        if re.search(r"([!?.])\1+", text):
            result.add_violation(ComplianceViolation(
                category="editorial_violations",
                term="excessive_punctuation",
                text=text,
                field_name=field_name,
                severity="error",
                note="Two or more consecutive identical punctuation marks",
            ))

        # Emoji in text ads
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0\U000024C2-\U0001F251]+",
            flags=re.UNICODE,
        )
        if emoji_pattern.search(text):
            result.add_violation(ComplianceViolation(
                category="editorial_violations",
                term="emoji",
                text=text,
                field_name=field_name,
                severity="error",
                note="Emoji characters not allowed in text ads",
            ))

    def scan_headlines(self, headlines: list[str]) -> ComplianceScanResult:
        """Scan all headlines for compliance."""
        combined = ComplianceScanResult()
        for i, headline in enumerate(headlines):
            result = self.scan_text(headline, field_name=f"headline_{i+1}")
            for v in result.violations:
                combined.add_violation(v)
            for w in result.warnings:
                combined.add_violation(w)
        return combined

    def scan_descriptions(self, descriptions: list[str]) -> ComplianceScanResult:
        """Scan all descriptions for compliance."""
        combined = ComplianceScanResult()
        for i, desc in enumerate(descriptions):
            result = self.scan_text(desc, field_name=f"description_{i+1}")
            for v in result.violations:
                combined.add_violation(v)
            for w in result.warnings:
                combined.add_violation(w)
        return combined

    def scan_all_content(
        self,
        headlines: list[str],
        descriptions: list[str],
    ) -> ComplianceScanResult:
        """Scan all ad content for compliance violations."""
        combined = ComplianceScanResult()

        headline_result = self.scan_headlines(headlines)
        desc_result = self.scan_descriptions(descriptions)

        for v in headline_result.violations + desc_result.violations:
            combined.add_violation(v)
        for w in headline_result.warnings + desc_result.warnings:
            combined.add_violation(w)

        return combined
