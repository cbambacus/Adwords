"""
Content validator for Writer Agent output.

Validates:
- Character limits (headlines ≤ 30, descriptions ≤ 90, display paths ≤ 15)
- Required counts (15 headlines, 4 descriptions, 2 display paths)
- No duplicate headlines or descriptions
- Primary keyword presence in headlines
- Content quality checks
"""

from __future__ import annotations

from dataclasses import dataclass, field

from poc.config.settings import (
    RSA_DESCRIPTION_COUNT,
    RSA_DESCRIPTION_MAX_CHARS,
    RSA_DISPLAY_PATH_COUNT,
    RSA_DISPLAY_PATH_MAX_CHARS,
    RSA_HEADLINE_COUNT,
    RSA_HEADLINE_MAX_CHARS,
)


@dataclass
class ValidationIssue:
    field: str       # e.g., "headline_3", "descriptions"
    issue: str       # description of the problem
    severity: str    # "error" or "warning"
    value: str = ""  # the offending value


@dataclass
class ContentValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def add(self, issue: ValidationIssue):
        self.issues.append(issue)


class ContentValidator:
    """Validates Writer Agent output against Google Ads RSA constraints."""

    def validate_headlines(
        self,
        headlines: list[str],
        primary_keywords: list[str] | None = None,
    ) -> ContentValidationResult:
        """Validate headlines for count, length, uniqueness, and keyword presence."""
        result = ContentValidationResult()

        # Count check
        if len(headlines) != RSA_HEADLINE_COUNT:
            result.add(ValidationIssue(
                field="headlines",
                issue=f"Expected {RSA_HEADLINE_COUNT} headlines, got {len(headlines)}",
                severity="error",
            ))

        # Character limit check
        for i, h in enumerate(headlines):
            if len(h) > RSA_HEADLINE_MAX_CHARS:
                result.add(ValidationIssue(
                    field=f"headline_{i+1}",
                    issue=f"Exceeds {RSA_HEADLINE_MAX_CHARS} chars ({len(h)} chars)",
                    severity="error",
                    value=h,
                ))

        # Empty check
        for i, h in enumerate(headlines):
            if not h.strip():
                result.add(ValidationIssue(
                    field=f"headline_{i+1}",
                    issue="Empty headline",
                    severity="error",
                ))

        # Uniqueness check
        seen = set()
        for i, h in enumerate(headlines):
            normalized = h.strip().lower()
            if normalized in seen:
                result.add(ValidationIssue(
                    field=f"headline_{i+1}",
                    issue="Duplicate headline",
                    severity="error",
                    value=h,
                ))
            seen.add(normalized)

        # Primary keyword presence (at least 3 headlines should contain a primary keyword)
        if primary_keywords:
            kw_count = 0
            for h in headlines:
                h_lower = h.lower()
                if any(kw.lower() in h_lower for kw in primary_keywords):
                    kw_count += 1

            if kw_count < 3:
                result.add(ValidationIssue(
                    field="headlines",
                    issue=f"Only {kw_count}/3 minimum headlines contain primary keywords",
                    severity="warning",
                ))

        return result

    def validate_descriptions(self, descriptions: list[str]) -> ContentValidationResult:
        """Validate descriptions for count, length, and uniqueness."""
        result = ContentValidationResult()

        # Count check
        if len(descriptions) != RSA_DESCRIPTION_COUNT:
            result.add(ValidationIssue(
                field="descriptions",
                issue=f"Expected {RSA_DESCRIPTION_COUNT} descriptions, got {len(descriptions)}",
                severity="error",
            ))

        # Character limit check
        for i, d in enumerate(descriptions):
            if len(d) > RSA_DESCRIPTION_MAX_CHARS:
                result.add(ValidationIssue(
                    field=f"description_{i+1}",
                    issue=f"Exceeds {RSA_DESCRIPTION_MAX_CHARS} chars ({len(d)} chars)",
                    severity="error",
                    value=d,
                ))

        # Empty check
        for i, d in enumerate(descriptions):
            if not d.strip():
                result.add(ValidationIssue(
                    field=f"description_{i+1}",
                    issue="Empty description",
                    severity="error",
                ))

        # Uniqueness check
        seen = set()
        for i, d in enumerate(descriptions):
            normalized = d.strip().lower()
            if normalized in seen:
                result.add(ValidationIssue(
                    field=f"description_{i+1}",
                    issue="Duplicate description",
                    severity="error",
                    value=d,
                ))
            seen.add(normalized)

        return result

    def validate_display_paths(self, paths: list[str]) -> ContentValidationResult:
        """Validate display URL paths."""
        result = ContentValidationResult()

        if len(paths) != RSA_DISPLAY_PATH_COUNT:
            result.add(ValidationIssue(
                field="display_paths",
                issue=f"Expected {RSA_DISPLAY_PATH_COUNT} display paths, got {len(paths)}",
                severity="error",
            ))

        for i, p in enumerate(paths):
            if len(p) > RSA_DISPLAY_PATH_MAX_CHARS:
                result.add(ValidationIssue(
                    field=f"display_path_{i+1}",
                    issue=f"Exceeds {RSA_DISPLAY_PATH_MAX_CHARS} chars ({len(p)} chars)",
                    severity="error",
                    value=p,
                ))

        return result

    def validate_all(
        self,
        headlines: list[str],
        descriptions: list[str],
        display_paths: list[str] | None = None,
        primary_keywords: list[str] | None = None,
    ) -> ContentValidationResult:
        """Run all validations on writer output."""
        combined = ContentValidationResult()

        for issue in self.validate_headlines(headlines, primary_keywords).issues:
            combined.add(issue)

        for issue in self.validate_descriptions(descriptions).issues:
            combined.add(issue)

        if display_paths is not None:
            for issue in self.validate_display_paths(display_paths).issues:
                combined.add(issue)

        return combined
