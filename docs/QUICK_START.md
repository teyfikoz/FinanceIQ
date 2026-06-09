# FundPilot Quick Start

## Current Identity

- Product name: `FundPilot`
- Canonical public host: `https://fundpilot.techsyncanalytica.com`
- Repository slug: `FinanceIQ`
- Local repo path: `/Users/teyfikoz/Projects/saas/financeiq`

## Local Start

```bash
cd /Users/teyfikoz/Projects/saas/financeiq
python3 scripts/release_guard.py --skip-pytest
streamlit run main.py
```

Open:

- `http://localhost:8501`

## Local Validation

Fast validation:

```bash
pytest -q tests/test_navigation_state.py
python3 scripts/release_guard.py --skip-pytest
```

Full validation:

```bash
pytest -q tests/
python3 scripts/release_guard.py
```

## Production Runtime

- App dir: `/opt/fundportal/app`
- Venv: `/opt/fundportal/venv`
- Env file: `/etc/fundportal/fundportal.env`
- Service: `fundportal`
- Reverse proxy: `nginx`
- Public host: `fundpilot.techsyncanalytica.com`

## Production Smoke

```bash
ssh -o BatchMode=yes root@46.62.164.198 \
  "cd /opt/fundportal/app && bash scripts/post_deploy_smoke.sh"
```

Expected result:

- `FundPilot post-deploy smoke passed.`

## Core Environment Variables

```bash
FINANCEIQ_APP_DISPLAY_NAME=FundPilot
FINANCEIQ_PUBLIC_APP_URL=https://fundpilot.techsyncanalytica.com
FINANCEIQ_PUBLIC_APP_HOST=fundpilot.techsyncanalytica.com
FINANCEIQ_REQUIRE_AUTH=false
FINANCEIQ_DIRECT_ACCESS=true
FRED_API_KEY=your_fred_key_here
TCMB_EVDS_API_KEY=your_tcmb_evds_key_here
```

## Most Important Recent Fix

The public sidebar navigation bug is fixed in production:

- `Research` now routes to `?view=stock-research`
- `Workspace` now routes to `?view=portfolio`
- quick routes no longer corrupt Streamlit widget state
