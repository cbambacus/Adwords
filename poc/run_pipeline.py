#!/usr/bin/env python3
"""
AI Recruitment Advertising POC — CLI Pipeline

Run the full pipeline for a job order:
  Step 1: Parse Job Order
  Step 2: Strategy Agent (Claude API)
  Step 3: Writer Agent (Claude API)
  Step 4: Campaign Builder
  Step 5: Publish to Google Ads (test account)

Usage:
  python run_pipeline.py <job_order.json>
  python run_pipeline.py Tests/test-job-orders/test-001-senior-ux-designer.json
"""

from __future__ import annotations

import json
import sys
import shutil
from datetime import datetime
from pathlib import Path

from rich.console import Console

# Ensure poc package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from poc.config.settings import OUTPUT_DIR
from poc.pipeline.job_order import parse_job_order, extract_signals
from poc.agents.strategy_agent import run_strategy_agent
from poc.agents.writer_agent import run_writer_agent
from poc.pipeline.campaign_builder import build_campaign, get_campaign_summary
from poc.validation.compliance_scanner import ComplianceScanner
from poc.validation.content_validator import ContentValidator
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
    display_publish_result,
)
from poc.cli.prompts import prompt_continue, prompt_publish


def _ensure_output_dir(job_id: str) -> Path:
    """Create and return the output directory for a job run."""
    run_dir = OUTPUT_DIR / job_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _save_json(data: dict, filepath: Path):
    """Save dict as formatted JSON."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print_info(f"  Saved: {filepath.name}")


def _save_yaml(text: str, filepath: Path):
    """Save raw YAML string."""
    with open(filepath, "w") as f:
        f.write(text)
    print_info(f"  Saved: {filepath.name}")


def _save_text(text: str, filepath: Path):
    """Save plain text."""
    with open(filepath, "w") as f:
        f.write(text)


class RunLog:
    """Timestamped log for the pipeline run."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self._lines = []
        self.log(f"Pipeline run started")

    def log(self, message: str):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        line = f"[{timestamp}] {message}"
        self._lines.append(line)
        with open(self.filepath, "a") as f:
            f.write(line + "\n")

    def save(self):
        with open(self.filepath, "w") as f:
            f.write("\n".join(self._lines) + "\n")


