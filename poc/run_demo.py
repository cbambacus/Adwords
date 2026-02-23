#!/usr/bin/env python3
"""
Demo mode — runs the full pipeline with fixture data (no API calls).

Shows exactly what the live pipeline looks like, using pre-built
Strategy Brief and Writer content for TEST-001.
"""

from __future__ import annotations

import json
import sys
import shutil
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from poc.config.settings import OUTPUT_DIR
from poc.pipeline.job_order import parse_job_order, extract_signals
from poc.pipeline.campaign_builder import build_campaign, get_campaign_summary
from poc.validation.brief_validator import parse_strategy_brief, validate_brief
from poc.validation.content_validator import ContentValidator
from poc.validation.compliance_scanner import ComplianceScanner
from poc.cli.display import (
    console,
    print_header,
    print_success,
    print_warning,
    print_error,
    print_info,
    display_job_order,
    display_strategy_summary,
    display_strategy_full,
    display_writer_validation,
    display_headlines,
    display_descriptions,
    display_campaign_summary,
    display_campaign_json,
)
from poc.cli.prompts import prompt_continue, prompt_publish


# --- Fixture data (what the Claude API would return) ---

STRATEGY_BRIEF_YAML = """\
job_title: Senior UX Designer
job_id: TEST-001
client: FinTech Innovations Inc.
location: San Francisco, CA (hybrid)
work_arrangement: hybrid
compensation: "$130,000 - $155,000/yr"

audience:
  seniority_level: Senior
  years_experience: "5-10"
  current_likely_titles:
    - UX Designer
    - Senior Product Designer
    - Lead UX Designer
    - UI/UX Designer
  candidate_mindset: mixed
  primary_motivations:
    - Career growth into design leadership
    - Working on impactful fintech products
    - Competitive compensation with hybrid flexibility
  pain_points_to_address:
    - Limited growth at current company
    - Want more influence on product direction
    - Seeking better work-life balance

key_selling_points:
  primary:
    point: Lead the redesign of a flagship mobile banking application
    rationale: Senior designers want ownership, impact, and the chance to shape products
  secondary:
    - point: "$130K-$155K with contract-to-hire path to permanent"
      rationale: Salary transparency required in CA; competitive range signals value
    - point: "Hybrid 3 days/week in San Francisco fintech"
      rationale: Flexibility matters; SF is a premier design hub
    - point: Mentor junior designers and grow the design practice
      rationale: Leadership opportunity without full management burden

differentiators:
  - Mentorship opportunity with junior designers
  - Fintech innovation space with modern design tooling
  - Contract-to-hire path provides try-before-you-commit

avoid_messaging:
  - Generic "fast-paced environment"
  - Overused "rock star" or "ninja" language
  - Vague "competitive benefits" without specifics

tone_guidelines:
  overall_tone: Inspirational
  formality_level: 2
  industry_conventions: Design community values craft, portfolio work, and real product impact

platforms:
  google_search:
    enabled: true
    headlines_needed: 15
    descriptions_needed: 4
    headline_max_chars: 30
    description_max_chars: 90
    special_notes: Include salary in at least one headline and one description (CA compliance). Highlight hybrid arrangement and fintech context.
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
  - courses
  - training
  - certification
  - tutorial
  - bootcamp
  - salary survey
  - freelance
  - freelancer
  - intern
  - internship
  - junior designer
  - entry level
  - template
  - free download
  - DIY
  - resume template
  - cover letter
  - interview questions
  - what does a UX designer do
  - UX design degree
  - learn UX design

compliance_checklist:
  no_discriminatory_language: REQUIRED
  salary_disclosure: REQUIRED
  equal_opportunity_mention: REQUIRED
  no_guaranteed_outcomes: REQUIRED
  platform_policy_compliant: REQUIRED

variation_strategy:
  total_variations_needed: 3
  a_b_test_elements:
    - Salary in headline vs. benefit-led headline
    - CTA phrasing (Apply Now vs. Learn More vs. See Role)
"""

WRITER_CONTENT = {
    "headlines": [
        "Senior UX Designer - Apply",
        "UX Design Lead | FinTech",
        "$130K-$155K UX Designer",
        "Hybrid UX Role in SF",
        "Lead Mobile UX Redesign",
        "UX Designer San Francisco",
        "Senior Figma UX Designer",
        "Apply: Senior UX Role",
        "UX Designer | Hybrid 3d/wk",
        "FinTech UX Design Lead",
        "Mentor + Design in SF",
        "UX Designer - Apply Now",
        "Mobile Banking UX Lead",
        "Top UX Role in FinTech",
        "Join Our Design Team"
    ],
    "descriptions": [
        "Lead the redesign of our mobile banking app. $130K-$155K. Hybrid in SF. Apply today!",
        "Senior UX Designer role in fintech. Figma, WCAG, B2C experience valued. Hybrid SF.",
        "Shape the future of mobile banking UX. Mentor junior designers. Contract-to-hire.",
        "5+ yrs UX experience? Join our SF fintech team. Hybrid schedule, competitive salary."
    ],
    "display_paths": ["UX-Design", "Apply"]
}


