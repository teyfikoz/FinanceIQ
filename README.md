# FundPilot

FundPilot is the live financial research and fund intelligence application deployed at `https://fundpilot.techsyncanalytica.com`.

The product started as `FinanceIQ`, but the production identity, host, and runtime are now centered on `FundPilot` as a privacy-first FastAPI web app.

## Current Production State

[![Build](https://github.com/teyfikoz/financeiq/actions/workflows/publish.yml/badge.svg)](https://github.com/teyfikoz/financeiq/actions/workflows/publish.yml)
- Canonical URL: `https://fundpilot.techsyncanalytica.com`
- Runtime: `FastAPI + Jinja2`
- Server: `Hetzner` at `46.62.164.198`
- Reverse proxy: `nginx`
- Service: `fundpilot.service`
- App path: `/opt/fundpilot/app`
- Python env: `/opt/fundpilot/venv`

## Product Scope

FundPilot combines multiple financial workflows inside one production app shell:

- market dashboard and macro snapshot
- Turkish markets and TEFAS fund workflows
- comprehensive stock research
- ETF and fund analysis
- institutional and sovereign fund views
- scenario, allocation, and cycle analysis
- AI-assisted research helpers

## Current UX/Performance Model

The public production surface is now a read-only web app designed for:

- open-access dashboarding
- Turkish fund signal board workflows
- sponsor and affiliate inventory without ad-network scripts
- no login wall and no cookie-based personalization
- server-side rendering with progressive enhancement only

Core runtime files:

- [app/main.py](/Users/teyfikoz/github-projects/FinanceIQ/app/main.py)
- [app/web/routes.py](/Users/teyfikoz/github-projects/FinanceIQ/app/web/routes.py)
- [app/services/public_dashboard.py](/Users/teyfikoz/github-projects/FinanceIQ/app/services/public_dashboard.py)
- [app/services/tr_funds.py](/Users/teyfikoz/github-projects/FinanceIQ/app/services/tr_funds.py)

## Local Development

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open locally

```text
http://localhost:8000
```

## Sponsor Slot Configuration

The public dashboard renders direct sponsor and affiliate cards without third-party ad scripts.

Optional environment variables:

- `FUNDPILOT_SLOT_1_TITLE`
- `FUNDPILOT_SLOT_1_LABEL`
- `FUNDPILOT_SLOT_1_HREF`
- `FUNDPILOT_SLOT_1_DESCRIPTION`
- `FUNDPILOT_SLOT_1_BADGE`

Repeat the same pattern for slots `2` and `3`.

## Production Deployment

Primary deployment documentation:

- [DEPLOYMENT_GUIDE.md](/Users/teyfikoz/github-projects/FinanceIQ/DEPLOYMENT_GUIDE.md)

Deployment assets:

- [deployment/fundpilot.service](/Users/teyfikoz/github-projects/FinanceIQ/deployment/fundpilot.service)
- [deployment/fundpilot.nginx.conf](/Users/teyfikoz/github-projects/FinanceIQ/deployment/fundpilot.nginx.conf)

## Legacy Streamlit Status

The old Streamlit surface is legacy code and is not the production runtime anymore.

Archived entrypoints:

- [archive/retired_streamlit_runtime/README.md](/Users/teyfikoz/github-projects/FinanceIQ/archive/retired_streamlit_runtime/README.md)

Google ad setup notes:

- [docs/ADSENSE_ADMOB_SETUP.md](/Users/teyfikoz/github-projects/FinanceIQ/docs/ADSENSE_ADMOB_SETUP.md)

## Design And QA Docs

- [DESIGN.md](/Users/teyfikoz/github-projects/FinanceIQ/DESIGN.md)
- [docs/FUNDPILOT_UI_REDESIGN_PLAN.md](/Users/teyfikoz/github-projects/FinanceIQ/docs/FUNDPILOT_UI_REDESIGN_PLAN.md)
- [docs/FUNDPILOT_FRONTEND_MIGRATION_PLAN.md](/Users/teyfikoz/github-projects/FinanceIQ/docs/FUNDPILOT_FRONTEND_MIGRATION_PLAN.md)
- [docs/CLAUDE_CODE_QA_PROMPTS.md](/Users/teyfikoz/github-projects/FinanceIQ/docs/CLAUDE_CODE_QA_PROMPTS.md)
- [docs/CLAUDE_CODE_MULTI_AGENT_AUDIT_PROMPT.md](/Users/teyfikoz/github-projects/FinanceIQ/docs/CLAUDE_CODE_MULTI_AGENT_AUDIT_PROMPT.md)
