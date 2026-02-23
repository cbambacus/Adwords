# Insight Automation

This document specifies the automated system for extracting, promoting, and retiring insights in the Learnings Database.

---

## Overview

Insights progress through a lifecycle based on statistical confidence:

```
┌─────────────────────────────────────────────────────────────────┐
│                    INSIGHT LIFECYCLE                            │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │ DETECTED │ →  │ TESTING  │ →  │  ACTIVE  │ →  │ RETIRED  │ │
│   │          │    │          │    │          │    │          │ │
│   │ conf<70  │    │ 70≤conf  │    │ conf≥85  │    │ conf<60  │ │
│   │          │    │   <85    │    │          │    │ or stale │ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Promotion Thresholds

### From Detected to Testing

A feature pattern moves to "testing" status when:

```yaml
testing_promotion:
  confidence_threshold: 70
  minimum_sample_size: 10
  minimum_lift: 5%  # Either positive or negative
```

### From Testing to Active

A pattern becomes an "active" insight when:

```yaml
active_promotion:
  confidence_threshold: 85
  minimum_sample_size: 30
  minimum_lift: 10%
  consistency_check: true  # Must hold across 3+ time periods
```

### Retirement Triggers

An active insight is retired when:

```yaml
retirement_triggers:
  confidence_decay: "confidence drops below 60%"
  contradiction: "new data shows opposite effect"
  staleness: "no supporting data in 90 days"
  superseded: "more specific insight created"
```

---

## Statistical Methods

### Confidence Calculation

```python
def calculate_confidence(
    metric_with_feature: float,
    metric_without_feature: float,
    n_with: int,
    n_without: int
) -> tuple[float, float]:
    """
    Calculate confidence level using two-sample t-test.

    Returns:
        (confidence_level, p_value)
    """
    from scipy import stats

    # Calculate standard errors
    # Assuming we have variance data
    se_with = std_with / math.sqrt(n_with)
    se_without = std_without / math.sqrt(n_without)

    # Two-sample t-test
    t_stat, p_value = stats.ttest_ind_from_stats(
        mean1=metric_with_feature,
        std1=std_with,
        nobs1=n_with,
        mean2=metric_without_feature,
        std2=std_without,
        nobs2=n_without
    )

    # Convert p-value to confidence level
    confidence = (1 - p_value) * 100

    return confidence, p_value
```

### Lift Calculation

```python
def calculate_lift(metric_with: float, metric_without: float) -> float:
    """
    Calculate percentage lift.

    Returns:
        Percentage change (positive = improvement)
    """
    if metric_without == 0:
        return 0

    lift = ((metric_with - metric_without) / metric_without) * 100
    return round(lift, 2)
```

### Sample Size Validation

```python
def validate_sample_size(n_with: int, n_without: int) -> bool:
    """
    Ensure minimum sample size for statistical validity.

    Using rule of thumb: at least 30 samples per group
    """
    MIN_SAMPLES = 10  # Lower for testing, 30 for production

    return n_with >= MIN_SAMPLES and n_without >= MIN_SAMPLES
```

---

## Feature Analysis Jobs

### Weekly Feature Performance Analysis

```python
def analyze_feature_performance():
    """
    Weekly job to calculate feature performance across all dimensions.
    """

    for feature_type in FEATURE_TYPES:
        for context_dimension in CONTEXT_DIMENSIONS:
            analyze_feature_in_context(feature_type, context_dimension)


def analyze_feature_in_context(feature_type: str, context_dimension: str):
    """
    Analyze a feature type within a specific context dimension.

    Example: "benefit_mention" in context of "seniority"
    """

    # Get all unique values for this feature type
    features = db.query("""
        SELECT DISTINCT feature_value
        FROM ad_features
        WHERE feature_type = %(feature_type)s
    """, {"feature_type": feature_type})

    # Get all unique values for context dimension
    contexts = db.query(f"""
        SELECT DISTINCT campaign_{context_dimension}
        FROM ad_features
        WHERE feature_type = %(feature_type)s
    """, {"feature_type": feature_type})

    for feature_value in features:
        for context_value in contexts:
            calculate_feature_performance(
                feature_type,
                feature_value,
                context_dimension,
                context_value
            )


