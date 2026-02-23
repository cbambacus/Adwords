# Learnings Database Architecture

This document specifies the database architecture that captures campaign performance insights and informs the Strategy Agent's decisions.

---

## Overview

The Learnings Database is a 4-layer system that transforms raw campaign data into actionable intelligence:

```
┌─────────────────────────────────────────────────────────────────┐
│                     LEARNINGS DATABASE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: PERFORMANCE FACTS (Raw Data)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Campaign → Ad Group → Ad → Metrics                       │   │
│  │ Every headline, description, keyword with performance    │   │
│  │ Updated: Real-time                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  Layer 2: DIMENSIONAL AGGREGATES (Pre-computed)                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Metrics rolled up by: Location, Seniority, Industry,     │   │
│  │ Role Type, Platform, Work Arrangement                    │   │
│  │ Updated: Nightly                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  Layer 3: FEATURE PERFORMANCE (Weighted Elements)               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Specific copy elements with performance scores           │   │
│  │ "remote" → +15% CTR in tech roles                        │   │
│  │ Updated: Weekly                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  Layer 4: INSIGHTS (Queryable Rules)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Auto-extracted insights with confidence scores           │   │
│  │ "Senior roles in finance respond to stability messaging" │   │
│  │ Updated: Continuous (auto-promoted when thresholds met)  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Performance Facts

Raw campaign data - the immutable source of truth.

### Campaign Table

```sql
CREATE TABLE campaigns (
    id VARCHAR(50) PRIMARY KEY,
    job_order_id VARCHAR(50) NOT NULL,
    platform VARCHAR(20) NOT NULL,  -- 'google_ads', 'linkedin', 'indeed', 'meta'
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,    -- 'draft', 'active', 'paused', 'completed'

    -- Job characteristics (denormalized for fast querying)
    job_title VARCHAR(200),
    role_type VARCHAR(20),          -- 'creative', 'technical', 'marketing', 'corporate', 'executive'
    seniority VARCHAR(20),          -- 'entry', 'mid', 'senior', 'executive'
    industry VARCHAR(100),
    location_city VARCHAR(100),
    location_state VARCHAR(50),
    location_country VARCHAR(50),
    work_arrangement VARCHAR(20),   -- 'remote', 'hybrid', 'onsite'
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(10),

    -- Campaign settings
    daily_budget DECIMAL(10,2),
    total_budget DECIMAL(10,2),
    bidding_strategy VARCHAR(50),

    -- Core metrics (updated by Optimizer)
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    ctr DECIMAL(5,4),               -- 0.0000 to 1.0000
    conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4),
    cost DECIMAL(10,2) DEFAULT 0,
    cpc DECIMAL(10,2),
    cpa DECIMAL(10,2),

    -- Extended conversion metrics (from Google Ads API)
    all_conversions DECIMAL(10,2),          -- Includes view-through, cross-device
    conversions_value DECIMAL(12,2),        -- Total value of conversions
    all_conversions_value DECIMAL(12,2),    -- Value including view-through
    view_through_conversions INTEGER,       -- Conversions after ad view (no click)

    -- Competitive metrics (Google Ads Search campaigns)
    search_impression_share DECIMAL(5,4),   -- % of eligible impressions received
    search_top_impression_share DECIMAL(5,4), -- % shown above organic results
    search_absolute_top_is DECIMAL(5,4),    -- % shown as very first ad
    search_budget_lost_is DECIMAL(5,4),     -- Impressions lost due to budget
    search_rank_lost_is DECIMAL(5,4),       -- Impressions lost due to rank

    -- Interaction metrics
    interactions BIGINT,                     -- All interactions (clicks + engagements)
    engagements BIGINT,                      -- Non-click engagements
    engagement_rate DECIMAL(5,4),

    -- Quality indicators
    quality_score DECIMAL(3,1),     -- Weighted average keyword quality score
    ad_strength VARCHAR(20),        -- 'poor', 'average', 'good', 'excellent'

    -- Metadata
    platform_campaign_id VARCHAR(100),
    INDEX idx_platform (platform),
    INDEX idx_role_type (role_type),
    INDEX idx_seniority (seniority),
    INDEX idx_location (location_city, location_state),
    INDEX idx_created (created_at)
);
```

### Ad Group Table

```sql
CREATE TABLE ad_groups (
    id VARCHAR(50) PRIMARY KEY,
    campaign_id VARCHAR(50) REFERENCES campaigns(id),
    name VARCHAR(200),
    theme VARCHAR(50),              -- 'role-seeking', 'skill-based', 'location-based'

    -- Metrics
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    cost DECIMAL(10,2) DEFAULT 0,

    platform_ad_group_id VARCHAR(100),
    INDEX idx_campaign (campaign_id)
);
```

### Ad Table

```sql
CREATE TABLE ads (
    id VARCHAR(50) PRIMARY KEY,
    ad_group_id VARCHAR(50) REFERENCES ad_groups(id),

    -- RSA assets
    headlines JSONB,                -- ["headline1", "headline2", ...]
    descriptions JSONB,             -- ["desc1", "desc2", ...]
    final_url VARCHAR(500),
    display_path JSONB,             -- ["path1", "path2"]

    -- Per-asset performance (populated from platform reports)
    headline_performance JSONB,     -- {"headline1": "Best", "headline2": "Good", ...}
    description_performance JSONB,

    -- Metrics
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions INTEGER DEFAULT 0,

    platform_ad_id VARCHAR(100),
    INDEX idx_ad_group (ad_group_id)
);
```

### Keyword Table

```sql
CREATE TABLE keywords (
    id VARCHAR(50) PRIMARY KEY,
    ad_group_id VARCHAR(50) REFERENCES ad_groups(id),

    text VARCHAR(200) NOT NULL,
    match_type VARCHAR(20),         -- 'broad', 'phrase', 'exact'
    status VARCHAR(20),             -- 'ENABLED', 'PAUSED', 'REMOVED'

    -- Quality Score and components (Google Ads specific)
    quality_score INTEGER,          -- 1-10 overall score
    expected_ctr VARCHAR(20),       -- 'ABOVE_AVERAGE', 'AVERAGE', 'BELOW_AVERAGE'
    ad_relevance VARCHAR(20),       -- 'ABOVE_AVERAGE', 'AVERAGE', 'BELOW_AVERAGE'
    landing_page_experience VARCHAR(20), -- 'ABOVE_AVERAGE', 'AVERAGE', 'BELOW_AVERAGE'
    historical_quality_score INTEGER, -- Historical QS for trend analysis

    -- Metrics
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    conversions_value DECIMAL(10,2),
    cost DECIMAL(10,2) DEFAULT 0,
    cpc DECIMAL(10,2),
    cpa DECIMAL(10,2),

    -- Approval status (for policy tracking)
    approval_status VARCHAR(50),    -- 'APPROVED', 'APPROVED_LIMITED', 'DISAPPROVED'

    platform_keyword_id VARCHAR(100),
    INDEX idx_ad_group (ad_group_id),
    INDEX idx_text (text),
    INDEX idx_quality_score (quality_score)
);
```

### Search Terms Table

Captures actual user search queries that triggered ads - critical for keyword discovery and negative keyword identification.

```sql
CREATE TABLE search_terms (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) REFERENCES campaigns(id),
    ad_group_id VARCHAR(50) REFERENCES ad_groups(id),
    keyword_id VARCHAR(50) REFERENCES keywords(id),

    search_term TEXT NOT NULL,          -- Actual query user typed
    match_type_triggered VARCHAR(20),   -- How it matched: 'BROAD', 'PHRASE', 'EXACT', 'NEAR_EXACT'

    -- Metrics
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    cost DECIMAL(10,2) DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    conversions_value DECIMAL(10,2),
    ctr DECIMAL(5,4),
    cpc DECIMAL(10,2),

    -- Classification and actions
    added_as_keyword BOOLEAN DEFAULT FALSE,     -- Promoted to keyword
    added_as_negative BOOLEAN DEFAULT FALSE,    -- Added as negative keyword
    classification VARCHAR(20),                  -- 'high_value', 'irrelevant', 'uncertain'

    -- For learning system
    job_relevance_score DECIMAL(3,2),           -- 0.00-1.00 estimated relevance

    -- Timestamps
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,

    -- Context for dimensional analysis
    campaign_seniority VARCHAR(20),
    campaign_role_type VARCHAR(20),
    campaign_location VARCHAR(100),

    INDEX idx_campaign (campaign_id),
    INDEX idx_search_term (search_term),
    INDEX idx_conversions (conversions DESC),
    INDEX idx_classification (classification),
    INDEX idx_dates (first_seen, last_seen)
);
```

**Why Search Terms Matter for Learning:**
- Discover high-converting queries to add as keywords
- Identify irrelevant queries for negative keywords
- Understand how candidates actually search for jobs
- Extract patterns for Writer Agent (e.g., "remote UX jobs" vs "UX designer work from home")

### Asset Performance Table

Detailed performance tracking for individual RSA headlines and descriptions - replaces the JSONB approach with full metrics.

```sql
CREATE TABLE asset_performance (
    id SERIAL PRIMARY KEY,
    ad_id VARCHAR(50) REFERENCES ads(id),
    campaign_id VARCHAR(50) REFERENCES campaigns(id),

    asset_type VARCHAR(20) NOT NULL,        -- 'HEADLINE', 'DESCRIPTION'
    asset_text TEXT NOT NULL,
    position INTEGER,                        -- Pin position if set (1, 2, 3, or NULL)

    -- Performance label (legacy, being deprecated June 2025)
    performance_label VARCHAR(20),          -- 'BEST', 'GOOD', 'LOW', 'PENDING', 'UNSPECIFIED'

    -- Full metrics (available as of June 2025)
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    cost DECIMAL(10,2) DEFAULT 0,

    -- Computed ratios (directional only - assets shown in combination)
    ctr DECIMAL(5,4),
    conversion_rate DECIMAL(5,4),

    -- Context for feature analysis (denormalized)
    campaign_seniority VARCHAR(20),
    campaign_role_type VARCHAR(20),
    campaign_location VARCHAR(100),
    campaign_industry VARCHAR(100),

    -- Extracted features (for Layer 3 analysis)
    features_extracted JSONB,               -- ["salary_shown", "remote_mentioned", "urgency"]

    last_updated TIMESTAMP NOT NULL,

    INDEX idx_ad (ad_id),
    INDEX idx_campaign (campaign_id),
    INDEX idx_asset_type (asset_type),
    INDEX idx_performance (performance_label),
    INDEX idx_context (campaign_seniority, campaign_role_type)
);
```

**Note on Asset Metrics:** Google cautions that asset-level metrics should be used directionally only. Assets are shown in combinations, so individual asset metrics don't reflect isolated performance. Aggregate at campaign/ad group level for accurate analysis.

### Conversion Actions Table

Track different types of conversions separately (e.g., Application Started vs Application Completed).

```sql
CREATE TABLE conversion_actions (
    id VARCHAR(50) PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,          -- 'google_ads', 'linkedin', etc.
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),                   -- 'SUBMIT_LEAD_FORM', 'PAGE_VIEW', 'PHONE_CALL'
    counting_type VARCHAR(20),              -- 'ONE_PER_CLICK', 'MANY_PER_CLICK'
    is_primary BOOLEAN DEFAULT FALSE,       -- Used for bid optimization
    value_settings JSONB,                   -- Default value, currency, etc.

    platform_conversion_id VARCHAR(100),

    INDEX idx_platform (platform),
    INDEX idx_category (category),
    INDEX idx_primary (is_primary)
);

