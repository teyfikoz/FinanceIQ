# Retired Streamlit Runtime

This folder contains preserved Streamlit entrypoints that are no longer part of the active
FundPilot production runtime.

Current production stack:

- `app.main` on FastAPI
- server-rendered Jinja templates under `app/web`
- nginx + systemd deployment artifacts under `deployment/`

Why these files were archived:

- the public site no longer depends on Streamlit session state
- production startup no longer requires the `streamlit` package
- direct sponsor and affiliate monetization is easier to control on a server-rendered stack

Do not wire new production features into these archived files.
