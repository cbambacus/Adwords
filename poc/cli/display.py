"""
Rich terminal output for the pipeline CLI.

Displays formatted tables, summaries, and validation results.
"""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def print_header(step_num: int, title: str):
    """Print a step header."""
    console.print()
    console.rule(f"[bold cyan]Step {step_num}: {title}[/]", style="cyan")
    console.print()


def print_success(message: str):
    console.print(f"  [green]\u2713[/] {message}")


def print_warning(message: str):
    console.print(f"  [yellow]\u26a0[/] {message}")


def print_error(message: str):
    console.print(f"  [red]\u2717[/] {message}")


def print_info(message: str):
    console.print(f"  {message}")


def display_job_order(job, signals: dict):
    """Display parsed job order details."""
    print_success(f"Valid job order: {job.job_id}")

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim", width=16)
    table.add_column()

    table.add_row("Title:", job.job_title)

    loc_str = job.work_arrangement.capitalize()
    if job.location.city:
        loc_str = f"{job.location.city}, {job.location.state} ({job.work_arrangement})"
    table.add_row("Location:", loc_str)

    if job.salary and job.salary.min:
        table.add_row("Salary:", f"${job.salary.min:,.0f} - ${job.salary.max:,.0f}/yr")
    else:
        table.add_row("Salary:", "[dim]Not provided[/]")

    table.add_row("Client:", job.client or "[dim]Not specified[/]")
    table.add_row("Employment:", job.employment_type or "[dim]Not specified[/]")
    table.add_row("Urgency:", signals["urgency"].capitalize())
    table.add_row("Seniority:", signals["seniority"].capitalize())
    table.add_row("Role Type:", signals["role_type"].capitalize())
    table.add_row("Geo Tier:", signals["geo_tier"].capitalize())

    if signals["salary_required"]:
        table.add_row("Compliance:", "[yellow]Salary disclosure REQUIRED[/]")
    if signals["client_confidential"]:
        table.add_row("Client:", "[yellow]CONFIDENTIAL - suppress name[/]")

    console.print(table)


def display_strategy_summary(brief: dict, signals: dict):
    """Display Strategy Brief summary table."""
    audience = brief.get("audience", {})
    tone = brief.get("tone_guidelines", {})
    compliance = brief.get("compliance_checklist", {})
    primary_kw = brief.get("primary_keywords", [])
    secondary_kw = brief.get("secondary_keywords", [])
    negative_kw = brief.get("negative_keywords", [])

    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column(style="dim", width=20)
    table.add_column()

    table.add_row("Seniority", audience.get("seniority_level", "N/A"))
    table.add_row("Role Type", signals.get("role_type", "N/A"))
    table.add_row("Candidate Mind.", audience.get("candidate_mindset", "N/A"))
    table.add_row("Tone", f"{tone.get('overall_tone', 'N/A')}, formal: {tone.get('formality_level', 'N/A')}")

    budget = brief.get("budget", {})
    if isinstance(budget, dict):
        table.add_row("Daily Budget", f"${budget.get('daily', 'N/A')} (Google Ads)")
    else:
        from poc.config.settings import BASE_DAILY_BUDGET, URGENCY_MULTIPLIER, GEO_ADJUSTMENT
        base = BASE_DAILY_BUDGET.get(signals["seniority"], 112)
        mult = URGENCY_MULTIPLIER.get(signals["urgency"], 1.0)
        adj = GEO_ADJUSTMENT.get(signals["geo_tier"], 1.0)
        daily = round(base * mult * adj)
        table.add_row("Daily Budget", f"${daily} (Google Ads)")

    if isinstance(compliance, dict):
        salary_disc = compliance.get("salary_disclosure", "N/A")
        table.add_row("Compliance", f"Salary: {salary_disc}")

    table.add_row("Primary KWs", f"{len(primary_kw)} keywords")
    table.add_row("Secondary KWs", f"{len(secondary_kw)} keywords")
    table.add_row("Negative KWs", f"{len(negative_kw)} keywords")

    console.print(table)


def display_strategy_full(brief: dict):
    """Display the full Strategy Brief YAML."""
    import yaml
    yaml_str = yaml.dump(brief, default_flow_style=False, sort_keys=False)
    console.print(Panel(yaml_str, title="Full Strategy Brief", border_style="cyan"))


