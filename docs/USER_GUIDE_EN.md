# FinanceIQ User Guide (English)

This guide explains the main sections of FinanceIQ, typical workflows, and practical usage tips.

---

## 1) Overview
FinanceIQ brings global markets, ETFs/funds, technical analysis, institutional tracking, and macro indicators into one Streamlit app. The entry point is `main.py`.

**Live app**
```
https://financeiq.streamlit.app/
```

---

## 2) Screen Layout and Navigation
Top tabs provide access to all modules and sub‑features.

### Sidebar
- **Open Access Mode**: If auth is disabled, anyone can access.
- **Auto‑refresh (30s)**: Periodically reloads the page (may increase API usage).
- **System Status**:
  - Environment (production/dev)
  - Auth status
  - TradingView Bridge status
  - API keys set/missing (values are hidden)

### Data Quality Labels
You may see `Real/Cache/Fallback` badges:
- **Real**: Live data
- **Cache**: Recently cached data
- **Fallback**: Rate‑limited or unavailable source; delayed/synthetic data

---

## 3) Main Tabs and Content

### 3.1 Dashboard
Quick market snapshot:
- Major indices and daily changes
- Sector performance comparison
- Global market chart

### 3.2 Stock Research
Two primary subtabs:
- **Individual Stock**: Single‑stock analysis
  - Price, volume, key metrics
  - Candlestick + SMA/EMA + MACD + RSI
  - Fund holdings (ETF and mutual fund)
  - AI sentiment summary (if available)
- **Compare Stocks**: Multi‑stock comparison

**Tip:** For Turkish stocks, use the `.IS` suffix (e.g., `THYAO.IS`).

### 3.3 Screener
Filter‑based stock screening.

### 3.4 Strategy Lab
Backtesting and indicator analysis:
- **Backtesting**: Configure parameters and run tests
- **Indicator Lab**: IMSE + classic indicators
- **TradingView Tools**: Pine export and bridge info

### 3.5 ETFs & Funds
Global ETF and fund performance:
- Returns, trends, and comparisons
- Fund/ETF allocation views

### 3.6 Institutional
Institutional investors and major funds:
- Sovereign Wealth Funds (e.g., Norway GPF, GIC, PIF)
- Portfolio and performance summaries

### 3.7 Turkish Markets
Turkey‑focused view:
- BIST indices
- BIST 30 list
- TEFAS portfolio analysis (if enabled)

### 3.8 AI Tools (Game Changer)
Creative and analytical features:
- **Social Features**: Portfolio snapshots, public watchlists, ticker notes, leaderboard
- **Advanced Visualizations**: Calendar heatmap, sector rotation, fear&greed, 3D portfolio
- **AI Lite Tools**:
  - Monte Carlo simulation
  - Strategy backtesting
  - Auto‑annotated chart
  - News sentiment analysis
- **Export & Share**: Export outputs

### 3.9 Education
Beginner‑to‑expert learning content:
- Fundamental and technical analysis
- Sector analysis steps
- Market cycles
- ETFs and funds
- Long‑term vs short‑term vs trader perspectives
- Risk management and psychology

### 3.10 Whale Intelligence
Institutional movement and network insights:
- Whale investor tracking
- Whale correlation network
- Whale momentum tracker
- ETF‑Whale linkage
- Hedge fund radar
- Event reaction lab

### 3.11 Entropy Analysis
Market uncertainty and regime analysis.

### 3.12 Crypto Dominance
Crypto dominance trends and analysis.

### 3.13 Cycle Intelligence
Macro cycle signals and risk/return regimes.

### 3.14 Portfolio
Portfolio building and reporting:
- Add portfolios and positions
- Performance summary
- Export to Excel / CSV / HTML

### 3.15 Watchlist
Watchlists (if auth is enabled):
- Create new watchlists
- Live pricing table

### 3.16 Alerts
Price alert rules (if auth is enabled):
- Upper/lower threshold alerts

