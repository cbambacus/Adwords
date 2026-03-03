# Google Ads API Setup Guide

This guide walks through getting full API access to programmatically create Google Ads campaigns.

## Overview

You need four things to use the Google Ads API:
1. **Google Ads Manager Account (MCC)** - To manage ad accounts
2. **Developer Token** - API access key (requires approval)
3. **OAuth 2.0 Credentials** - For authentication
4. **Google Ads Customer ID** - The account to manage

**Timeline:** The developer token approval process typically takes 1-2 weeks.

---

## Step 1: Create a Google Ads Manager Account (MCC)

A Manager Account lets you manage multiple Google Ads accounts from one place.

1. Go to [Google Ads Manager Accounts](https://ads.google.com/home/tools/manager-accounts/)
2. Click **Create a manager account**
3. Sign in with a Google account (use a company/service account, not personal)
4. Fill in:
   - Account name: "Ads Automation" (or similar)
   - Primary use: "Manage other people's accounts"
   - Country and timezone
5. Complete the setup

**Note:** If the company already has a Google Ads account, you'll link it under this manager account later.

---

## Step 2: Set Up a Google Cloud Project

The Google Ads API uses Google Cloud for OAuth authentication.

### 2.1 Create the Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown (top left) → **New Project**
3. Name it: "Ads Automation"
4. Click **Create**

### 2.2 Enable the Google Ads API

1. In your new project, go to **APIs & Services** → **Library**
2. Search for "Google Ads API"
3. Click on it and press **Enable**

### 2.3 Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **Internal** (if using Google Workspace) or **External**
3. Fill in:
   - App name: "Ads Automation"
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. On Scopes page, click **Add or Remove Scopes**
6. Add: `https://www.googleapis.com/auth/adwords`
7. Save and continue through remaining steps

### 2.4 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app** (for initial setup/testing)
4. Name: "Ads CLI"
5. Click **Create**
6. **Download the JSON file** - save as `client_secret.json`

**Keep this file secure - it contains your client secret!**

---

## Step 3: Apply for a Developer Token

This is the critical step that requires Google approval.

### 3.1 Access the API Center

1. Sign into your Manager Account at [ads.google.com](https://ads.google.com)
2. Click the **Tools & Settings** icon (wrench) in the top right
3. Under **Setup**, click **API Center**

### 3.2 Apply for Access

1. You'll see your **Developer Token** (initially with "Test Account" access)
2. Fill out the **API Access Application**:

**Required Information:**

| Field | Recommended Response |
|-------|---------------------|
| **Tool/Service Description** | "Internal automation tool for creating job recruitment advertising campaigns. Programmatically creates search campaigns when new job orders are received." |
| **API Usage** | Select: "Building an internal tool" |
| **Website** | aquent.com |
| **How will you use the API?** | "We will use the API to: 1) Create search campaigns for job postings, 2) Set up ad groups with relevant keywords, 3) Create responsive search ads, 4) Monitor campaign performance, 5) Pause/adjust campaigns based on results" |

### 3.3 Access Levels

| Level | Capabilities | Requirements |
|-------|-------------|--------------|
| **Test Account** | Immediate, but only works with test accounts | None |
| **Basic Access** | 15,000 operations/day, mutate operations allowed | Approval required |
| **Standard Access** | 1,000,000 operations/day | Higher bar for approval |

**For this project, Basic Access is sufficient to start.**

### 3.4 Tips for Faster Approval

- Be specific about your use case (job recruitment advertising)
- Mention you're building an internal tool, not a third-party service
- Explain the business value (automating campaign creation for staffing)
- Be honest - they may ask follow-up questions

---

## Step 4: Generate Refresh Token

Once you have OAuth credentials, generate a refresh token for API access.

### 4.1 Using Google's OAuth Playground (Quick Method)

1. Go to [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
2. Click the gear icon (settings) in top right
3. Check **Use your own OAuth credentials**
4. Enter your Client ID and Client Secret from Step 2.4
5. In the left panel, find **Google Ads API v17**
6. Select `https://www.googleapis.com/auth/adwords`
7. Click **Authorize APIs**
8. Sign in with the Google account that has access to your Ads account
9. Click **Exchange authorization code for tokens**
10. Copy the **Refresh Token**

### 4.2 Using Python Script (Recommended for Production)

```python
# generate_refresh_token.py
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/adwords']

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES
    )

    credentials = flow.run_local_server(port=8080)

    print(f"Refresh Token: {credentials.refresh_token}")
    print("\nSave this token securely!")

if __name__ == '__main__':
    main()
```

---

## Step 5: Get Your Customer ID

1. Sign into [Google Ads](https://ads.google.com)
2. Your **Customer ID** is displayed in the top right (format: XXX-XXX-XXXX)
3. If using a Manager Account, you'll also need the **Manager Customer ID**

**Remove the dashes when using in API calls** (e.g., `1234567890`)

---

## Step 6: Create Configuration File

Create a `google-ads.yaml` file for the Python client library:

```yaml
# google-ads.yaml
developer_token: YOUR_DEVELOPER_TOKEN
client_id: YOUR_CLIENT_ID.apps.googleusercontent.com
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
login_customer_id: YOUR_MANAGER_ACCOUNT_ID  # Optional: if using MCC

# Use this for test accounts during development:
# use_proto_plus: True
```

**Security Notes:**
- Never commit this file to version control
- Add `google-ads.yaml` to `.gitignore`
- Use environment variables in production

---

## Step 7: Verify Your Setup

Test your configuration with this Python script:

```python
# test_connection.py
from google.ads.googleads.client import GoogleAdsClient

def main():
    # Load credentials from google-ads.yaml
    client = GoogleAdsClient.load_from_storage("google-ads.yaml")

    # Get the customer service
    customer_service = client.get_service("CustomerService")

    # List accessible customers
    response = customer_service.list_accessible_customers()

    print("Accessible customers:")
    for resource_name in response.resource_names:
        print(f"  {resource_name}")

if __name__ == '__main__':
    main()
```

If this runs without errors and lists your accounts, you're set up!

---

## Troubleshooting

### "Developer token is not approved"
- Your token is still in Test Account mode
- Wait for Basic Access approval, or use a test account for development

### "The customer account can't be accessed"
- Verify the Customer ID is correct (no dashes)
- Ensure the authenticated user has access to that account
- Check if `login_customer_id` is needed (for MCC setups)

### "Invalid OAuth credentials"
- Regenerate the refresh token
- Verify client ID and secret match your Google Cloud project
- Ensure the Google Ads API is enabled in your Cloud project

### "User does not have permission"
- The Google account used for OAuth needs admin access to the Ads account
- Add the user as an admin in Google Ads settings

---

## Next Steps

Once you have API access:

1. [ ] Create test campaigns manually to understand the structure
2. [ ] Set up the Python project with `google-ads` library
3. [ ] Build campaign creation automation
4. [ ] Implement A/B testing for ad copy

---

## Useful Links

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [Python Client Library](https://github.com/googleads/google-ads-python)
- [API Reference](https://developers.google.com/google-ads/api/reference/rpc)
- [Google Ads API Support](https://support.google.com/google-ads/thread/new)

---

## Checklist

- [ ] Manager Account created
- [ ] Google Cloud project created
- [ ] Google Ads API enabled
- [ ] OAuth consent screen configured
- [ ] OAuth credentials created (client_secret.json downloaded)
- [ ] Developer token applied for
- [ ] Developer token approved (Basic Access)
- [ ] Refresh token generated
- [ ] google-ads.yaml configured
- [ ] Test connection successful