-- Junction table for campaign-level conversion breakdown
CREATE TABLE campaign_conversions (
    campaign_id VARCHAR(50) REFERENCES campaigns(id),
    conversion_action_id VARCHAR(50) REFERENCES conversion_actions(id),

    conversions INTEGER DEFAULT 0,
    conversions_value DECIMAL(12,2) DEFAULT 0,
    all_conversions DECIMAL(10,2) DEFAULT 0,
    all_conversions_value DECIMAL(12,2) DEFAULT 0,

    last_updated TIMESTAMP NOT NULL,

    PRIMARY KEY (campaign_id, conversion_action_id)
);
```

**Example Conversion Actions for Recruitment:**
```yaml
- id: "CONV-001"
  name: "Application Started"
  category: "PAGE_VIEW"
  is_primary: false

- id: "CONV-002"
  name: "Application Completed"
  category: "SUBMIT_LEAD_FORM"
  is_primary: true  # This is what we optimize bids for

- id: "CONV-003"
  name: "Phone Call"
  category: "PHONE_CALL"
  is_primary: false
```

---

## Layer 2: Dimensional Aggregates

Pre-computed rollups for fast Strategy Agent queries.

### Dimensions

| Dimension | Column | Values | Purpose |
|-----------|--------|--------|---------|
| `location` | location_city, location_state, location_country | Geographic areas | "What works in SF vs NYC" |
| `seniority` | seniority | entry, mid, senior, executive | "How to message senior roles" |
| `role_type` | role_type | creative, technical, marketing, corporate | "What resonates with designers" |
| `industry` | industry | Tech, Finance, Healthcare, etc. | "Industry-specific messaging" |
| `work_arrangement` | work_arrangement | remote, hybrid, onsite | "Remote keyword performance" |
| `platform` | platform | google_ads, linkedin, indeed, meta | "Platform-specific patterns" |
| `salary_band` | computed | <50K, 50-100K, 100-150K, 150K+ | "High-salary ad approaches" |

### Dimensional Metrics Table

```sql
CREATE TABLE dimensional_metrics (
    id SERIAL PRIMARY KEY,

    -- Primary dimension
    dimension_type VARCHAR(50) NOT NULL,    -- 'seniority', 'location', etc.
    dimension_value VARCHAR(100) NOT NULL,  -- 'senior', 'San Francisco', etc.

    -- Optional secondary dimension for cross-analysis
    secondary_dimension_type VARCHAR(50),
    secondary_dimension_value VARCHAR(100),

    -- Aggregate metrics
    campaign_count INTEGER NOT NULL,
    total_impressions BIGINT,
    total_clicks BIGINT,
    avg_ctr DECIMAL(5,4),
    total_conversions INTEGER,
    avg_conversion_rate DECIMAL(5,4),
    total_cost DECIMAL(12,2),
    avg_cpc DECIMAL(10,2),
    avg_cpa DECIMAL(10,2),

    -- Statistical confidence
    statistical_significance BOOLEAN,
    confidence_level DECIMAL(5,2),          -- 0-100
    sample_size INTEGER,

    -- Metadata
    last_updated TIMESTAMP NOT NULL,
    data_start_date DATE,
    data_end_date DATE,

    UNIQUE (dimension_type, dimension_value, secondary_dimension_type, secondary_dimension_value),
    INDEX idx_dimension (dimension_type, dimension_value),
    INDEX idx_secondary (secondary_dimension_type, secondary_dimension_value)
);
```

### Example Data

```yaml
- dimension_type: "seniority"
  dimension_value: "senior"
  secondary_dimension_type: "location"
  secondary_dimension_value: "San Francisco"
  campaign_count: 47
  avg_ctr: 0.0312
  avg_cpa: 52.50
  confidence_level: 89

