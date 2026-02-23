# Optimizer Agent Data Flow

This document specifies how the Optimizer Agent collects performance data from advertising platforms and feeds it into the Learnings Database.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      OPTIMIZER AGENT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │   Collect    │ →  │   Process    │ →  │    Store     │     │
│   │    Metrics   │    │   & Enrich   │    │   to DB      │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│          ↑                                       │              │
│          │                                       ↓              │
│   ┌──────────────┐                      ┌──────────────┐       │
│   │   Platform   │                      │   Learnings  │       │
│   │     APIs     │                      │   Database   │       │
│   └──────────────┘                      └──────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Collection Schedule

| Data Type | Frequency | Source | Database Table |
|-----------|-----------|--------|----------------|
| Campaign metrics (core) | Every 6 hours | `campaign` resource | campaigns |
| Campaign metrics (competitive) | Daily | `campaign` resource | campaigns |
| Conversion breakdown | Daily | `campaign` + `segments.conversion_action` | campaign_conversions |
| Ad group metrics | Every 6 hours | `ad_group` resource | ad_groups |
| Ad metrics | Daily | `ad_group_ad` resource | ads |
| Asset performance | Daily | `ad_group_ad_asset_view` | asset_performance |
| Keyword metrics | Daily | `keyword_view` resource | keywords |
| Quality score components | Daily | `ad_group_criterion.quality_info` | keywords |
| Search terms | Daily | `search_term_view` resource | search_terms |
| Conversion actions | On change | `conversion_action` resource | conversion_actions |

---

## Collection Process

### Step 1: Identify Active Campaigns

```python
def get_campaigns_to_update():
    """Get all campaigns needing metric updates."""

    # Active campaigns: update every 6 hours
    active = db.query("""
        SELECT id, platform, platform_campaign_id
        FROM campaigns
        WHERE status = 'active'
    """)

    # Recently completed: update daily for 7 days
    recent = db.query("""
        SELECT id, platform, platform_campaign_id
        FROM campaigns
        WHERE status = 'completed'
          AND updated_at > NOW() - INTERVAL '7 days'
    """)

    return active + recent
```

### Step 2: Fetch Metrics from Platform APIs

#### Google Ads Metrics Collection

```python
def collect_google_ads_metrics(campaign):
    """Fetch metrics from Google Ads API."""

    # Campaign-level metrics (core + competitive)
    campaign_query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.conversions,
            metrics.conversions_value,
            metrics.all_conversions,
            metrics.all_conversions_value,
            metrics.view_through_conversions,
            metrics.cost_micros,
            metrics.average_cpc,
            metrics.cost_per_conversion,
            metrics.interactions,
            metrics.engagements,
            metrics.engagement_rate,
            metrics.search_impression_share,
            metrics.search_top_impression_share,
            metrics.search_absolute_top_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_rank_lost_impression_share
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING LAST_7_DAYS
    """

    # Campaign conversions by action
    conversion_query = """
        SELECT
            campaign.id,
            segments.conversion_action,
            segments.conversion_action_name,
            metrics.conversions,
            metrics.conversions_value,
            metrics.all_conversions,
            metrics.all_conversions_value
        FROM campaign
        WHERE campaign.id = {campaign_id}
          AND segments.date DURING LAST_7_DAYS
    """

    # Ad group metrics
    ad_group_query = """
        SELECT
            ad_group.id,
            ad_group.name,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions,
            metrics.cost_micros
        FROM ad_group
        WHERE campaign.id = {campaign_id}
    """

    # Ad asset performance (RSA headlines/descriptions)
    # Note: Full metrics available as of June 2025 (replaces performance_label)
    asset_query = """
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad_asset_view.asset,
            ad_group_ad_asset_view.field_type,
            ad_group_ad_asset_view.performance_label,
            asset.text_asset.text,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions,
            metrics.cost_micros
        FROM ad_group_ad_asset_view
        WHERE campaign.id = {campaign_id}
          AND ad_group_ad_asset_view.field_type IN ('HEADLINE', 'DESCRIPTION')
    """

    # Keyword performance with quality score components
    keyword_query = """
        SELECT
            ad_group_criterion.criterion_id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            ad_group_criterion.approval_status,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            metrics.historical_quality_score,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions,
            metrics.conversions_value,
            metrics.cost_micros,
            metrics.average_cpc
        FROM keyword_view
        WHERE campaign.id = {campaign_id}
    """

    # Search terms (critical for learning)
    search_terms_query = """
        SELECT
            search_term_view.search_term,
            search_term_view.ad_group,
            segments.keyword.info.text,
            segments.keyword.info.match_type,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions,
            metrics.conversions_value,
            metrics.cost_micros
        FROM search_term_view
        WHERE campaign.id = {campaign_id}
          AND metrics.impressions > 0
          AND segments.date DURING LAST_7_DAYS
        ORDER BY metrics.impressions DESC
        LIMIT 1000
    """

    return {
        "campaign": execute_query(campaign_query),
        "conversions": execute_query(conversion_query),
        "ad_groups": execute_query(ad_group_query),
        "assets": execute_query(asset_query),
        "keywords": execute_query(keyword_query),
        "search_terms": execute_query(search_terms_query)
    }
```

