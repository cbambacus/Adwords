# System Architecture Overview

Aquent AI-Powered Recruitment Advertising System

## Executive Summary

This document describes the architecture for an AI-powered system that automates recruitment advertising across multiple platforms. The system ingests job data from Cloudwall, generates optimized advertisements, distributes them across advertising platforms, and continuously learns from performance data to improve results.

## System Overview

### Core Concept

The system operates as an autonomous advertising engine that:
1. Receives job postings from Cloudwall (intake-controlled)
2. Analyzes job requirements and determines optimal advertising strategy
3. Generates platform-specific ad copy
4. Publishes ads across multiple platforms
5. Monitors performance and optimizes in real-time
6. Captures learnings to improve future campaigns

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLOUDWALL                                   │
│                         (Job Data Source)                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Job Title | Description | Salary | Location | Work Arr. | Notes │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           AI AGENT LAYER                                 │
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │   STRATEGY   │───▶│    WRITER    │───▶│   PLATFORM ADAPTERS      │  │
│  │    AGENT     │    │    AGENT     │    │  ┌────────────────────┐  │  │
│  └──────────────┘    └──────────────┘    │  │ Google Ads         │  │  │
│         │                                 │  │ LinkedIn           │  │  │
│         │                                 │  │ Indeed             │  │  │
│         ▼                                 │  │ (extensible)       │  │  │
│  ┌──────────────┐                        │  └────────────────────┘  │  │
│  │  OPTIMIZER   │◀───────────────────────┤                          │  │
│  │    AGENT     │                        └──────────────────────────┘  │
│  └──────────────┘                                                       │
│         │                                                                │
│         ▼                                                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     LEARNINGS DATABASE                            │  │
│  │         (Performance patterns, successful strategies)             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ADVERTISING PLATFORMS                             │
│                                                                          │
│    Google Ads    │    LinkedIn    │    Indeed    │    Others...         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    Impressions → Clicks → Conversions
                                    │
                                    ▼
                         Performance Metrics
                      (fed back to Optimizer Agent)
```

## Three-Agent Architecture

### Strategy Agent

**Purpose**: Analyzes job requirements and determines the optimal advertising approach.

**Inputs**:
- Job data from Cloudwall
- Historical performance data from Learnings Database
- Budget constraints and business rules

**Responsibilities**:
- Analyze job type, seniority, location, and market conditions
- Determine which platforms to advertise on
- Allocate budget across platforms
- Set targeting parameters (keywords, audiences, demographics)
- Define campaign goals and KPIs

**Outputs**:
- Campaign strategy document
- Platform allocation with budgets
- Targeting specifications
- Success criteria for the Writer and Optimizer agents

### Writer Agent

**Purpose**: Generates optimized ad copy for each target platform.

**Inputs**:
- Job data from Cloudwall
- Strategy specifications from Strategy Agent
- Platform-specific requirements and constraints
- Brand guidelines and compliance rules
- Historical copy performance from Learnings Database

**Responsibilities**:
- Generate headlines, descriptions, and CTAs
- Adapt copy for each platform's format requirements
- Ensure compliance with advertising policies
- Maintain brand voice consistency
- Create multiple variations for A/B testing

**Outputs**:
- Platform-specific ad copy packages
- Multiple variations per platform for testing
- Copy rationale for transparency/audit

### Optimizer Agent

**Purpose**: Monitors performance and continuously improves campaign results.

**Inputs**:
- Real-time performance data from advertising platforms
- Campaign goals from Strategy Agent
- Historical benchmarks from Learnings Database

**Responsibilities**:
- Monitor key metrics (CTR, conversion rate, cost-per-click, cost-per-qualified-candidate)
- Adjust bids based on performance
- Pause underperforming ads/keywords
- Reallocate budget to high-performing segments
- Identify and add negative keywords
- Detect anomalies and alert on edge cases
- Extract learnings and update the Learnings Database

**Outputs**:
- Real-time bid/budget adjustments
- Performance reports
- Learnings for future campaigns
- Alerts for human review when needed

## Cloudwall Integration

### Intake Model

The system operates on an **intake-controlled** model:
- Cloudwall initiates all job advertising requests
- The system does not autonomously discover or create campaigns
- Each job posting triggers the advertising workflow

### Data Contract

Jobs from Cloudwall include:

| Field | Description | Required |
|-------|-------------|----------|
| job_title | Position title | Yes |
| job_description | Full job description | Yes |
| salary_range | Compensation information | No |
| location | Job location(s) | Yes |
| work_arrangement | Remote/Hybrid/Onsite | Yes |
| notes | Additional context | No |

### Integration Pattern

```
Cloudwall ──webhook/API──▶ System Intake ──▶ Strategy Agent
```

## Multi-Platform Output

### Supported Platforms

**Phase 1 (Initial)**:
- Google Ads (Search, Display)

**Phase 2 (Expansion)**:
- LinkedIn Ads
- Indeed Sponsored Jobs

**Phase 3 (Future)**:
- Meta (Facebook/Instagram)
- Programmatic display networks
- Industry-specific job boards

### Modular Adapter Pattern

Each platform is integrated via a dedicated adapter:

```
┌─────────────────────────────────────────────┐
│              Platform Adapter               │
├─────────────────────────────────────────────┤
│ • Translate generic ad spec to platform API │
│ • Handle authentication/authorization       │
│ • Manage rate limits and quotas             │
│ • Normalize performance data                │
│ • Platform-specific optimizations           │
└─────────────────────────────────────────────┘
```

This pattern enables:
- Adding new platforms without core system changes
- Platform-specific optimizations
- Isolated testing and deployment
- ATS flexibility for future integrations

## Feedback Loop Mechanics

### Learning Cycle

```
Campaign Launch
      │
      ▼
