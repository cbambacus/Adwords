# POC Test Plan: AI Recruitment Advertising System

**Version**: 1.0
**Date**: 2026-02-18
**Status**: Draft — Pending Stakeholder Review

---

## Table of Contents

1. [POC Scope](#1-poc-scope)
2. [Test Job Orders](#2-test-job-orders)
3. [Test Cases](#3-test-cases)
   - [A. Input Validation](#a-input-validation)
   - [B. Strategy Agent](#b-strategy-agent)
   - [C. Writer Agent](#c-writer-agent)
   - [D. Campaign Builder](#d-campaign-builder)
   - [E. Human Review Gate](#e-human-review-gate)
   - [F. Google Ads Publisher](#f-google-ads-publisher)
   - [G. End-to-End Integration](#g-end-to-end-integration)
   - [H. Edge Cases](#h-edge-cases)
4. [Acceptance Criteria](#4-acceptance-criteria)
5. [Testing Execution Strategy](#5-testing-execution-strategy)

---

## 1. POC Scope

### Pipeline

```
Job Order (JSON) → Strategy Agent (Claude) → Writer Agent (Claude) → Campaign Builder → Human Review → Google Ads API
```

### Technology

- **Language**: Python
- **AI**: Claude API (Anthropic) for Strategy and Writer agents
- **Platform**: Google Ads only (architected for multi-platform expansion)
- **Approval**: Human review gate before campaign publish
- **API Access**: Google Ads API with developer token (Basic Access)

### What's In Scope

- Job order parsing and validation
- Strategy Agent: classification, keyword generation, compliance flags, budget calculation
- Writer Agent: RSA headline/description generation, keyword organization
- Campaign Builder: Google Ads campaign structure creation
- Human review and approval workflow
- Google Ads API publishing (PAUSED campaigns)

### What's Out of Scope (for POC)

- LinkedIn, Indeed, Meta platform adapters
- Optimizer Agent / performance monitoring
- Learnings Database
- Conversion tracking setup
- Cloudwall integration (manual job order input)
- Landing page creation

---

## 2. Test Job Orders

Five test job orders covering the key variations. Full JSON files in `Tests/test-job-orders/`.

| # | File | Title | Seniority | Role Type | Location | Work | Salary | Client | Key Coverage |
|---|------|-------|-----------|-----------|----------|------|--------|--------|-------------|
| 1 | `test-001-senior-ux-designer.json` | Senior UX Designer | Senior | Creative | SF, CA | Hybrid | $130K-$155K | Named | CA salary transparency, Tier-1 metro, urgent fill, contract-to-hire |
| 2 | `test-002-marketing-coordinator.json` | Marketing Coordinator | Entry | Corporate | Austin, TX | Onsite | $45K-$55K | Named | No salary mandate, no remote option, entry-level messaging |
| 3 | `test-003-python-developer.json` | Python Developer | Mid | Technical | Remote US | Remote | None | Named | No salary data, national targeting, technical keywords, remote prominence |
| 4 | `test-004-junior-graphic-designer.json` | Junior Graphic Designer | Entry | Creative | Denver, CO | Onsite | $40K-$50K | Confidential | CO salary transparency, short description (<100 words), confidential client |
| 5 | `test-005-vp-engineering.json` | VP of Engineering | Executive | Technical | NYC, NY | Hybrid | $280K-$350K | Confidential | NY salary transparency, executive tone, high budget, ASAP urgency |

### Coverage Matrix

| Variation | TEST-001 | TEST-002 | TEST-003 | TEST-004 | TEST-005 |
|-----------|----------|----------|----------|----------|----------|
| Seniority: Entry | | X | | X | |
| Seniority: Mid | | | X | | |
| Seniority: Senior | X | | | | |
| Seniority: Executive | | | | | X |
| Role: Creative | X | | | X | |
| Role: Technical | | | X | | X |
| Role: Corporate | | X | | | |
| Location: CA (salary required) | X | | | | |
| Location: TX (no mandate) | | X | | | |
| Location: Remote US | | | X | | |
| Location: CO (salary required) | | | | X | |
| Location: NY (salary required) | | | | | X |
| Work: Hybrid | X | | | | X |
| Work: Onsite | | X | | X | |
| Work: Remote | | | X | | |
| Salary: Provided | X | X | | X | X |
| Salary: Missing | | | X | | |
| Client: Named | X | X | X | | |
| Client: Confidential | | | | X | X |
| Urgency: High/ASAP | X | | | | X |
| Urgency: Standard | | X | X | X | |
| Short description (<100 words) | | | | X | |
| Contract/temp employment | X | | | | |

---

## 3. Test Cases

### A. Input Validation

Tests the job order parser. No API calls required.

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| A-001 | Valid complete job order | TEST-001 (all fields) | Parser returns structured object | All fields accessible; no errors |
| A-002 | Missing `job_title` | JSON with `job_title` omitted | Validation error | Error names `job_title`; pipeline halts |
| A-003 | Missing `job_description` | JSON with `job_description` omitted | Validation error | Error names `job_description`; pipeline halts |
| A-004 | Missing `location` | JSON with `location` omitted | Validation error | Error names `location`; pipeline halts |
| A-005 | Missing `work_arrangement` | JSON with `work_arrangement` omitted | Validation error | Error names `work_arrangement`; pipeline halts |
| A-006 | Invalid `work_arrangement` enum | `"work_arrangement": "flexible"` | Validation error listing valid values | Error enumerates remote/hybrid/onsite |
| A-007 | Missing optional salary | Valid required fields, `salary` omitted | Parser succeeds; downstream agents suppress salary messaging | No error; pipeline continues |
| A-008 | Negative salary value | `"min": -50000` | Validation error | Error identifies invalid value |
| A-009 | Salary min > max | `"min": 200000, "max": 100000` | Validation error | Error: min must be <= max |
| A-010 | Short description (<100 words) | TEST-004 (31 words) | Validation warning | Warning logged; human review suggested before proceeding |
| A-011 | Malformed JSON | Missing closing brace | JSON parse error | Descriptive error; pipeline halts cleanly |
| A-012 | Unknown extra fields | Valid JSON + `"bonus_structure": "quarterly"` | Extra fields ignored | Pipeline proceeds normally |
| A-013 | Unicode in job title | `"job_title": "Développeur Senior"` | UTF-8 handled correctly | Accented characters preserved |
| A-014 | Very long description (5000+ words) | 5000-word description | Accepted without truncation | Full description passed to Strategy Agent |

### B. Strategy Agent

Tests Claude API call producing the YAML Strategy Brief. Validates against rules in `Architecture/strategy-agent-rulebook.md`.

#### B.1 Output Structure

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| B-001 | Valid YAML output | TEST-001 | Strategy Brief parses as valid YAML | YAML parses without error |
| B-002 | All required sections present | TEST-001 | Brief contains all top-level keys from rulebook 5.1 | Keys present: `audience`, `key_selling_points`, `messaging_direction`, `platforms`, `keywords`, `compliance_checklist`, `budget_allocation` |

#### B.2 Seniority Classification (Rulebook 2.3)

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| B-003 | Classify Senior | TEST-001 ("Senior UX Designer", 5+ years) | `audience.seniority_level: Senior` | Correct classification |
| B-004 | Classify Entry-Level | TEST-002 ("Marketing Coordinator", 0-2 years) | `audience.seniority_level: Entry-Level` | Correct classification |
| B-005 | Classify Mid-Level | TEST-003 ("Python Developer", 3-5 years) | `audience.seniority_level: Mid-Level` | Correct classification |
| B-006 | Classify Entry-Level (Junior title) | TEST-004 ("Junior Graphic Designer") | `audience.seniority_level: Entry-Level` | Correct classification |
| B-007 | Classify Executive | TEST-005 ("VP of Engineering", 15+ years) | `audience.seniority_level: Executive` | Correct classification |

#### B.3 Role Type Classification (Rulebook 2.3)

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| B-008 | Classify Creative | TEST-001 (UX Designer) | Role type: Creative | Correct classification |
| B-009 | Classify Corporate/Marketing | TEST-002 (Marketing Coordinator) | Role type: Marketing/Corporate | Correct classification |
| B-010 | Classify Technical | TEST-003 (Python Developer) | Role type: Technical | Correct classification |
| B-011 | Classify Creative | TEST-004 (Graphic Designer) | Role type: Creative | Correct classification |
| B-012 | Classify Technical/Executive | TEST-005 (VP of Engineering) | Role type: Technical or Executive | Correct classification |

#### B.4 Compliance Flags

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| B-013 | Salary required: California | TEST-001 (SF, CA) | `compliance_checklist.salary_disclosure: REQUIRED` | Correctly flagged |
| B-014 | Salary optional: Texas | TEST-002 (Austin, TX) | `salary_disclosure: RECOMMENDED` or `OPTIONAL` | NOT marked REQUIRED |
| B-015 | Salary handling: Remote US, no data | TEST-003 (remote, no salary) | Conservative approach: flag salary as REQUIRED (remote = strictest state), note data unavailable | Compliance flag addresses both the requirement and the missing data |
| B-016 | Salary required: Colorado | TEST-004 (Denver, CO) | `salary_disclosure: REQUIRED` | Correctly flagged |
| B-017 | Salary required: New York | TEST-005 (NYC, NY) | `salary_disclosure: REQUIRED` | Correctly flagged |
| B-018 | EEOC flags present | All test orders | `no_discriminatory_language: REQUIRED`, `equal_opportunity_mention: REQUIRED`, `platform_policy_compliant: REQUIRED` | All three present on every brief |

#### B.5 Keyword Generation (Rulebook 6.1-6.2)

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| B-019 | Primary keywords count | TEST-001 | 5-10 primary keywords | Count in range |
| B-020 | Primary keywords relevance | TEST-001 | Includes job title variations and role keywords | Contains "UX designer jobs" or similar |
| B-021 | Secondary keywords count | TEST-001 | 10-20 secondary keywords | Count in range |
| B-022 | Negative keywords include universals | TEST-001 | Includes: course, training, salary, freelance, resume template | Universal negatives present (per rulebook 6.2) |
| B-023 | Role-specific negatives | TEST-001 (Senior role) | Includes "entry level", "junior", "intern" | Seniority-inappropriate terms negated |
| B-024 | Technical keyword specificity | TEST-003 | Keywords include tech stack terms (Python, Airflow, AWS) | Technology-specific keywords present |

#### B.6 Budget & Targeting

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| B-025 | Budget with Tier-1 metro + urgency | TEST-001 (SF, urgent) | Base * 1.5 (urgency) * 1.4 (Tier-1 geo) | Budget reflects both multipliers |
| B-026 | Budget with standard urgency, Tier-2 | TEST-002 (Austin, standard) | Base * 1.0 * ~1.1 | No urgency premium; modest geo adjustment |
| B-027 | Budget with executive + ASAP urgency | TEST-005 (NYC, ASAP) | Higher base (executive) * urgency * Tier-1 | Highest budget of all test cases |
| B-028 | Human approval threshold | Any order with budget > $500/day | Brief flags need for human budget approval | Approval flag present |

#### B.7 Audience Profile & Tone

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| B-029 | Audience likely titles | TEST-001 | 2-5 plausible current titles | Titles are realistic (e.g., "UX Designer", "Product Designer") |
| B-030 | Candidate mindset: Senior/specialized | TEST-001 | `PASSIVE` or `MIXED` | Aligns with rulebook for senior roles |
| B-031 | Candidate mindset: Entry-level | TEST-002 | `ACTIVE` or `MIXED` | Aligns with rulebook for entry roles |
| B-032 | Tone: Creative role | TEST-001 | `tone: inspirational/bold`, `formality: 2` | Matches rulebook tone matrix |
| B-033 | Tone: Executive role | TEST-005 | `tone: strategic/prestigious`, `formality: 5` | Matches rulebook tone matrix |
| B-034 | Avoid messaging populated | All test orders | `avoid_messaging` has >= 2 items | Non-empty with contextually relevant items |

#### B.8 Google Ads Platform Specs

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| B-035 | RSA specs in brief | All test orders | `platforms.google_search.headlines_needed: 15`, `headline_max_chars: 30`, `descriptions_needed: 4`, `description_max_chars: 90` | Exact values match Google Ads spec |

### C. Writer Agent

Tests Claude API call producing RSA content. Character limits are **hard constraints** — any violation is a test failure.

#### C.1 Hard Constraints (Automated)

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| C-001 | Exactly 15 headlines | All test orders | 15 headlines produced | `len(headlines) == 15` |
| C-002 | Exactly 4 descriptions | All test orders | 4 descriptions produced | `len(descriptions) == 4` |
| C-003 | Headlines <= 30 chars | All test orders | Every headline within limit | `all(len(h) <= 30 for h in headlines)` |
| C-004 | Descriptions <= 90 chars | All test orders | Every description within limit | `all(len(d) <= 90 for d in descriptions)` |
| C-005 | Display URL paths present | All test orders | 2 paths, each <= 15 chars | `len(path) <= 15` for both |
| C-006 | No duplicate headlines | All test orders | All 15 unique | `len(set(headlines)) == 15` |
| C-007 | No duplicate descriptions | All test orders | All 4 unique | `len(set(descriptions)) == 4` |

#### C.2 Keyword Integration

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| C-008 | Primary keywords in >= 3 headlines | All test orders | At least 3 headlines contain a primary keyword from Strategy Brief | Keyword match count >= 3 |
| C-009 | Keywords organized by 3 ad groups | All test orders | Intent-RoleSeeking, Intent-SkillBased, Intent-LocationBased | Three groups present |
| C-010 | Keywords have match types | All test orders | Each keyword has Broad, Phrase, or Exact | Every keyword entry has `match_type` |
| C-011 | Negative keywords per ad group | All test orders | Each ad group has negative keywords | All 3 groups have >= 1 negative keyword |

#### C.3 Compliance (Automated)

Scan against `Tests/compliance-wordlists/eeoc-prohibited-terms.json`.

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| C-012 | No age-discriminatory terms | All test orders | No "young", "digital native", "recent graduate", "fresh out of college" | Zero matches against age discrimination list |
| C-013 | No gender-coded terms | All test orders | No "salesman", "chairman", "manpower", "he/she" | Zero matches against gender list |
| C-014 | No national origin terms | All test orders | No "native English speaker", "American only" | Zero matches against national origin list |
| C-015 | Salary in copy when required: CA | TEST-001 | Salary range appears in >= 1 asset | Dollar amount or range present |
| C-016 | Salary in copy when required: CO | TEST-004 | Salary range appears in >= 1 asset | Dollar amount or range present |
| C-017 | Salary in copy when required: NY | TEST-005 | Salary range appears in >= 1 asset | Dollar amount or range present |
| C-018 | No salary claims when data missing + non-mandated | TEST-003 (remote, no salary) | No specific dollar figures in copy | No fabricated salary numbers |
| C-019 | No excessive capitalization | All test orders | No fully uppercase headlines/descriptions | No match for pattern `^[A-Z\s\d!]+$` |
| C-020 | No excessive punctuation | All test orders | No "!!", "??", "..." in headlines | No 2+ consecutive identical punctuation |
| C-021 | No emoji | All test orders | Zero emoji characters | Regex check returns no matches |

#### C.4 Content Quality (Human Review + Automated)

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| C-022 | Remote in >= 2 headlines for remote jobs | TEST-003 | "Remote" or "Work From Home" in >= 2 headlines | Count >= 2 |
| C-023 | Remote NOT prominent for onsite jobs | TEST-002 | "Remote" does not appear in headlines | Count == 0 |
| C-024 | CTA in >= 2 headlines | All test orders | Action language: "Apply", "Join", "Start", "Explore" | CTA count >= 2 |
| C-025 | Headline diversity: >= 4 themes | All test orders | Covers: title, company, benefits, location, salary, CTA, skills | Human review or topic classification >= 4 themes |
| C-026 | Descriptions standalone | All test orders | Each description reads coherently alone | Human review: each conveys complete thought |
| C-027 | Relevance to job order | All test orders | Content references correct role, skills, industry | Human review: clearly about the input job |
| C-028 | Tone matches Strategy Brief | All test orders | Copy tone aligns with brief specification | Human review: tone matches |
| C-029 | Confidential client: name absent | TEST-004, TEST-005 | Client name does not appear anywhere in copy | Zero occurrences of client name in all assets |

### D. Campaign Builder

Tests Python code that constructs Google Ads API structures. No API calls required.

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| D-001 | Campaign has required settings | Strategy + Writer output | Campaign includes: name, daily budget, bidding strategy, location targeting, dates | All fields present and non-null |
| D-002 | Bidding = MAXIMIZE_CONVERSIONS | All inputs | Bidding strategy set correctly | Exact match |
| D-003 | Campaign created in PAUSED state | All inputs | Status is PAUSED | `campaign.status == PAUSED` |
| D-004 | Campaign name includes job ID | TEST-001 | Name contains "TEST-001" | Job ID in campaign name |
| D-005 | Exactly 3 ad groups | All inputs | Intent-RoleSeeking, Intent-SkillBased, Intent-LocationBased | Count == 3; names match |
| D-006 | Each ad group has RSA | All inputs | RSA with 15 headlines + 4 descriptions | Asset counts match per ad group |
| D-007 | Keywords in correct ad groups | Writer output | Role keywords in RoleSeeking; skill in SkillBased; location in LocationBased | No misplaced keywords |
| D-008 | Daily budget matches Strategy Brief | Strategy Brief allocates to Google | Campaign budget matches Brief allocation | Exact match |
| D-009 | Location: hybrid = metro + ~50mi | TEST-001 (SF, hybrid) | Geo target: SF metro + surrounding area | Radius targeting configured |
| D-010 | Location: onsite = metro + ~25mi | TEST-002 (Austin, onsite) | Tighter radius than hybrid | Smaller radius configured |
| D-011 | Location: remote = national US | TEST-003 (remote) | Country-level US targeting | US national targeting |
| D-012 | Display URL paths set | All inputs | 2 path components from Writer output | Both populated; each <= 15 chars |
| D-013 | Negative keywords applied | All inputs | Each ad group has negative keywords | Non-empty lists for all 3 groups |

### E. Human Review Gate

Tests the approval workflow. Manual testing.

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| E-001 | All campaign details displayed | Complete campaign | Shows: settings, 3 ad groups, keywords, 15 headlines, 4 descriptions, paths, budget, targeting | All elements visible and readable |
| E-002 | Compliance summary displayed | Campaign for CA job | EEOC check, salary transparency flag, platform policy status visible | Compliance section prominently shown |
| E-003 | Strategy Brief viewable | Any campaign | Full YAML brief can be displayed on request | Brief shown in readable format |
| E-004 | Approve proceeds to publisher | User approves | Campaign forwarded to Google Ads Publisher | Publisher receives campaign object |
| E-005 | Reject halts pipeline | User rejects | Campaign NOT published; reason logged | Zero Google Ads API calls; rejection stored |
| E-006 | Edit a headline before approval | User modifies headline | Change accepted; updated campaign re-displayed | Modified headline shown in review |
| E-007 | Edit enforces character limits | User enters 35-char headline | Edit rejected | Validation prevents over-length save |

### F. Google Ads Publisher

Tests Google Ads API integration. Requires API credentials (test or production account).

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| F-001 | Campaign created via API | Approved campaign + valid credentials | Campaign created in PAUSED state | API returns success; campaign ID returned |
| F-002 | 3 ad groups created | Approved campaign | Ad groups linked to campaign | API confirms 3 ad groups |
| F-003 | RSAs created in each ad group | Approved campaign | RSAs with correct headlines/descriptions | Asset counts match |
| F-004 | Keywords created with match types | Approved campaign | Keywords created as specified | Match types correct |
| F-005 | Campaign confirmation returned | Successful publish | Campaign ID, ad group IDs, confirmation info | All IDs available for tracking |
| F-006 | Auth failure handling | Invalid/expired refresh token | Clear error message | No partial campaign; actionable error |
| F-007 | Rate limit handling | Exceeding 15,000 ops/day | Retry with backoff | No data loss; retry or escalation |
| F-008 | Editorial rejection handling | Headline with editorial violation | Specific rejected asset identified | Rejection reason surfaced; option to fix |
| F-009 | Network failure recovery | Simulated timeout | Partial state detected; cleanup/retry | No orphaned objects; clean recovery |
| F-010 | Test account mode | Test Account developer token | Campaign created in test account | Operates identically to production path |

### G. End-to-End Integration

Tests the full pipeline from JSON input to published campaign.

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| INT-001 | Happy path: Senior Creative, CA | TEST-001 | Full pipeline succeeds | Campaign published matching job order intent |
| INT-002 | Happy path: Entry Corporate, TX | TEST-002 | Full pipeline succeeds | Campaign published; no salary mandate applied |
| INT-003 | Happy path: Mid Technical, Remote | TEST-003 | Full pipeline succeeds | National targeting; remote prominent; no salary fabricated |
| INT-004 | Happy path: Entry Creative, CO, Confidential | TEST-004 | Full pipeline succeeds | CO salary included; client name absent; short desc warning |
| INT-005 | Happy path: Executive, NYC, Confidential | TEST-005 | Full pipeline succeeds | NY salary included; formal tone; client name absent |
| INT-006 | Job ID traceable through pipeline | TEST-001 | Job ID appears in Brief, campaign name, audit log | Traceable at every stage |
| INT-007 | Strategy keywords used by Writer | TEST-001 | Writer headlines contain Strategy Brief primary keywords | At least 3 headlines match (not different keywords) |
| INT-008 | Strategy tone honored by Writer | TEST-005 | Writer uses formal/strategic tone per Brief | Human review confirms tone match |
| INT-009 | Strategy compliance flags honored by Writer | TEST-001 | Salary in copy because Brief said REQUIRED | Salary present in output |
| INT-010 | Campaign Builder uses Writer's exact content | Any test order | Headlines/descriptions passed without alteration | No truncation or reordering |
| INT-011 | Campaign Builder uses Strategy's budget | Any test order | Daily budget matches Brief allocation | Exact match |
| INT-012 | Rejection prevents publishing | User rejects TEST-001 campaign | Zero Google Ads API calls | No API calls after rejection |
| INT-013 | Two job orders processed independently | TEST-001 then TEST-002 sequentially | Each produces distinct campaign | No data leakage between campaigns |
| INT-014 | Error propagation: Strategy Agent failure | Job order with extremely short description | Pipeline pauses; Writer not invoked with incomplete brief | No downstream processing of bad data |

### H. Edge Cases

| ID | Description | Input | Expected Behavior | Pass Criteria |
|----|-------------|-------|-------------------|---------------|
| EDGE-001 | Job title exceeds 30 chars | `"Senior Principal Staff Software Engineering Manager"` (56 chars) | Writer creates abbreviated headline variations | All 15 headlines <= 30 chars |
| EDGE-002 | Extremely broad salary range | `"min": 50000, "max": 200000` | Strategy flags; Writer includes range | No compliance violation |
| EDGE-003 | Hourly salary format | `"type": "hourly", "min": 45, "max": 65` | Writer formats as "$45-$65/hr" | Correct unit displayed |
| EDGE-004 | Remote + specific CO location | `remote` + `Denver, CO` | CO salary transparency applies; national targeting | Compliance correct; targeting national |
| EDGE-005 | Multi-state remote (CA, NY, WA) | Remote with state restrictions in notes | Strictest state rule applies (salary REQUIRED) | Salary disclosure REQUIRED |
| EDGE-006 | Confidential client in named field | `"client": "Confidential"` | Client name absent from all copy | Zero occurrences in headlines/descriptions |
| EDGE-007 | Discriminatory language in input | Description: "looking for a young, energetic team player" | Strategy Agent flags; Writer rephrases | No prohibited terms in output; flag in log |
| EDGE-008 | Non-US location | `London, UK` | No US salary rules; GDPR flagged; UK targeting | Correct compliance and targeting |
| EDGE-009 | No salary, no budget hints | Missing salary + no budget notes | Defaults from rulebook 4.1 | Budget calculated from defaults |
| EDGE-010 | Contract role with duration | `contract`, `duration_months: 3` | Contract nature mentioned in copy | "Contract" or "3-month" in ad copy |
| EDGE-011 | Niche technical role | `"Kubernetes Site Reliability Engineer"` | Specific keywords generated | "Kubernetes SRE", "K8s" in keywords |
| EDGE-012 | Non-USD currency | `"currency": "EUR"` | Euro symbol or "EUR" in copy | Correct currency (not "$") |
| EDGE-013 | Start date in the past | `"start_date": "2023-01-15"` | Validation warning | Warning logged |
| EDGE-014 | Headline at exactly 30 chars | Writer produces 30-char headline | Accepted | 30 chars is valid (not 29) |
| EDGE-015 | Description at exactly 90 chars | Writer produces 90-char description | Accepted | 90 chars is valid |
| EDGE-016 | Claude API timeout | Strategy Agent call times out | Retry with exponential backoff | No silent failure; eventual error is clear |
| EDGE-017 | Claude returns malformed YAML | Strategy Agent output isn't valid YAML | Parser catches error; retries | YAML error handled; retry or escalation |
| EDGE-018 | Ampersand in headline counting | "UX & UI Designer Role" | Ampersand = 1 char; total = 22 | Character count correct |
| EDGE-019 | Hawaii salary transparency | Honolulu, HI; 50+ employees | Salary disclosure REQUIRED | Compliance flag correct |
| EDGE-020 | Special characters in description | Description with &, <, >, quotes | Properly escaped for API | No API errors from special chars |

---

## 4. Acceptance Criteria

### P0 — Must Pass (POC is not accepted without these)

| ID | Criterion | Verified By |
|----|-----------|-------------|
| **AC-01** | System accepts valid JSON job order and produces a Google Ads campaign end-to-end | INT-001 through INT-005 |
| **AC-02** | All headlines <= 30 chars, all descriptions <= 90 chars, display paths <= 15 chars | C-001 through C-007 (all 5 test orders) |
| **AC-03** | Salary transparency correctly applied: salary in copy for CA, CO, NY jobs | B-013, B-016, B-017, C-015, C-016, C-017 |
| **AC-04** | No EEOC-prohibited language in any output across all 5 test job orders | C-012 through C-014 (all 5 test orders) |
| **AC-05** | Human rejection prevents any Google Ads API calls | E-005, INT-012 |
| **AC-06** | Valid campaign structure: 1 campaign, 3 ad groups, RSAs, keywords with match types | D-001 through D-013 |
| **AC-07** | Missing optional fields (salary, notes, duration) don't crash pipeline | A-007, INT-003 |
| **AC-08** | Invalid input produces clear, actionable error messages | A-002 through A-006, A-008, A-009, A-011 |
| **AC-09** | Strategy Brief is valid YAML with all required sections | B-001, B-002 (all 5 test orders) |
| **AC-10** | Confidential client names never appear in ad copy | C-029, INT-004, INT-005 |

### P1 — Should Pass

| ID | Criterion | Verified By |
|----|-----------|-------------|
| **AC-11** | Correct seniority classification for all 5 test orders | B-003 through B-007 |
| **AC-12** | Correct role type classification for all 5 test orders | B-008 through B-012 |
| **AC-13** | Primary keywords from Strategy Brief appear in >= 3 headlines | C-008, INT-007 |
| **AC-14** | Writer Agent tone matches Strategy Brief specification | C-028, INT-008 |
| **AC-15** | Budget follows formula: Base * Urgency * Geographic | B-025 through B-027 |
| **AC-16** | Google Ads API errors produce clear messages, no corrupted state | F-006 through F-009 |
| **AC-17** | All 15 headlines unique per job order | C-006 |
| **AC-18** | No data leakage between consecutive job order runs | INT-013 |
| **AC-19** | Job ID traceable through every pipeline stage | INT-006 |

### P2 — Nice to Have

| ID | Criterion | Verified By |
|----|-----------|-------------|
| **AC-20** | Headlines cover >= 4 distinct messaging themes | C-025 |
| **AC-21** | Descriptions are each standalone | C-026 |
| **AC-22** | Key info front-loaded (14-second decision window) | Human review of first 3 headlines |
| **AC-23** | Google Ads Ad Strength is "Good" or "Excellent" | Check in Google Ads UI after publish |
| **AC-24** | Pipeline completes in < 120 seconds (excluding human review) | Timing on INT-001 |
| **AC-25** | Negative keywords include all universal negatives from rulebook | B-022 comparison against rulebook 6.2 list |

---

## 5. Testing Execution Strategy

### Phase 1: Unit Tests (Automated, No API)

**Scope**: Categories A and D
**Method**: Python pytest suite
**Dependencies**: None (no API calls)
**What it validates**:
- Job order parsing and validation logic
- Campaign builder structure creation
- Character limit enforcement
- Data mapping correctness

### Phase 2: Agent Tests (Semi-Automated, Claude API)

**Scope**: Categories B and C
**Method**: Run each of the 5 test job orders through Strategy and Writer agents. Capture outputs. Run automated validation:
- YAML parsing (Strategy Brief)
- Character counts (all headlines/descriptions)
- Compliance term scanning (against `Tests/compliance-wordlists/`)
- Keyword count verification
- Duplicate detection
**Dependencies**: Claude API key
**Human review needed for**: Tone match (C-028), content relevance (C-027), description quality (C-026), headline diversity (C-025)

### Phase 3: Integration Tests (Google Ads Test Account)

**Scope**: Categories G and F
**Method**: End-to-end pipeline using Google Ads test account
**Dependencies**: Claude API key + Google Ads test account credentials
**What it validates**:
- Full data flow from JSON to published campaign
- Google Ads API structure validity
- Error handling and recovery

### Phase 4: Human Review Tests (Manual)

**Scope**: Category E + subjective quality review
**Method**: Manual walkthrough of review interface
**What it validates**:
- All campaign details displayed correctly
- Approve/reject workflow functions
- Edit capability works with validation
- Ad copy quality across all 5 test orders

### Phase 5: Edge Cases (Mixed)

**Scope**: Category H
**Priority order**:
1. EDGE-001 (long title) — high likelihood in production
2. EDGE-004 (remote + location) — common scenario
3. EDGE-006, EDGE-007 (confidential, discriminatory input) — compliance critical
4. EDGE-003 (hourly salary) — format handling
5. EDGE-016, EDGE-017 (API failures) — resilience
6. Remaining edge cases

---

## Appendix: Reference Files

| File | Purpose |
|------|---------|
| `Architecture/strategy-agent-rulebook.md` | Classification rules, budget formulas, YAML template |
| `Knowledge-Base/compliance/eeoc-guidelines.md` | Prohibited language lists |
| `Knowledge-Base/compliance/salary-transparency.md` | State-by-state salary requirements |
| `Knowledge-Base/compliance/platform-policies.md` | Google Ads editorial policies |
| `Knowledge-Base/platform-specs/google-ads.md` | RSA specs, ad strength, bidding |
| `Knowledge-Base/candidate-psychology/by-seniority.md` | Tone and messaging by level |
| `Knowledge-Base/candidate-psychology/by-function.md` | Messaging by role type |
| `Knowledge-Base/candidate-psychology/active-vs-passive.md` | Active vs passive targeting |
| `Knowledge-Base/benchmarks/recruitment-benchmarks.md` | CPA benchmarks, budget allocation |
| `Tests/compliance-wordlists/eeoc-prohibited-terms.json` | Machine-readable prohibited terms |
| `Tests/compliance-wordlists/salary-transparency-rules.json` | Machine-readable state rules |
| `Tests/test-job-orders/*.json` | 5 test job order files |
