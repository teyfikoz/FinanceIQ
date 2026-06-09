# FundPortal Deployment Checklist

## Pre-Deploy

- [ ] `python scripts/release_guard.py` passes locally
- [ ] working tree reviewed with `git status`
- [ ] release commit SHA noted
- [ ] previous known-good commit SHA noted
- [ ] `/etc/fundportal/fundportal.env` backup available on server if secrets changed

## Deploy

- [ ] sync `main.py`
- [ ] sync `modules/`
- [ ] sync `utils/`
- [ ] sync `app` without trailing slash
- [ ] sync `scripts/` if guard or smoke scripts changed
- [ ] restart `fundportal` systemd service

## Post-Deploy Smoke

- [ ] `bash scripts/post_deploy_smoke.sh` passes
- [ ] homepage returns `200`
- [ ] homepage HTML contains `FundPortal`
- [ ] internal Streamlit health returns `ok`
- [ ] `systemctl is-active fundportal` returns `active`

## Manual Product Checks

- [ ] stock research workspace loads
- [ ] Turkish funds / TEFAS workspace loads
- [ ] ETF and fund analysis workspace loads
- [ ] scenario / cycle tools load
- [ ] fallback warnings appear correctly if upstream data is unavailable

## Rollback Readiness

- [ ] rollback SHA available
- [ ] rollback rsync commands prepared
- [ ] smoke script ready to rerun after rollback

## Secrets Hygiene

- [ ] no concrete API keys in tracked docs or config files
- [ ] server env values updated only through `/etc/fundportal/fundportal.env`
- [ ] exposed keys rotated if they were ever pasted outside the secrets manager
