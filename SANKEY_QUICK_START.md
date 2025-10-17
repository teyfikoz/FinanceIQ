# Sankey Charts Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd global_liquidity_dashboard
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)

```bash
# Copy example to .env
cp .env.example .env

# Edit .env and add your keys (optional for basic functionality)
nano .env
```

**Note**: The system works without API keys using yfinance as fallback!

### 3. Launch Sankey Pages

#### Option A: Using the Launcher Script

```bash
chmod +x run_sankey.sh
./run_sankey.sh
```

Then select from menu:
- `1` - Income Statement Sankey
- `2` - Fund Holdings Sankey
- `3` - Macro Liquidity Sankey

#### Option B: Direct Launch

```bash
# Income Statement Sankey
streamlit run dashboard/pages/sankey_income.py

# Fund Holdings Sankey
streamlit run dashboard/pages/sankey_funds.py

# Macro Liquidity Sankey
streamlit run dashboard/pages/sankey_macro.py
```

## 📊 Usage Examples

### Income Statement Sankey

1. Open: `streamlit run dashboard/pages/sankey_income.py`
2. Enter ticker: `AAPL` (or MSFT, GOOGL, TSLA, etc.)
3. Select period: Annual or Quarterly
4. View flow from Revenue → Net Income
5. Check KPIs: Margins, YoY changes
6. Export: Download as PNG, HTML, or CSV

**Sample Tickers**: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, JPM, WMT

### Fund Holdings Sankey

1. Open: `streamlit run dashboard/pages/sankey_funds.py`

**Tab 1: Fund → Stocks**
- Enter fund: `SPY` (or QQQ, VOO, ARKK)
- Set top N: `10` holdings
- View holdings breakdown
- Check concentration metrics

**Tab 2: Stock → Funds**
- Enter stock: `AAPL`
- Select funds: SPY, QQQ, VOO, ARKK
- View which funds hold the stock
- Compare weights across funds

**Sample Funds**: SPY, QQQ, VOO, ARKK, VT, IWM, VTI, VUG

### Macro Liquidity Sankey

1. Open: `streamlit run dashboard/pages/sankey_macro.py`
2. Configure liquidity sources:
   - M2 Money Supply: 40
   - CB Balance Sheets: 35
   - Global Liquidity Index: 25
3. Set asset allocations:
   - Equities: 50%
   - Bitcoin: 30%
   - Gold: 20%
4. View normalized flows
5. Read insights and educational content

## 🧪 Run Tests

```bash
# All Sankey tests
pytest tests/test_sankey_transform.py tests/test_fund_holdings_sankey.py -v

# Specific test file
pytest tests/test_sankey_transform.py -v

# With coverage
pytest tests/ --cov=app.analytics --cov=dashboard.components -v
```

## ✨ Bonus Features

### 1. Export Charts

Every page includes export options:
- **PNG**: High-resolution image (requires `kaleido`)
- **HTML**: Interactive chart
- **CSV**: Underlying data

```bash
# Install kaleido for PNG export
pip install kaleido
```

### 2. Multi-Language Support (i18n)

```python
from dashboard.components.i18n import set_language, t

# Switch to Turkish
set_language('tr')

# Use translations
title = t('income_sankey_title')  # "Gelir Tablosu Sankey"
```

Available languages: `en` (English), `tr` (Turkish)

### 3. Comparison Mode

Compare multiple companies side-by-side:

```python
from dashboard.components.comparison import compare_income_statements

data_list = [
    {'ticker': 'AAPL', 'meta': sankey_meta_aapl},
    {'ticker': 'MSFT', 'meta': sankey_meta_msft},
]

fig = compare_income_statements(data_list, metric='net_margin')
```

### 4. FY vs LTM Comparison

```python
from dashboard.components.comparison import create_fy_vs_ltm_comparison

fig = create_fy_vs_ltm_comparison(fy_data, ltm_data, 'AAPL')
```

## 🔧 Configuration

### Cache Settings

```python
# In-memory cache (default)
# No configuration needed

# Redis cache (optional)
# .env file:
REDIS_URL=redis://localhost:6379/0
```

### API Keys (Optional)

```bash
# .env file
FMP_API_KEY=your_key_here              # 250 calls/day (free)
ALPHA_VANTAGE_API_KEY=your_key_here    # 25 calls/day (free)
```