- dimension_type: "role_type"
  dimension_value: "technical"
  secondary_dimension_type: "platform"
  secondary_dimension_value: "linkedin"
  campaign_count: 123
  avg_ctr: 0.0187
  avg_cpa: 78.00
  confidence_level: 95
```

---

## Layer 3: Feature Performance

Tracks specific copy elements and their measurable impact.

### Feature Types

| Feature Type | Examples | Extraction Method |
|--------------|----------|-------------------|
| `keyword_phrase` | "remote", "competitive", "growth" | NLP extraction from headlines |
| `headline_pattern` | "salary_shown", "urgency", "question" | Pattern matching |
| `benefit_mention` | salary, remote, benefits, culture | Keyword detection |
| `cta_type` | "Apply Now", "Learn More", "Join Us" | Classification |
| `urgency_signal` | "Immediate", "ASAP", "Hiring Now" | Keyword detection |
| `length_category` | short (<20 chars), medium, long | Character count |

### Feature Performance Table

```sql
CREATE TABLE feature_performance (
    id SERIAL PRIMARY KEY,

    feature_type VARCHAR(50) NOT NULL,      -- 'benefit_mention', 'headline_pattern', etc.
    feature_value VARCHAR(200) NOT NULL,    -- 'remote', 'salary_shown', etc.

    -- Context dimensions (where does this feature work?)
    context_dimension VARCHAR(50),          -- 'seniority', 'location', etc.
    context_value VARCHAR(100),             -- 'senior', 'San Francisco', etc.

    -- Performance comparison
    campaigns_with_feature INTEGER NOT NULL,
    campaigns_without_feature INTEGER NOT NULL,

    ctr_with_feature DECIMAL(5,4),
    ctr_without_feature DECIMAL(5,4),
    ctr_lift DECIMAL(6,2),                  -- Percentage: +15.5, -8.2

    conversion_rate_with DECIMAL(5,4),
    conversion_rate_without DECIMAL(5,4),
    conversion_lift DECIMAL(6,2),

    cpa_with DECIMAL(10,2),
    cpa_without DECIMAL(10,2),
    cpa_lift DECIMAL(6,2),                  -- Negative is better

    -- Statistical confidence
    p_value DECIMAL(6,5),
    confidence_level DECIMAL(5,2),          -- 0-100
    sample_size INTEGER,

    -- Metadata
    last_updated TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'active',    -- 'active', 'testing', 'retired'

    UNIQUE (feature_type, feature_value, context_dimension, context_value),
    INDEX idx_feature (feature_type, feature_value),
    INDEX idx_context (context_dimension, context_value),
    INDEX idx_confidence (confidence_level DESC)
);
```

### Example Data

```yaml
- feature_type: "benefit_mention"
  feature_value: "remote"
  context_dimension: "role_type"
  context_value: "technical"
  campaigns_with_feature: 89
  campaigns_without_feature: 34
  ctr_lift: +23.4
  conversion_lift: +18.2
  confidence_level: 95

