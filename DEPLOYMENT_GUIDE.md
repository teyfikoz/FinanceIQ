# FundPortal Deployment Guide

## Current Production State

- Product name: `FundPortal`
- Canonical URL: `https://fundpilot.techsyncanalytica.com`
- Runtime: `Streamlit`
- App entrypoint: [`main.py`](/Users/teyfikoz/github-projects/FundPortal/main.py)
- Server: `Hetzner` at `46.62.164.198`
- Reverse proxy: `nginx`
- Service unit: [`deployment/fundportal.service`](/Users/teyfikoz/github-projects/FundPortal/deployment/fundportal.service)
- Nginx site template: [`deployment/fundportal.nginx.conf`](/Users/teyfikoz/github-projects/FundPortal/deployment/fundportal.nginx.conf)
- Public branding and host config: [`utils/app_config.py`](/Users/teyfikoz/github-projects/FundPortal/utils/app_config.py)

## Current Architecture

```text
GoDaddy DNS
  fundpilot.techsyncanalytica.com -> 46.62.164.198

Hetzner Ubuntu
  nginx :80/:443
    -> proxy_pass 127.0.0.1:8501

Systemd
  fundportal.service
    -> streamlit run /opt/fundportal/app/main.py

App
  /opt/fundportal/app
  /opt/fundportal/venv
  /etc/fundportal/fundportal.env
```

## Runtime Paths

- App directory: `/opt/fundportal/app`
- Virtualenv: `/opt/fundportal/venv`
- Environment file: `/etc/fundportal/fundportal.env`
- Streamlit bind: `127.0.0.1:8501`
- Health endpoint: `http://127.0.0.1:8501/_stcore/health`

## Local To Production Workflow

### 1. Verify locally

```bash
python scripts/release_guard.py
```

### 2. Sync to server

```bash
rsync -az main.py root@46.62.164.198:/opt/fundportal/app/main.py
rsync -az modules/ root@46.62.164.198:/opt/fundportal/app/modules/
rsync -az utils/ root@46.62.164.198:/opt/fundportal/app/utils/
rsync -az app root@46.62.164.198:/opt/fundportal/app/
```

> **CRITICAL — `app` vs `app/`**
> Use `app` (no trailing slash). `app/` would expand the directory contents
> directly into `/opt/fundportal/app/`, overwriting the Streamlit `main.py`
> with `app/main.py` (FastAPI) and crashing the service with
> `ModuleNotFoundError: No module named 'fastapi'`.

### 3. Restart service

```bash
ssh -o BatchMode=yes root@46.62.164.198 \
  "cd /opt/fundportal/app && /opt/fundportal/venv/bin/python -m py_compile main.py && systemctl restart fundportal"
```

### 4. Validate

```bash
ssh -o BatchMode=yes root@46.62.164.198 \
  "curl -s http://127.0.0.1:8501/_stcore/health"

curl -I https://fundpilot.techsyncanalytica.com
```

Expected:

- health endpoint returns `ok`
- public host returns `HTTP 200`
- validate the HTTPS host as the canonical production endpoint

### 5. Run the smoke script

```bash
BASE_URL=https://fundpilot.techsyncanalytica.com \
SSH_TARGET=root@46.62.164.198 \
bash scripts/post_deploy_smoke.sh
```

## Current UX/Performance State

The production app has already been refactored away from the old multi-tab heavy render model.

Implemented:

- grouped primary navigation
- single active workspace rendering
- lazy loading for heavier modules
- performance mode toggle in sidebar
- session-persistent results for expensive tools
- reduced hidden Plotly render overhead
- persisted result payloads for rerun-heavy views such as TEFAS, ETF Tracker, Settlement Analysis, Screener, Backtest, and Sankey flows

Key files:

- [`main.py`](/Users/teyfikoz/github-projects/FundPortal/main.py)
- [`modules/tefas_portfolio_analysis_ui.py`](/Users/teyfikoz/github-projects/FundPortal/modules/tefas_portfolio_analysis_ui.py)
- [`modules/cycle_analysis_ui.py`](/Users/teyfikoz/github-projects/FundPortal/modules/cycle_analysis_ui.py)
- [`modules/portfolio_health_ui.py`](/Users/teyfikoz/github-projects/FundPortal/modules/portfolio_health_ui.py)
- [`modules/scenario_sandbox_ui.py`](/Users/teyfikoz/github-projects/FundPortal/modules/scenario_sandbox_ui.py)
- [`modules/etf_weight_tracker_ui.py`](/Users/teyfikoz/github-projects/FundPortal/modules/etf_weight_tracker_ui.py)

## Nginx Setup

Baseline site config:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name fundpilot.techsyncanalytica.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

Source file:

- [`deployment/fundportal.nginx.conf`](/Users/teyfikoz/github-projects/FundPortal/deployment/fundportal.nginx.conf)

## Systemd Setup

Service source:

- [`deployment/fundportal.service`](/Users/teyfikoz/github-projects/FundPortal/deployment/fundportal.service)

Core command:

```bash
/opt/fundportal/venv/bin/streamlit run /opt/fundportal/app/main.py \
  --server.port=8501 \
  --server.address=127.0.0.1 \
  --server.headless=true \
  --browser.gatherUsageStats=false
```

## DNS

Required record:

```text
Type: A
Name: fundportal
Value: 46.62.164.198
```

## Streamlit Cloud Status

`Streamlit Cloud` is no longer the primary production deployment target.

Legacy public URL:

- `https://financeiq.streamlit.app/`

Current policy:

- primary production host is Hetzner + nginx + systemd
- Streamlit Cloud is optional fallback/demo infrastructure only

See:

- [`STREAMLIT_CLOUD_DEPLOYMENT.md`](/Users/teyfikoz/github-projects/FundPortal/STREAMLIT_CLOUD_DEPLOYMENT.md)

## Release Checklist

- `scripts/release_guard.py` passes locally
- changed modules synced to `/opt/fundportal/app`
- `fundportal.service` restarted
- local health check returns `ok`
- `https://fundpilot.techsyncanalytica.com` returns `200`
- no production hostname regressions in branding or QR/export URLs

## Operational Docs

- [DEPLOYMENT_CHECKLIST.md](/Users/teyfikoz/github-projects/FundPortal/DEPLOYMENT_CHECKLIST.md)
- [docs/PRODUCTION_RUNBOOK.md](/Users/teyfikoz/github-projects/FundPortal/docs/PRODUCTION_RUNBOOK.md)

## Known Follow-Up Work

- convert remaining standalone helper/demo renderers to the same production navigation/runtime standard
- add compact chart mode for selected heavy Plotly surfaces
- expand structured observability beyond current logs and health checks
