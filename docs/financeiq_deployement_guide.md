# FinanceIQ Deployment & Product Guide (Production)

## Executive Summary
FinanceIQ is a unified Streamlit platform for multi‑market financial analysis, institutional activity insights, technical analysis, strategy backtesting, and macro context. The application runs from a single entrypoint (`main.py`) and is modular, production‑ready, and extensible.

**Live app:**
```
https://financeiq.streamlit.app/
```

## 1) What is FinanceIQ?
A professional-grade dashboard that aggregates global markets, ETFs/funds, crypto, Turkish markets, and institutional analytics into one interface.

## 2) What does it do?
- Multi‑market tracking (US, Europe, Turkey)
- Institutional/whale activity and fund flow analytics
- Technical analysis + backtesting
- Strategy lab and quantitative tools
- Macro context (FRED + Data360)
- Portfolio, watchlist, alerts

## 3) Core Features (Summary)
**Main tabs (main.py):**
- 🎯 Dashboard
- 🔍 Stock Research
- 📡 Screener
- 🧪 Strategy Lab
- 📊 ETFs & Funds
- 🏛️ Institutional
- 🇹🇷 Turkish Markets
- 🤖 AI Tools
- 🎓 Education
- 🐋 Whale Intelligence
- 🎲 Entropy Analysis
- 📊 Crypto Dominance
- 🌀 Cycle Intelligence
- 💼 Portfolio
- 👁️ Watchlist
- 🔔 Alerts
- 🔒 Privacy

**Recent updates (2026‑01‑28):**
- **Global Macro Snapshot** (FRED + Data360) in Education
- **News & Sentiment pipeline** (Finnhub → Alpha Vantage → yfinance)
- **TwelveData fallback** for intraday/FX
- **English‑only UI** (TR/EN toggle removed)
- **HF Insights removed** from the app

## 4) Architecture & Entrypoints
- **Entrypoint:** `main.py`
- **UI/Analytics:** `app/analytics/*`, `app/ui/*`
- **Data layer:** `utils/*`, `app/data_collectors/*`, `api/*`
- **Market data fallback:** `utils/market_data_fetcher.py`
- **DB/Auth:** `utils/database.py`, `utils/authentication.py`

**Auth control:**
- Default: direct access (no login)
- Enable with ENV: `FINANCEIQ_REQUIRE_AUTH=true`

## 5) System Architecture (Mermaid)
```mermaid
flowchart TD
    A[main.py] --> B[UI Tabs]
    B --> C[Analytics Modules]
    B --> D[Strategy Lab]
    B --> E[Whale Intelligence]

    C --> F[Market Data Fetcher]
    F --> G[yfinance]
    F --> H[Fallback/Synthetic]
    F --> I[TradingView Bridge (optional)]

    D --> J[Indicator Lab]
    J --> K[IMSE Engine]
    J --> L[Core Indicators]

    E --> M[Fund Flow Radar / TEFAS]
    E --> N[Institutional Events]

    B --> O[Education]
    O --> P[FRED]
    O --> Q[Data360]
```

## 6) Repos & References
**Main repo:**
```
https://github.com/teyfikoz/FinanceIQ
```

**Optional data bridge:**
```
https://github.com/Mathieu2301/TradingView-API
```

## 7) Data Sources & APIs
**Primary/free sources:**
- Yahoo Finance (yfinance)
- TEFAS (Turkish funds)
- KAP VYK API (Turkey disclosures)

**Optional / API‑key sources:**
- FRED (macro data)
- Alpha Vantage
- Financial Modeling Prep (FMP)
- Finnhub
- TwelveData (intraday/FX)
- Polygon
- CoinGecko (Pro optional)
- Binance
- NewsAPI
- World Bank / Data360
- TradingEconomics

## 8) Local Setup
```bash
cd /Users/teyfikoz/github-projects/FinanceIQ
pip install -r requirements.txt
python3 -m streamlit run main.py
```

App URL: http://localhost:8501

**Note:** `.env` is auto‑loaded if present (local convenience only).

## 9) Environment Variables / Secrets
The app runs without keys; these are optional:

```bash
# Macro / markets
FRED_API_KEY=...
ALPHA_VANTAGE_API_KEY=...
FMP_API_KEY=...
FINNHUB_API_KEY=...
TWELVEDATA_API_KEY=...
DATA360_API_BASE=https://extdataportal.worldbank.org/api/data360
POLYGON_API_KEY=...
NEWSAPI_KEY=...
COINGECKO_API_KEY=...
BINANCE_API_KEY=...
BINANCE_SECRET_KEY=...

# TradingView bridge
TRADINGVIEW_SESSION=...
TRADINGVIEW_SIGNATURE=...

# Auth / env
FINANCEIQ_ENV=production
FINANCEIQ_REQUIRE_AUTH=true
FINANCEIQ_DIRECT_ACCESS=false
```

## 10) Streamlit Cloud Deploy
- App URL: https://financeiq.streamlit.app/
- Main file: `main.py`
- Python: 3.10 / 3.11 recommended

**Streamlit Secrets example:**
```toml
[api_keys]
FRED_API_KEY = "..."
ALPHA_VANTAGE_API_KEY = "..."
FMP_API_KEY = "..."
FINNHUB_API_KEY = "..."
TWELVEDATA_API_KEY = "..."
DATA360_API_BASE = "https://extdataportal.worldbank.org/api/data360"

[app]
FINANCEIQ_ENV = "production"
FINANCEIQ_REQUIRE_AUTH = false
FINANCEIQ_DIRECT_ACCESS = true
FINANCEIQ_CREATE_DEMO_USER = false
```

## 11) Custom Domain + DNS + SSL (Streamlit Cloud)
1. Streamlit Cloud → App → **Settings** → **Custom Domain**
2. Enter domain (e.g., `app.financeiq.com`)
3. DNS records:
   - CNAME: `app.financeiq.com` → Streamlit target
4. SSL is automatic after DNS verification

## 12) Docker (Optional)
Repo includes `Dockerfile` and `docker-compose.yml`. Use if you want containerized deployment.