Performance Data Collection (hourly/daily)
      │
      ▼
Optimizer Agent Analysis
      │
      ├──▶ Immediate Actions (bid adjustments, pauses)
      │
      └──▶ Learnings Extraction
                  │
                  ▼
           Learnings Database
                  │
    ┌─────────────┴─────────────┐
    ▼                           ▼
Strategy Agent              Writer Agent
(future targeting)     (future copy generation)
```

### Learnings Database Contents

- **Copy patterns**: Which headlines/descriptions perform best for job types
- **Targeting patterns**: Effective keywords and audiences by role/industry
- **Budget patterns**: Optimal spend levels by job type and location
- **Timing patterns**: Best days/times for different campaigns
- **Platform patterns**: Which platforms work best for which job types

## Guardrails and Safety

### Budget Controls

| Control | Description |
|---------|-------------|
| Campaign daily cap | Maximum daily spend per campaign |
| Platform daily cap | Maximum daily spend per platform |
| Monthly budget ceiling | Hard stop at monthly budget limit |
| Cost-per-click threshold | Alert when CPC exceeds threshold |
| Cost-per-conversion threshold | Alert when CPA exceeds acceptable range |

### Operational Guardrails

- **Edge case alerts**: Unusual patterns trigger human review
- **Anomaly detection**: Sudden performance changes flagged
- **Compliance checks**: All ads verified against platform policies
- **Audit logging**: All decisions and changes logged for review

### Human Oversight Points

1. Initial campaign approval (Phase 1)
2. Budget threshold exceeded
3. Anomaly detected
4. Edge case identified
5. Weekly performance review

## Phased Autonomy Roadmap

### Phase 1: Supervised Operation

- All campaigns require human approval before launch
- Real-time monitoring with manual intervention capability
- Learning database population
- Performance baseline establishment

**Exit Criteria**: 3 months of stable operation, baseline metrics established

### Phase 2: Semi-Autonomous Operation

- Campaigns auto-launch within pre-approved parameters
- Human approval for exceptions and edge cases
- Automated optimization within defined bounds
- Expanded to additional platforms

**Exit Criteria**: 6 months of stable operation, demonstrated ROI improvement

### Phase 3: Autonomous Operation

- Full autonomous operation within guardrails
- Human oversight via dashboards and alerts
- Continuous learning and improvement
- Self-adjusting strategy based on market conditions

**Ongoing**: Regular audits, guardrail refinement, capability expansion

## Technical Considerations

### API Dependencies

- **Google Ads API**: Developer token required (verification pending)
- **LinkedIn Marketing API**: Partner access required
- **Indeed API**: Sponsored jobs integration

### Data Storage

- Campaign configurations and history
- Performance metrics (time-series)
- Learnings database (patterns and insights)
- Audit logs

### Compliance

- **GDPR**: European candidate data handling
- **CCPA**: California consumer privacy
- **Platform policies**: Advertising policy compliance per platform

## Future Considerations

Items explicitly out of scope for current phase:

- Individual agent specification documents
- Detailed data schema definitions
- Integration API documentation
- Prototype implementation
- ATS integrations beyond Cloudwall

---

*Document Version: 1.0*
*Last Updated: 2026-02-04*
*Status: Architecture Documentation Phase*