def calculate_feature_performance(
    feature_type: str,
    feature_value: str,
    context_dimension: str,
    context_value: str
):
    """
    Calculate performance metrics for a feature in a specific context.
    """

    # Get campaigns WITH feature in this context
    with_feature = db.query("""
        SELECT
            c.ctr, c.conversion_rate, c.cpa
        FROM campaigns c
        JOIN ad_features af ON c.id = af.campaign_id
        WHERE af.feature_type = %(feature_type)s
          AND af.feature_value = %(feature_value)s
          AND c.{context_dimension} = %(context_value)s
          AND c.status = 'completed'
          AND c.conversions > 0
    """, {
        "feature_type": feature_type,
        "feature_value": feature_value,
        "context_value": context_value
    })

    # Get campaigns WITHOUT feature in this context
    without_feature = db.query("""
        SELECT
            c.ctr, c.conversion_rate, c.cpa
        FROM campaigns c
        WHERE c.{context_dimension} = %(context_value)s
          AND c.status = 'completed'
          AND c.conversions > 0
          AND c.id NOT IN (
              SELECT campaign_id FROM ad_features
              WHERE feature_type = %(feature_type)s
                AND feature_value = %(feature_value)s
          )
    """, {
        "feature_type": feature_type,
        "feature_value": feature_value,
        "context_value": context_value
    })

    # Calculate metrics
    ctr_with = mean([r.ctr for r in with_feature])
    ctr_without = mean([r.ctr for r in without_feature])
    ctr_lift = calculate_lift(ctr_with, ctr_without)

    conv_with = mean([r.conversion_rate for r in with_feature])
    conv_without = mean([r.conversion_rate for r in without_feature])
    conv_lift = calculate_lift(conv_with, conv_without)

    # Calculate confidence
    confidence, p_value = calculate_confidence(
        ctr_with, ctr_without,
        len(with_feature), len(without_feature)
    )

    # Store or update feature performance
    upsert_feature_performance(
        feature_type=feature_type,
        feature_value=feature_value,
        context_dimension=context_dimension,
        context_value=context_value,
        campaigns_with=len(with_feature),
        campaigns_without=len(without_feature),
        ctr_with=ctr_with,
        ctr_without=ctr_without,
        ctr_lift=ctr_lift,
        conversion_lift=conv_lift,
        confidence_level=confidence,
        p_value=p_value
    )

    # Check for promotion
    check_insight_promotion(feature_type, feature_value, context_dimension, context_value)
```

---

## Insight Promotion Logic

### Automatic Promotion

```python
def check_insight_promotion(
    feature_type: str,
    feature_value: str,
    context_dimension: str,
    context_value: str
):
    """
    Check if a feature should be promoted to an insight.
    """

    fp = db.get_feature_performance(
        feature_type, feature_value,
        context_dimension, context_value
    )

    # Check if already has an insight
    existing = db.get_insight_for_feature(
        feature_type, feature_value,
        context_dimension, context_value
    )

    if existing:
        # Update existing insight confidence
        update_insight_confidence(existing.id, fp.confidence_level)
        return

    # Check promotion thresholds
    total_samples = fp.campaigns_with_feature + fp.campaigns_without_feature

    if fp.confidence_level >= 85 and total_samples >= 30 and abs(fp.ctr_lift) >= 10:
        # Promote to active insight
        create_insight(fp, status="active")

    elif fp.confidence_level >= 70 and total_samples >= 10 and abs(fp.ctr_lift) >= 5:
        # Create testing insight
        create_insight(fp, status="testing")


def create_insight(fp: FeaturePerformance, status: str):
    """
    Create a new insight from feature performance data.
    """

    # Generate human-readable statement
    statement = generate_insight_statement(fp)

    # Generate guidance
    strategy_guidance = generate_strategy_guidance(fp)
    writer_guidance = generate_writer_guidance(fp)

    db.execute("""
        INSERT INTO insights (
            id, type, status, statement,
            applies_to, strategy_guidance, writer_guidance,
            confidence, created_at, created_by
        ) VALUES (
            %(id)s, 'data_derived', %(status)s, %(statement)s,
            %(applies_to)s, %(strategy_guidance)s, %(writer_guidance)s,
            %(confidence)s, NOW(), 'system:auto'
        )
    """, {
        "id": generate_insight_id(),
        "status": status,
        "statement": statement,
        "applies_to": json.dumps({
            fp.context_dimension: [fp.context_value]
        }),
        "strategy_guidance": strategy_guidance,
        "writer_guidance": writer_guidance,
        "confidence": fp.confidence_level
    })