### Step 3: Process and Enrich Data

```python
def process_metrics(raw_data, campaign):
    """Process raw platform data into standardized format."""

    c = raw_data["campaign"]
    impressions = c["impressions"] or 0
    clicks = c["clicks"] or 0

    processed = {
        "campaign": {
            # Core metrics
            "impressions": impressions,
            "clicks": clicks,
            "ctr": clicks / impressions if impressions > 0 else 0,
            "conversions": c["conversions"],
            "conversion_rate": c["conversions"] / clicks if clicks > 0 else 0,
            "cost": c["cost_micros"] / 1_000_000,
            "cpc": c["average_cpc"] / 1_000_000 if c["average_cpc"] else None,
            "cpa": c["cost_per_conversion"] / 1_000_000 if c["cost_per_conversion"] else None,

            # Extended conversion metrics
            "all_conversions": c.get("all_conversions"),
            "conversions_value": c.get("conversions_value"),
            "all_conversions_value": c.get("all_conversions_value"),
            "view_through_conversions": c.get("view_through_conversions"),

            # Competitive metrics
            "search_impression_share": c.get("search_impression_share"),
            "search_top_impression_share": c.get("search_top_impression_share"),
            "search_absolute_top_is": c.get("search_absolute_top_impression_share"),
            "search_budget_lost_is": c.get("search_budget_lost_impression_share"),
            "search_rank_lost_is": c.get("search_rank_lost_impression_share"),

            # Interaction metrics
            "interactions": c.get("interactions"),
            "engagements": c.get("engagements"),
            "engagement_rate": c.get("engagement_rate"),
        }
    }

    # Enrich with derived metrics
    processed["campaign"]["quality_score"] = calculate_weighted_quality_score(
        raw_data["keywords"]
    )

    # Classify ad strength
    processed["campaign"]["ad_strength"] = determine_ad_strength(
        raw_data["assets"]
    )

    # Process conversion breakdowns
    processed["conversions"] = process_conversion_actions(raw_data["conversions"])

    # Process search terms
    processed["search_terms"] = process_search_terms(raw_data["search_terms"], campaign)

    # Process asset performance
    processed["assets"] = process_asset_performance(raw_data["assets"], campaign)

    # Process keywords with quality components
    processed["keywords"] = process_keywords(raw_data["keywords"])

    return processed


def process_search_terms(search_terms_data, campaign):
    """Process search terms for storage and classification."""
    processed = []
    for st in search_terms_data:
        processed.append({
            "search_term": st["search_term"],
            "match_type_triggered": st.get("match_type"),
            "impressions": st["impressions"],
            "clicks": st["clicks"],
            "conversions": st.get("conversions", 0),
            "conversions_value": st.get("conversions_value"),
            "cost": st["cost_micros"] / 1_000_000,
            "ctr": st["clicks"] / st["impressions"] if st["impressions"] > 0 else 0,
            # Classification will be done by separate analysis job
            "classification": classify_search_term(st, campaign),
            # Denormalize campaign context
            "campaign_seniority": campaign.seniority,
            "campaign_role_type": campaign.role_type,
            "campaign_location": campaign.location_state,
        })
    return processed


def process_keywords(keywords_data):
    """Process keywords with quality score components."""
    processed = []
    for kw in keywords_data:
        processed.append({
            "text": kw["keyword_text"],
            "match_type": kw["match_type"],
            "status": kw.get("status"),
            "quality_score": kw.get("quality_score"),
            "expected_ctr": map_quality_label(kw.get("search_predicted_ctr")),
            "ad_relevance": map_quality_label(kw.get("creative_quality_score")),
            "landing_page_experience": map_quality_label(kw.get("post_click_quality_score")),
            "historical_quality_score": kw.get("historical_quality_score"),
            "impressions": kw["impressions"],
            "clicks": kw["clicks"],
            "conversions": kw.get("conversions", 0),
            "conversions_value": kw.get("conversions_value"),
            "cost": kw["cost_micros"] / 1_000_000,
            "cpc": kw.get("average_cpc", 0) / 1_000_000,
        })
    return processed


def map_quality_label(api_value):
    """Map Google Ads quality component values to readable labels."""
    mapping = {
        "ABOVE_AVERAGE": "ABOVE_AVERAGE",
        "AVERAGE": "AVERAGE",
        "BELOW_AVERAGE": "BELOW_AVERAGE",
        None: None
    }
    return mapping.get(api_value)
```