def display_writer_validation(content: dict, content_result, compliance_result, primary_keywords: list = None):
    """Display Writer Agent validation results."""
    headlines = content.get("headlines", [])
    descriptions = content.get("descriptions", [])
    display_paths = content.get("display_paths", [])

    # Validation summary
    h_valid = all(len(h) <= 30 for h in headlines)
    d_valid = all(len(d) <= 90 for d in descriptions)
    p_valid = all(len(p) <= 15 for p in display_paths) if display_paths else True

    if h_valid and len(headlines) == 15:
        print_success(f"{len(headlines)} headlines (all \u226430 chars)")
    else:
        print_error(f"{len(headlines)} headlines (issues found)")

    if d_valid and len(descriptions) == 4:
        print_success(f"{len(descriptions)} descriptions (all \u226490 chars)")
    else:
        print_error(f"{len(descriptions)} descriptions (issues found)")

    if display_paths:
        if p_valid and len(display_paths) == 2:
            print_success(f"{len(display_paths)} display paths (all \u226415 chars)")
        else:
            print_error(f"{len(display_paths)} display paths (issues found)")

    if compliance_result.passed:
        print_success("Compliance scan: no prohibited terms")
    else:
        print_error(f"Compliance scan: {len(compliance_result.violations)} violation(s)")
        for v in compliance_result.violations:
            print_error(f"  {v.field_name}: {v.category} - '{v.term}'")

    if compliance_result.warnings:
        for w in compliance_result.warnings:
            print_warning(f"  {w.field_name}: {w.category} - '{w.term}' ({w.note})")

    # Keyword integration
    if primary_keywords:
        kw_count = 0
        for h in headlines:
            if any(kw.lower() in h.lower() for kw in primary_keywords):
                kw_count += 1
        if kw_count >= 3:
            print_success(f"Primary keywords in {kw_count}/{len(headlines)} headlines")
        else:
            print_warning(f"Primary keywords in only {kw_count}/{len(headlines)} headlines (3+ recommended)")

    # Duplicate check
    h_unique = len(set(h.lower() for h in headlines))
    if h_unique == len(headlines):
        print_success("No duplicates")
    else:
        print_error(f"Found {len(headlines) - h_unique} duplicate headline(s)")


def display_headlines(headlines: list[str]):
    """Display headlines with character counts."""
    console.print()
    console.print("  [bold]Headlines:[/]")
    for i, h in enumerate(headlines):
        char_count = len(h)
        status = "[green]" if char_count <= 30 else "[red]"
        dots = "." * max(1, 40 - len(h))
        console.print(f'   {i+1:2d}. "{h}" {dots}({status}{char_count} chars[/])')


def display_descriptions(descriptions: list[str]):
    """Display descriptions with character counts."""
    console.print()
    console.print("  [bold]Descriptions:[/]")
    for i, d in enumerate(descriptions):
        char_count = len(d)
        status = "[green]" if char_count <= 90 else "[red]"
        console.print(f"   {i+1}. \"{d}\"")
        console.print(f"      ({status}{char_count} chars[/])")


def display_campaign_summary(summary: dict):
    """Display campaign builder summary."""
    print_success("Campaign structure built")
    console.print()

    console.print(f"  Campaign: [bold]{summary['campaign_name']}[/] (PAUSED)")
    console.print(f"  Budget:   ${summary['daily_budget']}/day | Bidding: {summary['bidding_strategy']}")

    loc = summary["location"]
    if loc["target_type"] == "radius":
        console.print(f"  Location: {loc.get('city', '')} +{loc.get('radius_miles', '')}mi radius")
    else:
        console.print(f"  Location: National ({loc.get('country', 'US')})")

    # Ad groups table
    table = Table(box=box.SIMPLE, padding=(0, 2))
    table.add_column("Ad Group", style="bold")
    table.add_column("KWs", justify="right")
    table.add_column("Negs", justify="right")
    table.add_column("RSA")

    for ag in summary["ad_groups"]:
        table.add_row(
            ag["name"],
            str(ag["keyword_count"]),
            str(ag["negative_keyword_count"]),
            ag["rsa_summary"],
        )

    console.print(table)


def display_campaign_json(campaign: dict):
    """Display full campaign JSON."""
    import json
    json_str = json.dumps(campaign, indent=2, default=str)
    console.print(Panel(json_str, title="Full Campaign Structure (JSON)", border_style="cyan"))


def display_publish_result(result: dict):
    """Display Google Ads publish results."""
    if result.get("success"):
        print_success(f"Campaign created: {result.get('campaign_resource_name', 'N/A')}")
        for item in result.get("created", []):
            print_success(item)
    else:
        print_error(f"Publish failed: {result.get('error', 'Unknown error')}")
