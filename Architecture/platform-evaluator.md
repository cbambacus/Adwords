# Platform Evaluator

This document specifies the Strategy Agent's logic for evaluating and selecting advertising platforms for each job order.

---

## Overview

The Platform Evaluator is a module within the Strategy Agent that:
1. Receives a job order from Cloudwall
2. Scores each available platform based on fit
3. Recommends platforms above a threshold
4. Allocates budget across selected platforms
5. Returns a ranked selection with allocations

```
┌─────────────────────────────────────────────────────────────┐
│                    PLATFORM EVALUATOR                       │
│                                                             │
│  Input: Job Order + Budget + Constraints                    │
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │   Analyze   │ → │    Score    │ → │   Allocate  │       │
│  │  Job Order  │   │  Platforms  │   │   Budget    │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│                                                             │
│  Output: Platform Selection with Budget Allocations         │
└─────────────────────────────────────────────────────────────┘
```

---

## Scoring Model

### Factor Weights

| Factor | Weight | Description |
|--------|--------|-------------|
| Role Fit | 30% | How well platform audience matches role type |
| Audience Match | 25% | Active vs passive, seniority alignment |
| Geographic Coverage | 15% | Platform strength in target location |
| Cost Efficiency | 15% | Expected CPA vs budget constraints |
| Urgency Fit | 10% | Platform's speed to results |
| Historical Performance | 5% | Learnings from Optimizer Agent |

**Total:** 100%

### Scoring Formula

```
Platform Score = Σ (Factor Score × Factor Weight)

Where each Factor Score is 0-100
```

---

## Factor Scoring Logic

### 1. Role Fit (30%)

Maps role type to platform strength.

**Role Classification:**
```yaml
role_types:
  creative:
    titles: ["designer", "art director", "creative", "ux", "ui", "graphic"]
    platforms:
      linkedin: 85
      google_ads: 70
      meta: 60
      indeed: 50

  technical:
    titles: ["engineer", "developer", "architect", "devops", "data"]
    platforms:
      linkedin: 90
      google_ads: 75
      indeed: 55
      meta: 40

  marketing:
    titles: ["marketing", "brand", "content", "social media", "seo"]
    platforms:
      linkedin: 85
      google_ads: 70
      meta: 75
      indeed: 55

  corporate:
    titles: ["finance", "accounting", "hr", "legal", "operations"]
    platforms:
      linkedin: 80
      indeed: 75
      google_ads: 60
      meta: 45

  entry_level:
    indicators: ["entry", "junior", "associate", "coordinator", "assistant"]
    platforms:
      indeed: 90
      meta: 75
      google_ads: 65
      linkedin: 55

  executive:
    titles: ["director", "vp", "chief", "head of", "president"]
    platforms:
      linkedin: 95
      google_ads: 60
      indeed: 40
      meta: 30
```

**Scoring Logic:**
```python
def score_role_fit(job_order, platform):
    role_type = classify_role(job_order.job_title)
    base_score = role_type.platforms[platform.id]

    # Adjust for specific skills mentioned
    if has_niche_skills(job_order) and platform.supports_skill_targeting:
        base_score += 10

    return min(base_score, 100)
```

---

### 2. Audience Match (25%)

Evaluates alignment between job requirements and platform audience characteristics.

**Active vs Passive Assessment:**
```yaml
active_indicators:
  - salary included
  - "immediate" or "urgent" in notes
  - contract or temp position
  - entry level
  score_impact:
    indeed: +20
    google_ads: +15
    meta: +10
    linkedin: -5

passive_indicators:
  - senior or executive level
  - no urgency
  - permanent position
  - competitive salary
  score_impact:
    linkedin: +20
    meta: +5
    google_ads: -5
    indeed: -10
```

**Seniority Alignment:**
```yaml
seniority_scores:
  entry:
    indeed: 90
    meta: 75
    google_ads: 70
    linkedin: 50
  mid:
    linkedin: 80
    google_ads: 75
    indeed: 75
    meta: 60
  senior:
    linkedin: 90
    google_ads: 70
    indeed: 55
    meta: 45
  executive:
    linkedin: 95
    google_ads: 55
    indeed: 35
    meta: 25
```

---

### 3. Geographic Coverage (15%)

Scores platform strength in target location.

**Regional Strength Modifiers:**
```yaml
geographic_scores:
  us_major_metros:  # SF, NYC, LA, Chicago, etc.
    linkedin: 95
    google_ads: 90
    indeed: 85
    meta: 80

  us_secondary:     # Denver, Austin, Atlanta, etc.
    linkedin: 85
    google_ads: 85
    indeed: 85
    meta: 75

  us_rural:
    indeed: 80
    google_ads: 75
    meta: 70
    linkedin: 60

  remote_us:
    linkedin: 90
    google_ads: 85
    indeed: 75
    meta: 65

  international:    # Varies by country
    linkedin: varies
    google_ads: varies
    indeed: limited
    meta: varies
```

