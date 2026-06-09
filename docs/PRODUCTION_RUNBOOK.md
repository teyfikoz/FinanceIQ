# FundPortal Production Runbook

## Purpose

This runbook covers the operational steps that remain after the codebase is release-ready:

- pre-release validation
- production sync and restart
- post-deploy smoke checks
- rollback
- monitoring expectations
- secrets rotation discipline

## 1. Pre-Release Guard

Run the full repo guard locally before every deploy:

```bash
python scripts/release_guard.py
```

What it checks:

- `pytest -q tests/`
- silent `import main`
- Python compile sanity
- legacy branding regression
- `@st.cache_data` annotation discipline
- obvious hardcoded secret values in tracked text files

## 2. Production Deploy

Primary host:

- `https://fundpilot.techsyncanalytica.com`

Primary server:

- `46.62.164.198`

Primary paths:

- app: `/opt/fundportal/app`
- venv: `/opt/fundportal/venv`
- env file: `/etc/fundportal/fundportal.env`

Sync commands:

```bash
rsync -az main.py root@46.62.164.198:/opt/fundportal/app/main.py
rsync -az modules/ root@46.62.164.198:/opt/fundportal/app/modules/
rsync -az utils/ root@46.62.164.198:/opt/fundportal/app/utils/
rsync -az app root@46.62.164.198:/opt/fundportal/app/
rsync -az scripts/ root@46.62.164.198:/opt/fundportal/app/scripts/
rsync -az docs/ root@46.62.164.198:/opt/fundportal/app/docs/
```

Important:

- Use `app` and not `app/` for the last command.
- A trailing slash on `app/` can flatten the FastAPI package into the Streamlit app root and break imports.

Restart:

```bash
ssh -o BatchMode=yes root@46.62.164.198 \
  "cd /opt/fundportal/app && /opt/fundportal/venv/bin/python -m py_compile main.py utils/unified_api_manager.py && systemctl restart fundportal"
```

## 3. Post-Deploy Smoke

Quick smoke:

```bash
BASE_URL=https://fundpilot.techsyncanalytica.com \
SSH_TARGET=root@46.62.164.198 \
bash scripts/post_deploy_smoke.sh
```

Manual checks:

- homepage returns `200`
- homepage HTML contains `FundPortal`
- Streamlit health endpoint returns `ok`
- `systemctl is-active fundportal` returns `active`
- primary workflows open without fallback regressions

High-value manual pages:

- `/`
- stock research
- TEFAS / Turkish funds
- ETF and fund analysis
- scenario and cycle tools

## 4. Rollback

Rollback should be explicit and reversible.

Keep available before every deploy:

- current production commit SHA
- previous known-good commit SHA
- current `/etc/fundportal/fundportal.env` backup
- current nginx and systemd unit backups if infra changed

Rollback flow:

```bash
ssh -o BatchMode=yes root@46.62.164.198 "cd /opt/fundportal/app && git rev-parse HEAD"
git checkout <known-good-sha>
python scripts/release_guard.py
rsync -az main.py root@46.62.164.198:/opt/fundportal/app/main.py
rsync -az modules/ root@46.62.164.198:/opt/fundportal/app/modules/
rsync -az utils/ root@46.62.164.198:/opt/fundportal/app/utils/
rsync -az app root@46.62.164.198:/opt/fundportal/app/
ssh -o BatchMode=yes root@46.62.164.198 "systemctl restart fundportal"
```

Then rerun the smoke script.

## 5. Monitoring

Minimum production monitoring:

- process alive: `systemctl is-active fundportal`
- internal health: `http://127.0.0.1:8501/_stcore/health`
- public host reachability: `https://fundpilot.techsyncanalytica.com`
- error logs: `journalctl -u fundportal -n 200`
- fallback behavior trends for yfinance, TEFAS, and macro feeds
- cache hit/miss behavior where available in app logs

Recommended cadence:

- automated uptime ping every 1 minute
- daily log scan for repeated fallback spikes
- weekly `release_guard.py --skip-pytest` sanity pass against production branch

## 6. Secrets Rotation

Secrets must not live in tracked files or docs.

Rotate when:

- a secret was pasted into chat, email, or docs
- a server/user account changed
- an external provider reported unusual API use

Rotation workflow:

1. Create a new key in the provider console.
2. Update `/etc/fundportal/fundportal.env` on the server.
3. Restart `fundportal`.
4. Verify the dependent workflow manually.
5. Revoke the old key.

Known providers that should be treated this way:

- `FRED_API_KEY`
- `TCMB_EVDS_API_KEY`
- `FINNHUB_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `FMP_API_KEY`

Detailed checklist:

- [SECRET_ROTATION_CHECKLIST.md](/Users/teyfikoz/Projects/saas/financeiq/docs/SECRET_ROTATION_CHECKLIST.md)

## 7. CI Contract

GitHub Actions now runs the same release guard used locally.

Required green checks before production sync:

- `CI Release Guard`

Do not bypass this for routine production changes.
