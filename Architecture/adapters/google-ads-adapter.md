# Google Ads Adapter Specification

This document specifies the Google Ads adapter implementation—the first platform adapter for the recruitment advertising system.

---

## Adapter Overview

| Property | Value |
|----------|-------|
| Platform ID | `google_ads` |
| Platform Name | Google Ads |
| Status | Active |
| Interface Version | 1.0 |
| Channels | Search, Display, Performance Max |
| Primary Use | Intent-based job seeker targeting |

---

## Platform Capabilities

```yaml
capabilities:
  channelTypes:
    - search
    - display
    - video  # YouTube via Google Ads

  targetingOptions:
    keywords: true
    jobTitle: false
    skills: false
    industry: false
    company: false
    seniority: false
    location: true
    demographics: true  # age, gender, household income
    interests: true     # in-market, affinity audiences
    retargeting: true

  adFormats:
    - responsiveSearch  # RSAs - primary format
    - textAd           # Legacy, limited use
    - responsiveDisplay
    - performanceMax

  biddingStrategies:
    - manualCpc
    - targetCpa
    - targetRoas
    - maximizeClicks
    - maximizeConversions
    - maximizeConversionValue
```

---

## Ad Requirements

### Responsive Search Ads (RSAs)

```yaml
rsa_requirements:
  headlines:
    minCount: 3
    maxCount: 15
    minLength: 1
    maxLength: 30
    recommendations:
      - "Provide at least 8-10 unique headlines"
      - "Include keywords in 2-3 headlines"
      - "Include call-to-action in 1-2 headlines"
      - "Include salary/compensation if available"
      - "Avoid repetition across headlines"

  descriptions:
    minCount: 2
    maxCount: 4
    minLength: 1
    maxLength: 90
    recommendations:
      - "Provide all 4 descriptions"
      - "Each should stand alone (may show in any order)"
      - "Include key benefits and requirements"
      - "End with clear call-to-action"

  finalUrl:
    required: true
    httpsRequired: true
    mustMatchDomain: true  # Display URL domain

  displayPath:
    maxParts: 2
    maxLengthPerPart: 15
    example: "aquent.com/Jobs/UX-Designer"
```

### Character Limit Reference

| Asset | Min | Max | Best Practice |
|-------|-----|-----|---------------|
| Headline | 1 | 30 | Use 25-30 chars |
| Description | 1 | 90 | Use 80-90 chars |
| Display Path | - | 15 each | Use both paths |

---

## Campaign Structure Mapping

### Job Order → Campaign Hierarchy

```
Cloudwall Job Order
    │
    └── Google Ads Campaign
        ├── Campaign Settings
        │   ├── Name: "{job_id}-{role_type}"
        │   ├── Budget: {allocated_daily_budget}
        │   ├── Bidding: Target CPA or Maximize Conversions
        │   ├── Networks: Search Network only (initially)
        │   ├── Locations: {job_order.location}
        │   └── Schedule: Based on urgency
        │
        ├── Ad Group: "Intent-RoleSeeking"
        │   ├── Theme: Users searching for this type of role
        │   ├── Keywords: [role-based keywords]
        │   └── RSA: [role-focused copy]
        │
        ├── Ad Group: "Intent-SkillBased"
        │   ├── Theme: Users searching by skill
        │   ├── Keywords: [skill-based keywords]
        │   └── RSA: [skill-focused copy]
        │
        └── Ad Group: "Intent-LocationBased"
            ├── Theme: Users searching by location
            ├── Keywords: [location-based keywords]
            └── RSA: [location-focused copy]
```

### Campaign Settings Defaults

```yaml
campaign_defaults:
  network: SEARCH
  status: PAUSED  # Review before activating

  bidding:
    default_strategy: MAXIMIZE_CONVERSIONS
    target_cpa_eligible: true  # If conversion history exists

  budget:
    delivery_method: STANDARD  # Not accelerated

  geo_targeting:
    method: PRESENCE  # "People in or regularly in"

  ad_schedule:
    default: ALL_DAYS  # 24/7 initially

  ad_rotation:
    type: OPTIMIZE  # Let Google optimize
```

---

## Keyword Strategy

### Keyword Generation Logic

```python
def generate_keywords(job_order):
    keywords = {
        "role_seeking": [],
        "skill_based": [],
        "location_based": []
    }

    # Role-seeking keywords
    job_title = job_order.job_title
    keywords["role_seeking"] = [
        f"{job_title} jobs",
        f"{job_title} careers",
        f"{job_title} positions",
        f"hiring {job_title}",
        f"{job_title} openings",
    ]

    # Skill-based keywords
    skills = extract_skills(job_order.job_description)
    for skill in skills[:5]:  # Top 5 skills
        keywords["skill_based"].extend([
            f"{skill} jobs",
            f"{skill} {job_title}",
        ])

    # Location-based keywords
    location = job_order.location
    keywords["location_based"] = [
        f"{job_title} {location.city}",
        f"{job_title} jobs {location.city}",
        f"{job_title} {location.state}",
    ]

    # Add remote keywords if applicable
    if job_order.work_arrangement in ["remote", "hybrid"]:
        keywords["role_seeking"].append(f"remote {job_title}")
        keywords["role_seeking"].append(f"work from home {job_title}")

    return keywords
```

