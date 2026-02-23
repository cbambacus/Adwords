# LinkedIn - Platform Specifications

## Overview

LinkedIn is the premier B2B and professional recruitment platform with 900M+ members globally. Offers multiple ad formats optimized for professional audiences.

## Ad Formats for Recruitment

### 1. Sponsored Content (Single Image)

Most common format for recruitment campaigns.

| Element | Specification |
|---------|---------------|
| Introductory text | 600 characters max (150 recommended for mobile) |
| Headline | 200 characters max (70 recommended) |
| Description | 300 characters max (on desktop only) |
| Image | 1200x627 pixels (1.91:1 ratio) |
| File size | Max 5MB |
| CTA button | Apply, Learn More, etc. |

[VERIFY] LinkedIn may have updated character limits in 2025.

### 2. Sponsored Content (Video)

| Element | Specification |
|---------|---------------|
| Video length | 3 seconds - 30 minutes (15-30 seconds optimal for recruitment) |
| File size | 75KB - 200MB |
| Aspect ratio | 16:9 (landscape), 1:1 (square), 9:16 (vertical) |
| Resolution | 360p minimum, 1080p recommended |
| Introductory text | 600 characters max |

### 3. Sponsored Content (Carousel)

| Element | Specification |
|---------|---------------|
| Cards | 2-10 cards per ad |
| Card image | 1080x1080 pixels (1:1 ratio) |
| Card headline | 45 characters max |
| Introductory text | 255 characters max |

Use case: Showcase multiple roles, office locations, or team members.

### 4. Message Ads (Sponsored InMail)

Direct messaging to candidate inboxes.

| Element | Specification |
|---------|---------------|
| Sender | Real LinkedIn member (recruiter profile) |
| Subject line | 60 characters max |
| Message body | 1,500 characters max |
| CTA button | Custom text, 20 characters max |
| Banner image (optional) | 300x250 pixels |

**Best Practices**:
- Personalization tokens: %FIRSTNAME%, %LASTNAME%, %JOBTITLE%
- Send from a real recruiter profile (not company page)
- [VERIFY] Current InMail open rate benchmarks

### 5. Conversation Ads

Interactive message format with multiple CTAs.

| Element | Specification |
|---------|---------------|
| Message layers | Up to 5 |
| CTA buttons per layer | Up to 5 |
| Button text | 25 characters max |
| Message text | 500 characters per layer |

### 6. Job Slots (LinkedIn Jobs)

Dedicated job posting (not Campaign Manager ads).

| Element | Specification |
|---------|---------------|
| Job title | 200 characters max |
| Job description | 2,000 characters max |
| Skills | Up to 10 required, 10 preferred |
| Easy Apply | One-click application option |

[VERIFY] Current Job Slot pricing tiers.

## Targeting Options

### Professional Attributes

| Targeting Type | Options |
|----------------|---------|
| Job Title | Exact or similar titles |
| Job Function | 26 functions (Marketing, Engineering, etc.) |
| Seniority | Entry, Senior, Manager, Director, VP, C-Suite |
| Industry | 148 industries |
| Company | By name, size, growth rate |
| Skills | 35,000+ skills |
| Education | Degree, field of study, school |
| Years of Experience | Ranges (1-2, 3-5, 6-10, etc.) |

### Demographics
- Age (aggregated only, not individual targeting)
- Gender (aggregated only)
- Location (country, state, metro, radius)

### Matched Audiences
- Website retargeting
- Contact list upload
- Account list upload
- Lookalike audiences

[VERIFY] Minimum audience size requirements for each targeting type.

## Bidding Options

| Bid Type | Best For |
|----------|----------|
| Maximum Delivery | Spending full budget, maximizing reach |
| Cost Cap | Controlling cost per result |
| Manual Bidding | Fine-tuned control |

### Bid Recommendations

[VERIFY] Current LinkedIn suggested bid ranges by region and targeting.

## Campaign Objectives for Recruitment

| Objective | Use Case |
|-----------|----------|
| Website Visits | Drive to careers page |
| Lead Generation | Collect applications via Lead Gen Forms |
| Job Applicants | Dedicated job promotion objective |
| Video Views | Employer branding content |

## Lead Gen Forms

Native forms that pre-populate with LinkedIn profile data.

| Field Type | Options |
|------------|---------|
| Standard | First name, last name, email, phone, job title, company, etc. |
| Custom | Up to 3 custom questions |
| Checkbox | Consent/privacy policy |

**Advantage**: Reduces friction; ~80% of form fields auto-fill from profile.

## Reporting Metrics

| Metric | Description |
|--------|-------------|
| Impressions | Ad views |
| Clicks | Total clicks on ad |
| CTR | Click-through rate |
| Leads | Form submissions |
| Cost per Lead | Total spend / leads |
| Qualified Leads | [VERIFY] How LinkedIn defines this |

## Editorial Policies

- No discriminatory language or targeting
- Clear representation of employer
- Accurate job information
- [VERIFY] LinkedIn's current employment ad policies

## Integration Notes

- HRIS integrations available (Workday, Greenhouse, etc.)
- [VERIFY] Current API capabilities for automated job posting
