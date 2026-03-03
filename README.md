# AI Recruitment Advertising System

AI-powered recruitment advertising system that automates job ad creation, placement, and optimization across multiple advertising platforms.

## What It Does

Takes a job order from Cloudwall and automatically:
1. **Analyzes** the role (seniority, type, urgency, compliance requirements)
2. **Strategizes** targeting, budget, and keywords via an AI Strategy Agent
3. **Writes** platform-optimized ad copy via an AI Writer Agent
4. **Builds** a Google Ads campaign structure with intent-based ad groups
5. **Publishes** to a Google Ads test account (human-approved)

## Three-Agent Architecture

| Agent | Role |
|-------|------|
| **Strategy Agent** | Analyzes job data, determines targeting, allocates budget, generates keyword strategy |
| **Writer Agent** | Generates RSA content (15 headlines, 4 descriptions) within character limits |
| **Optimizer Agent** | Monitors performance, adjusts bids, feeds learnings back (future phase) |

## Quick Start

```bash
# Install dependencies
pip3 install -r poc/requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY=your-key-here

# Run the pipeline on a test job order
python3 poc/run_pipeline.py Tests/test-job-orders/test-001-senior-ux-designer.json

# Or run the demo (no API key needed)
python3 poc/run_demo.py Tests/test-job-orders/test-001-senior-ux-designer.json

# Run tests
python3 -m pytest poc/tests/ -v
```

## Repository Structure

```
Adwords/
├── Architecture/          # System specification documents
│   ├── system-overview.md
│   ├── strategy-agent-rulebook.md
│   ├── optimizer-data-flow.md
│   ├── learnings-database.md
│   ├── platform-interface.md
│   └── adapters/
├── Knowledge-Base/        # Strategy Agent reference materials
│   ├── platform-specs/    # Google Ads, LinkedIn, Indeed, Meta
│   ├── candidate-psychology/
│   ├── compliance/        # EEOC, salary transparency
│   └── benchmarks/
├── Research/              # Background research
├── Tests/
│   ├── poc-test-plan.md
│   ├── test-job-orders/   # 5 test job orders (JSON)
│   └── compliance-wordlists/
├── poc/                   # POC implementation
│   ├── run_pipeline.py    # CLI entry point
│   ├── run_demo.py        # Demo mode (no API calls)
│   ├── agents/            # Strategy + Writer Claude API agents
│   ├── pipeline/          # Job parser, campaign builder, publisher
│   ├── validation/        # Compliance scanner, content validator
│   ├── cli/               # Rich terminal UI
│   └── tests/             # 132 pytest tests
└── CLAUDE.md              # AI assistant project context
```

## Pipeline Flow

```
$ python3 poc/run_pipeline.py <job_order.json>

Step 1: Parse Job Order      → Validates input, extracts signals
Step 2: Strategy Agent        → Claude API → YAML Strategy Brief
Step 3: Writer Agent          → Claude API → RSA headlines + descriptions
Step 4: Campaign Builder      → Maps to Google Ads campaign structure
Step 5: Publish to Google Ads → Test account only (human-gated)
```

Each step pauses for human review. All intermediate outputs are saved to `poc/output/<job_id>/`.

## Test Job Orders

| ID | Role | Seniority | Location | Key Coverage |
|----|------|-----------|----------|-------------|
| TEST-001 | Senior UX Designer | Senior | SF, CA (hybrid) | CA salary law, tier-1 CPC, urgent fill |
| TEST-002 | Marketing Coordinator | Entry | Austin, TX (onsite) | No salary mandate, entry messaging |
| TEST-003 | Python Developer | Mid | Remote US | National targeting, no salary data |
| TEST-004 | Junior Graphic Designer | Entry | Denver, CO (onsite) | CO salary law, confidential client |
| TEST-005 | VP of Engineering | Executive | NYC, NY (hybrid) | NYC salary law, executive tone, critical urgency |

## Current Phase

**POC** — Google Ads test account only. All campaigns created in PAUSED state. No real ads serve, no real money spent. Switching to production requires a config change in `poc/config/settings.py`.

## Stakeholders

| Name | Role |
|------|------|
| Chris | Product Owner |
| John | CEO |
| Simon | Operations |
| Randy | Google Ads SME |
| Aarthi | Dev Lead |
| Zac | CTO |
| Jason | Marketing |
