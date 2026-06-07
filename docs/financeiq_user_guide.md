# FundPortal User Guide (Comprehensive)

## 1) Quick Start
**Local:**
```bash
cd /Users/teyfikoz/github-projects/FundPortal
pip install -r requirements.txt
python3 -m streamlit run main.py
```
Open: http://localhost:8501

**Cloud:**
Use Streamlit Cloud and set secrets in the app settings (see deployment guide).

## 2) Navigation Overview
FundPortal is organized by feature tabs:

- **🎯 Dashboard** – global market summary, KPIs, snapshots
- **🔍 Stock Research** – company overview, fundamentals, news, indicators
- **📡 Screener** – filter instruments by metrics and technicals
- **🧪 Strategy Lab** – indicators, backtesting, signals
- **📊 ETFs & Funds** – ETF profiles, holdings, sector/country exposure
- **🏛️ Institutional** – 13F/ownership, flow analytics
- **🇹🇷 Turkish Markets** – TEFAS funds, KAP‑style insights
- **🤖 AI Tools** – Monte Carlo, backtesting, chart annotation, news sentiment
- **🎓 Education** – macro context, cycles, global snapshot
- **🐋 Whale Intelligence** – large investor and flow signals
- **🎲 Entropy Analysis** – distribution/entropy-based regime hints
- **📊 Crypto Dominance** – BTC/alt dominance and cycle signals
- **🌀 Cycle Intelligence** – multi‑indicator cycle dashboards
- **💼 Portfolio** – positions, allocations, risk
- **👁️ Watchlist** – saved tickers, quick tracking
- **🔔 Alerts** – price alerts and monitoring
- **🔒 Privacy** – privacy‑first UI controls

## 3) Core Workflows
### 3.1 Stock Research
1. Enter a ticker (e.g., `AAPL`).
2. Review overview, valuation, and technicals.
3. Use News/Sentiment to gauge current narrative.

**Tip:** For BIST symbols use the `.IS` suffix (e.g., `ASELS.IS`).

### 3.2 Strategy Lab
- Test indicator combinations (SMA/RSI/MACD).
- Use Backtesting for different time horizons.
- Interpret signals alongside market regime tools.

### 3.3 Macro Snapshot (Education)
- Provides country‑level macro context using FRED + Data360.
- Useful for portfolio tilts and regime framing.

### 3.4 ETFs & Funds
- Explore ETF holdings and sector/country exposure.
- Use for diversification audits.

### 3.5 Alerts & Watchlist
- Add tickers to watchlist.
- Set alerts for price thresholds.

## 4) Data Sources & Fallbacks
FundPortal uses a multi‑source data layer:
- **Primary:** yfinance
- **Fallbacks:** Finnhub → Alpha Vantage → TwelveData (where available)

If data is missing:
- Ensure API keys are set.
- Try alternative symbols or suffixes.
- Expect some local markets to return fewer news items.

## 5) API Keys (Optional but Recommended)
Set in `.env` (local) or Streamlit secrets (cloud):

```toml
[api_keys]
FRED_API_KEY = "..."
FINNHUB_API_KEY = "..."
ALPHA_VANTAGE_API_KEY = "..."
TWELVEDATA_API_KEY = "..."
DATA360_API_BASE = "https://extdataportal.worldbank.org/api/data360"
```

## 6) Troubleshooting
**No news appears:**
- yfinance may return no news for some symbols
- Add API keys (Finnhub/NewsAPI)
- Try another ticker like `AAPL`

**Macro snapshot empty:**
- Add `FRED_API_KEY` and `DATA360_API_BASE`

**Slow response:**
- First load can be slow due to model/data warm‑up
- Reduce watchlist size and disable auto‑refresh if needed

## 7) Security & Secrets
- Never commit API keys to git.
- Store keys in Streamlit secrets or environment variables.
- Rotate exposed keys immediately.

## 8) FAQ
**Q: Is the UI multilingual?**
A: No. The app is English‑only by design.

**Q: Can I run without API keys?**
A: Yes. Core features still work via free sources, but coverage is reduced.

**Q: Why are Turkish markets missing news?**
A: Most free sources have limited coverage. Use paid APIs for better coverage.

---

If you want a deeper operator guide (observability, scaling, CI/CD), say the word.