- feature_type: "headline_pattern"
  feature_value: "salary_shown"
  context_dimension: "location"
  context_value: "California"
  ctr_lift: +31.2
  confidence_level: 92

- feature_type: "urgency_signal"
  feature_value: "urgent"
  context_dimension: "seniority"
  context_value: "executive"
  ctr_lift: -12.5    # Executives don't respond to urgency
  confidence_level: 78
```

---

## Layer 4: Extracted Insights

Human-readable, actionable rules derived from feature performance data.

### Insight Table

```sql
CREATE TABLE insights (
    id VARCHAR(50) PRIMARY KEY,

    -- Classification
    type VARCHAR(20) NOT NULL,              -- 'data_derived', 'seeded', 'human_observed'
    status VARCHAR(20) NOT NULL,            -- 'active', 'testing', 'retired', 'pending'
    priority INTEGER DEFAULT 50,            -- 1-100, higher = more important

    -- The insight itself
    statement TEXT NOT NULL,                -- Human-readable statement

    -- Applicability conditions (JSONB for flexible querying)
    applies_to JSONB NOT NULL,
    -- Example: {"seniority": ["senior", "executive"], "industry": ["finance"]}

    -- Guidance for agents
    strategy_guidance TEXT,                 -- For Strategy Agent
    writer_guidance TEXT,                   -- For Writer Agent

    -- Evidence and confidence
    supporting_features JSONB,              -- Feature IDs that support this insight
    supporting_campaigns JSONB,             -- Campaign IDs as evidence
    confidence DECIMAL(5,2) NOT NULL,       -- 0-100

    -- Lifecycle
    created_at TIMESTAMP NOT NULL,
    created_by VARCHAR(100),                -- 'system:auto', 'seed:research', 'human:name'
    last_validated TIMESTAMP,
    validation_result VARCHAR(50),          -- 'confirmed', 'weakened', 'contradicted'
    expires_at TIMESTAMP,                   -- For time-sensitive insights

    INDEX idx_status (status),
    INDEX idx_confidence (confidence DESC),
    INDEX idx_applies_to USING GIN (applies_to)
);
```

### Example Insights

```yaml
- id: "INS-001"
  type: "data_derived"
  status: "active"
  statement: "Senior roles in finance respond better to stability and growth messaging than urgency"
  applies_to:
    seniority: ["senior", "executive"]
    industry: ["finance", "banking", "insurance"]
  strategy_guidance: "Avoid urgency signals, emphasize career growth and company stability"
  writer_guidance: "Use phrases like 'established team', 'growth trajectory', 'leadership opportunity'. Avoid 'ASAP', 'immediately', 'urgent'."
  confidence: 87
  created_by: "system:auto"

