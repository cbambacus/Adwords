# Platform Interface Definition

This document defines the contract that all advertising platform adapters must implement. This enables the Strategy Agent to work with any platform in a consistent way.

---

## Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PlatformAdapter                          │
├─────────────────────────────────────────────────────────────┤
│ Identity                                                    │
│   getPlatformId() → string                                  │
│   getPlatformName() → string                                │
│   getStatus() → "active" | "planned" | "deprecated"         │
├─────────────────────────────────────────────────────────────┤
│ Capabilities                                                │
│   getPlatformCapabilities() → PlatformCapabilities          │
│   getAdRequirements() → AdRequirements                      │
│   getSupportedRegions() → Region[]                          │
├─────────────────────────────────────────────────────────────┤
│ Evaluation                                                  │
│   scoreForJob(jobOrder) → PlatformScore                     │
│   estimateCost(jobOrder) → CostEstimate                     │
├─────────────────────────────────────────────────────────────┤
│ Campaign Operations                                         │
│   generateCampaign(jobOrder, strategy) → Campaign           │
│   validateCampaign(campaign) → ValidationResult             │
│   publishCampaign(campaign) → PublishResult                 │
│   pauseCampaign(campaignId) → void                          │
│   resumeCampaign(campaignId) → void                         │
├─────────────────────────────────────────────────────────────┤
│ Performance                                                 │
│   getPerformanceMetrics(campaignId) → PerformanceMetrics    │
│   getCostReport(campaignId) → CostReport                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Types

### PlatformCapabilities

```yaml
PlatformCapabilities:
  channelTypes:
    - search        # Intent-based search ads (Google, Bing)
    - social        # Social media feed ads (LinkedIn, Meta)
    - display       # Banner/visual ads
    - jobBoard      # Native job listing (Indeed, ZipRecruiter)
    - video         # Video ads (YouTube, TikTok)

  targetingOptions:
    keywords: boolean       # Can target by search keywords
    jobTitle: boolean       # Can target by current job title
    skills: boolean         # Can target by listed skills
    industry: boolean       # Can target by industry
    company: boolean        # Can target by current/past company
    seniority: boolean      # Can target by seniority level
    location: boolean       # Can target by geography
    demographics: boolean   # Can target by age, gender (where legal)
    interests: boolean      # Can target by interests/behaviors
    retargeting: boolean    # Can retarget previous visitors

  adFormats:
    - textAd          # Simple text-based ad
    - responsiveSearch # Multiple headlines/descriptions (RSA)
    - singleImage      # Image + text
    - carousel         # Multiple images
    - video            # Video content
    - jobPosting       # Native job format
    - inMail           # Direct message (LinkedIn)

  biddingStrategies:
    - manualCpc       # Manual cost-per-click
    - targetCpa       # Target cost-per-acquisition
    - targetRoas      # Target return on ad spend
    - maximizeClicks  # Maximize clicks within budget
    - maximizeConversions # Maximize conversions within budget
```

### AdRequirements

```yaml
AdRequirements:
  headlines:
    minCount: number      # Minimum headlines required
    maxCount: number      # Maximum headlines allowed
    minLength: number     # Minimum characters per headline
    maxLength: number     # Maximum characters per headline

  descriptions:
    minCount: number
    maxCount: number
    minLength: number
    maxLength: number

  images:
    required: boolean
    formats: string[]     # ["jpg", "png", "gif"]
    minWidth: number
    minHeight: number
    maxFileSize: number   # in KB

  videos:
    required: boolean
    formats: string[]
    minDuration: number   # seconds
    maxDuration: number

  landingPage:
    required: boolean
    httpsRequired: boolean
    mobileOptimized: boolean

  additionalAssets:
    sitelinks: boolean
    callouts: boolean
    structuredSnippets: boolean
    callExtension: boolean
    locationExtension: boolean
```

### PlatformScore

```yaml
PlatformScore:
  platformId: string
  overallScore: number    # 0-100

  factorScores:
    roleFit: number       # 0-100
    audienceMatch: number
    geographicCoverage: number
    costEfficiency: number
    urgencyFit: number
    historicalPerformance: number

  recommendation: "highly_recommended" | "recommended" | "consider" | "not_recommended"
  reasoning: string       # Explanation for the score

  constraints:
    - type: string        # e.g., "special_ad_category"
      description: string
      impact: "blocker" | "limitation" | "consideration"
```

### CostEstimate

```yaml
CostEstimate:
  platformId: string

  projectedCpc:
    low: number
    mid: number
    high: number
    currency: string

  projectedCpa:
    low: number
    mid: number
    high: number
    currency: string

  recommendedDailyBudget:
    minimum: number
    recommended: number
    aggressive: number

  estimatedReach:
    impressionsPerDay: number
    clicksPerDay: number
    applicationsPerDay: number

  confidenceLevel: "high" | "medium" | "low"
  basedOn: string         # e.g., "historical data" or "industry benchmarks"
```

### Campaign