### 3.17 Privacy
Privacy settings (if auth is enabled).

---

## 4) Example Workflows

### Stock Analysis
1. Stock Research -> Individual Stock
2. Enter symbol and period
3. Analyze Stock
4. Review charts and metrics

### Strategy Test
1. Strategy Lab -> Backtesting
2. Select ticker and parameters
3. Run Backtest
4. Evaluate results

### IMSE / Indicator Lab
1. Strategy Lab -> Indicator Lab
2. Choose symbol and data source
3. Use profile tabs (Daily/Short/Medium/Long)
4. Review IMSE score, trend and confidence

### Portfolio Report
1. Portfolio tab
2. Add portfolio and transactions
3. Export Excel/CSV/HTML

---

## 5) Role‑Based Quick Tours

### 5.1 Short‑Term Trader
1. Dashboard: check daily changes and sector performance
2. Stock Research: 1d/5d technical view
3. Strategy Lab: test a short‑term setup
4. Watchlist/Alerts: monitor entries and exits

### 5.2 Long‑Term Investor
1. ETFs & Funds: compare broad and sector ETFs
2. Institutional: review large holder exposure
3. Portfolio: track performance over time
4. Export: save long‑term reports

### 5.3 Macro Analyst
1. Dashboard: index + sector overview
2. Cycle Intelligence: risk‑on / risk‑off signals
3. Entropy Analysis: uncertainty metrics
4. Crypto Dominance: sentiment proxy

---

## 6) Video Storyboards

### Video 1: General Tour (60–90s)
- Dashboard overview -> Stock Research -> Strategy Lab -> Portfolio export

### Video 2: IMSE Indicator Lab (45–60s)
- Symbol selection -> profile tabs -> IMSE signals

### Video 3: Whale Intelligence (60–90s)
- Momentum -> Correlation -> ETF‑Whale linkage -> Event reactions

### Video 4: Education Tab (60–90s)
- Fundamentals -> Indicators -> Sector analysis -> Risk & psychology

---

## 7) Screenshot Checklist

Recommended screenshots:
- Dashboard overview
- Stock Research (candlestick + RSI/MACD)
- Strategy Lab (backtest results)
- Indicator Lab (IMSE score and plots)
- ETFs & Funds performance
- Education overview
- Whale Intelligence (momentum/correlation)
- Portfolio export
- System Status (sidebar)

Tip: 1280x720 or 1440x900 works well for docs.

---

## 8) Optional Settings and Integrations
- **TradingView Bridge**: Requires Node.js + `@mathieuc/tradingview`
- **AI**: HF API token enables LLM‑based summaries
- **FRED / Alpha Vantage / FMP**: Optional macro/alternative data

---

## 9) FAQ (Extended)

**No data / N/A shown**
- Check symbol format (TR stocks require `.IS`)
- You may be rate‑limited; wait a few minutes
- Try disabling auto‑refresh

**TradingView Bridge shows "unavailable"**
- Node.js is not installed
- `@mathieuc/tradingview` package missing
- Streamlit Cloud does not allow Node installation (local only)

**Crypto Dominance is empty**
- CoinGecko rate limits or availability issues

**TEFAS module missing**
- Module import failed; check logs and `PHASE_3_4_MODULES`

**AI sections show no output**
- HF API key not configured
- Data source might be unavailable

**Real/Cache/Fallback meaning**
- Real: live data
- Cache: recent cached data
- Fallback: rate‑limited or unavailable

**Watchlist/Alerts not working**
- Requires auth; open access mode only shows info messages

**Browser console warnings**
- `content.js` warnings come from extensions
- Theme warnings are explained in `docs/DEPLOYMENT_TROUBLESHOOTING.md`

---

## 10) Tips
- Use auto‑refresh only when needed
- Avoid querying too many symbols at once
- Start with a small set of tickers and expand

---

## 11) Note
FinanceIQ is for educational purposes only. It is not financial advice.