- id: "INS-002"
  type: "data_derived"
  status: "active"
  statement: "Including explicit salary range in headlines increases CTR by 25-35% in California"
  applies_to:
    location: ["California", "CA"]
  strategy_guidance: "Always include salary in headlines for CA roles"
  writer_guidance: "Lead headline with salary range: '$130K-$155K Senior UX Designer'"
  confidence: 94
  created_by: "system:auto"

- id: "SEED-001"
  type: "seeded"
  status: "active"
  statement: "Remote work mention increases applications 3x"
  applies_to:
    work_arrangement: ["remote", "hybrid"]
  strategy_guidance: "Prioritize remote/hybrid messaging when applicable"
  writer_guidance: "Include 'Remote' or 'Work from Home' prominently in headlines"
  confidence: 80  # Lower until validated with own data
  created_by: "seed:recruitment-advertising-resources.md"
```

---

## Query Interface

### API for Strategy Agent

```python
class LearningsDatabase:
    """Query interface for Strategy Agent to access learnings."""

    def get_metrics(self, dimensions: dict) -> DimensionalMetrics:
        """
        Get aggregate performance for a dimension combination.

        Args:
            dimensions: {"seniority": "senior", "location": "San Francisco"}

        Returns:
            DimensionalMetrics with avg_cpa, avg_ctr, campaign_count, etc.
        """
        pass

    def get_feature_performance(
        self,
        feature_type: str,
        context: dict,
        min_confidence: float = 70
    ) -> List[FeaturePerformance]:
        """
        Get feature performance for a specific context.

        Args:
            feature_type: "benefit_mention", "headline_pattern", etc.
            context: {"seniority": "senior", "role_type": "technical"}
        """
        pass

    def get_insights(
        self,
        job_order: JobOrder,
        status: str = "active"
    ) -> List[Insight]:
        """
        Get all applicable insights for a job order.

        Matches insights where job_order dimensions match insight.applies_to
        """
        pass

    def find_similar_campaigns(
        self,
        job_order: JobOrder,
        limit: int = 5,
        min_performance: str = "good"  # 'good', 'average', 'any'
    ) -> List[Campaign]:
        """
        Find similar past campaigns for reference.

        Similarity based on: role_type, seniority, location, industry
        """
        pass

    def get_top_performing_copy(
        self,
        context: dict,
        limit: int = 10
    ) -> CopyRecommendations:
        """
        Get top performing headlines and descriptions for context.

        Returns headlines/descriptions with "Best" performance rating
        in similar campaigns.
        """
        pass