def run_demo(job_order_path: str):
    """Run the pipeline demo with fixture data."""

    # ━━━ Step 1: Parse Job Order ━━━
    print_header(1, "Parse Job Order")

    try:
        job = parse_job_order(job_order_path)
    except Exception as e:
        print_error(f"Failed to parse job order: {e}")
        return

    signals = extract_signals(job)
    display_job_order(job, signals)

    run_dir = OUTPUT_DIR / job.job_id
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(job_order_path, run_dir / "job-order.json")

    choice = prompt_continue()
    if choice == "q":
        return

    # ━━━ Step 2: Strategy Agent ━━━
    print_header(2, "Strategy Agent")
    print_info("Calling Claude API...")

    # Simulate API delay
    time.sleep(1.5)

    brief = parse_strategy_brief(STRATEGY_BRIEF_YAML)
    brief_validation = validate_brief(brief)

    if brief_validation.passed:
        print_success("Strategy Brief generated (valid YAML)")
    else:
        print_warning(f"Strategy Brief has {len(brief_validation.errors)} issue(s)")
        for err in brief_validation.errors:
            print_warning(f"  {err.path}: {err.issue}")

    console.print()
    console.print("  [bold]Summary:[/]")
    display_strategy_summary(brief, signals)

    # Save
    with open(run_dir / "strategy-brief.yaml", "w") as f:
        f.write(STRATEGY_BRIEF_YAML)
    print_info(f"  Saved: strategy-brief.yaml")

    while True:
        choice = prompt_continue({"v": "View full Strategy Brief"})
        if choice == "v":
            display_strategy_full(brief)
        elif choice == "q":
            return
        else:
            break

    # ━━━ Step 3: Writer Agent ━━━
    print_header(3, "Writer Agent")
    print_info("Calling Claude API...")

    time.sleep(1.5)

    content = WRITER_CONTENT
    validator = ContentValidator()
    scanner = ComplianceScanner()

    content_validation = validator.validate_all(
        headlines=content["headlines"],
        descriptions=content["descriptions"],
        display_paths=content["display_paths"],
        primary_keywords=brief.get("primary_keywords", []),
    )
    compliance_scan = scanner.scan_all_content(content["headlines"], content["descriptions"])

    if content_validation.passed and compliance_scan.passed:
        print_success("Content generated")
    else:
        print_warning("Content generated with issues")

    console.print()
    console.print("  [bold]Validation:[/]")
    display_writer_validation(content, content_validation, compliance_scan, brief.get("primary_keywords", []))
    display_headlines(content["headlines"])

    # Save
    with open(run_dir / "writer-content.json", "w") as f:
        json.dump(content, f, indent=2)
    print_info(f"  Saved: writer-content.json")

    validation_report = {
        "content_validation": {"passed": content_validation.passed, "errors": len(content_validation.errors)},
        "compliance_scan": {"passed": compliance_scan.passed, "violations": len(compliance_scan.violations)},
    }
    with open(run_dir / "validation-report.json", "w") as f:
        json.dump(validation_report, f, indent=2)

    while True:
        choice = prompt_continue({
            "v": "View all headlines + descriptions",
            "r": "Regenerate (re-run Writer Agent)",
        })
        if choice == "v":
            display_headlines(content["headlines"])
            display_descriptions(content["descriptions"])
        elif choice == "q":
            return
        else:
            break

    # ━━━ Step 4: Campaign Builder ━━━
    print_header(4, "Campaign Builder")

    brief["job_id"] = job.job_id
    campaign = build_campaign(brief, content, signals)
    summary = get_campaign_summary(campaign)

    display_campaign_summary(summary)

    with open(run_dir / "campaign-structure.json", "w") as f:
        json.dump(campaign, f, indent=2, default=str)
    print_info(f"  Saved: campaign-structure.json")

    while True:
        choice = prompt_continue({"v": "View full campaign structure (JSON)"})
        if choice == "v":
            display_campaign_json(campaign)
        elif choice == "q":
            return
        else:
            break

    # ━━━ Step 5: Publish to Google Ads ━━━
    print_header(5, "Publish to Google Ads")
    console.print("  Target: [bold yellow]TEST ACCOUNT[/] (no real spend)")
    console.print()
    console.print("  [yellow]⚠ This will create a campaign in your Google Ads test account.[/]")
    console.print("  [yellow]  No real ads will serve. No real money will be spent.[/]")

    choice = prompt_publish()

    if choice == "p":
        print_warning("Google Ads test account not configured yet.")
        print_info("Campaign structure saved — ready to publish when account is set up.")
    elif choice == "s":
        print_success(f"Campaign saved to: {run_dir / 'campaign-structure.json'}")
    else:
        return

    # Final
    console.print()
    console.rule("[bold green]Pipeline Complete[/]", style="green")
    console.print()
    console.print(f"  All artifacts saved to: [bold]{run_dir}[/]")
    console.print()


def main():
    if len(sys.argv) < 2:
        console.print("[bold]AI Recruitment Advertising POC — Demo Mode[/]")
        console.print()
        console.print("Usage: python run_demo.py <job_order.json>")
        console.print()
        console.print("Example:")
        console.print("  python run_demo.py Tests/test-job-orders/test-001-senior-ux-designer.json")
        sys.exit(1)

    run_demo(sys.argv[1])


if __name__ == "__main__":
    main()
