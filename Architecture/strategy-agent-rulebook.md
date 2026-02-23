# Strategy Agent Rulebook

Version: 1.0
Last Updated: 2026-02-04
Status: Architecture Documentation Phase

---

## Table of Contents

1. [Agent Mission](#1-agent-mission)
2. [Input Processing Rules](#2-input-processing-rules)
3. [Platform Selection Logic](#3-platform-selection-logic)
4. [Budget Allocation Rules](#4-budget-allocation-rules)
5. [Writer Agent Guidance Template](#5-writer-agent-guidance-template)
6. [Keyword Strategy Rules](#6-keyword-strategy-rules)
7. [Guardrails and Constraints](#7-guardrails-and-constraints)

---

## 1. Agent Mission

### Purpose Statement

The Strategy Agent serves as the **decision-making brain** of the recruitment advertising system. It analyzes job orders received from Cloudwall, determines optimal advertising strategy, allocates budget across platforms, and provides actionable guidance to the Writer Agent.

### Core Responsibilities

| Responsibility | Description |
|----------------|-------------|
| **Analyze** | Parse job data to extract targeting signals and campaign requirements |
| **Strategize** | Determine which platforms, audiences, and approaches will yield the best cost-per-qualified-candidate |
| **Allocate** | Distribute budget optimally across selected platforms |
| **Guide** | Provide the Writer Agent with specific, actionable direction for ad creation |
| **Learn** | Incorporate historical performance data from the Learnings Database into all decisions |

### Decision Authority

The Strategy Agent has authority to:
- Select advertising platforms for each campaign
- Allocate budget within approved thresholds
- Define targeting parameters (keywords, audiences, demographics, locations)
- Set campaign goals and KPIs
- Specify messaging direction for the Writer Agent

The Strategy Agent does NOT have authority to:
- Exceed budget thresholds without human approval
- Launch campaigns (Phase 1 requires human approval)
- Override compliance requirements
- Modify brand guidelines

### Success Metrics

The Strategy Agent optimizes for:
- **Primary**: Cost-per-qualified-candidate (CPQC)
- **Secondary**: Time-to-first-qualified-candidate
- **Tertiary**: Talent pipeline volume

---

## 2. Input Processing Rules

### 2.1 Required Data Fields

Every job order from Cloudwall must contain:

| Field | Type | Use |
|-------|------|-----|
| `job_title` | String | Role classification, keyword generation |
| `job_description` | Text | Skills extraction, selling points identification |
| `location` | String/Array | Geographic targeting, platform selection |
| `work_arrangement` | Enum | Remote/Hybrid/Onsite - affects targeting strategy |

### 2.2 Optional Data Fields

| Field | Type | Default If Missing |
|-------|------|-------------------|
| `salary_range` | Object | Suppress compensation messaging |
| `notes` | Text | No special handling |
| `urgency` | Enum | Standard (7-day campaign ramp) |
| `client_name` | String | Generic employer branding |

### 2.3 Signal Extraction Process

For each job order, extract and classify the following signals:

#### Seniority Level Classification

| Signal Indicators | Classification | Impact |
|-------------------|----------------|--------|
| "Director", "VP", "Head of", "Chief", 10+ years | **Executive** | LinkedIn priority, passive candidate focus |
| "Senior", "Lead", "Principal", 5-10 years | **Senior** | Mixed active/passive, higher CPC tolerance |
| "Manager", 3-5 years experience | **Mid-Level** | Balanced platform approach |
| "Associate", "Junior", 0-3 years, "entry" | **Entry-Level** | Indeed priority, active candidate focus |

#### Role Type Classification

| Category | Indicators | Primary Platforms |
|----------|------------|-------------------|
| **Creative** | Designer, Art Director, Copywriter, UX, UI, Creative Director, Video, Motion | LinkedIn, Google Display, Instagram (Phase 3) |
| **Technical** | Developer, Engineer, Architect, Data Scientist, DevOps, QA | LinkedIn, Google Search, Stack Overflow (Future) |
| **Marketing** | Marketing Manager, SEO, PPC, Content, Social Media, Brand | LinkedIn, Google Search |
| **Corporate** | HR, Finance, Legal, Operations, Project Manager, Admin | Indeed, LinkedIn, Google Search |
| **Executive** | C-Suite, VP, Director, General Manager | LinkedIn (priority), Targeted Display |

#### Skills Extraction

Extract the top 5-7 skills from the job description for keyword targeting:

1. **Primary Skills** (must-have): First 3 mentioned or emphasized skills
2. **Secondary Skills** (nice-to-have): Next 2-4 skills mentioned
3. **Tools/Technologies**: Specific software, platforms, or technologies mentioned

#### Geographic Analysis

| Work Arrangement | Geographic Strategy |
|------------------|---------------------|
| **Remote (US)** | National targeting, exclude high-CPC metros if budget-constrained |
| **Remote (Global)** | English-speaking markets, timezone-appropriate targeting |
| **Hybrid** | Core metro + 50-mile radius, commutable areas |
| **Onsite** | Core metro + 25-mile radius only |

#### Urgency Assessment

| Urgency Level | Indicators | Campaign Approach |
|---------------|------------|-------------------|
| **Critical** | "ASAP", "Immediate", explicit deadline < 7 days | Maximum budget frontload, all platforms simultaneous, higher CPC tolerance (+30%) |
| **High** | Deadline 7-14 days, "urgent" mentioned | Accelerated ramp, primary platform + 1 secondary |
| **Standard** | No urgency indicators, deadline > 14 days | Normal 7-day learning phase, measured rollout |
| **Passive** | Evergreen role, "ongoing need" | Extended timeline, passive candidate focus, lower daily spend |

#### Candidate Profile Prediction

| Profile | Likely Signals | Targeting Implication |
|---------|----------------|----------------------|
| **Active Job Seeker** | Entry-level, high unemployment industry, commodity skills, onsite requirement | Indeed priority, Google Search (job-related keywords), lower CPC |
| **Passive Candidate** | Senior+, specialized skills, competitive industry, remote-friendly | LinkedIn priority, Google Display for awareness, content marketing approach |
| **Mixed** | Mid-level, transferable skills | Balanced platform allocation |

### 2.4 Input Validation Rules

Before proceeding, validate:

1. **Completeness Check**: All required fields present
2. **Location Validity**: Location can be geocoded to known metro/region
3. **Description Quality**: Job description contains extractable skills (minimum 100 words)
4. **Logical Consistency**: Work arrangement matches location (e.g., no "Remote" with specific office address only)

If validation fails, flag for human review before proceeding.

---

## 3. Platform Selection Logic

### 3.1 Platform Capabilities Matrix

| Platform | Strengths | Weaknesses | Best For |
|----------|-----------|------------|----------|
| **Google Search** | High intent, immediate need, broad reach | Expensive for competitive terms, less targeting precision | Active job seekers, commodity roles |
| **Google Display** | Awareness, retargeting, visual creative | Lower intent, higher volume needed | Employer branding, creative roles |
| **LinkedIn** | Professional targeting, passive reach, B2B | Higher CPC, smaller scale | Senior roles, specialized skills, passive candidates |
| **Indeed** | Job seeker intent, volume, lower CPC | Less targeting control, quality variance | Entry/mid-level, high-volume hiring |

### 3.2 Platform Selection Decision Tree

```
START
  |
  v
[Is role Executive/Director level?]
  |
  +-- YES --> LinkedIn PRIMARY (60%+ budget)
  |             |
  |             v
  |           [Is urgency Critical/High?]
  |             |
  |             +-- YES --> Add Google Display (awareness)
  |             +-- NO --> LinkedIn only, extend timeline
  |
  +-- NO --> [Is role Technical (Developer/Engineer)?]
               |
               +-- YES --> [Is seniority Senior+?]
               |             |
               |             +-- YES --> LinkedIn PRIMARY, Google Search SECONDARY
               |             +-- NO --> Google Search PRIMARY, Indeed SECONDARY
               |
               +-- NO --> [Is role Creative?]
                           |
                           +-- YES --> LinkedIn PRIMARY, Google Display SECONDARY
                           |
                           +-- NO --> [Is role Entry-Level?]
                                       |
                                       +-- YES --> Indeed PRIMARY, Google Search SECONDARY
                                       +-- NO --> Google Search PRIMARY, LinkedIn SECONDARY
```

### 3.3 Platform Selection Rules by Role Type

| Role Type | Seniority | Primary Platform | Secondary Platform | Tertiary |
|-----------|-----------|------------------|-------------------|----------|
| Creative | Senior+ | LinkedIn (50%) | Google Display (30%) | Google Search (20%) |
| Creative | Entry/Mid | Indeed (40%) | LinkedIn (35%) | Google Display (25%) |
| Technical | Senior+ | LinkedIn (55%) | Google Search (30%) | Google Display (15%) |
| Technical | Entry/Mid | Google Search (45%) | Indeed (35%) | LinkedIn (20%) |
| Marketing | Senior+ | LinkedIn (50%) | Google Search (35%) | Google Display (15%) |
| Marketing | Entry/Mid | Google Search (40%) | LinkedIn (35%) | Indeed (25%) |
| Corporate | Senior+ | LinkedIn (60%) | Google Search (25%) | Indeed (15%) |
| Corporate | Entry/Mid | Indeed (45%) | Google Search (30%) | LinkedIn (25%) |
| Executive | All | LinkedIn (70%) | Google Display (20%) | Targeted Search (10%) |

### 3.4 Geographic Adjustments

| Geography | Platform Modification |
|-----------|----------------------|
| **Major Tech Hub** (SF, NYC, Seattle, Austin) | Increase LinkedIn allocation +10%, expect higher CPCs |
| **Secondary Metro** | Standard allocation |
| **Remote US** | Reduce Indeed allocation -10% (less geo-relevant), increase Google Search |
| **International** | LinkedIn primary for professional roles, adjust for local platforms (Future) |

### 3.5 Budget Constraint Adjustments

| Daily Budget | Platform Strategy |
|--------------|-------------------|
| **< $50/day** | Single platform only (highest priority for role type) |
| **$50-150/day** | Two platforms maximum |
| **$150-500/day** | Full platform mix as indicated by role type |
| **> $500/day** | Full platform mix + experimental allocation (10%) |

---

## 4. Budget Allocation Rules

### 4.1 Budget Calculation Framework

#### Base Daily Budget by Role Level

| Seniority | Base Daily Budget | Rationale |
|-----------|-------------------|-----------|
| Executive | $200-500 | Longer sales cycle, higher CPC, smaller audience |
| Senior | $100-250 | Competitive market, quality over volume |
| Mid-Level | $75-150 | Balanced approach |
| Entry-Level | $50-100 | Volume-focused, lower CPC |

#### Urgency Multipliers

| Urgency | Budget Multiplier | Duration Adjustment |
|---------|-------------------|---------------------|
| Critical | 2.0x base | Compress to 5-7 days |
| High | 1.5x base | Compress to 10-14 days |
| Standard | 1.0x base | Standard 21-day campaign |
| Passive | 0.7x base | Extended 30-45 day campaign |

#### Geographic Adjustments

| Market Type | CPC Adjustment |
|-------------|----------------|
| Tier 1 Metro (SF, NYC, Boston) | +40% budget allowance |
| Tier 2 Metro (Austin, Denver, Chicago) | +20% budget allowance |
| Tier 3 Metro / Suburban | Standard |
| Remote / National | -10% (broader, less competitive) |

### 4.2 Platform Budget Split

Apply after total daily budget is determined:

```
Total Daily Budget = Base * Urgency Multiplier * Geographic Adjustment

Platform Allocation:
- Primary Platform: 50-70% of total
- Secondary Platform: 20-35% of total
- Tertiary Platform: 10-15% of total (if applicable)
```

### 4.3 Minimum Viable Spend Thresholds

Do not allocate to a platform if the allocation falls below these minimums:

| Platform | Minimum Daily Spend | Rationale |
|----------|---------------------|-----------|
| Google Search | $20/day | Need sufficient impressions for learning |
| Google Display | $15/day | Volume-dependent channel |
| LinkedIn | $30/day | Higher CPC floor |
| Indeed | $15/day | Volume-based pricing |

**Rule**: If calculated allocation < minimum threshold, reallocate that budget to primary platform.

### 4.4 Budget Pacing Strategy

| Campaign Phase | Daily Spend Rate | Duration |
|----------------|------------------|----------|
| **Learning Phase** | 70% of daily budget | Days 1-3 |
| **Optimization Phase** | 100% of daily budget | Days 4-14 |
| **Steady State** | 80-120% of daily budget (performance-based) | Days 15+ |

### 4.5 Human Approval Thresholds

Flag for human approval when:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Total campaign budget | > $5,000 | Require approval before launch |
| Daily budget | > $500/day | Require approval before launch |
| CPC exceeds | > 3x historical average for role type | Alert and await guidance |
| Campaign extension | > 30 days | Re-approval required |
| Budget increase request | > 25% of original | Require approval |

---

## 5. Writer Agent Guidance Template

For each campaign, the Strategy Agent must provide the Writer Agent with the following structured guidance document:

### 5.1 Guidance Document Structure

```yaml
# Writer Agent Brief
campaign_id: [GENERATED_ID]
job_id: [CLOUDWALL_JOB_ID]
generated_date: [TIMESTAMP]

# Core Job Information
job_title: [EXACT_TITLE]
client: [CLIENT_NAME_OR_CONFIDENTIAL]
location: [LOCATION_SUMMARY]
work_arrangement: [REMOTE/HYBRID/ONSITE]
compensation: [RANGE_OR_SUPPRESS]

# Target Audience Profile
audience:
  seniority_level: [ENTRY/MID/SENIOR/EXECUTIVE]
  years_experience: [RANGE]
  current_likely_titles:
    - [TITLE_1]
    - [TITLE_2]
    - [TITLE_3]
  candidate_mindset: [ACTIVE_SEEKER/PASSIVE/MIXED]
  primary_motivations:
    - [MOTIVATION_1]
    - [MOTIVATION_2]
    - [MOTIVATION_3]
  pain_points_to_address:
    - [PAIN_POINT_1]
    - [PAIN_POINT_2]

# Messaging Direction
key_selling_points:
  primary:
    point: [MAIN_SELLING_POINT]
    rationale: [WHY_THIS_MATTERS_TO_AUDIENCE]
  secondary:
    - point: [SELLING_POINT_2]
      rationale: [WHY]
    - point: [SELLING_POINT_3]
      rationale: [WHY]

differentiators:
  - [WHAT_MAKES_THIS_ROLE_UNIQUE]
  - [CLIENT_OR_COMPANY_STRENGTH]

avoid_messaging:
  - [TOPIC_TO_AVOID]
  - [OVERUSED_PHRASE_TO_AVOID]

# Tone and Voice
tone_guidelines:
  overall_tone: [PROFESSIONAL/CONVERSATIONAL/URGENT/INSPIRATIONAL]
  formality_level: [1-5 SCALE, 5=MOST_FORMAL]
  industry_conventions: [SPECIFIC_NOTES]

# Platform-Specific Requirements
platforms:
  google_search:
    enabled: [TRUE/FALSE]
    headlines_needed: 15
    descriptions_needed: 4
    headline_max_chars: 30
    description_max_chars: 90
    special_notes: [RSA_SPECIFIC_GUIDANCE]

  google_display:
    enabled: [TRUE/FALSE]
    headlines_needed: 5
    descriptions_needed: 5
    headline_max_chars: 30
    description_max_chars: 90
    visual_direction: [IMAGE_STYLE_NOTES]

  linkedin:
    enabled: [TRUE/FALSE]
    headline_max_chars: 70
    intro_text_max_chars: 150
    special_notes: [LINKEDIN_SPECIFIC_GUIDANCE]

  indeed:
    enabled: [TRUE/FALSE]
    title_max_chars: 60
    special_notes: [INDEED_SPECIFIC_GUIDANCE]

# Keywords for Integration
primary_keywords:
  - [KEYWORD_1]
  - [KEYWORD_2]
  - [KEYWORD_3]

secondary_keywords:
  - [KEYWORD_4]
  - [KEYWORD_5]

# Compliance Requirements
compliance_checklist:
  - no_discriminatory_language: REQUIRED
  - salary_disclosure: [REQUIRED_IF_CA_CO_NY/OPTIONAL/SUPPRESS]
  - equal_opportunity_mention: REQUIRED
  - no_guaranteed_outcomes: REQUIRED
  - platform_policy_compliant: REQUIRED

# Variation Requirements
variation_strategy:
  total_variations_needed: [NUMBER]
  a_b_test_elements:
    - [ELEMENT_TO_TEST_1]
    - [ELEMENT_TO_TEST_2]
```

### 5.2 Target Audience Description Guidelines

When describing the target audience, include:

1. **Demographic profile**: Seniority, likely current role, industry background
2. **Psychographic profile**: Career motivations, pain points, aspirations
3. **Behavioral signals**: Active vs passive job seeking, platform usage patterns
4. **Decision factors**: What will make them click, what will make them apply

### 5.3 Key Selling Points Framework

Prioritize selling points in this order:

| Priority | Category | Examples |
|----------|----------|----------|
| 1 | **Career Growth** | Promotion path, skill development, mentorship |
| 2 | **Compensation** | Salary range, bonus, equity (if disclosable) |
| 3 | **Work Flexibility** | Remote options, flexible hours, work-life balance |
| 4 | **Company/Client** | Brand recognition, culture, mission |
| 5 | **Project/Work** | Interesting challenges, technology stack, impact |
| 6 | **Benefits** | Healthcare, PTO, perks |

### 5.4 Tone Calibration Matrix

| Role Type | Seniority | Recommended Tone | Formality (1-5) |
|-----------|-----------|------------------|-----------------|
| Creative | Any | Inspirational, bold | 2 |
| Technical | Senior+ | Direct, substantive | 3 |
| Technical | Entry/Mid | Enthusiastic, growth-focused | 2 |
| Corporate | Senior+ | Professional, opportunity-focused | 4 |
| Corporate | Entry/Mid | Welcoming, development-focused | 3 |
| Executive | All | Strategic, prestigious | 5 |

### 5.5 Platform-Specific Guidance

#### Google Search RSAs

- Provide 15 unique headlines with varied messaging angles
- At least 3 headlines should include primary keyword naturally
- Descriptions should be standalone (each description should work with any headline)
- Include urgency/CTA in at least 2 headlines
- Avoid repetitive phrasing across headlines

#### Google Display

- Focus on employer brand and visual appeal
- Shorter, punchier copy
- Clear CTA ("Apply Now", "Learn More")
- Complement visual creative direction

#### LinkedIn

- Professional tone, industry-appropriate language
- Highlight career advancement
- Leverage professional identity (speak to their expertise)
- Can be slightly longer-form

#### Indeed

- Job title optimization for search
- Front-load key requirements and benefits
- Straightforward, informative approach
- Salary transparency increases click-through

---

## 6. Keyword Strategy Rules

### 6.1 Keyword Generation Framework

For each campaign, generate keywords in three tiers:

#### Primary Keywords (5-10 keywords)

**Definition**: High-intent, role-specific keywords that directly match what the ideal candidate would search.

**Generation Rules**:
1. Exact job title + "jobs" (e.g., "senior product manager jobs")
2. Job title variations (e.g., "product manager", "PM", "product owner")
3. Job title + location (e.g., "product manager jobs NYC")
4. Job title + work arrangement (e.g., "remote product manager")

**Match Type**: Start with Phrase Match, expand to Broad Match after learning phase if Smart Bidding is enabled.

#### Secondary Keywords (10-20 keywords)

**Definition**: Related terms, skill-based keywords, and industry variations.

**Generation Rules**:
1. Primary skills + "jobs" (e.g., "agile product management jobs")
2. Industry + role (e.g., "fintech product manager")
3. Seniority variations (e.g., "lead product manager", "associate PM")
4. Tool/technology + role (e.g., "JIRA product manager")
5. Related job titles (e.g., "product owner", "technical product manager")

**Match Type**: Phrase Match or Broad Match with Smart Bidding.

#### Long-Tail Keywords (15-30 keywords)

**Definition**: Specific, lower-volume queries with higher intent and lower competition.

**Generation Rules**:
1. Job title + specific industry vertical (e.g., "product manager healthcare SaaS")
2. Job title + company size preference (e.g., "product manager startup jobs")
3. Job title + specific benefit (e.g., "product manager remote work from home")
4. Question-based queries (e.g., "how to become a senior product manager")
5. Career transition queries (e.g., "developer to product manager jobs")

**Match Type**: Phrase Match initially.

### 6.2 Negative Keyword Strategy

#### Universal Negative Keywords (Apply to all campaigns)

```
# Training/Education (not job seekers)
- course
- courses
- training
- certification
- certify
- tutorial
- learn how to
- how to become
- bootcamp
- degree
- university

# Salary Research (not applying)
- salary
- salaries
- pay scale
- compensation survey
- how much do

# DIY/Freelance (not seeking employment)
- freelance
- freelancer
- consultant
- contract work
- gig
- side hustle

# Wrong Intent
- interview questions
- resume template
- cover letter
- job description template
- what does a [role] do
```

#### Role-Specific Negative Keywords

| Role Type | Negative Keywords |
|-----------|-------------------|
| Technical | "no coding", "non-technical", "for beginners" |
| Senior | "entry level", "junior", "internship", "graduate" |
| Entry-Level | "director", "VP", "head of", "10 years" |
| Creative | "template", "free download", "DIY" |

#### Geographic Negative Keywords

For location-specific roles, add negatives for non-target locations:
- If targeting NYC only, negative: "remote", "California", "Texas", etc.
- If targeting US only, negative: country names outside scope

### 6.3 Match Type Recommendations

| Campaign Phase | Recommended Match Types | Rationale |
|----------------|-------------------------|-----------|
| Week 1 (Learning) | Phrase Match (primary), Exact Match (core terms) | Controlled learning, quality data |
| Week 2-3 | Add Broad Match for primary keywords (with Smart Bidding) | Expand reach with AI protection |
| Week 4+ | Broad Match + Smart Bidding ("Power Pair") | Maximum AI-driven optimization |

### 6.4 Industry-Specific Keyword Patterns

#### Technology Roles

```
Patterns:
- [language/framework] + developer (e.g., "Python developer")
- [technology] + engineer (e.g., "AWS engineer")
- [specialty] + architect (e.g., "solutions architect")
- [technology] + [seniority] (e.g., "senior React developer")

Include:
- Programming language variations (JavaScript/JS, Python/Py)
- Framework names (React, Angular, Django)
- Cloud platforms (AWS, Azure, GCP)
```

#### Creative Roles

```
Patterns:
- [tool] + designer (e.g., "Figma designer")
- [specialty] + designer (e.g., "UX designer", "motion designer")
- [industry] + creative (e.g., "agency creative")
- [deliverable] + [role] (e.g., "brand identity designer")

Include:
- Software tool names (Adobe, Figma, Sketch)
- Style/medium variations (digital, print, motion)
```

#### Marketing Roles

```
Patterns:
- [channel] + marketing (e.g., "social media marketing")
- [specialty] + manager (e.g., "SEO manager", "content manager")
- [industry] + marketing (e.g., "B2B marketing", "e-commerce marketing")

Include:
- Platform names (Google Ads, HubSpot, Salesforce)
- Metric-focused terms (growth, performance, conversion)
```

### 6.5 Keyword Handoff to Writer Agent

Include in the Writer Agent guidance:

```yaml
keywords:
  primary:
    - keyword: "[KEYWORD]"
      monthly_volume: [ESTIMATED_VOLUME]
      competition: [HIGH/MEDIUM/LOW]
      include_in_headlines: TRUE
    # ... repeat for all primary keywords

  secondary:
    - keyword: "[KEYWORD]"
      context: "[HOW_TO_USE_NATURALLY]"
    # ... repeat

  integration_guidelines:
    - "Include primary keywords in at least 3 headlines naturally"
    - "Avoid keyword stuffing - readability first"
    - "Match keyword intent in description copy"
```

---

## 7. Guardrails and Constraints

### 7.1 Budget Guardrails

#### Hard Limits (Cannot be exceeded without human override)

| Guardrail | Threshold | Action on Breach |
|-----------|-----------|------------------|
| Campaign total budget | $10,000 | Block - require human approval |
| Daily spend | $750/day | Block - require human approval |
| Single platform daily | $500/day | Alert and await confirmation |
| Cost-per-click | 5x historical average | Pause keyword, alert |
| Cost-per-application | 3x target | Alert, reduce budget allocation |

#### Soft Limits (Trigger alerts, continue with monitoring)

| Guardrail | Threshold | Action on Breach |
|-----------|-----------|------------------|
| CPC | 2x historical average | Log warning, increase monitoring |
| CTR | Below 1% after 1000 impressions | Flag for copy review |
| Conversion rate | Below 2% after 500 clicks | Flag for landing page review |
| Budget pacing | >120% of daily target | Reduce bids 10% |

### 7.2 CPC Caps by Platform

| Platform | Standard Role Max CPC | Senior Role Max CPC | Executive Max CPC |
|----------|----------------------|---------------------|-------------------|
| Google Search | $8.00 | $15.00 | $25.00 |
| Google Display | $3.00 | $5.00 | $8.00 |
| LinkedIn | $12.00 | $20.00 | $35.00 |
| Indeed | $4.00 | $8.00 | $12.00 |

**Note**: These are starting caps. Optimizer Agent may request increases based on performance data.

### 7.3 Compliance Checks

Before handing off to Writer Agent, verify:

#### Anti-Discrimination Compliance

- [ ] No age-related language (e.g., "young", "digital native", "recent graduate")
- [ ] No gender-coded language
- [ ] No nationality/origin requirements beyond legal work authorization
- [ ] No religious or political references
- [ ] No physical requirements unless bona fide occupational qualification

#### Salary Transparency Compliance

| Jurisdiction | Requirement |
|--------------|-------------|
| California | Salary range required in job posting |
| Colorado | Salary range required in job posting |
| New York (state) | Salary range required in job posting |
| New York City | Salary range required in job posting |
| Washington | Salary range required in job posting |
| Other | Recommended but not required |

**Rule**: If job location includes covered jurisdiction, mark salary disclosure as REQUIRED in Writer Agent guidance.

#### Platform Policy Compliance

| Platform | Key Policy Requirements |
|----------|------------------------|
| Google Ads | No misleading claims, no excessive capitalization, no gimmicky punctuation |
| LinkedIn | Professional content, no fake urgency, accurate job representation |
| Indeed | Accurate job title, real location, no bait-and-switch |

### 7.4 Quality Assurance Checks

Before campaign launch, verify:

1. **Data Completeness**: All required fields populated
2. **Platform Viability**: Selected platforms meet minimum budget thresholds
3. **Keyword Quality**: Primary keywords have reasonable search volume
4. **Geographic Accuracy**: Targeting matches job location requirements
5. **Competitive Analysis**: CPC estimates are within acceptable range
6. **Historical Baseline**: Similar roles have been benchmarked in Learnings Database

### 7.5 Escalation Protocols

| Trigger | Escalation Level | Response Time |
|---------|------------------|---------------|
| Budget threshold exceeded | Human approval required | 24 hours |
| Compliance flag | Immediate pause, human review | 4 hours |
| Anomaly detected (spend spike, CTR crash) | Alert to operations | 2 hours |
| Edge case (unusual role, new market) | Strategy review | 24 hours |
| System error / API failure | Technical escalation | 1 hour |

### 7.6 Audit Trail Requirements

The Strategy Agent must log all decisions with:

1. **Decision Made**: What was decided
2. **Inputs Considered**: What data informed the decision
3. **Rules Applied**: Which rules from this document were triggered
4. **Alternatives Rejected**: Other options considered and why rejected
5. **Confidence Level**: High/Medium/Low
6. **Timestamp**: When decision was made

Example log entry:
```json
{
  "decision_id": "STR-2026-0204-001",
  "job_id": "CW-12345",
  "timestamp": "2026-02-04T14:30:00Z",
  "decision_type": "platform_selection",
  "decision_made": {
    "primary": "linkedin",
    "allocation": 0.55,
    "secondary": "google_search",
    "allocation": 0.30,
    "tertiary": "google_display",
    "allocation": 0.15
  },
  "inputs_considered": {
    "role_type": "technical",
    "seniority": "senior",
    "location": "remote_us",
    "urgency": "standard"
  },
  "rules_applied": [
    "3.3 - Technical Senior+ platform allocation",
    "3.4 - Remote US geographic adjustment"
  ],
  "alternatives_rejected": {
    "indeed_primary": "seniority too high for Indeed primary",
    "linkedin_only": "budget sufficient for multi-platform"
  },
  "confidence": "high",
  "learnings_database_consulted": true
}
```

### 7.7 Learning Integration

The Strategy Agent must:

1. **Before each decision**: Query Learnings Database for similar past campaigns
2. **Weight historical data**: Apply learnings with decay (recent data weighted higher)
3. **Flag contradictions**: If rules conflict with historical performance, log and proceed with historical insight but flag for review
4. **Contribute learnings**: After Optimizer Agent provides feedback, update decision patterns

---

## Appendix A: Cloudwall Data Contract

Expected job order structure:

```json
{
  "job_id": "string (required)",
  "job_title": "string (required)",
  "job_description": "string (required)",
  "location": {
    "city": "string",
    "state": "string",
    "country": "string",
    "remote": "boolean"
  },
  "work_arrangement": "enum: REMOTE | HYBRID | ONSITE (required)",
  "salary_range": {
    "min": "number",
    "max": "number",
    "currency": "string",
    "period": "enum: HOURLY | ANNUAL"
  },
  "client": {
    "name": "string",
    "confidential": "boolean"
  },
  "notes": "string",
  "urgency": "enum: CRITICAL | HIGH | STANDARD | PASSIVE",
  "intake_timestamp": "ISO 8601 datetime"
}
```

---

## Appendix B: Platform API Reference

### Phase 1: Google Ads

- API Version: v17+
- Authentication: OAuth 2.0, Developer Token
- Rate Limits: 15,000 operations/day (standard)
- Key Endpoints: Campaigns, Ad Groups, Keywords, Responsive Search Ads

### Phase 2: LinkedIn Marketing API

- API Version: 202401+
- Authentication: OAuth 2.0, Partner Access
- Key Endpoints: Ad Accounts, Campaigns, Creatives, Targeting

### Phase 2: Indeed Sponsored Jobs

- Integration: XML Feed + Sponsored Budget API
- Authentication: API Key
- Key Features: Cost-per-click sponsorship, performance tracking

---

## Appendix C: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | Strategy Agent Design Team | Initial document |

---

*This rulebook is a living document and will be updated based on operational learnings and system evolution.*