### Step 4: Store to Learnings Database

```python
def store_metrics(campaign_id, processed_data):
    """Store processed metrics to Layer 1."""

    campaign = processed_data["campaign"]

    # Update campaign record with all metrics
    db.execute("""
        UPDATE campaigns SET
            -- Core metrics
            impressions = %(impressions)s,
            clicks = %(clicks)s,
            ctr = %(ctr)s,
            conversions = %(conversions)s,
            conversion_rate = %(conversion_rate)s,
            cost = %(cost)s,
            cpc = %(cpc)s,
            cpa = %(cpa)s,

            -- Extended conversion metrics
            all_conversions = %(all_conversions)s,
            conversions_value = %(conversions_value)s,
            all_conversions_value = %(all_conversions_value)s,
            view_through_conversions = %(view_through_conversions)s,

            -- Competitive metrics
            search_impression_share = %(search_impression_share)s,
            search_top_impression_share = %(search_top_impression_share)s,
            search_absolute_top_is = %(search_absolute_top_is)s,
            search_budget_lost_is = %(search_budget_lost_is)s,
            search_rank_lost_is = %(search_rank_lost_is)s,

            -- Interaction metrics
            interactions = %(interactions)s,
            engagements = %(engagements)s,
            engagement_rate = %(engagement_rate)s,

            -- Quality indicators
            quality_score = %(quality_score)s,
            ad_strength = %(ad_strength)s,

            updated_at = NOW()
        WHERE id = %(campaign_id)s
    """, {
        "campaign_id": campaign_id,
        **campaign
    })

    # Store conversion breakdowns
    for conv in processed_data.get("conversions", []):
        store_campaign_conversion(campaign_id, conv)

    # Store asset performance (detailed table)
    for asset in processed_data.get("assets", []):
        store_asset_performance(campaign_id, asset)

    # Update keyword performance with quality components
    for keyword in processed_data.get("keywords", []):
        store_keyword_performance(campaign_id, keyword)

    # Store search terms
    for search_term in processed_data.get("search_terms", []):
        store_search_term(campaign_id, search_term)


def store_campaign_conversion(campaign_id, conversion_data):
    """Store conversion breakdown by action."""
    db.execute("""
        INSERT INTO campaign_conversions (
            campaign_id, conversion_action_id,
            conversions, conversions_value,
            all_conversions, all_conversions_value,
            last_updated
        ) VALUES (
            %(campaign_id)s, %(conversion_action_id)s,
            %(conversions)s, %(conversions_value)s,
            %(all_conversions)s, %(all_conversions_value)s,
            NOW()
        )
        ON CONFLICT (campaign_id, conversion_action_id)
        DO UPDATE SET
            conversions = EXCLUDED.conversions,
            conversions_value = EXCLUDED.conversions_value,
            all_conversions = EXCLUDED.all_conversions,
            all_conversions_value = EXCLUDED.all_conversions_value,
            last_updated = NOW()
    """, {
        "campaign_id": campaign_id,
        **conversion_data
    })
```