```

### Example Query Flow

```python
def enrich_strategy_with_learnings(job_order, strategy):
    db = LearningsDatabase()

    # 1. Get dimensional benchmarks for expected performance
    benchmarks = db.get_metrics({
        "seniority": job_order.seniority,
        "location": job_order.location_state,
        "role_type": classify_role(job_order.job_title)
    })
    strategy.expected_cpa = benchmarks.avg_cpa
    strategy.expected_ctr = benchmarks.avg_ctr

    # 2. Get applicable insights
    insights = db.get_insights(job_order)
    for insight in insights:
        if insight.confidence >= 80:
            strategy.add_hard_guidance(insight.strategy_guidance)
            strategy.writer_brief.add_requirement(insight.writer_guidance)
        else:
            strategy.add_soft_guidance(insight.strategy_guidance)
            strategy.writer_brief.add_suggestion(insight.writer_guidance)

    # 3. Get feature performance for copy recommendations
    for feature_type in ["benefit_mention", "headline_pattern", "cta_type"]:
        features = db.get_feature_performance(feature_type, {
            "seniority": job_order.seniority,
            "industry": job_order.industry
        })
        for f in features:
            if f.ctr_lift > 10 and f.confidence_level >= 80:
                strategy.writer_brief.add_recommended_element(f.feature_value)
            elif f.ctr_lift < -10 and f.confidence_level >= 80:
                strategy.writer_brief.add_avoid_element(f.feature_value)

    # 4. Find similar successful campaigns for reference
    similar = db.find_similar_campaigns(job_order, limit=3, min_performance="good")
    strategy.reference_campaigns = [
        {
            "headlines": c.top_headlines,
            "ctr": c.ctr,
            "cpa": c.cpa
        }
        for c in similar
    ]

    return strategy