**Remote Work Modifier:**
```python
def adjust_for_remote(base_score, job_order, platform):
    if job_order.work_arrangement == "remote":
        # Remote roles benefit from broader reach platforms
        if platform.id in ["linkedin", "google_ads"]:
            return base_score + 10
    elif job_order.work_arrangement == "onsite":
        # Onsite benefits from local-strong platforms
        if platform.id == "indeed":
            return base_score + 5
    return base_score
```

---

### 4. Cost Efficiency (15%)

Compares expected cost to budget constraints.

**Cost Efficiency Calculation:**
```python
def score_cost_efficiency(job_order, platform, budget):
    expected_cpa = platform.estimate_cpa(job_order)

    # Get budget allocated to this platform (preliminary)
    platform_budget = budget.daily * 0.3  # Assume 30% for estimation

    # Calculate how many applications budget could yield
    estimated_applications = platform_budget / expected_cpa

    # Score based on efficiency
    if estimated_applications >= 5:
        return 90
    elif estimated_applications >= 3:
        return 75
    elif estimated_applications >= 1:
        return 60
    else:
        return 40

    # Penalize if minimum spend not met
    if platform_budget < platform.minimum_daily_spend:
        return score * 0.5
```

**Platform Cost Benchmarks:**
```yaml
recruitment_benchmarks:
  google_ads:
    cpc_range: [1.50, 4.50]
    cpa_range: [25, 75]
    min_daily: 50

  linkedin:
    cpc_range: [5, 12]
    cpa_range: [50, 150]
    min_daily: 75

  indeed:
    cpc_range: [0.25, 1.50]
    cpa_range: [15, 40]
    min_daily: 25

  meta:
    cpc_range: [0.50, 2.00]
    cpa_range: [20, 60]
    min_daily: 30
```

---

### 5. Urgency Fit (10%)

Scores platform's ability to deliver results quickly.

**Platform Speed Characteristics:**
```yaml
time_to_results:
  google_ads:
    review_time: "hours"
    ramp_up: "1-2 days"
    speed_score: 95

  linkedin:
    review_time: "24-48 hours"
    ramp_up: "2-3 days"
    speed_score: 80

  indeed:
    review_time: "immediate"
    ramp_up: "same day"
    speed_score: 90

  meta:
    review_time: "24 hours"
    ramp_up: "1-2 days"
    speed_score: 85
```

**Urgency Adjustment:**
```python
def score_urgency_fit(job_order, platform):
    urgency = assess_urgency(job_order)
    base_speed_score = platform.speed_score

    if urgency == "critical":  # < 1 week
        # Heavily favor fast platforms
        return base_speed_score
    elif urgency == "high":    # 1-2 weeks
        return base_speed_score * 0.9
    elif urgency == "normal":  # 2-4 weeks
        return base_speed_score * 0.8
    else:  # passive
        # Speed matters less
        return 70  # Normalize all platforms
```

---

### 6. Historical Performance (5%)

Incorporates learnings from Optimizer Agent.

**Learning Integration:**
```python
def score_historical(job_order, platform, learnings_db):
    # Find similar past campaigns
    similar_campaigns = learnings_db.find_similar(
        role_type=job_order.role_type,
        location=job_order.location,
        seniority=job_order.seniority,
        platform=platform.id
    )

    if not similar_campaigns:
        return 50  # Neutral if no data

    # Calculate performance score
    avg_cpa = mean([c.cpa for c in similar_campaigns])
    avg_quality = mean([c.applicant_quality_score for c in similar_campaigns])

    # Normalize to 0-100
    cpa_score = normalize_cpa(avg_cpa, platform.benchmark_cpa)
    quality_score = avg_quality * 10  # Assuming 1-10 scale

    return (cpa_score + quality_score) / 2
```

**Cold Start Handling:**
- New platform: Score = 50 (neutral)
- New role type: Use closest match from learnings
- Weight increases as data accumulates (5% → 15% over time)

---

## Platform Selection

### Selection Threshold

```python
SELECTION_THRESHOLD = 60  # Minimum score to include platform

def select_platforms(job_order, budget):
    scores = []
    for platform in get_active_platforms():
        score = calculate_platform_score(job_order, platform, budget)
        scores.append((platform, score))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    # Select platforms above threshold
    selected = [(p, s) for p, s in scores if s >= SELECTION_THRESHOLD]

    # Ensure at least one platform selected
    if not selected:
        selected = [scores[0]]  # Take highest scoring even if below threshold

    return selected
```