---

## Asset Performance Tracking

### Detailed Asset Storage

```python
def store_asset_performance(campaign_id, asset_data):
    """
    Store individual headline/description performance to asset_performance table.

    Note: Full metrics (impressions, clicks, conversions) available as of June 2025.
    """

    # Extract features from asset text for Layer 3 analysis
    features = extract_features_from_text(asset_data["text"])

    db.execute("""
        INSERT INTO asset_performance (
            ad_id, campaign_id,
            asset_type, asset_text, position,
            performance_label,
            impressions, clicks, conversions, cost,
            ctr, conversion_rate,
            campaign_seniority, campaign_role_type,
            campaign_location, campaign_industry,
            features_extracted,
            last_updated
        ) VALUES (
            %(ad_id)s, %(campaign_id)s,
            %(asset_type)s, %(asset_text)s, %(position)s,
            %(performance_label)s,
            %(impressions)s, %(clicks)s, %(conversions)s, %(cost)s,
            %(ctr)s, %(conversion_rate)s,
            %(campaign_seniority)s, %(campaign_role_type)s,
            %(campaign_location)s, %(campaign_industry)s,
            %(features)s,
            NOW()
        )
        ON CONFLICT (ad_id, asset_type, asset_text)
        DO UPDATE SET
            performance_label = EXCLUDED.performance_label,
            impressions = EXCLUDED.impressions,
            clicks = EXCLUDED.clicks,
            conversions = EXCLUDED.conversions,
            cost = EXCLUDED.cost,
            ctr = EXCLUDED.ctr,
            conversion_rate = EXCLUDED.conversion_rate,
            last_updated = NOW()
    """, {
        "campaign_id": campaign_id,
        "features": json.dumps(features),
        **asset_data
    })
```

### Search Term Storage

```python
def store_search_term(campaign_id, search_term_data):
    """
    Store search term data for keyword discovery and negative keyword analysis.
    """

    db.execute("""
        INSERT INTO search_terms (
            campaign_id, ad_group_id, keyword_id,
            search_term, match_type_triggered,
            impressions, clicks, cost, conversions, conversions_value,
            ctr, cpc,
            classification, job_relevance_score,
            first_seen, last_seen,
            campaign_seniority, campaign_role_type, campaign_location
        ) VALUES (
            %(campaign_id)s, %(ad_group_id)s, %(keyword_id)s,
            %(search_term)s, %(match_type_triggered)s,
            %(impressions)s, %(clicks)s, %(cost)s, %(conversions)s, %(conversions_value)s,
            %(ctr)s, %(cpc)s,
            %(classification)s, %(job_relevance_score)s,
            CURRENT_DATE, CURRENT_DATE,
            %(campaign_seniority)s, %(campaign_role_type)s, %(campaign_location)s
        )
        ON CONFLICT (campaign_id, search_term)
        DO UPDATE SET
            impressions = search_terms.impressions + EXCLUDED.impressions,
            clicks = search_terms.clicks + EXCLUDED.clicks,
            cost = search_terms.cost + EXCLUDED.cost,
            conversions = search_terms.conversions + EXCLUDED.conversions,
            last_seen = CURRENT_DATE
    """, {
        "campaign_id": campaign_id,
        **search_term_data
    })


def classify_search_term(search_term_data, campaign):
    """
    Classify search term relevance for action recommendations.

    Returns: 'high_value', 'irrelevant', 'uncertain'
    """
    st = search_term_data

    # High value: has conversions
    if st.get("conversions", 0) > 0:
        return "high_value"

    # High value: good CTR and cost efficiency
    ctr = st["clicks"] / st["impressions"] if st["impressions"] > 0 else 0
    if ctr > 0.05 and st["clicks"] >= 5:
        return "high_value"

    # Irrelevant: high impressions, no clicks
    if st["impressions"] > 100 and st["clicks"] == 0:
        return "irrelevant"

    # Irrelevant: contains obvious non-job terms
    irrelevant_patterns = ['salary', 'interview questions', 'resume template', 'free course']
    if any(pattern in st["search_term"].lower() for pattern in irrelevant_patterns):
        return "irrelevant"

    return "uncertain"
```