```

### Statement Generation

```python
def generate_insight_statement(fp: FeaturePerformance) -> str:
    """
    Generate human-readable insight statement.
    """

    direction = "increases" if fp.ctr_lift > 0 else "decreases"
    metric = "CTR" if abs(fp.ctr_lift) > abs(fp.conversion_lift) else "conversion rate"
    lift = abs(fp.ctr_lift) if metric == "CTR" else abs(fp.conversion_lift)

    # Map feature types to readable descriptions
    feature_descriptions = {
        "benefit_mention": {
            "remote": "mentioning remote work",
            "salary_shown": "showing salary in ad copy",
            "benefits": "highlighting benefits",
        },
        "urgency_signal": {
            "urgent": "using urgency language",
        },
        "headline_pattern": {
            "question": "using questions in headlines",
            "includes_number": "including numbers",
        }
    }

    feature_desc = feature_descriptions.get(
        fp.feature_type, {}
    ).get(fp.feature_value, f"using '{fp.feature_value}'")

    context_desc = f"for {fp.context_value} {fp.context_dimension}"

    return f"{feature_desc.capitalize()} {direction} {metric} by {lift:.0f}% {context_desc}"


def generate_strategy_guidance(fp: FeaturePerformance) -> str:
    """Generate guidance for Strategy Agent."""

    if fp.ctr_lift > 0:
        return f"Include {fp.feature_value} in ad copy for {fp.context_value} {fp.context_dimension} campaigns"
    else:
        return f"Avoid {fp.feature_value} in ad copy for {fp.context_value} {fp.context_dimension} campaigns"


def generate_writer_guidance(fp: FeaturePerformance) -> str:
    """Generate guidance for Writer Agent."""

    guidance_templates = {
        ("benefit_mention", "remote"): {
            "positive": "Include 'Remote', 'Work from Home', or 'Flexible Location' prominently in headlines",
            "negative": "De-emphasize remote work; focus on other benefits"
        },
        ("benefit_mention", "salary_shown"): {
            "positive": "Lead with salary range in first headline: '$XXX-$XXX Job Title'",
            "negative": "Omit salary from headlines; mention in description if required"
        },
        ("urgency_signal", "urgent"): {
            "positive": "Use urgency language: 'Hiring Now', 'Immediate Opening', 'Start ASAP'",
            "negative": "Avoid urgency language; use professional, measured tone"
        }
    }

    key = (fp.feature_type, fp.feature_value)
    direction = "positive" if fp.ctr_lift > 0 else "negative"

    if key in guidance_templates:
        return guidance_templates[key][direction]

    # Fallback generic guidance
    if fp.ctr_lift > 0:
        return f"Include '{fp.feature_value}' in ad copy"
    else:
        return f"Avoid '{fp.feature_value}' in ad copy"
```

---

## Insight Retirement

### Retirement Checks

```python
def check_insight_retirement():
    """
    Daily job to check for insights that should be retired.
    """

    active_insights = db.query("""
        SELECT * FROM insights WHERE status = 'active'
    """)

    for insight in active_insights:
        should_retire, reason = evaluate_retirement(insight)
        if should_retire:
            retire_insight(insight.id, reason)


def evaluate_retirement(insight) -> tuple[bool, str]:
    """
    Evaluate if an insight should be retired.

    Returns:
        (should_retire, reason)
    """

    # Check confidence decay
    current_confidence = recalculate_confidence(insight)
    if current_confidence < 60:
        return True, f"Confidence decayed to {current_confidence}%"

    # Check staleness
    latest_supporting = db.query("""
        SELECT MAX(c.updated_at)
        FROM campaigns c
        JOIN ad_features af ON c.id = af.campaign_id
        WHERE af.feature_type = %(feature_type)s
          AND af.feature_value = %(feature_value)s
    """, insight.supporting_features)

    if latest_supporting < datetime.now() - timedelta(days=90):
        return True, "No supporting data in 90 days"

    # Check for contradiction
    if check_contradiction(insight):
        return True, "Contradicted by recent data"

    return False, None


def retire_insight(insight_id: str, reason: str):
    """Retire an insight with documented reason."""

    db.execute("""
        UPDATE insights SET
            status = 'retired',
            validation_result = %(reason)s,
            last_validated = NOW()
        WHERE id = %(id)s
    """, {
        "id": insight_id,
        "reason": reason
    })

    # Log for audit
    log_insight_lifecycle(insight_id, "retired", reason)
