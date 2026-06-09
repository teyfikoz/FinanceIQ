# FundPilot Streamlit Cloud Notes

## Status

Streamlit Cloud is **not** the current primary production path.

Current production:

- Product: `FundPilot`
- Canonical host: `https://fundpilot.techsyncanalytica.com`
- Infra: `Hetzner + nginx + systemd + Streamlit`

This file remains only as an optional fallback/reference if you ever want a secondary Streamlit Cloud deployment.

## Repository Naming Note

- Public product brand: `FundPilot`
- GitHub repo slug: legacy repository name

If you create a Streamlit Cloud app from the current repo, use the current GitHub repository for this project but name the app itself `FundPilot`.

## Minimum Streamlit Cloud Settings

- Main file: `main.py`
- Python: `3.12` if available, otherwise `3.11`
- Secrets:

```toml
FINANCEIQ_APP_DISPLAY_NAME = "FundPilot"
FINANCEIQ_PUBLIC_APP_URL = "https://fundpilot.techsyncanalytica.com"
FINANCEIQ_PUBLIC_APP_HOST = "fundpilot.techsyncanalytica.com"
FINANCEIQ_REQUIRE_AUTH = false
FINANCEIQ_DIRECT_ACCESS = true
FRED_API_KEY = "your_fred_key_here"
TCMB_EVDS_API_KEY = "your_tcmb_evds_key_here"
```

## Important Caveat

The production fixes validated on Hetzner include:

- correct HTTPS termination
- fixed sidebar navigation state
- production smoke script
- env-backed `FundPilot` branding

If a Streamlit Cloud deployment is created later, validate those same behaviors explicitly. Do not assume parity automatically.
