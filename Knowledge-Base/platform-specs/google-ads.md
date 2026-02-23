# Google Ads - Platform Specifications

## Responsive Search Ads (RSAs)

RSAs are the primary text ad format for Google Search campaigns. Google's AI dynamically assembles headlines and descriptions to optimize performance.

### Character Limits

| Element | Max Characters | Quantity |
|---------|---------------|----------|
| Headlines | 30 characters each | 3-15 headlines |
| Descriptions | 90 characters each | 2-4 descriptions |
| Display URL Path | 15 characters each | 2 paths |
| Final URL | 2048 characters | 1 required |

### Best Practices

- **Minimum recommended**: 8-10 headlines, 3-4 descriptions
- **Optimal**: 15 headlines, 4 descriptions (maximizes combinations)
- Include keywords in at least 3 headlines
- Vary headline themes (job title, company, benefits, location, salary)

### Pinning Rules

Pinning forces specific assets to appear in designated positions:

| Position | Use Case |
|----------|----------|
| Headline 1 | Job title or company name (brand consistency) |
| Headline 2 | Key differentiator or location |
| Headline 3 | Call to action |
| Description 1 | Primary job details |
| Description 2 | Benefits or culture highlights |

**Caution**: Over-pinning reduces Google's optimization ability. Pin only when legally required (e.g., salary transparency) or for brand consistency.

### Ad Strength Indicator

| Rating | Meaning |
|--------|---------|
| Incomplete | Missing required elements |
| Poor | Low variety, needs improvement |
| Average | Acceptable but room for improvement |
| Good | Well-optimized |
| Excellent | Maximum optimization potential |

[VERIFY] Google may have updated Ad Strength weighting factors recently.

## Performance Max Campaigns

For recruitment, Performance Max can extend reach across Google's inventory:
- Search
- Display
- YouTube
- Gmail
- Discover
- Maps

### Asset Requirements

| Asset Type | Specifications |
|------------|----------------|
| Text | Same as RSA (headlines/descriptions) |
| Images | 1200x628 (landscape), 1200x1200 (square), 960x1200 (portrait) |
| Logos | 1200x1200 (square), 1200x300 (landscape) |
| Video | YouTube hosted, 10+ seconds recommended |

[VERIFY] Performance Max asset group limits may have changed in 2025.

## Keyword Match Types

| Match Type | Syntax | Reach | Control |
|------------|--------|-------|---------|
| Broad Match | keyword | Highest | Lowest |
| Phrase Match | "keyword" | Medium | Medium |
| Exact Match | [keyword] | Lowest | Highest |

**Recommendation for Recruitment**: Use Broad Match + Smart Bidding for maximum reach, with strong negative keyword lists.

## Smart Bidding Strategies

| Strategy | Best For |
|----------|----------|
| Maximize Conversions | Volume-focused campaigns |
| Target CPA | Cost-controlled campaigns |
| Maximize Conversion Value | When candidate quality varies |
| Target ROAS | [VERIFY] Applicability to recruitment |

## Audience Targeting

### Custom Segments
- Search terms people use
- Apps they use
- Websites they visit

### In-Market Audiences
[VERIFY] Current job seeker in-market segments available in Google Ads.

### Demographics
- Age ranges
- Household income
- Parental status

**Note**: Employment ads have targeting restrictions. Cannot exclude based on protected characteristics.

## Quality Score Factors

1. **Expected CTR** - Historical performance prediction
2. **Ad Relevance** - Keyword-to-ad alignment
3. **Landing Page Experience** - Page quality and relevance

## Conversion Tracking

Required conversion actions for recruitment:
- Application started
- Application submitted
- [VERIFY] Best practice for tracking qualified candidates

## Character Counting Tips

- Spaces count as characters
- Special characters count (& = 1, % = 1)
- Emojis not allowed in text ads
- Dynamic keyword insertion: `{KeyWord:default}` counts as default text length

## Editorial Policies

- No excessive capitalization (OK: "Marketing Manager", Not OK: "APPLY NOW")
- No misleading claims
- No prohibited content
- [VERIFY] Current Google Ads employment advertising policies
