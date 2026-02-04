# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the **system specification** for Aquent's AI-powered recruitment advertising system. The system automates job ad creation, placement, and optimization across multiple advertising platforms with a continuous learning feedback loop.

**Current Phase**: Architecture Documentation

## Project Vision & Goals

Build an autonomous recruitment advertising system that:
- Automatically generates optimized job advertisements from Cloudwall job data
- Places ads across multiple platforms (Google Ads, LinkedIn, Indeed, etc.)
- Continuously learns from performance data to improve results
- Minimizes cost-per-qualified-candidate while maximizing talent pipeline quality

## Three-Agent Architecture

The system uses three specialized AI agents working in concert:

| Agent | Responsibility |
|-------|----------------|
| **Strategy Agent** | Analyzes job requirements, determines targeting strategy, allocates budget across platforms |
| **Writer Agent** | Generates ad copy optimized for each platform's requirements and audience |
| **Optimizer Agent** | Monitors performance metrics, adjusts bids/targeting, feeds learnings back to other agents |

See [Architecture/system-overview.md](Architecture/system-overview.md) for detailed specifications.

## Data Flow

```
Cloudwall (Job Data Source)
    ↓
Strategy Agent → Writer Agent → Multi-Platform Ads
    ↓                               ↓
    ←←← Optimizer Agent ←←← Performance Data
            ↓
    Learnings Database (feeds back to Strategy & Writer)
```

## Cloudwall Data Inputs

The system receives job data from Cloudwall containing:
- Job title
- Job description
- Salary/compensation
- Location
- Work arrangement (remote/hybrid/onsite)
- Additional notes

## Stakeholders

| Name | Role | Responsibility |
|------|------|----------------|
| Chris | Product Owner | Requirements, prioritization, acceptance |
| John | CEO | Strategic direction, business alignment |
| Simon | Operations | Operational integration, process alignment |
| Randy | SME | Google Ads expertise, domain knowledge |
| Aarthi | Dev Lead | Technical leadership, implementation |
| Zac | CTO | Technical strategy, architecture approval |
| Jason | Marketing | Marketing alignment, brand consistency |

## Success Metrics

- **Primary**: Cost-per-qualified-candidate
- **Secondary**: Talent pipeline volume and quality
- Platform-specific metrics (CTR, conversion rate, quality score)

## Compliance Requirements

- **GDPR**: European data protection compliance
- **CCPA**: California consumer privacy compliance
- Platform-specific advertising policies

## Repository Structure

```
Adwords/
├── CLAUDE.md              # This file - project overview and guidance
├── Architecture/          # System specification documents
│   └── system-overview.md # High-level architecture documentation
├── Research/              # Background research and primers
│   ├── chatgpt-primer.md  # Google Ads fundamentals
│   ├── gemini-primer.md   # AI optimization strategy (3 phases)
│   └── *-sources.md/csv   # Curated research sources
└── AI-Ads-flowchart.png   # Visual architecture diagram
```

**Note**: The flowchart shows "Crosswall" which should be "Cloudwall" - image update pending.

## Working with This Repository

1. Start with this file for project context
2. Review [Architecture/system-overview.md](Architecture/system-overview.md) for technical specifications
3. Reference Research/ directory for Google Ads fundamentals and optimization strategies
4. Use the flowchart for visual system overview

## Key Optimization Framework

From the research primers, the core optimization approach follows three phases:

1. **Phase A**: Optimize ad copy using AI (RSAs, Gemini integration)
2. **Phase B**: Optimize targets (Performance Max, Broad Match + Smart Bidding)
3. **Phase C**: Monitor & steer (Insights, negative keywords, weekly Search Terms Report)

## Development Notes

- Google Ads API developer token access needs verification before prototyping phase
- Intake is Cloudwall-controlled (system responds to job postings, doesn't initiate)
- Budget guardrails and cost thresholds must be implemented before any autonomous operation