```

---

## Data Aggregation Jobs

### Nightly: Dimensional Aggregates

```sql
-- Refresh dimensional metrics for seniority × location
INSERT INTO dimensional_metrics (
    dimension_type, dimension_value,
    secondary_dimension_type, secondary_dimension_value,
    campaign_count, total_impressions, total_clicks, avg_ctr,
    total_conversions, avg_conversion_rate, avg_cpa,
    last_updated
)
SELECT
    'seniority' as dimension_type,
    c.seniority as dimension_value,
    'location' as secondary_dimension_type,
    c.location_state as secondary_dimension_value,
    COUNT(*) as campaign_count,
    SUM(c.impressions) as total_impressions,
    SUM(c.clicks) as total_clicks,
    AVG(c.ctr) as avg_ctr,
    SUM(c.conversions) as total_conversions,
    AVG(c.conversion_rate) as avg_conversion_rate,
    AVG(c.cpa) as avg_cpa,
    NOW() as last_updated
FROM campaigns c
WHERE c.status = 'completed'
  AND c.conversions > 0
GROUP BY c.seniority, c.location_state
ON CONFLICT (dimension_type, dimension_value, secondary_dimension_type, secondary_dimension_value)
DO UPDATE SET
    campaign_count = EXCLUDED.campaign_count,
    total_impressions = EXCLUDED.total_impressions,
    -- ... etc
    last_updated = NOW();
```

### Weekly: Feature Performance Analysis

See `Architecture/insight-automation.md` for feature extraction and analysis jobs.

---

## Performance Considerations

### Indexing Strategy

```sql
-- Fast dimension lookups
CREATE INDEX idx_campaigns_dimensions ON campaigns (role_type, seniority, location_state);

-- Fast insight matching with GIN index on JSONB
CREATE INDEX idx_insights_applies_to ON insights USING GIN (applies_to);

-- Time-based queries for recent data
CREATE INDEX idx_campaigns_created ON campaigns (created_at DESC);

-- Search terms analysis (high-volume table)
CREATE INDEX idx_search_terms_conversions ON search_terms (conversions DESC) WHERE conversions > 0;
CREATE INDEX idx_search_terms_unclassified ON search_terms (classification) WHERE classification = 'uncertain';
CREATE INDEX idx_search_terms_text_trgm ON search_terms USING gin (search_term gin_trgm_ops);  -- For text similarity

-- Asset performance analysis
CREATE INDEX idx_asset_perf_best ON asset_performance (performance_label) WHERE performance_label = 'BEST';
CREATE INDEX idx_asset_perf_context ON asset_performance (campaign_role_type, campaign_seniority);

-- Keyword quality score analysis
CREATE INDEX idx_keywords_low_qs ON keywords (quality_score) WHERE quality_score < 6;
CREATE INDEX idx_keywords_qs_components ON keywords (expected_ctr, ad_relevance, landing_page_experience);

-- Conversion action analysis
CREATE INDEX idx_campaign_conv_primary ON campaign_conversions (conversion_action_id)
    WHERE conversion_action_id IN (SELECT id FROM conversion_actions WHERE is_primary = true);
```

### Query Optimization

- Dimensional aggregates are pre-computed for <10ms query time
- Feature performance queries limited to high-confidence results
- Insight matching uses GIN index for fast JSONB containment queries
- Similar campaign search uses materialized view of campaign vectors

### Data Retention

```yaml
retention_policy:
  layer_1_performance_facts:
    campaigns: "indefinite"
    ad_groups: "indefinite"
    ads: "indefinite"
    keywords: "indefinite"

    # High-volume tables with retention limits
    search_terms:
      raw_data: "12 months"
      aggregated: "indefinite"
      high_converting: "indefinite"  # Keep all search terms with conversions > 0

    asset_performance:
      raw_data: "12 months"
      top_performers: "indefinite"  # Keep BEST rated assets forever

    campaign_conversions:
      raw_data: "indefinite"

  layer_2_dimensional_aggregates:
    rolling_window: "last 12 months"
    refresh: "nightly"

  layer_3_feature_performance:
    active_features: "indefinite"
    retired_features: "archive after 6 months"

  layer_4_insights:
    active: "indefinite"
    retired: "archive after 12 months"