### Match Types

```yaml
match_type_strategy:
  phase_1:  # Initial launch
    primary: BROAD  # Broad match with Smart Bidding
    use_case: "Discovery phase, let Google find relevant queries"

  phase_2:  # After data collection
    primary: PHRASE
    secondary: BROAD
    use_case: "Refine based on Search Terms Report"

  exact_match:
    use_case: "High-performing queries identified by Optimizer"
```

### Negative Keywords

```yaml
universal_negatives:
  - "free"
  - "volunteer"
  - "internship"  # Unless entry-level
  - "course"
  - "training"
  - "certification"
  - "salary"  # Often research queries
  - "interview questions"
  - "resume"
  - "template"

role_specific_negatives:
  senior_roles:
    - "entry level"
    - "junior"
    - "associate"
    - "intern"

  professional_roles:
    - "part time"  # Unless applicable
    - "freelance"  # Unless contract
```

---

## Conversion Tracking

### Required Conversions

```yaml
conversion_actions:
  primary:
    name: "Application Submitted"
    category: SUBMIT_LEAD_FORM
    counting: ONE_PER_CLICK
    value: 1  # Or dynamic value based on role level

  secondary:
    - name: "Application Started"
      category: PAGE_VIEW
      counting: ONE_PER_CLICK

    - name: "Job View"
      category: PAGE_VIEW
      counting: ONE_PER_CLICK
```

### Tracking Implementation

```yaml
tracking_options:
  recommended: GOOGLE_TAG  # gtag.js

  implementation:
    - Install Google Tag on job landing pages
    - Configure conversion linker
    - Set up application form tracking
    - Enable enhanced conversions (if available)

  attribution:
    model: DATA_DRIVEN  # Or LAST_CLICK if insufficient data
    window: 30_DAYS
```

---

## API Integration

### Required Credentials

```yaml
credentials:
  developer_token:
    description: "Google Ads API developer token"
    level: "Basic access (initially) or Standard access"
    obtain: "Apply via Google Ads API Center"

  oauth2:
    client_id: required
    client_secret: required
    refresh_token: required
    scopes:
      - "https://www.googleapis.com/auth/adwords"

  customer_id:
    description: "The company's Google Ads customer ID"
    format: "XXX-XXX-XXXX"
```

### Key API Operations

```yaml
api_operations:
  campaign_management:
    create_campaign:
      service: CampaignService
      method: mutate

    create_ad_group:
      service: AdGroupService
      method: mutate

    create_ad:
      service: AdGroupAdService
      method: mutate

    add_keywords:
      service: AdGroupCriterionService
      method: mutate

  reporting:
    get_performance:
      service: GoogleAdsService
      method: searchStream
      query: "SELECT campaign.id, metrics.clicks, metrics.conversions..."

  recommendations:
    get_recommendations:
      service: RecommendationService
      method: search
```

### Rate Limits

```yaml
rate_limits:
  basic_access:
    daily_operations: 15000

  standard_access:
    daily_operations: unlimited

  best_practices:
    - Batch operations where possible
    - Use searchStream for large reports
    - Implement exponential backoff
```

---

## Campaign Generation

### generateCampaign() Implementation

```python
def generate_campaign(job_order, strategy):
    """
    Creates a Google Ads campaign structure from job order and strategy.

    Args:
        job_order: Cloudwall job order data
        strategy: Strategy Agent guidance including Writer Agent output

    Returns:
        Campaign object ready for validation and publishing
    """

    campaign = Campaign(
        platform_id="google_ads",
        job_order_id=job_order.job_id,
        name=f"{job_order.job_id}-{classify_role(job_order.job_title)}",
        status="DRAFT"
    )

    # Campaign settings
    campaign.settings = CampaignSettings(
        budget=DailyBudget(
            amount=strategy.budget_allocation.google_ads.amount,
            currency="USD"
        ),
        bidding=BiddingStrategy(
            strategy="MAXIMIZE_CONVERSIONS",
            target_cpa=strategy.target_cpa if strategy.target_cpa else None
        ),
        location=LocationTargeting(
            target=job_order.location,
            radius_miles=50 if job_order.work_arrangement == "hybrid" else None
        ),
        schedule=determine_schedule(job_order.urgency)
    )

    # Generate ad groups
    keywords = generate_keywords(job_order)
    writer_output = strategy.writer_output.google_ads

    campaign.ad_groups = [
        create_ad_group(
            name="Intent-RoleSeeking",
            keywords=keywords["role_seeking"],
            rsa=writer_output.rsa_role_focused
        ),
        create_ad_group(
            name="Intent-SkillBased",
            keywords=keywords["skill_based"],
            rsa=writer_output.rsa_skill_focused
        ),
        create_ad_group(
            name="Intent-LocationBased",
            keywords=keywords["location_based"],
            rsa=writer_output.rsa_location_focused
        )
    ]

    # Add negative keywords
    campaign.negative_keywords = get_negative_keywords(job_order)

    # Tracking
    campaign.tracking = TrackingConfig(
        conversion_actions=["Application Submitted"],
        utm_source="google",
        utm_medium="cpc",
        utm_campaign=campaign.name
    )

    return campaign
```

