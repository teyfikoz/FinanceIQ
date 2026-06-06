# FundPilot Deployment Guide

## Current Production State

- Product name: `FundPilot`
- Canonical URL: `https://fundpilot.techsyncanalytica.com`
- Runtime: `FastAPI + Jinja2`
- App entrypoint: [`app/main.py`](/Users/teyfikoz/github-projects/FinanceIQ/app/main.py)
- Server: `Hetzner` at `46.62.164.198`
- Reverse proxy: `nginx`
- Service unit: [`deployment/fundpilot.service`](/Users/teyfikoz/github-projects/FinanceIQ/deployment/fundpilot.service)
- Nginx site template: [`deployment/fundpilot.nginx.conf`](/Users/teyfikoz/github-projects/FinanceIQ/deployment/fundpilot.nginx.conf)
- Public branding and host config: [`app/core/config.py`](/Users/teyfikoz/github-projects/FinanceIQ/app/core/config.py)

## Current Architecture

```text
GoDaddy DNS
  fundpilot.techsyncanalytica.com -> 46.62.164.198

Hetzner Ubuntu
  nginx :80/:443
    -> proxy_pass 127.0.0.1:8004

Systemd
  fundpilot.service
    -> uvicorn app.main:app --host 127.0.0.1 --port 8004

App
  /opt/fundpilot/app
  /opt/fundpilot/venv
  /etc/fundpilot/fundpilot.env
```

## Runtime Paths

- App directory: `/opt/fundpilot/app`
- Virtualenv: `/opt/fundpilot/venv`
- Environment file: `/etc/fundpilot/fundpilot.env`
- App bind: `127.0.0.1:8004`
- Health endpoint: `http://127.0.0.1:8004/health`

## Local To Production Workflow

### 1. Verify locally

```bash
python3 -m py_compile app/main.py
python3 -m py_compile app/services/*.py
python3 -m py_compile app/web/routes.py
```

### 2. Sync to server

```bash
rsync -az app root@46.62.164.198:/opt/fundpilot/app/
rsync -az deployment/ root@46.62.164.198:/opt/fundpilot/app/deployment/
rsync -az requirements.txt root@46.62.164.198:/opt/fundpilot/app/requirements.txt
```

### 3. Restart service

```bash
ssh -o BatchMode=yes root@46.62.164.198 \
  "cd /opt/fundpilot/app && /opt/fundpilot/venv/bin/python -m py_compile app/main.py && systemctl restart fundpilot"
```

### 4. Validate

```bash
ssh -o BatchMode=yes root@46.62.164.198 \
  "curl -s http://127.0.0.1:8004/health"

curl -I https://fundpilot.techsyncanalytica.com
```

Expected:

- health endpoint returns JSON with `"status": "healthy"`
- public host returns `HTTP 200`
- validate the HTTPS host as the canonical production endpoint

## Current UX/Performance State

The production app is now a read-only public web surface optimized for:

- open-access dashboarding
- Turkish funds signal board
- sponsor and affiliate inventory without ad-network scripts
- no account wall, no client-side portfolio storage
- server-side rendering with progressive enhancement only

Key files:

- [`app/main.py`](/Users/teyfikoz/github-projects/FinanceIQ/app/main.py)
- [`app/web/routes.py`](/Users/teyfikoz/github-projects/FinanceIQ/app/web/routes.py)
- [`app/services/public_dashboard.py`](/Users/teyfikoz/github-projects/FinanceIQ/app/services/public_dashboard.py)
- [`app/services/tr_funds.py`](/Users/teyfikoz/github-projects/FinanceIQ/app/services/tr_funds.py)

## Nginx Setup

Baseline site config:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name fundpilot.techsyncanalytica.com;

    location / {
        proxy_pass http://127.0.0.1:8004;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60;
    }
}
```

Source file:

- [`deployment/fundpilot.nginx.conf`](/Users/teyfikoz/github-projects/FinanceIQ/deployment/fundpilot.nginx.conf)

## Systemd Setup

Service source:

- [`deployment/fundpilot.service`](/Users/teyfikoz/github-projects/FinanceIQ/deployment/fundpilot.service)

Core command:

```bash
/opt/fundpilot/venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8004 \
  --workers 2 \
  --proxy-headers \
  --forwarded-allow-ips=*
```

## DNS

Required record:

```text
Type: A
Name: fundpilot
Value: 46.62.164.198
```

## Legacy Streamlit Status

The old Streamlit app is legacy code and not the production runtime anymore.

Archived entrypoints live under:

- [`archive/retired_streamlit_runtime/README.md`](/Users/teyfikoz/github-projects/FinanceIQ/archive/retired_streamlit_runtime/README.md)

## Release Checklist

- code compiles locally
- changed modules synced to `/opt/fundpilot/app`
- `fundpilot.service` restarted
- local health check returns healthy JSON
- `https://fundpilot.techsyncanalytica.com` returns `200`
- no production hostname regressions in branding or QR/export URLs

## Known Follow-Up Work

- clean up remaining package-level Streamlit helper modules that are no longer needed for reference
- add structured uptime monitoring and sponsor slot analytics that do not require third-party trackers