**Fallback chain**: FMP → Alpha Vantage → yfinance → Error

### Performance Tuning

```python
# Adjust cache TTL in data collectors
@st.cache_data(ttl=3600)  # 1 hour
def load_data():
    pass

# Clear cache manually
st.cache_data.clear()
```

## 📁 File Structure

```
global_liquidity_dashboard/
├── app/
│   ├── analytics/
│   │   ├── sankey_transform.py      # ✅ Transform data → Sankey
│   │   └── sanity_checks.py         # ✅ Validate data
│   ├── data_collectors/
│   │   ├── fundamentals_collector.py # ✅ Fetch income statements
│   │   └── holdings_collector_ext.py # ✅ Fetch fund holdings
│   └── services/
│       └── cache.py                  # ✅ Caching (Redis/in-memory)
├── dashboard/
│   ├── components/
│   │   ├── charts_sankey.py         # ✅ Plotly Sankey builders
│   │   ├── kpis.py                  # ✅ KPI components
│   │   ├── export_utils.py          # ✅ Export functionality
│   │   ├── i18n.py                  # ✅ Translations
│   │   └── comparison.py            # ✅ Comparison tools
│   └── pages/
│       ├── sankey_income.py         # ✅ Income page
│       ├── sankey_funds.py          # ✅ Holdings page
│       └── sankey_macro.py          # ✅ Macro page
├── tests/
│   ├── fixtures/
│   │   └── financials_apple_fy22.json
│   ├── test_sankey_transform.py     # ✅ Unit tests
│   └── test_fund_holdings_sankey.py # ✅ Integration tests
├── run_sankey.sh                    # ✅ Launch script
├── SANKEY_MODULE_README.md          # ✅ Full documentation
└── SANKEY_QUICK_START.md            # ✅ This file
```

## 🐛 Troubleshooting

### "No financial data found"
- **Solution**: Check ticker symbol, try different period, or verify API keys

### "Redis connection failed"
- **Solution**: System auto-fallbacks to in-memory cache (no action needed)

### "Holdings data not available"
- **Solution**: Try popular ETFs (SPY, QQQ, VOO) or use simulated data

### "PNG export failed"
- **Solution**: Install kaleido: `pip install kaleido`

### Rate limit exceeded
- **Solution**: Wait or use cache (data is cached for 6-12 hours)

## 🎯 Common Use Cases

### 1. Analyze Company Profitability
```
Page: Income Statement Sankey
Ticker: AAPL
Action: Compare gross/operating/net margins
```

### 2. Find Top ETF Holdings
```
Page: Fund Holdings (Tab 1)
Fund: SPY
Action: View top 10 holdings + concentration
```

### 3. See Stock Ownership
```
Page: Fund Holdings (Tab 2)
Stock: TSLA
Funds: SPY, QQQ, ARKK
Action: Compare weights across funds
```

### 4. Track Liquidity Flows
```
Page: Macro Liquidity
Sources: M2 (40), CB (35), GLI (25)
Assets: Equities (50), BTC (30), Gold (20)
Action: Visualize normalized flows
```

## 📚 Next Steps

1. **Read full documentation**: `SANKEY_MODULE_README.md`
2. **Explore comparison features**: Check `comparison.py`
3. **Add custom translations**: Edit `i18n.py`
4. **Integrate with main dashboard**: Add to navigation
5. **Deploy to production**: Configure Redis, set API keys

## 🔗 Resources

- **Plotly Sankey**: https://plotly.com/python/sankey-diagram/
- **Streamlit**: https://docs.streamlit.io/
- **FMP API**: https://site.financialmodelingprep.com/developer/docs/
- **Alpha Vantage**: https://www.alphavantage.co/documentation/
- **yfinance**: https://github.com/ranaroussi/yfinance

## 💡 Tips

1. **Cache Strategy**: Data is cached for performance. Use "Refresh" button to update.
2. **Free APIs**: Works great with free tier APIs or no API keys at all.
3. **Offline Mode**: Use fixture data in tests for offline development.
4. **Customization**: Easy to extend with new chart types or data sources.
5. **Performance**: <3s load time with cache, <6s without.

---

**Happy Visualizing! 📊✨**

For issues or questions, check `SANKEY_MODULE_README.md` or review test files for examples.
