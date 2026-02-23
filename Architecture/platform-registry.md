# Platform Registry

This document catalogs all advertising platforms for the recruitment system, including active integrations and planned future platforms.

---

## Registry Overview

| Platform | ID | Status | Priority | Channel Type |
|----------|-----|--------|----------|--------------|
| Google Ads | `google_ads` | **Active** | P0 | Search, Display |
| LinkedIn | `linkedin` | Planned | P1 | Social, Job Board |
| Indeed | `indeed` | Planned | P1 | Job Board |
| Meta (Facebook/Instagram) | `meta` | Planned | P2 | Social, Display |
| ZipRecruiter | `ziprecruiter` | Planned | P3 | Job Board |
| Microsoft Advertising | `microsoft_ads` | Planned | P3 | Search |
| TikTok | `tiktok` | Planned | P4 | Social, Video |
| Programmatic (Appcast) | `appcast` | Planned | P2 | Aggregator |

---

## Platform Details

### Google Ads
**Status:** Active (Phase 1)
**Platform ID:** `google_ads`

#### Capabilities Matrix

| Capability | Supported | Notes |
|------------|-----------|-------|
| Search Ads | Yes | RSAs with 15 headlines, 4 descriptions |
| Display Ads | Yes | Image + responsive display |
| Video Ads | Yes | YouTube via Google Ads |
| Performance Max | Yes | Multi-surface AI-driven |
| Keyword Targeting | Yes | Broad, phrase, exact match |
| Location Targeting | Yes | Country, region, city, radius |
| Demographic Targeting | Yes | Age, gender, household income |
| Audience Targeting | Yes | In-market, affinity, custom |
| Smart Bidding | Yes | Target CPA, ROAS, Maximize Conversions |

#### Best Fit Scenarios
- Active job seekers searching for roles
- Intent-based targeting ("senior ux designer jobs")
- Geographic-specific campaigns
- High-urgency fills (quick ramp-up)

#### Typical Costs (Recruitment)
- CPC: $1.50 - $4.50
- CPA: $25 - $75 per application
- Recommended minimum daily budget: $50

#### Integration Requirements
- Google Ads API developer token
- OAuth2 credentials
- Customer ID
- Conversion tracking (Google Tag)

---

### LinkedIn
**Status:** Planned (P1)
**Platform ID:** `linkedin`

#### Capabilities Matrix

| Capability | Supported | Notes |
|------------|-----------|-------|
| Sponsored Content | Yes | Single image, carousel, video |
| Sponsored InMail | Yes | Direct message ads |
| Job Slots | Yes | Native job postings |
| Text Ads | Yes | Sidebar placement |
| Job Title Targeting | Yes | Current and past titles |
| Skills Targeting | Yes | Listed skills on profiles |
| Company Targeting | Yes | Current/past employers |
| Seniority Targeting | Yes | Entry to Executive |
| Industry Targeting | Yes | 147 industries |

#### Best Fit Scenarios
- Senior/executive roles
- Passive candidate outreach
- Professional/corporate positions
- B2B-adjacent roles (marketing, sales, tech)

#### Typical Costs (Recruitment)
- CPC: $5 - $12
- CPA: $50 - $150 per application
- Recommended minimum daily budget: $75
- InMail: $0.50 - $1.50 per send

#### Integration Requirements
- LinkedIn Marketing API access
- OAuth2 credentials
- Company Page admin access
- Insight Tag for conversion tracking

---

### Indeed
**Status:** Planned (P1)
**Platform ID:** `indeed`

#### Capabilities Matrix

| Capability | Supported | Notes |
|------------|-----------|-------|
| Sponsored Jobs | Yes | Boosted job listings |
| Indeed Apply | Yes | Streamlined application |
| Job Title Optimization | Yes | SEO for job search |
| Location Targeting | Yes | City, state, remote |
| Salary Display | Yes | Increases visibility |
| Urgently Hiring Badge | Yes | For urgent roles |
| Resume Database | Yes | Proactive sourcing |

#### Best Fit Scenarios
- High-volume hiring
- Active job seekers
- Entry to mid-level roles
- Broad geographic reach
- Cost-sensitive campaigns

#### Typical Costs (Recruitment)
- CPC: $0.25 - $1.50
- CPA: $15 - $40 per application
- Recommended minimum daily budget: $25

#### Integration Requirements
- Indeed Employer API
- Company account
- Apply tracking integration

---

### Meta (Facebook/Instagram)
**Status:** Planned (P2)
**Platform ID:** `meta`

#### Capabilities Matrix

| Capability | Supported | Notes |
|------------|-----------|-------|
| Feed Ads | Yes | Image, video, carousel |
| Stories Ads | Yes | Full-screen vertical |
| Reels Ads | Yes | Short-form video |
| Interest Targeting | Limited | Special Ad Category restrictions |
| Lookalike Audiences | Limited | Employment restrictions apply |
| Location Targeting | Yes | Country, region, city |
| Age Targeting | No | Prohibited for employment |

#### Special Ad Category Restrictions
**Employment ads on Meta require Special Ad Category designation:**
- Cannot target by age
- Cannot target by gender
- Cannot target by zip code (15-mile minimum radius)
- Limited interest targeting
- No exclusion of protected groups

#### Best Fit Scenarios
- Broad awareness campaigns
- Entry-level and hourly roles
- Younger workforce (Instagram/Reels)
- Local hiring
- Employer branding