### Keyword Storage with Quality Components

```python
def store_keyword_performance(campaign_id, keyword_data):
    """Store keyword metrics including quality score components."""

    db.execute("""
        UPDATE keywords SET
            status = %(status)s,
            quality_score = %(quality_score)s,
            expected_ctr = %(expected_ctr)s,
            ad_relevance = %(ad_relevance)s,
            landing_page_experience = %(landing_page_experience)s,
            historical_quality_score = %(historical_quality_score)s,
            impressions = %(impressions)s,
            clicks = %(clicks)s,
            conversions = %(conversions)s,
            conversions_value = %(conversions_value)s,
            cost = %(cost)s,
            cpc = %(cpc)s,
            cpa = CASE WHEN %(conversions)s > 0
                       THEN %(cost)s / %(conversions)s
                       ELSE NULL END,
            updated_at = NOW()
        WHERE text = %(text)s
          AND ad_group_id IN (
              SELECT id FROM ad_groups WHERE campaign_id = %(campaign_id)s
          )
    """, {
        "campaign_id": campaign_id,
        **keyword_data
    })
```

### Performance Labels Mapping

| Platform Label | Internal Label | Meaning |
|---------------|----------------|---------|
| BEST | best | Top performing, keep and expand |
| GOOD | good | Performing well, maintain |
| LOW | low | Underperforming, consider replacing |
| PENDING | pending | Not enough data yet |
| UNSPECIFIED | unknown | No data available |

---

## Feature Extraction

After metrics are stored, extract features for Layer 3 analysis.

### Extract Features from Ad Copy

```python
def extract_features(ad):
    """Extract features from ad headlines and descriptions."""

    features = []

    for headline in ad.headlines:
        # Check for benefit mentions
        if contains_salary(headline):
            features.append(("benefit_mention", "salary_shown"))
        if contains_remote(headline):
            features.append(("benefit_mention", "remote"))
        if contains_benefits(headline):
            features.append(("benefit_mention", "benefits"))

        # Check for patterns
        if is_question(headline):
            features.append(("headline_pattern", "question"))
        if has_urgency(headline):
            features.append(("urgency_signal", "urgent"))
        if has_number(headline):
            features.append(("headline_pattern", "includes_number"))

        # Check for CTAs
        cta = extract_cta(headline)
        if cta:
            features.append(("cta_type", cta))

        # Length category
        length_cat = categorize_length(headline)
        features.append(("length_category", length_cat))

    return features

def contains_salary(text):
    patterns = [r'\$\d+', r'\d+k', r'salary', r'compensation']
    return any(re.search(p, text.lower()) for p in patterns)

def contains_remote(text):
    patterns = ['remote', 'work from home', 'wfh', 'virtual']
    return any(p in text.lower() for p in patterns)

def has_urgency(text):
    patterns = ['urgent', 'immediate', 'asap', 'now hiring', 'hiring now']
    return any(p in text.lower() for p in patterns)
```

### Link Features to Performance

```python
def link_features_to_performance(campaign_id, ad_id, features):
    """
    Associate extracted features with ad performance.

    This creates the data needed for Layer 3 analysis.
    """

    ad = db.get_ad(ad_id)
    campaign = db.get_campaign(campaign_id)

    for feature_type, feature_value in features:
        db.execute("""
            INSERT INTO ad_features (
                ad_id, campaign_id,
                feature_type, feature_value,
                ad_performance,
                campaign_seniority, campaign_role_type,
                campaign_location, campaign_industry
            ) VALUES (
                %(ad_id)s, %(campaign_id)s,
                %(feature_type)s, %(feature_value)s,
                %(ad_performance)s,
                %(seniority)s, %(role_type)s,
                %(location)s, %(industry)s
            )
        """, {
            "ad_id": ad_id,
            "campaign_id": campaign_id,
            "feature_type": feature_type,
            "feature_value": feature_value,
            "ad_performance": get_ad_performance_label(ad),
            "seniority": campaign.seniority,
            "role_type": campaign.role_type,
            "location": campaign.location_state,
            "industry": campaign.industry
        })
```

