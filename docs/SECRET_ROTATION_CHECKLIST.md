# FundPortal Secret Rotation Checklist

## When To Rotate

Rotate immediately if any secret:

- was pasted into chat, email, or issue threads
- appeared in tracked docs or config files
- was shared in screenshots or terminal recordings
- may still exist in old shell history or deployment notes

## Current Secret Inventory

Application and provider keys referenced by the active FundPortal runtime:

- `SECRET_KEY`
- `FRED_API_KEY`
- `TCMB_EVDS_API_KEY`
- `FINNHUB_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `FMP_API_KEY`
- `POLYGON_API_KEY`
- `TRADINGECONOMICS_KEY`
- `NEWSAPI_KEY`
- `COINGECKO_API_KEY`
- `TWELVEDATA_API_KEY`
- `BINANCE_API_KEY`
- `BINANCE_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `SMTP_PASSWORD`

Primary production file:

- `/etc/fundportal/fundportal.env`

Template in repo:

- [.env.example](/Users/teyfikoz/Projects/saas/financeiq/.env.example)

## Recommended Rotation Order

Priority 1:

- `FRED_API_KEY`
- `TCMB_EVDS_API_KEY`

Priority 2:

- `FINNHUB_API_KEY`
- `ALPHA_VANTAGE_API_KEY`
- `FMP_API_KEY`
- `POLYGON_API_KEY`
- `TRADINGECONOMICS_KEY`

Priority 3:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `SMTP_PASSWORD`
- any optional provider keys currently enabled in production

## Rotation Procedure

For each provider:

1. Create a new key in the provider console.
2. Do not delete the old key yet.
3. SSH into production and back up the env file:

```bash
ssh -o BatchMode=yes root@46.62.164.198 \
  "cp /etc/fundportal/fundportal.env /etc/fundportal/fundportal.env.bak.$(date +%Y%m%d%H%M%S)"
```

4. Update the specific key in `/etc/fundportal/fundportal.env`.
5. Restart the service:

```bash
ssh -o BatchMode=yes root@46.62.164.198 "systemctl restart fundportal"
```

6. Run smoke:

```bash
BASE_URL=https://fundpilot.techsyncanalytica.com \
SSH_TARGET=root@46.62.164.198 \
bash scripts/post_deploy_smoke.sh
```

7. Verify the related workflow manually.
8. Revoke the old key in the provider console only after validation passes.

## Provider-Specific Checks

After rotating `FRED_API_KEY`:

- open a macro-heavy workspace
- confirm FRED-backed cards load

After rotating `TCMB_EVDS_API_KEY`:

- verify TCMB reserve / EVDS cards load

After rotating `ALPHA_VANTAGE_API_KEY` or `FMP_API_KEY`:

- verify stock fundamentals or backup data paths still work

After rotating `FINNHUB_API_KEY` or `NEWSAPI_KEY`:

- verify news/sentiment surfaces still populate

After rotating `POSTGRES_PASSWORD`:

- update the database user password first
- then update `/etc/fundportal/fundportal.env`
- then restart FundPortal

After rotating `SECRET_KEY`:

- assume any sessions/tokens signed with the previous key become invalid

## Post-Rotation Validation

Run:

```bash
python scripts/release_guard.py --skip-pytest
BASE_URL=https://fundpilot.techsyncanalytica.com \
SSH_TARGET=root@46.62.164.198 \
bash scripts/post_deploy_smoke.sh
```

Then manually verify:

- homepage
- stock research
- Turkish funds / TEFAS
- macro dashboard
- one provider-backed view for every rotated key

## Do Not Do

- do not store real secrets in repo docs
- do not commit `.env`
- do not delete the old key before smoke passes
- do not rotate multiple unrelated infra passwords without a rollback path