### Maximum Platforms

```yaml
max_platforms_by_budget:
  under_50: 1
  50_to_100: 2
  100_to_250: 3
  over_250: 4
```

---

## Budget Allocation

### Allocation Algorithm

```python
def allocate_budget(selected_platforms, total_budget):
    total_score = sum([score for _, score in selected_platforms])

    allocations = {}
    for platform, score in selected_platforms:
        # Base allocation proportional to score
        base_allocation = (score / total_score) * total_budget

        # Ensure minimum viable spend
        min_spend = platform.minimum_daily_spend
        allocation = max(base_allocation, min_spend)

        allocations[platform.id] = {
            "amount": allocation,
            "percent": allocation / total_budget * 100,
            "rationale": generate_rationale(platform, score)
        }

    # Normalize if over budget
    allocations = normalize_allocations(allocations, total_budget)

    return allocations
```

### Allocation Constraints

```yaml
constraints:
  minimum_per_platform: 25  # USD daily
  maximum_single_platform: 70%  # Of total budget
  reserve_for_optimization: 10%  # Held back for Optimizer adjustments
```

---

## Output Format

### Platform Selection Response

```yaml
PlatformSelection:
  job_order_id: string
  evaluated_at: timestamp
  total_budget:
    daily: number
    currency: string

  selected_platforms:
    - platform_id: string
      platform_name: string
      score: number
      recommendation: "highly_recommended" | "recommended" | "consider"
      allocation:
        daily_budget: number
        percent_of_total: number
      rationale: string
      factor_breakdown:
        role_fit: number
        audience_match: number
        geographic_coverage: number
        cost_efficiency: number
        urgency_fit: number
        historical_performance: number

  rejected_platforms:
    - platform_id: string
      score: number
      rejection_reason: string

  constraints_applied:
    - constraint: string
      impact: string

  writer_guidance:
    # Passed to Writer Agent
    platforms: string[]
    tone: string
    key_selling_points: string[]
    compliance_notes: string[]
```

---

## Example Evaluation

### Input: Senior UX Designer (from job-order-test.md)

```yaml
job_order:
  job_title: "Senior UX Designer"
  location: "San Francisco, CA"
  work_arrangement: "hybrid"
  salary: "$130,000 - $155,000"
  urgency: "high"

budget:
  daily: 150
```

### Scoring

| Platform | Role Fit | Audience | Geo | Cost | Urgency | History | **Total** |
|----------|----------|----------|-----|------|---------|---------|-----------|
| LinkedIn | 85 × 0.30 | 80 × 0.25 | 95 × 0.15 | 70 × 0.15 | 80 × 0.10 | 50 × 0.05 | **81.25** |
| Google Ads | 70 × 0.30 | 70 × 0.25 | 90 × 0.15 | 85 × 0.15 | 95 × 0.10 | 50 × 0.05 | **75.75** |
| Indeed | 50 × 0.30 | 60 × 0.25 | 85 × 0.15 | 90 × 0.15 | 90 × 0.10 | 50 × 0.05 | **66.25** |
| Meta | 60 × 0.30 | 50 × 0.25 | 80 × 0.15 | 80 × 0.15 | 85 × 0.10 | 50 × 0.05 | **63.00** |

### Selection

All platforms score ≥ 60, but budget limits to 3 platforms.

**Selected:**
1. LinkedIn (81.25) - 45% → $67.50/day
2. Google Ads (75.75) - 35% → $52.50/day
3. Indeed (66.25) - 20% → $30.00/day

**Rejected:**
- Meta (63.00) - Budget constraint, lower fit for senior role

---

## Integration Points

### Input Sources
- **Cloudwall**: Job order data
- **Platform Registry**: Available platforms and capabilities
- **Learnings Database**: Historical performance data
- **Budget Service**: Campaign budget constraints

### Output Consumers
- **Writer Agent**: Receives platform list and guidance
- **Campaign Generator**: Receives allocations for each platform
- **Audit Log**: Records selection rationale

---

## Maintenance

### Tuning the Model

The scoring weights and thresholds should be adjusted based on:
1. Aggregate campaign performance analysis (quarterly)
2. Significant platform changes (new features, pricing)
3. Market shifts (new platforms gaining traction)

### A/B Testing

Consider testing alternative scoring models:
- Run parallel evaluations with different weights
- Compare predicted vs actual performance
- Gradually shift weights based on outcomes