#### Typical Costs (Recruitment)
- CPC: $0.50 - $2.00
- CPA: $20 - $60 per application
- Recommended minimum daily budget: $30

#### Integration Requirements
- Meta Business Suite access
- Marketing API credentials
- Meta Pixel for tracking
- Special Ad Category compliance

---

### ZipRecruiter
**Status:** Planned (P3)
**Platform ID:** `ziprecruiter`

#### Capabilities Matrix

| Capability | Supported | Notes |
|------------|-----------|-------|
| Job Distribution | Yes | Posts to 100+ job boards |
| AI Matching | Yes | Invites matching candidates |
| TrafficBoost | Yes | Sponsored visibility |
| Resume Database | Yes | Proactive outreach |

#### Best Fit Scenarios
- Volume hiring
- Broad distribution needs
- Entry to mid-level roles
- Supplementary reach

#### Typical Costs
- CPC: $1 - $3
- Monthly subscription + per-job costs

---

### Microsoft Advertising (Bing)
**Status:** Planned (P3)
**Platform ID:** `microsoft_ads`

#### Capabilities Matrix

| Capability | Supported | Notes |
|------------|-----------|-------|
| Search Ads | Yes | Similar to Google RSAs |
| Audience Targeting | Yes | LinkedIn profile targeting available |
| Import from Google | Yes | Easy campaign mirroring |

#### Best Fit Scenarios
- Supplementary search coverage
- Older demographic reach
- Lower CPC alternative to Google
- Enterprise/Microsoft ecosystem users

#### Typical Costs
- CPC: $1 - $3 (often 20-30% lower than Google)
- Smaller volume than Google

---

### TikTok
**Status:** Planned (P4)
**Platform ID:** `tiktok`

#### Capabilities Matrix

| Capability | Supported | Notes |
|------------|-----------|-------|
| In-Feed Video Ads | Yes | 9-60 seconds |
| Spark Ads | Yes | Boost organic content |
| Interest Targeting | Yes | Based on engagement |
| Age Targeting | Limited | 18+ only, restrictions apply |

#### Best Fit Scenarios
- Gen Z workforce
- Creative/design roles
- Employer branding
- Entry-level hiring
- Culture-forward companies

#### Typical Costs
- CPM: $10 - $20
- CPC: $0.20 - $2.50

---

### Appcast (Programmatic)
**Status:** Planned (P2)
**Platform ID:** `appcast`

#### Capabilities Matrix

| Capability | Supported | Notes |
|------------|-----------|-------|
| Multi-Board Distribution | Yes | Hundreds of job sites |
| Programmatic Bidding | Yes | Real-time optimization |
| CPA-Based Pricing | Yes | Pay per application |
| ATS Integration | Yes | Major ATS platforms |

#### Best Fit Scenarios
- Scale hiring across many roles
- Automated budget optimization
- Broad reach without managing individual platforms
- CPA-focused campaigns

#### Typical Costs
- CPA: $15 - $50 (varies by role)
- No direct CPC model

---

## Platform Selection Matrix

### By Role Type

| Role Type | Primary | Secondary | Consider |
|-----------|---------|-----------|----------|
| Creative (Design, UX) | LinkedIn | Google Ads | Dribbble, Behance |
| Technical (Engineering) | LinkedIn | Google Ads | Stack Overflow |
| Marketing | LinkedIn | Google Ads | Meta |
| Corporate (Finance, HR, Legal) | LinkedIn | Indeed | Google Ads |
| Entry Level | Indeed | Meta | Google Ads |
| Hourly/Frontline | Indeed | Meta | ZipRecruiter |
| Executive | LinkedIn | Google Ads | - |

### By Candidate Type

| Candidate Type | Primary | Secondary |
|----------------|---------|-----------|
| Active Job Seekers | Indeed, Google Ads | ZipRecruiter |
| Passive Candidates | LinkedIn | Meta |
| Career Changers | Google Ads | LinkedIn |

### By Urgency

| Urgency | Approach |
|---------|----------|
| Critical (< 1 week) | Google Ads (immediate), LinkedIn (fast review) |
| High (1-2 weeks) | Multi-platform: Google + LinkedIn + Indeed |
| Normal (2-4 weeks) | Balanced multi-platform |
| Passive (ongoing) | LinkedIn primarily, programmatic |

### By Budget

| Daily Budget | Recommended Platforms |
|--------------|----------------------|
| < $50 | Indeed only |
| $50 - $100 | Google Ads OR LinkedIn |
| $100 - $250 | Google Ads + LinkedIn |
| $250 - $500 | Google + LinkedIn + Indeed |
| $500+ | Multi-platform with programmatic |

---

## Future Considerations

### Platforms Under Evaluation
- **Glassdoor** - Employer branding + job listings
- **AngelList/Wellfound** - Startup ecosystem
- **Handshake** - College recruiting
- **Dice** - Tech specialization
- **The Muse** - Culture-focused

### Programmatic Alternatives
- **PandoLogic** (pandoIQ)
- **Joveo**
- **Recruitics**
- **Talroo**

---

## Registry Maintenance

This registry should be updated when:
1. A platform changes its capabilities or API
2. Pricing/cost benchmarks shift significantly
3. New platforms are added or deprecated
4. Integration status changes

**Last Updated:** 2024-02-05
**Maintained By:** Strategy Agent Team
