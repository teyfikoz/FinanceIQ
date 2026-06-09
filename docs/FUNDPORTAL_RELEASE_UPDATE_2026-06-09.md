# FundPortal Release Update — 2026-06-09

## Scope

This update closes the last production-hardening and operations gaps for FundPortal.

## What Changed

### Production guardrail

- Added repo-level release guard: `scripts/release_guard.py`
- Guard enforces:
  - `pytest -q tests/`
  - silent `import main`
  - Python compile sanity
  - legacy branding regression checks
  - `@st.cache_data` intent annotation checks
  - obvious hardcoded secret detection in tracked text files

### CI

- Replaced the old workflow with `.github/workflows/ci.yml`
- CI now runs the same release guard used locally

### Deploy operations

- Added post-deploy smoke script: `scripts/post_deploy_smoke.sh`
- Added production runbook: `docs/PRODUCTION_RUNBOOK.md`
- Added deploy checklist: `DEPLOYMENT_CHECKLIST.md`
- Added secret rotation checklist: `docs/SECRET_ROTATION_CHECKLIST.md`
- Added `.env.example` for production-safe environment variable templating

### Secret hygiene

- Removed real API key examples from tracked documentation
- Normalized placeholder values for provider keys and app/database secrets
- Tightened guard checks for secret-like values in docs and config files

### Runtime config

- Updated `app/core/config.py` defaults to production-safe placeholders
- Updated packaging metadata and pytest labeling to FundPortal naming

### Nginx / Hetzner production fix

- Fixed `fundpilot.techsyncanalytica.com` HTTPS vhost
- Added explicit `443 ssl` server block with the correct Let's Encrypt certificate
- Reloaded nginx successfully
- Verified:
  - correct certificate for `fundpilot.techsyncanalytica.com`
  - `HTTP/2 200` on the public host
  - active `fundportal` systemd service
  - passing post-deploy smoke script

## Validation

- `python3 scripts/release_guard.py` passes locally
- `pytest -q tests/` passes with `123 passed`
- production smoke passes on Hetzner

## Remaining Manual Step

Secrets should still be rotated in provider consoles because some keys were shared outside the normal secret-management path.

Priority order:

1. `FRED_API_KEY`
2. `TCMB_EVDS_API_KEY`
3. active market/news provider keys
4. optional integrations if enabled in production
