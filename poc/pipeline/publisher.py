"""
Google Ads Publisher — Creates campaigns in a Google Ads test account.

Uses the google-ads Python client library to:
1. Create a campaign (PAUSED)
2. Create ad groups
3. Create responsive search ads
4. Create keywords and negative keywords

All operations target a TEST ACCOUNT only until pipeline is fully verified.
Switching to production requires changing config/settings.py values.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, List

from poc.config.settings import (
    GOOGLE_ADS_USE_TEST_ACCOUNT,
    GOOGLE_ADS_YAML_PATH,
)


def _get_google_ads_client():
    """Create and return a Google Ads API client."""
    from google.ads.googleads.client import GoogleAdsClient

    if not GOOGLE_ADS_YAML_PATH.exists():
        raise FileNotFoundError(
            f"Google Ads config not found at {GOOGLE_ADS_YAML_PATH}. "
            f"Create this file with your credentials. See google-ads-api-setup.md."
        )

    client = GoogleAdsClient.load_from_storage(str(GOOGLE_ADS_YAML_PATH))
    return client


def _get_customer_id() -> str:
    """Load the customer ID from the google-ads.yaml config."""
    with open(GOOGLE_ADS_YAML_PATH) as f:
        config = yaml.safe_load(f)
    # login_customer_id is the manager account; use client_customer_id for the test account
    customer_id = config.get("client_customer_id") or config.get("login_customer_id")
    # Remove dashes if present
    return str(customer_id).replace("-", "")


def _create_campaign(client, customer_id: str, campaign_data: dict) -> str:
    """Create a campaign and return its resource name."""
    campaign_service = client.get_service("CampaignService")
    campaign_budget_service = client.get_service("CampaignBudgetService")

    # Create campaign budget first
    budget_operation = client.get_type("CampaignBudgetOperation")
    budget = budget_operation.create
    budget.name = f"Budget-{campaign_data['campaign_name']}"
    budget.amount_micros = campaign_data["budget"]["amount_micros"]
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD

    budget_response = campaign_budget_service.mutate_campaign_budgets(
        customer_id=customer_id,
        operations=[budget_operation],
    )
    budget_resource_name = budget_response.results[0].resource_name

    # Create campaign
    campaign_operation = client.get_type("CampaignOperation")
    campaign = campaign_operation.create
    campaign.name = campaign_data["campaign_name"]
    campaign.campaign_budget = budget_resource_name
    campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    campaign.status = client.enums.CampaignStatusEnum.PAUSED

    # Network settings
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = True
    campaign.network_settings.target_content_network = False

    # Bidding strategy: maximize conversions
    campaign.maximize_conversions.target_cpa_micros = 0

    campaign_response = campaign_service.mutate_campaigns(
        customer_id=customer_id,
        operations=[campaign_operation],
    )
    return campaign_response.results[0].resource_name


def _create_ad_group(client, customer_id: str, campaign_resource_name: str, ad_group_data: dict) -> str:
    """Create an ad group and return its resource name."""
    ad_group_service = client.get_service("AdGroupService")

    operation = client.get_type("AdGroupOperation")
    ad_group = operation.create
    ad_group.name = ad_group_data["name"]
    ad_group.campaign = campaign_resource_name
    ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
    ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD

    response = ad_group_service.mutate_ad_groups(
        customer_id=customer_id,
        operations=[operation],
    )
    return response.results[0].resource_name


def _create_rsa(client, customer_id: str, ad_group_resource_name: str, rsa_data: dict) -> str:
    """Create a Responsive Search Ad."""
    ad_group_ad_service = client.get_service("AdGroupAdService")

    operation = client.get_type("AdGroupAdOperation")
    ad_group_ad = operation.create
    ad_group_ad.ad_group = ad_group_resource_name
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

    ad = ad_group_ad.ad
    ad.final_urls.append(rsa_data.get("final_url", "https://aquent.com/find-work"))

    # Add headlines
    for h_data in rsa_data.get("headlines", []):
        headline = client.get_type("AdTextAsset")
        headline.text = h_data["text"]
        ad.responsive_search_ad.headlines.append(headline)

    # Add descriptions
    for d_data in rsa_data.get("descriptions", []):
        description = client.get_type("AdTextAsset")
        description.text = d_data["text"]
        ad.responsive_search_ad.descriptions.append(description)

    # Display paths
    paths = rsa_data.get("display_paths", [])
    if len(paths) >= 1:
        ad.responsive_search_ad.path1 = paths[0]
    if len(paths) >= 2:
        ad.responsive_search_ad.path2 = paths[1]

    response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id,
        operations=[operation],
    )
    return response.results[0].resource_name


def _create_keywords(client, customer_id: str, ad_group_resource_name: str, keywords: list) -> int:
    """Create keywords for an ad group. Returns count created."""
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")

    operations = []
    for kw_data in keywords:
        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        criterion.ad_group = ad_group_resource_name
        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        criterion.keyword.text = kw_data["text"]

        match_type_str = kw_data.get("match_type", "PHRASE").upper()
        if match_type_str == "EXACT":
            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.EXACT
        elif match_type_str == "BROAD":
            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
        else:
            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.PHRASE

        operations.append(operation)

    if operations:
        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations,
        )
        return len(response.results)
    return 0


def _create_negative_keywords(client, customer_id: str, campaign_resource_name: str, negatives: list) -> int:
    """Create campaign-level negative keywords. Returns count created."""
    campaign_criterion_service = client.get_service("CampaignCriterionService")

    operations = []
    seen = set()
    for neg_data in negatives:
        text = neg_data["text"]
        if text.lower() in seen:
            continue
        seen.add(text.lower())

        operation = client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = campaign_resource_name
        criterion.negative = True
        criterion.keyword.text = text
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.PHRASE
        operations.append(operation)

    if operations:
        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations,
        )
        return len(response.results)
    return 0


def publish_campaign(campaign_data: dict) -> dict:
    """
    Publish a campaign structure to Google Ads test account.

    Args:
        campaign_data: Campaign structure dict from campaign_builder

    Returns:
        dict with publish results
    """
    if not GOOGLE_ADS_USE_TEST_ACCOUNT:
        raise RuntimeError(
            "SAFETY: GOOGLE_ADS_USE_TEST_ACCOUNT is False. "
            "The POC must only use test accounts. "
            "Change config/settings.py to enable test account mode."
        )

    try:
        client = _get_google_ads_client()
        customer_id = _get_customer_id()
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Failed to initialize Google Ads client: {e}"}

    created = []
    total_keywords = 0
    total_negatives = 0

    try:
        # 1. Create campaign
        campaign_rn = _create_campaign(client, customer_id, campaign_data)
        created.append(f"Campaign created: {campaign_rn}")

        # 2. Collect all negative keywords (campaign-level)
        all_negatives = []
        for ag in campaign_data.get("ad_groups", []):
            all_negatives.extend(ag.get("negative_keywords", []))

        # Deduplicate negatives
        total_negatives = _create_negative_keywords(client, customer_id, campaign_rn, all_negatives)
        created.append(f"{total_negatives} negative keywords created (campaign-level)")

        # 3. Create ad groups with RSAs and keywords
        ad_group_count = 0
        rsa_count = 0
        for ag_data in campaign_data.get("ad_groups", []):
            ag_rn = _create_ad_group(client, customer_id, campaign_rn, ag_data)
            ad_group_count += 1

            # Create RSA
            for ad_data in ag_data.get("ads", []):
                _create_rsa(client, customer_id, ag_rn, ad_data)
                rsa_count += 1

            # Create keywords
            kw_count = _create_keywords(client, customer_id, ag_rn, ag_data.get("keywords", []))
            total_keywords += kw_count

        created.append(f"{ad_group_count} ad groups created")
        created.append(f"{rsa_count} RSAs created")
        created.append(f"{total_keywords} keywords created")

        return {
            "success": True,
            "campaign_resource_name": campaign_rn,
            "customer_id": customer_id,
            "created": created,
            "stats": {
                "ad_groups": ad_group_count,
                "rsas": rsa_count,
                "keywords": total_keywords,
                "negative_keywords": total_negatives,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "partial_created": created,
        }