---

## Aggregation Triggers

The Optimizer triggers aggregation jobs after significant data collection.

### Trigger Conditions

```yaml
aggregation_triggers:
  layer_2_dimensional:
    trigger: "nightly at 2 AM"
    condition: "always"

  layer_3_feature_performance:
    trigger: "weekly on Sunday"
    condition: "at least 10 new campaigns completed"

  layer_4_insight_extraction:
    trigger: "continuous"
    condition: "feature confidence crosses threshold"
```

### Nightly Dimensional Aggregation

```python
def trigger_dimensional_aggregation():
    """Trigger Layer 2 aggregation job."""

    # Run aggregation for each dimension combination
    dimension_pairs = [
        ("seniority", "location"),
        ("seniority", "platform"),
        ("role_type", "location"),
        ("role_type", "platform"),
        ("work_arrangement", "role_type"),
        ("industry", "seniority"),
        # ... etc
    ]

    for dim1, dim2 in dimension_pairs:
        run_aggregation_job(dim1, dim2)

    # Also run single-dimension aggregates
    for dim in ["seniority", "role_type", "location", "industry", "platform"]:
        run_single_dimension_aggregation(dim)
```

### Weekly Feature Analysis

```python
def trigger_feature_analysis():
    """Trigger Layer 3 feature performance analysis."""

    # For each feature type
    for feature_type in FEATURE_TYPES:
        # For each context dimension
        for context_dim in CONTEXT_DIMENSIONS:
            analyze_feature_performance(feature_type, context_dim)
```

---

## Error Handling

### API Failures

```python
def collect_with_retry(campaign, max_retries=3):
    """Collect metrics with retry logic."""

    for attempt in range(max_retries):
        try:
            return collect_metrics(campaign)
        except RateLimitError:
            wait_time = 2 ** attempt * 60  # Exponential backoff
            time.sleep(wait_time)
        except AuthenticationError:
            refresh_oauth_token(campaign.platform)
            continue
        except PlatformUnavailableError:
            log_error(f"Platform unavailable: {campaign.platform}")
            schedule_retry(campaign, delay_minutes=30)
            return None

    log_error(f"Max retries exceeded for campaign {campaign.id}")
    alert_operations_team(campaign)
    return None
```

### Data Validation

```python
def validate_metrics(raw_data):
    """Validate metrics before storage."""

    errors = []

    # Check for negative values
    if raw_data["impressions"] < 0:
        errors.append("Negative impressions")

    # Check CTR bounds
    if raw_data["ctr"] > 1.0:
        errors.append("CTR > 100%")

    # Check CPA reasonableness
    if raw_data["cpa"] > 1000:
        errors.append(f"Unusually high CPA: ${raw_data['cpa']}")

    # Check for data freshness
    if raw_data["data_date"] < datetime.now() - timedelta(days=2):
        errors.append("Stale data")

    return errors
```

---

## Monitoring

### Collection Metrics

```yaml
monitoring_metrics:
  - name: "campaigns_collected"
    type: counter
    labels: [platform, status]

  - name: "collection_latency_seconds"
    type: histogram
    labels: [platform]

  - name: "collection_errors"
    type: counter
    labels: [platform, error_type]

  - name: "features_extracted"
    type: counter
    labels: [feature_type]
```

### Alerts

```yaml
alerts:
  - name: "CollectionFailureRate"
    condition: "error_rate > 10% over 1 hour"
    severity: "warning"

  - name: "PlatformAPIDown"
    condition: "0 successful collections over 2 hours"
    severity: "critical"

  - name: "DataFreshnessAlert"
    condition: "oldest_campaign_update > 24 hours"
    severity: "warning"
```

---

## Related Documents

- [Learnings Database](learnings-database.md) - Full database schema
- [Insight Automation](insight-automation.md) - How insights are extracted
- [Google Ads Adapter](adapters/google-ads-adapter.md) - Platform-specific API details
