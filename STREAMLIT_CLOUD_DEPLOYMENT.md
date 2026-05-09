# Streamlit Cloud Deployment Guide

## Status

`Streamlit Cloud` is now legacy infrastructure for this project.

Current production host:

- `https://fundpilot.techsyncanalytica.com`

Legacy Streamlit Cloud host:

- `https://financeiq.streamlit.app/`

Current deployment policy:

- primary production deployment: `Hetzner + nginx + systemd`
- optional fallback/demo deployment: `Streamlit Cloud`

Primary production guide:

- [DEPLOYMENT_GUIDE.md](/Users/teyfikoz/github-projects/FinanceIQ/DEPLOYMENT_GUIDE.md)

## When To Use Streamlit Cloud

Use Streamlit Cloud only for:

- quick demo environments
- temporary validation before syncing to Hetzner
- fallback sharing links

Do not treat it as the source of truth for:

- canonical branding
- production DNS
- long-lived operational deployment

## Current App Identity

- Product name: `FundPilot`
- Internal legacy name: `FinanceIQ`
- Preferred public URL: `https://fundpilot.techsyncanalytica.com`

If Streamlit Cloud is used again, the app should still present:

- `FundPilot` branding
- `fundpilot.techsyncanalytica.com` as the canonical public URL

## Streamlit Cloud Requirements

- Python `3.10` or `3.11`
- `main.py` as the entrypoint
- dependencies from `requirements.txt`

## Recommended Secrets

Only optional keys are needed. The app can still run in degraded mode without paid data providers.

```toml
[app]
FINANCEIQ_ENV = "production"
FINANCEIQ_REQUIRE_AUTH = false
FINANCEIQ_DIRECT_ACCESS = true
FINANCEIQ_CREATE_DEMO_USER = false
FINANCEIQ_PUBLIC_APP_URL = "https://fundpilot.techsyncanalytica.com"
FINANCEIQ_APP_DISPLAY_NAME = "FundPilot"
FINANCEIQ_SUPPORT_EMAIL = "support@techsyncanalytica.com"

[api_keys]
FRED_API_KEY = ""
ALPHA_VANTAGE_API_KEY = ""
FMP_API_KEY = ""
FINNHUB_API_KEY = ""
POLYGON_API_KEY = ""
NEWSAPI_KEY = ""
COINGECKO_API_KEY = ""

[ai]
HF_API_TOKEN = ""
HF_SUMMARY_MODEL = "facebook/bart-large-cnn"
HF_SENTIMENT_MODEL = "ProsusAI/finbert"
HF_RISK_MODEL = "google/flan-t5-base"
```

## Deploy Steps

### 1. Push the current branch

```bash
git add .
git commit -m "Update FundPilot deployment state"
git push origin main
```

### 2. Create or update the Streamlit app

- repository: this repo
- branch: `main`
- main file: `main.py`

### 3. Apply secrets

Set the secrets shown above in the Streamlit Cloud app settings.

### 4. Validate

- app starts without import errors
- branding shows `FundPilot`
- exports and QR links point to `https://fundpilot.techsyncanalytica.com`

## Limits And Caveats

Streamlit Cloud remains weaker than the Hetzner production path for this app because:

- resource limits are tighter
- cold starts are more likely
- custom operational control is lower
- heavier analytics views are less predictable under load

## Release Rule

If the Streamlit Cloud version and the Hetzner version diverge, the Hetzner deployment is the authoritative production state.