def run_pipeline(job_order_path: str):
    """Run the full pipeline for a job order."""

    # ━━━ Step 1: Parse Job Order ━━━
    print_header(1, "Parse Job Order")

    try:
        job = parse_job_order(job_order_path)
    except FileNotFoundError as e:
        print_error(f"File not found: {e}")
        return
    except Exception as e:
        print_error(f"Failed to parse job order: {e}")
        return

    signals = extract_signals(job)
    display_job_order(job, signals)

    # Set up output directory and log
    run_dir = _ensure_output_dir(job.job_id)
    run_log = RunLog(run_dir / "run-log.txt")
    run_log.log(f"Job order: {job.job_id} - {job.job_title}")
    run_log.log(f"Signals: {json.dumps(signals)}")

    # Save copy of input
    shutil.copy2(job_order_path, run_dir / "job-order.json")

    choice = prompt_continue()
    if choice == "q":
        run_log.log("User quit at Step 1")
        return

    # ━━━ Step 2: Strategy Agent ━━━
    print_header(2, "Strategy Agent")
    print_info("Calling Claude API...")

    try:
        strategy_result = run_strategy_agent(job, signals)
    except Exception as e:
        print_error(f"Strategy Agent failed: {e}")
        run_log.log(f"Strategy Agent error: {e}")
        return

    brief = strategy_result["brief"]
    brief_yaml = strategy_result["brief_yaml"]
    brief_validation = strategy_result["validation"]

    if brief_validation.passed:
        print_success("Strategy Brief generated (valid YAML)")
    else:
        print_warning(f"Strategy Brief has {len(brief_validation.errors)} validation issue(s)")
        for err in brief_validation.errors:
            print_warning(f"  {err.path}: {err.issue}")

    console.print()
    console.print("  [bold]Summary:[/]")
    display_strategy_summary(brief, signals)

    # Save strategy brief
    _save_yaml(brief_yaml, run_dir / "strategy-brief.yaml")
    run_log.log("Strategy Brief generated and saved")

    while True:
        choice = prompt_continue({"v": "View full Strategy Brief"})
        if choice == "v":
            display_strategy_full(brief)
        elif choice == "q":
            run_log.log("User quit at Step 2")
            return
        else:
            break

    # ━━━ Step 3: Writer Agent ━━━
    print_header(3, "Writer Agent")

    while True:
        print_info("Calling Claude API...")

        try:
            writer_result = run_writer_agent(brief)
        except Exception as e:
            print_error(f"Writer Agent failed: {e}")
            run_log.log(f"Writer Agent error: {e}")
            return

        content = writer_result["content"]
        content_validation = writer_result["content_validation"]
        compliance_scan = writer_result["compliance_scan"]

        if content_validation.passed and compliance_scan.passed:
            print_success("Content generated")
        else:
            print_warning("Content generated with issues")

        console.print()
        console.print("  [bold]Validation:[/]")
        display_writer_validation(
            content,
            content_validation,
            compliance_scan,
            primary_keywords=brief.get("primary_keywords", []),
        )

        display_headlines(content.get("headlines", []))

        # Save writer content
        _save_json(content, run_dir / "writer-content.json")

        # Save validation report
        validation_report = {
            "content_validation": {
                "passed": content_validation.passed,
                "errors": [
                    {"field": i.field, "issue": i.issue, "value": i.value}
                    for i in content_validation.errors
                ],
                "warnings": [
                    {"field": i.field, "issue": i.issue, "value": i.value}
                    for i in content_validation.warnings
                ],
            },
            "compliance_scan": {
                "passed": compliance_scan.passed,
                "violations": [
                    {"category": v.category, "term": v.term, "field": v.field_name}
                    for v in compliance_scan.violations
                ],
                "warnings": [
                    {"category": w.category, "term": w.term, "field": w.field_name}
                    for w in compliance_scan.warnings
                ],
            },
        }
        _save_json(validation_report, run_dir / "validation-report.json")
        run_log.log("Writer content generated and saved")

        while True:
            choice = prompt_continue({
                "v": "View all headlines + descriptions",
                "r": "Regenerate (re-run Writer Agent)",
            })

            if choice == "v":
                display_headlines(content.get("headlines", []))
                display_descriptions(content.get("descriptions", []))
                continue
            elif choice == "r":
                run_log.log("User requested Writer Agent regeneration")
                break  # inner loop → re-run writer
            elif choice == "q":
                run_log.log("User quit at Step 3")
                return
            else:
                break  # inner loop → proceed

        if choice != "r":
            break  # outer loop → proceed to step 4

    # ━━━ Step 4: Campaign Builder ━━━
    print_header(4, "Campaign Builder")

    # Add job_id to brief for campaign builder
    brief["job_id"] = job.job_id
    campaign = build_campaign(brief, content, signals)
    summary = get_campaign_summary(campaign)

    display_campaign_summary(summary)

    # Save campaign structure
    _save_json(campaign, run_dir / "campaign-structure.json")
    run_log.log("Campaign structure built and saved")

    while True:
        choice = prompt_continue({"v": "View full campaign structure (JSON)"})
        if choice == "v":
            display_campaign_json(campaign)
        elif choice == "q":
            run_log.log("User quit at Step 4")
            return
        else:
            break

    # ━━━ Step 5: Publish to Google Ads ━━━
    print_header(5, "Publish to Google Ads")
    console.print("  Target: [bold yellow]TEST ACCOUNT[/] (no real spend)")
    console.print()
    console.print("  [yellow]\u26a0 This will create a campaign in your Google Ads test account.[/]")
    console.print("  [yellow]  No real ads will serve. No real money will be spent.[/]")

    choice = prompt_publish()

    if choice == "p":
        print_info("Publishing...")
        try:
            from poc.pipeline.publisher import publish_campaign
            result = publish_campaign(campaign)
            display_publish_result(result)
            _save_json(result, run_dir / "campaign-result.json")
            run_log.log(f"Campaign published: {result.get('campaign_resource_name', 'N/A')}")
        except ImportError:
            print_warning("Google Ads publisher not yet configured.")
            print_info("Campaign structure saved to JSON — you can import it manually.")
            run_log.log("Publish skipped: publisher not configured")
        except Exception as e:
            print_error(f"Publish failed: {e}")
            run_log.log(f"Publish error: {e}")

    elif choice == "s":
        print_success(f"Campaign saved to: {run_dir / 'campaign-structure.json'}")
        run_log.log("User chose save only (skip publish)")

    else:
        run_log.log("User quit at Step 5")
        return

    # Final summary
    console.print()
    console.rule("[bold green]Pipeline Complete[/]", style="green")
    console.print()
    console.print(f"  All artifacts saved to: [bold]{run_dir}[/]")
    console.print()
    run_log.log("Pipeline complete")


def main():
    if len(sys.argv) < 2:
        console.print("[bold]AI Recruitment Advertising POC[/]")
        console.print()
        console.print("Usage: python run_pipeline.py <job_order.json>")
        console.print()
        console.print("Example:")
        console.print("  python run_pipeline.py Tests/test-job-orders/test-001-senior-ux-designer.json")
        sys.exit(1)

    job_order_path = sys.argv[1]
    run_pipeline(job_order_path)


if __name__ == "__main__":
    main()