```

---

## Seed Insights

Initial insights from research, loaded at system initialization.

### Seed Data Structure

```python
SEED_INSIGHTS = [
    {
        "id": "SEED-001",
        "type": "seeded",
        "statement": "Remote work mention increases applications 3x",
        "applies_to": {"work_arrangement": ["remote", "hybrid"]},
        "strategy_guidance": "Prioritize remote/hybrid messaging when job allows",
        "writer_guidance": "Include 'Remote' or 'Work from Home' prominently in headlines",
        "confidence": 80,
        "source": "recruitment-advertising-resources.md"
    },
    {
        "id": "SEED-002",
        "type": "seeded",
        "statement": "Job ads with 201-400 words achieve 8-8.5% apply rate",
        "applies_to": {},  # Universal
        "strategy_guidance": "Target 201-400 words for job descriptions",
        "writer_guidance": "Keep ad copy concise but complete; aim for 200-400 words total",
        "confidence": 75,
        "source": "recruitment-advertising-resources.md"
    },
    {
        "id": "SEED-003",
        "type": "seeded",
        "statement": "Salary transparency increases applications 20-30%",
        "applies_to": {},  # Universal, but especially CA, CO, NY, WA
        "strategy_guidance": "Include salary when available; required in some states",
        "writer_guidance": "Show salary range in headlines when possible: '$130K-$155K'",
        "confidence": 85,
        "source": "recruitment-advertising-resources.md"
    },
    {
        "id": "SEED-004",
        "type": "seeded",
        "statement": "Candidates decide in 14 seconds - lead with strongest hook",
        "applies_to": {},  # Universal
        "strategy_guidance": "Front-load key information in first headline",
        "writer_guidance": "First headline must contain: role + top benefit (salary OR remote OR company)",
        "confidence": 70,
        "source": "recruitment-advertising-resources.md"
    },
    {
        "id": "SEED-005",
        "type": "seeded",
        "statement": "LinkedIn posts under 150 words get 17.8% more frequent applications",
        "applies_to": {"platform": ["linkedin"]},
        "strategy_guidance": "Keep LinkedIn ad copy brief",
        "writer_guidance": "LinkedIn primary text: under 150 words. Focus on key points only.",
        "confidence": 75,
        "source": "recruitment-advertising-resources.md"
    },
    {
        "id": "SEED-006",
        "type": "seeded",
        "statement": "Urgently Hiring badge on Indeed leads to 5 days faster hires",
        "applies_to": {"platform": ["indeed"]},
        "strategy_guidance": "Enable Urgently Hiring badge for time-sensitive roles",
        "writer_guidance": "For Indeed: mention urgency in copy to match badge",
        "confidence": 70,
        "source": "recruitment-advertising-resources.md"
    }
]


def load_seed_insights():
    """Load seed insights into database."""

    for seed in SEED_INSIGHTS:
        db.execute("""
            INSERT INTO insights (
                id, type, status, statement,
                applies_to, strategy_guidance, writer_guidance,
                confidence, created_at, created_by
            ) VALUES (
                %(id)s, %(type)s, 'active', %(statement)s,
                %(applies_to)s, %(strategy_guidance)s, %(writer_guidance)s,
                %(confidence)s, NOW(), %(source)s
            )
            ON CONFLICT (id) DO NOTHING
        """, {
            **seed,
            "applies_to": json.dumps(seed["applies_to"]),
            "source": f"seed:{seed['source']}"
        })
```

---

## Monitoring and Alerts

### Metrics

```yaml
insight_metrics:
  - name: "insights_total"
    type: gauge
    labels: [status, type]

  - name: "insights_promoted"
    type: counter
    labels: [from_status, to_status]

  - name: "insight_confidence_distribution"
    type: histogram
    buckets: [50, 60, 70, 80, 90, 100]

  - name: "feature_analysis_duration"
    type: histogram
```

### Alerts

```yaml
alerts:
  - name: "NoActiveInsights"
    condition: "count(insights where status='active') < 5"
    severity: "warning"
    message: "System has fewer than 5 active insights"

  - name: "HighRetirementRate"
    condition: "retirement_rate > 20% in last week"
    severity: "warning"
    message: "Many insights being retired - check data quality"

  - name: "FeatureAnalysisStale"
    condition: "last_analysis > 10 days ago"
    severity: "warning"
    message: "Feature analysis job hasn't run recently"
```

---

## Related Documents

- [Learnings Database](learnings-database.md) - Full database schema
- [Optimizer Data Flow](optimizer-data-flow.md) - How data enters the system
- [Strategy Agent Rulebook](strategy-agent-rulebook.md) - How insights are used