```

### Data Volume Estimates

| Table | Rows/Campaign | Est. Annual Volume | Notes |
|-------|---------------|-------------------|-------|
| campaigns | 1 | ~1,000 | One per job order |
| ad_groups | 3 | ~3,000 | 3 themes per campaign |
| ads | 3-6 | ~5,000 | 1-2 RSAs per ad group |
| keywords | 30-50 | ~40,000 | 10-15 per ad group |
| search_terms | 500-2000 | ~1,000,000 | High volume, needs pruning |
| asset_performance | 50-100 | ~75,000 | 15 headlines + 4 desc per ad |
| campaign_conversions | 2-3 | ~2,500 | Per conversion action |

---

## Integration Points

### Data Sources

#### Google Ads API (Primary - Active)

| API Resource | Data Retrieved | Update Frequency |
|--------------|----------------|------------------|
| `campaign` | Campaign metrics, budget, status | Every 6 hours |
| `ad_group` | Ad group metrics, themes | Every 6 hours |
| `ad_group_ad` | Ad metrics, RSA content | Daily |
| `ad_group_ad_asset_view` | Asset performance labels & metrics | Daily |
| `keyword_view` | Keyword metrics, quality scores | Daily |
| `ad_group_criterion` | Quality score components | Daily |
| `search_term_view` | Search terms and metrics | Daily |
| `conversion_action` | Conversion definitions | On change |
| Campaign metrics segmented by `conversion_action` | Conversion breakdowns | Daily |

**Key GAQL Queries:**
```sql
-- Campaign metrics with competitive data
SELECT
  campaign.id, campaign.name,
  metrics.impressions, metrics.clicks, metrics.cost_micros,
  metrics.conversions, metrics.conversions_value,
  metrics.all_conversions, metrics.view_through_conversions,
  metrics.search_impression_share, metrics.search_top_impression_share,
  metrics.search_budget_lost_impression_share
FROM campaign
WHERE segments.date DURING LAST_7_DAYS

-- Keyword quality score components
SELECT
  ad_group_criterion.keyword.text,
  ad_group_criterion.quality_info.quality_score,
  ad_group_criterion.quality_info.creative_quality_score,
  ad_group_criterion.quality_info.post_click_quality_score,
  ad_group_criterion.quality_info.search_predicted_ctr
FROM keyword_view

-- Asset performance (full metrics as of June 2025)
SELECT
  ad_group_ad_asset_view.asset,
  ad_group_ad_asset_view.field_type,
  ad_group_ad_asset_view.performance_label,
  metrics.impressions, metrics.clicks, metrics.conversions
FROM ad_group_ad_asset_view

-- Search terms for learning
SELECT
  search_term_view.search_term,
  metrics.impressions, metrics.clicks, metrics.conversions
FROM search_term_view
WHERE metrics.impressions > 10
```

#### LinkedIn Marketing API (Future)
- Campaign performance metrics
- Audience insights
- InMail performance

#### Indeed API (Future)
- Sponsored job metrics
- Apply rate data

### Data Consumers
- **Strategy Agent**: Queries all layers for new campaign planning
- **Writer Agent**: Receives copy recommendations from Strategy
- **Optimizer Agent**: Writes to Layer 1, triggers aggregation jobs
- **Reporting Dashboard**: Reads aggregates for business reporting
- **Negative Keyword Service**: Analyzes search_terms for irrelevant queries
- **Keyword Discovery**: Mines search_terms for high-performing additions

---

## Related Documents

- [Optimizer Data Flow](optimizer-data-flow.md) - How data enters the database
- [Insight Automation](insight-automation.md) - Auto-promotion rules
- [Platform Evaluator](platform-evaluator.md) - How Strategy Agent uses learnings
