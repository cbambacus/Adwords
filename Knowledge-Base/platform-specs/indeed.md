# Indeed - Platform Specifications

## Overview

Indeed is the world's largest job site with 300M+ unique monthly visitors. Operates on a pay-per-click or pay-per-application model for sponsored job postings.

## Sponsored Jobs

### Job Title Optimization

The job title is the most critical element for Indeed's matching algorithm.

| Element | Specification |
|---------|---------------|
| Job title | 80 characters max [VERIFY] |
| Recommended length | Under 60 characters for full display |

**Title Best Practices**:
- Use standard, searchable job titles (not internal codes)
- Include seniority level when relevant (Senior, Lead, Junior)
- Avoid special characters, all caps, or excessive punctuation
- Don't include salary in title (use dedicated field)
- Don't include location in title (use location field)

**Good Examples**:
- "Marketing Manager"
- "Senior Software Engineer - Python"
- "Graphic Designer"

**Bad Examples**:
- "AMAZING OPPORTUNITY!!!"
- "Marketing Ninja/Rockstar"
- "Job ID: MKT-2024-001"
- "Marketing Manager - $80K - Remote - NYC"

### Job Description

| Element | Specification |
|---------|---------------|
| Length | No strict limit, 700-2000 words recommended |
| Format | HTML supported (basic tags) |
| Sections | Clear headers improve readability |

**Recommended Structure**:
1. Company overview (2-3 sentences)
2. Role summary (what they'll do)
3. Responsibilities (bullet points)
4. Requirements (must-have qualifications)
5. Nice-to-haves (preferred qualifications)
6. Benefits & perks
7. Salary information (when required/appropriate)
8. Application instructions

[VERIFY] Current Indeed ranking factors for job descriptions.

### Salary Information

| Element | Specification |
|---------|---------------|
| Salary field | Dedicated field, not in title/description |
| Display options | Exact, range, or "Estimated by Indeed" |
| Currency | Auto-detected by location |

**Note**: Jobs with salary information receive significantly more applications. [VERIFY] Current lift percentage.

### Location Settings

| Type | Description |
|------|-------------|
| On-site | Specific address or city |
| Hybrid | Office location + remote flexibility |
| Remote | Remote within country/region |
| Remote - USA | Remote work from anywhere in US |

### Easy Apply

Indeed's one-click application feature.

**Screener Questions**: Up to 3 [VERIFY] dealbreaker questions
- Yes/No questions
- Must-have qualifications
- Visa/work authorization

## Sponsored Jobs Bidding

### Pricing Models

| Model | Description |
|-------|-------------|
| Pay-per-click | Pay when candidate clicks to view job |
| Pay-per-application | Pay when candidate completes application |
| Pay-per-started-application | Pay when candidate starts application |

[VERIFY] Current Indeed pricing model availability and rates.

### Bid Strategies

| Strategy | Use Case |
|----------|----------|
| Maximize applications | Volume focus, budget-constrained |
| Balanced | Even spend throughout campaign |
| Target CPA | Cost-controlled application acquisition |

### Budget Settings

| Setting | Options |
|---------|---------|
| Daily budget | Minimum varies by market |
| Sponsorship level | Standard, Featured |
| Duration | Ongoing or fixed end date |

## Indeed Resume Database

Separate from job postings - proactive candidate sourcing.

| Feature | Specification |
|---------|---------------|
| Search filters | Title, skills, location, experience, education |
| Contact credits | Required to message candidates |
| Boolean search | Supported |

[VERIFY] Current Indeed Resume pricing tiers.

## Targeting & Matching

Indeed uses algorithmic matching based on:
- Job title
- Job description keywords
- Location
- Candidate search history
- Resume content

**No demographic targeting available** - Indeed matches based on professional qualifications only.

## Quality Score Factors

Indeed's internal ranking considers:
1. Job title clarity and searchability
2. Description completeness
3. Salary transparency
4. Company profile completeness
5. Response rate to candidates
6. Historical performance (CTR, application rate)

[VERIFY] Current Indeed ranking algorithm factors.

## Company Page

| Element | Impact |
|---------|--------|
| Logo | Increases trust |
| Photos | Employer branding |
| Reviews | Candidate research tool |
| Benefits listed | Improves conversion |

**Recommendation**: Maintain updated Indeed Company Page for better organic visibility.

## Reporting Metrics

| Metric | Description |
|--------|-------------|
| Impressions | Job views in search results |
| Clicks | Clicks to job detail page |
| Applications | Completed applications |
| CTR | Clicks / Impressions |
| Apply Rate | Applications / Clicks |
| Cost per Application | Spend / Applications |

## Integration Options

- Indeed Apply API
- ATS integrations (direct posting)
- XML feed posting (for high-volume employers)

[VERIFY] Current ATS integration list and capabilities.

## Editorial Policies

- Must represent real, open positions
- No misleading information
- No discriminatory requirements
- Salary accuracy requirements (some states)
- Clear employer identification

## Indeed Hiring Platform vs. Sponsored Jobs

| Feature | Sponsored Jobs | Hiring Platform |
|---------|---------------|-----------------|
| Posting | Campaign Manager | Integrated dashboard |
| ATS | External | Indeed's built-in ATS |
| Screening | Basic questions | Full workflow |
| Cost | Pay-per-result | Subscription + per-result |

[VERIFY] Current Indeed Hiring Platform features and pricing.