```yaml
Campaign:
  id: string              # Internal campaign ID
  platformId: string
  jobOrderId: string

  name: string
  status: "draft" | "pending_review" | "active" | "paused" | "completed"

  settings:
    budget:
      dailyBudget: number
      totalBudget: number
      currency: string
    bidding:
      strategy: string
      targetCpa: number   # if applicable
      maxCpc: number      # if applicable
    schedule:
      startDate: date
      endDate: date
      dayParting: object  # optional time-of-day settings
    location:
      targetLocations: string[]
      excludeLocations: string[]
      radiusMiles: number

  adGroups:
    - id: string
      name: string
      theme: string       # e.g., "role-seeking", "skill-based"
      keywords: Keyword[]
      ads: Ad[]

  targeting:
    audiences: Audience[]
    demographics: object

  tracking:
    conversionActions: string[]
    utmParameters: object
```

### PerformanceMetrics

```yaml
PerformanceMetrics:
  campaignId: string
  platformId: string
  dateRange:
    start: date
    end: date

  impressions: number
  clicks: number
  ctr: number             # Click-through rate

  conversions: number     # Applications submitted
  conversionRate: number

  cost: number
  cpc: number             # Cost per click
  cpa: number             # Cost per application

  qualityIndicators:
    qualityScore: number  # Platform-specific (Google: 1-10)
    adStrength: string    # "Poor" | "Average" | "Good" | "Excellent"

  topPerformers:
    headlines: string[]   # Best performing headlines
    descriptions: string[]
    keywords: string[]

  recommendations:
    - type: string
      description: string
      priority: "high" | "medium" | "low"
```

---

## Method Specifications

### getPlatformCapabilities()

Returns the platform's capabilities. Used by Strategy Agent to determine if a platform can support the job order requirements.

**Returns:** `PlatformCapabilities`

**Example:**
```json
{
  "channelTypes": ["search", "display"],
  "targetingOptions": {
    "keywords": true,
    "jobTitle": false,
    "skills": false,
    "location": true
  },
  "adFormats": ["responsiveSearch", "textAd"],
  "biddingStrategies": ["targetCpa", "maximizeConversions"]
}
```

---

### scoreForJob(jobOrder)

Evaluates how well this platform fits the given job order. Called by Platform Evaluator.

**Parameters:**
- `jobOrder`: The Cloudwall job order data

**Returns:** `PlatformScore`

**Scoring Logic:**
Each adapter implements platform-specific scoring based on:
1. Role type alignment with platform audience
2. Geographic match
3. Budget appropriateness
4. Historical performance for similar roles
5. Any constraints (e.g., Special Ad Category for employment)

---

### generateCampaign(jobOrder, strategy)

Creates a campaign structure ready for publishing.

**Parameters:**
- `jobOrder`: The Cloudwall job order data
- `strategy`: Strategy Agent's guidance (targeting, budget allocation, Writer Agent output)

**Returns:** `Campaign`

**Responsibilities:**
1. Map job order fields to platform-specific campaign settings
2. Structure ad groups by intent/theme
3. Include Writer Agent's ad copy in correct format
4. Set up conversion tracking
5. Apply compliance requirements (EEOC, salary transparency)

---

### publishCampaign(campaign)

Pushes the campaign to the platform's API.

**Parameters:**
- `campaign`: Validated campaign object

**Returns:** `PublishResult`
```yaml
PublishResult:
  success: boolean
  platformCampaignId: string  # Platform's assigned ID
  status: string
  reviewRequired: boolean
  estimatedReviewTime: string
  errors: Error[]
  warnings: Warning[]
```

---

### getPerformanceMetrics(campaignId)

Retrieves current performance data for Optimizer Agent.

**Parameters:**
- `campaignId`: Internal or platform campaign ID

**Returns:** `PerformanceMetrics`

**Frequency:** Called by Optimizer on schedule (e.g., every 6 hours for active campaigns)

---

## Implementation Requirements

### Required Methods (Must Implement)

All adapters MUST implement:
- `getPlatformId()`
- `getPlatformName()`
- `getStatus()`
- `getPlatformCapabilities()`
- `getAdRequirements()`
- `scoreForJob(jobOrder)`
- `generateCampaign(jobOrder, strategy)`
- `validateCampaign(campaign)`

### Optional Methods (If Platform Supports)

- `publishCampaign()` - Required for active platforms, not for "planned"
- `getPerformanceMetrics()` - Required for active platforms
- `pauseCampaign()` / `resumeCampaign()` - If platform supports
- `estimateCost()` - If platform provides cost estimation APIs

---

## Error Handling

All methods should return structured errors:

```yaml
PlatformError:
  code: string            # e.g., "AUTH_FAILED", "QUOTA_EXCEEDED"
  message: string
  platformErrorCode: string  # Original platform error code
  retryable: boolean
  retryAfter: number      # seconds, if retryable
```

Common error codes:
- `AUTH_FAILED` - Authentication/authorization error
- `QUOTA_EXCEEDED` - API quota or budget limit reached
- `VALIDATION_FAILED` - Campaign/ad validation failed
- `POLICY_VIOLATION` - Platform policy violation
- `RATE_LIMITED` - Too many requests
- `PLATFORM_UNAVAILABLE` - Platform API down

---

## Adapter Registration

Each adapter registers itself with the Platform Registry:

```yaml
AdapterRegistration:
  platformId: string
  adapterVersion: string
  interfaceVersion: string  # Version of this interface implemented
  maintainer: string
  lastUpdated: date
```
