# FundPortal

FundPortal is the live financial research and fund intelligence application currently deployed at `https://fundpilot.techsyncanalytica.com`.

The product started as `FundPortal`, but the active production identity, host, and deployment flow are now centered on `FundPortal`.

## Current Production State

- Canonical URL: `https://fundpilot.techsyncanalytica.com`
- Runtime: `Streamlit`
- Server: `Hetzner` at `46.62.164.198`
- Reverse proxy: `nginx`
- Service: `fundportal.service`
- App path: `/opt/fundportal/app`
- Python env: `/opt/fundportal/venv`

## Product Scope

FundPortal combines multiple financial workflows inside one production app shell:

- market dashboard and macro snapshot
- Turkish markets and TEFAS fund workflows
- comprehensive stock research
- ETF and fund analysis
- institutional and sovereign fund views
- scenario, allocation, and cycle analysis
- AI-assisted research helpers

## Current UX/Performance Model

The production runtime has been refactored away from the old heavy multi-tab model.

Implemented in the live app:

- grouped primary navigation
- single active workspace rendering
- lazy loading for heavier modules
- sidebar `Performance Mode`
- session-persistent results for expensive analysis views
- reduced hidden Plotly render overhead

Core runtime files:

- [main.py](/Users/teyfikoz/github-projects/FundPortal/main.py)
- [modules/tr_funds_launchpad_ui.py](/Users/teyfikoz/github-projects/FundPortal/modules/tr_funds_launchpad_ui.py)
- [modules/tefas_portfolio_analysis_ui.py](/Users/teyfikoz/github-projects/FundPortal/modules/tefas_portfolio_analysis_ui.py)
- [modules/cycle_analysis_ui.py](/Users/teyfikoz/github-projects/FundPortal/modules/cycle_analysis_ui.py)
- [modules/portfolio_health_ui.py](/Users/teyfikoz/github-projects/FundPortal/modules/portfolio_health_ui.py)
- [modules/scenario_sandbox_ui.py](/Users/teyfikoz/github-projects/FundPortal/modules/scenario_sandbox_ui.py)
- [modules/etf_weight_tracker_ui.py](/Users/teyfikoz/github-projects/FundPortal/modules/etf_weight_tracker_ui.py)

## Local Development

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run main.py --server.port 8501
```

### 3. Open locally

```text
http://localhost:8501
```

## Production Deployment

Primary deployment documentation:

- [DEPLOYMENT_GUIDE.md](/Users/teyfikoz/github-projects/FundPortal/DEPLOYMENT_GUIDE.md)

Deployment assets:

- [deployment/fundportal.service](/Users/teyfikoz/github-projects/FundPortal/deployment/fundportal.service)
- [deployment/fundportal.nginx.conf](/Users/teyfikoz/github-projects/FundPortal/deployment/fundportal.nginx.conf)

## Legacy Streamlit Cloud Status

`Streamlit Cloud` is no longer the primary production target.

Legacy host:

- `https://financeiq.streamlit.app/`

Current policy:

- production runs on Hetzner + nginx + systemd
- Streamlit Cloud is optional fallback/demo infrastructure only

See:

- [STREAMLIT_CLOUD_DEPLOYMENT.md](/Users/teyfikoz/github-projects/FundPortal/STREAMLIT_CLOUD_DEPLOYMENT.md)

## Design And QA Docs

- [DESIGN.md](/Users/teyfikoz/github-projects/FundPortal/DESIGN.md)
- [docs/FUNDPILOT_UI_REDESIGN_PLAN.md](/Users/teyfikoz/github-projects/FundPortal/docs/FUNDPILOT_UI_REDESIGN_PLAN.md)
- [docs/FUNDPILOT_FRONTEND_MIGRATION_PLAN.md](/Users/teyfikoz/github-projects/FundPortal/docs/FUNDPILOT_FRONTEND_MIGRATION_PLAN.md)
- [docs/CLAUDE_CODE_QA_PROMPTS.md](/Users/teyfikoz/github-projects/FundPortal/docs/CLAUDE_CODE_QA_PROMPTS.md)
- [docs/CLAUDE_CODE_MULTI_AGENT_AUDIT_PROMPT.md](/Users/teyfikoz/github-projects/FundPortal/docs/CLAUDE_CODE_MULTI_AGENT_AUDIT_PROMPT.md)
