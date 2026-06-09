# FundPilot Deployment & Product Guide

## Identity

- Public product name: `FundPilot`
- Canonical host: `https://fundpilot.techsyncanalytica.com`
- Repository slug: legacy GitHub repo name
- Runtime: `Streamlit`
- Current production host: `Hetzner`

## What This File Is

This file is kept for backward compatibility because older internal notes referenced `financeiq_deployement_guide.md`.  
The live product is `FundPilot`, not the old internal repo alias and not `FundPortal`.

## Current Production Topology

```text
fundpilot.techsyncanalytica.com
  -> nginx :80/:443
  -> proxy_pass 127.0.0.1:8501
  -> streamlit run /opt/fundportal/app/main.py
```

## Key Paths

- App: `/opt/fundportal/app`
- Service: `/etc/systemd/system/fundportal.service`
- Env: `/etc/fundportal/fundportal.env`
- Health: `http://127.0.0.1:8501/_stcore/health`

## Core Product Surfaces

- `Market Desk`
- `Research`
- `Workspace`
- `Turkish Markets / TEFAS`
- `Institutional / 13F`
- `Entropy / cycle / macro layers`

## Important June 2026 Production Notes

- product brand corrected back to `FundPilot`
- canonical host verified as `fundpilot.techsyncanalytica.com`
- sidebar navigation bug fixed:
  - `Research` now opens `?view=stock-research`
  - `Workspace` now opens `?view=portfolio`
- nginx HTTPS vhost aligned with the correct certificate
- post-deploy smoke passes on Hetzner

## Deploy Flow

1. Run local guard:

```bash
cd /Users/teyfikoz/Projects/saas/financeiq
python3 scripts/release_guard.py
```

2. Sync changed files:

```bash
rsync -az main.py root@46.62.164.198:/opt/fundportal/app/main.py
rsync -az utils/ root@46.62.164.198:/opt/fundportal/app/utils/
rsync -az app root@46.62.164.198:/opt/fundportal/app/
```

3. Restart:

```bash
ssh -o BatchMode=yes root@46.62.164.198 "systemctl restart fundportal"
```

4. Smoke:

```bash
ssh -o BatchMode=yes root@46.62.164.198 \
  "cd /opt/fundportal/app && bash scripts/post_deploy_smoke.sh"
```

## Related Docs

- [DEPLOYMENT_GUIDE.md](/Users/teyfikoz/Projects/saas/financeiq/DEPLOYMENT_GUIDE.md)
- [DEPLOYMENT_CHECKLIST.md](/Users/teyfikoz/Projects/saas/financeiq/DEPLOYMENT_CHECKLIST.md)
- [PRODUCTION_RUNBOOK.md](/Users/teyfikoz/Projects/saas/financeiq/docs/PRODUCTION_RUNBOOK.md)
- [SECRET_ROTATION_CHECKLIST.md](/Users/teyfikoz/Projects/saas/financeiq/docs/SECRET_ROTATION_CHECKLIST.md)
