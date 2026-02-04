## Google Ads (AdWords) — 1-page primer (with an eye toward AI optimization)

Google Ads is an auction-based advertising platform where you choose *who* to reach (keywords/audiences/locations), *what* to say (ad assets), *how much* to bid (manual or automated), and *what success means* (conversion goals). Each search (or impression opportunity) triggers a real-time auction that decides **whether** you show and **where**, based on more than just money.

### 1) The auction: why “best ad” can beat “highest bid”

When someone searches, Google runs an auction among eligible ads. Your position isn’t purely “highest bidder wins.” Google computes **Ad Rank** to decide eligibility and ordering. Ad Rank considers:

* **Bid** (or Smart Bidding’s computed bid)
* **Ad/landing page quality**
* **Expected impact of assets (extensions) and other ad formats**
* **Context of the search** (device, location, time, query intent, etc.)
* **Minimum thresholds** to keep low-quality ads from showing ([Google Help][1])

**Takeaway:** Improving relevance + landing page experience can lower your cost-per-click and improve position, not just raising bids. Quality Score is a *diagnostic* view (1–10) of how your quality compares at the keyword level. ([Google Help][2])

### 2) Core building blocks (how accounts are organized)

At a practical level, most teams operate around this hierarchy:

* **Account** → billing, settings, access
* **Campaign** → objective, budget, network (Search/Display/Video/Performance Max), geo, bidding strategy
* **Ad group / Asset group** → a theme (keywords or assets) and the ads shown for it
* **Ads (assets)** → headlines/descriptions/images/videos that Google assembles into the final ad, depending on format (e.g., Responsive Search Ads)

Responsive Search Ads (RSAs) let you supply multiple headlines and descriptions; Google mixes and matches combinations. Pinning is possible, but too much pinning can reduce flexibility. ([Google Help][3])

### 3) Targeting: keywords, match types, and “what you actually showed for”

For **Search campaigns**, targeting is heavily driven by **keywords + match types**:

* **Exact / Phrase / Broad** control how closely user searches must align with your keyword’s meaning/intent. ([Google Help][4])
* **Negative keywords** prevent wasted spend by excluding unwanted queries (with their own match types). ([Google Help][5])
* The **Search terms report** shows the real queries that triggered your ads—critical for adding negatives and spotting new opportunities. ([Google Help][6])

For **Performance Max**, Google uses your assets + signals to serve across multiple Google surfaces (Search, YouTube, Display, Discover, Gmail, Maps). Audience signals guide exploration but aren’t strict targeting in the same way as Search keywords. ([Google Help][7])

### 4) Bidding: manual vs. Google AI (Smart Bidding)

Bidding determines how aggressively you compete in each auction.

* **Manual bidding**: you set CPCs/adjustments.
* **Smart Bidding** uses Google AI with “auction-time bidding” to adjust bids per auction based on many signals, optimizing for your goal. ([Google Help][8])

Common Smart Bidding strategies:

* **Maximize conversions** / **Maximize conversion value**
* **Target CPA** (cost per acquisition) ([Google Help][9])
* **Target ROAS** (return on ad spend) ([Google Help][10])

**Takeaway:** If you want AI to optimize effectively, you need clean conversion measurement and enough conversion volume for learning.

### 5) Measurement: conversions are the “north star”

Google can optimize toward what you track. **Conversion tracking** measures actions you care about (leads, purchases, calls, button clicks, etc.). ([Google Help][11])
If conversions are misconfigured (wrong event, double-counting, missing values), Smart Bidding will optimize toward the wrong thing—fast.

### 6) How to use AI to improve copy + targeting (safe, high-impact loop)

If your end goal is “AI optimization,” focus on a tight iteration loop with guardrails:

**A. Start with one objective per campaign**

* Lead gen? Purchases? Pipeline value? Choose one primary conversion goal and align bidding to it. ([Google Help][12])

**B. Use AI on the inputs you control**

* **Ad assets (copy):** Generate headline/description variants mapped to intent (“pricing,” “near me,” “compare,” “enterprise,” etc.). RSAs reward breadth as long as each line stands alone and doesn’t contradict others. ([Google Help][3])
* **Keyword expansion:** Mine the Search terms report; have AI cluster queries into themes → add winners as keywords (or ad groups), add losers as negatives. ([Google Help][6])
* **Landing page alignment:** For top themes, ensure the page matches the promise (message match). This supports quality/relevance outcomes. ([Google Help][2])

**C. Evaluate with the right scorecard**
Don’t optimize to CTR alone. Prefer: conversion rate, CPA, ROAS, conversion value, and (when possible) downstream quality (SQL rate, revenue).

**D. Change one thing at a time**
AI bidding systems learn. Make controlled edits (asset set, negatives, landing page, conversion definition) so you can attribute impact.

### 7) A practical “first week” checklist

1. Verify conversion actions, attribution settings, and which conversions count in the main “Conversions” column. ([Google Help][13])
2. Pull last 30–90 days: Search terms report → add obvious negatives, identify top intent clusters. ([Google Help][6])
3. For each high-intent cluster: one tight ad group/theme, one strong RSA with varied headlines, and a landing page that matches. ([Google Help][3])
4. Choose bidding strategy aligned to goal (Target CPA / Target ROAS when appropriate). ([Google Help][8])
5. Establish an AI workflow: weekly query clustering + negative keyword proposals + new RSA asset suggestions + a short experiment log.

If you tell me what campaign types you’re running (Search vs Performance Max), your primary conversion (lead form? call? purchase?), and whether you’re on Smart Bidding today, I’ll suggest an AI optimization workflow that fits your setup (including what data to export and what prompts/rules to use).

[1]: https://support.google.com/google-ads/answer/6366577?hl=en&utm_source=chatgpt.com "How the Google Ads auction works"
[2]: https://support.google.com/google-ads/answer/6167118?hl=en&utm_source=chatgpt.com "About Quality Score for Search campaigns - Google Ads Help"
[3]: https://support.google.com/google-ads/answer/7684791?hl=en&utm_source=chatgpt.com "About responsive search ads"
[4]: https://support.google.com/google-ads/answer/7478529?utm_source=chatgpt.com "About keyword matching options - Google Ads Help"
[5]: https://support.google.com/google-ads/answer/7302703?hl=en&utm_source=chatgpt.com "Negative broad match: Definition - Google Ads Help"
[6]: https://support.google.com/google-ads/answer/2472708?hl=en&utm_source=chatgpt.com "About the search terms report - Google Ads Help"
[7]: https://support.google.com/google-ads/answer/10724817?hl=en&utm_source=chatgpt.com "About Performance Max campaigns - Google Ads Help"
[8]: https://support.google.com/google-ads/answer/7065882?hl=en&utm_source=chatgpt.com "About Smart Bidding - Google Ads Help"
[9]: https://support.google.com/google-ads/answer/6268632?hl=en&utm_source=chatgpt.com "About Target CPA bidding - Google Ads Help"
[10]: https://support.google.com/google-ads/answer/6268637?hl=en&utm_source=chatgpt.com "About Target ROAS bidding - Google Ads Help"
[11]: https://support.google.com/google-ads/answer/6308?hl=en&utm_source=chatgpt.com "Conversion tracking: Definition - Google Ads Help"
[12]: https://support.google.com/google-ads/answer/1722022?hl=en&utm_source=chatgpt.com "About conversion measurement - Google Ads Help"
[13]: https://support.google.com/google-ads/answer/1722054?hl=en&utm_source=chatgpt.com "Different ways to track conversions - Google Ads Help"