---

## Validation Rules

### Pre-Publish Validation

```yaml
validation_rules:
  campaign_level:
    - budget >= 10  # Minimum daily budget
    - at_least_one_location_target
    - bidding_strategy_set

  ad_group_level:
    - at_least_one_keyword
    - at_least_one_ad
    - keywords_not_duplicate_across_groups

  ad_level:
    - headlines >= 3
    - descriptions >= 2
    - final_url_valid
    - no_trademark_violations
    - no_excessive_punctuation
    - no_all_caps

  keyword_level:
    - not_trademarked
    - not_restricted_content
    - character_limit <= 80

  compliance:
    - no_discriminatory_language
    - salary_transparency_if_required
    - eeoc_compliant
```

### Common Validation Errors

```yaml
common_errors:
  HEADLINE_TOO_LONG:
    message: "Headline exceeds 30 characters"
    fix: "Shorten headline or use abbreviations"

  DESCRIPTION_TOO_LONG:
    message: "Description exceeds 90 characters"
    fix: "Condense copy"

  DUPLICATE_HEADLINES:
    message: "Headlines are too similar"
    fix: "Diversify headline content"

  URL_NOT_WORKING:
    message: "Final URL returns error"
    fix: "Verify landing page is live"

  POLICY_VIOLATION:
    message: "Ad content violates policy"
    fix: "Review Google Ads policies, adjust copy"
```

---

## Performance Metrics

### Metrics Retrieved

```yaml
metrics:
  core:
    - impressions
    - clicks
    - ctr  # Click-through rate
    - conversions
    - conversion_rate
    - cost
    - cpc  # Cost per click
    - cpa  # Cost per acquisition

  quality:
    - quality_score  # 1-10 at keyword level
    - ad_strength    # "Poor" to "Excellent"
    - expected_ctr
    - ad_relevance
    - landing_page_experience

  competitive:
    - search_impression_share
    - search_top_impression_share
    - search_absolute_top_impression_share

  asset_performance:
    - headline_performance  # "Best", "Good", "Low"
    - description_performance
```

### Reporting Query

```sql
SELECT
  campaign.id,
  campaign.name,
  ad_group.id,
  ad_group.name,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.conversions,
  metrics.cost_micros,
  metrics.average_cpc,
  metrics.cost_per_conversion,
  ad_group_criterion.quality_info.quality_score
FROM ad_group
WHERE campaign.id = {campaign_id}
  AND segments.date DURING LAST_7_DAYS
```

---

## Error Handling

### API Error Codes

```yaml
error_handling:
  AUTHENTICATION_ERROR:
    action: "Refresh OAuth token"
    retryable: true

  QUOTA_ERROR:
    action: "Wait and retry with backoff"
    retryable: true

  POLICY_VIOLATION:
    action: "Return violation details for copy revision"
    retryable: false

  RESOURCE_NOT_FOUND:
    action: "Verify resource IDs"
    retryable: false

  INTERNAL_ERROR:
    action: "Retry with exponential backoff"
    retryable: true
    max_retries: 3
```

---

## Implementation Checklist

### Phase 1: Setup
- [ ] Obtain Google Ads API developer token
- [ ] Set up OAuth2 credentials
- [ ] Configure customer ID access
- [ ] Implement conversion tracking on job pages

### Phase 2: Core Functions
- [ ] Implement `getPlatformCapabilities()`
- [ ] Implement `getAdRequirements()`
- [ ] Implement `scoreForJob()`
- [ ] Implement `generateCampaign()`
- [ ] Implement `validateCampaign()`

### Phase 3: Publishing
- [ ] Implement `publishCampaign()`
- [ ] Implement `pauseCampaign()` / `resumeCampaign()`
- [ ] Test with sandbox/test account

### Phase 4: Reporting
- [ ] Implement `getPerformanceMetrics()`
- [ ] Implement `getCostReport()`
- [ ] Set up scheduled metric retrieval

### Phase 5: Production
- [ ] Test end-to-end with real job order
- [ ] Set up monitoring and alerts
- [ ] Document operational procedures
