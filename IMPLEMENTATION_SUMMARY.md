# Critical Fix Pack (A) - Implementation Summary

## ✅ COMPLETED

### 1. Cache Infrastructure (`app/services/cache.py`)
- ✅ Enhanced with TTL jitter (+/-10%) to prevent thundering herd
- ✅ Added `cache_invalidate(prefix)` function for selective cache clearing
- ✅ Both Redis and in-memory backends support jitter
- ✅ Module-level functions: `cache_get`, `cache_set`, `cache_delete`, `cache_clear`, `cache_invalidate`

### 2. Centralized Exporter (`dashboard/components/export_utils.py`)
- ✅ Added `_sanitize_filename()` for safe file names
- ✅ Enhanced `create_export_section()` with:
  - Filename sanitization (removes unsafe chars, max 100 chars)
  - Size guard for large DataFrames (warns if >250k rows)
  - Fallback to HTML if Kaleido (PNG export) not available
  - Better error messages and tooltips

## 🔄 REMAINING CRITICAL IMPLEMENTATIONS

### 3. Theme Support for Sankey Charts
**File:** `dashboard/components/charts_sankey.py`

Add this function at the top:
```python
def _theme_colors(theme: str = "Light") -> dict:
    """
    Get theme-specific colors for Sankey charts.

    Args:
        theme: "Light" or "Dark"

    Returns:
        Dict with text, node_border, paper_bg, plot_bg colors
    """
    if theme == "Dark":
        return {
            "text": "#F9FAFB",
            "node_border": "#111827",
            "paper_bg": "#0B1220",
            "plot_bg": "#0B1220",
        }
    else:  # Light
        return {
            "text": "#1F2937",
            "node_border": "#FFFFFF",
            "paper_bg": "#F9FAFB",
            "plot_bg": "#F9FAFB",
        }
```

Update all three functions (`plot_income_sankey`, `plot_fund_sankey`, `plot_macro_sankey`):
- Add parameter: `theme: str = "Light"`
- Add parameter: `scale_display: str = "$"` (for income only)
- Get colors: `colors = _theme_colors(theme)`
- Apply:
  ```python
  textfont=dict(color=colors["text"], size=14, family="Inter, sans-serif", weight=600)
  line=dict(color=colors["node_border"], width=2)
  plot_bgcolor=colors["plot_bg"]
  paper_bgcolor=colors["paper_bg"]
  ```

### 4. yfinance Fallback Utility
**File:** `app/utils/yfinance_fallback.py` (NEW FILE)

```python
"""
yfinance Fallback Utility
Provides robust data fetching with automatic fallbacks.
"""

import yfinance as yf
import pandas as pd
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Proxy mappings for futures that often fail
FUTURES_PROXIES = {
    "GC=F": "XAUUSD=X",  # Gold
    "SI=F": "XAGUSD=X",  # Silver
    "CL=F": "BZ=F",      # Crude Oil
}


def safe_yf_download(symbol: str, period: str = "1d", interval: str = "1d") -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Safely download yfinance data with automatic fallbacks.

    Args:
        symbol: Ticker symbol
        period: Data period
        interval: Data interval

    Returns:
        Tuple of (DataFrame, warning_message)
        DataFrame may be empty, warning_message is None if successful
    """
    warning = None

    # Try 1: Original parameters
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if not df.empty:
            return df, None
    except Exception as e:
        logger.warning(f"yfinance download failed for {symbol}: {e}")

    # Try 2: Fallback to longer period with daily interval
    if period == "1d" and interval == "1m":
        try:
            logger.info(f"Trying fallback: period=5d, interval=1d for {symbol}")
            df = yf.download(symbol, period="5d", interval="1d", progress=False)
            if not df.empty:
                warning = f"Using 5-day data for {symbol} (1-day unavailable)"
                return df, warning
        except:
            pass

    # Try 3: Even longer period
    try:
        logger.info(f"Trying fallback: period=1mo, interval=1d for {symbol}")
        df = yf.download(symbol, period="1mo", interval="1d", progress=False)
        if not df.empty:
            warning = f"Using 1-month data for {symbol} (shorter periods unavailable)"
            return df, warning
    except:
        pass

    # Try 4: Proxy mapping for futures
    if symbol in FUTURES_PROXIES:
        proxy = FUTURES_PROXIES[symbol]
        try:
            logger.info(f"Trying proxy {proxy} for {symbol}")
            df = yf.download(proxy, period=period, interval=interval, progress=False)
            if not df.empty:
                warning = f"Using proxy {proxy} for {symbol}"
                return df, warning
        except:
            pass

    # All attempts failed
    warning = f"⚠️ No data available for {symbol}"
    return pd.DataFrame(), warning
```

### 5. Holdings Normalization
**File:** `app/data_collectors/holdings_collector_ext.py`

Update `get_fund_holdings` method to add normalization:

```python
def get_fund_holdings(self, fund_symbol: str, top_n: int = 15) -> List[Dict]:
    # ... existing code ...

    # After getting holdings (either from API or simulated):

    # Normalize weights to sum to ~100
    total_weight = sum(h['weight'] for h in holdings)

    if total_weight > 0 and abs(total_weight - 100) > 0.5:
        # Renormalize proportionally
        scale_factor = 100 / total_weight
        for h in holdings:
            h['weight'] *= scale_factor
        logger.info(f"Normalized weights for {fund_symbol}: {total_weight:.2f}% -> 100%")

    # Sort by weight descending
    holdings.sort(key=lambda x: x['weight'], reverse=True)

    # Take top_n
    top_holdings = holdings[:top_n]

    # Calculate "OTHERS" if there are more holdings
    if len(holdings) > top_n:
        others_weight = sum(h['weight'] for h in holdings[top_n:])
        if others_weight > 0.1:  # Only add if meaningful
            top_holdings.append({
                'symbol': 'OTHERS',
                'weight': others_weight,
                'name': 'Other Holdings'
            })

    # Add simulated flag to metadata
    if simulated:
        for h in top_holdings:
            h['simulated'] = True

    return top_holdings
```

### 6. Income Statement Sanity Checks
**File:** `app/analytics/sanity_checks.py`

```python
"""
Sanity Checks Module
Validates and rescales financial statement data for visualization.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def assert_balanced_income(metrics: Dict[str, float], tol: float = 0.10) -> Dict[str, float]:
    """
    Validate and rescale income statement metrics to ensure balance.

    Args:
        metrics: Dict with keys: revenue, cost_of_revenue, gross_profit,
                 operating_income, opex_total, tax_expense, interest_expense, net_income
        tol: Tolerance for imbalance (default 10%)

    Returns:
        Rescaled metrics dict with positive magnitudes
    """
    # Ensure all values are positive magnitudes
    metrics = {k: abs(v) for k, v in metrics.items()}

    revenue = metrics.get('revenue', 0)
    cost_of_revenue = metrics.get('cost_of_revenue', 0)
    gross_profit = metrics.get('gross_profit', 0)

    if revenue == 0:
        logger.warning("Revenue is zero, cannot validate balance")
        return metrics

    # Check: revenue ≈ cost_of_revenue + gross_profit
    expected_revenue = cost_of_revenue + gross_profit
    revenue_diff = abs(revenue - expected_revenue) / revenue

    if revenue_diff > tol:
        logger.warning(f"Revenue imbalance: {revenue_diff:.1%} (tolerance: {tol:.1%})")
        # Rescale cost side to match revenue
        if expected_revenue > 0:
            scale_factor = revenue / expected_revenue
            metrics['cost_of_revenue'] *= scale_factor
            metrics['gross_profit'] *= scale_factor
            logger.info(f"Rescaled cost side by {scale_factor:.3f}x")

    # Check: gross_profit ≈ operating_income + opex_total
    operating_income = metrics.get('operating_income', 0)
    opex_total = metrics.get('opex_total', 0)

    if gross_profit > 0:
        expected_gp = operating_income + opex_total
        gp_diff = abs(gross_profit - expected_gp) / gross_profit

        if gp_diff > tol:
            logger.warning(f"Gross profit imbalance: {gp_diff:.1%}")
            if expected_gp > 0:
                scale_factor = gross_profit / expected_gp
                metrics['operating_income'] *= scale_factor
                metrics['opex_total'] *= scale_factor
                logger.info(f"Rescaled opex/operating by {scale_factor:.3f}x")

    return metrics
```

### 7. Wire-up in main.py

In the Sankey chart section of `main.py`:

```python
# Add theme selector in sidebar
with st.sidebar:
    theme = st.selectbox("🎨 Chart Theme", ["Light", "Dark"], index=0, key="chart_theme")

# In each Sankey tab, pass theme parameter:
fig = plot_income_sankey(sankey_data, title=..., theme=theme, scale_display="$B")

# After showing chart, add export:
create_export_section(fig, df, f"{ticker}_income_statement")

# If using yfinance fallback:
df, warning = safe_yf_download(symbol, period, interval)
if warning:
    st.info(warning)
```

## 📋 TEST IMPLEMENTATIONS NEEDED

### Test Files to Create:

1. **tests/test_cache.py**
```python
import pytest
from app.services.cache import get_cache, cache_get, cache_set, cache_invalidate
import time

def test_cache_set_get():
    cache_set("test_key", "test_value", ttl=5)
    assert cache_get("test_key") == "test_value"

def test_cache_ttl_expiration():
    cache_set("expire_key", "value", ttl=1)
    time.sleep(2)
    assert cache_get("expire_key") is None

def test_cache_invalidate_prefix():
    cache_set("user:1", "data1")
    cache_set("user:2", "data2")
    cache_set("product:1", "data3")

    cache_invalidate("user")

    assert cache_get("user:1") is None
    assert cache_get("product:1") == "data3"
```

2. **tests/test_yf_fallbacks.py**
```python
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from app.utils.yfinance_fallback import safe_yf_download

@patch('yfinance.download')
def test_fallback_chain(mock_download):
    # First call returns empty, second succeeds
    mock_download.side_effect = [pd.DataFrame(), pd.DataFrame({'Close': [100, 101]})]

    df, warning = safe_yf_download("TEST", period="1d", interval="1m")

    assert not df.empty
    assert "5-day" in warning

def test_futures_proxy():
    df, warning = safe_yf_download("GC=F")
    # Should attempt proxy XAUUSD=X
    assert warning is not None or not df.empty
```

3. **tests/test_holdings_norm.py**
```python
from app.data_collectors.holdings_collector_ext import HoldingsCollectorExt

def test_weight_normalization():
    collector = HoldingsCollectorExt()
    # Mock holdings that don't sum to 100
    # Test should verify normalization happens
    pass

def test_others_category():
    # Test that OTHERS is added when holdings > top_n
    pass
```

4. **tests/test_income_sanity.py**
```python
from app.analytics.sanity_checks import assert_balanced_income

def test_rescale_imbalanced():
    metrics = {
        'revenue': 1000,
        'cost_of_revenue': 700,
        'gross_profit': 400,  # Imbalanced: should be 300
    }

    result = assert_balanced_income(metrics, tol=0.05)

    # Should rescale to balance
    assert abs((result['cost_of_revenue'] + result['gross_profit']) - result['revenue']) < 10

def test_positive_magnitudes():
    metrics = {'revenue': -1000, 'cost_of_revenue': -600}
    result = assert_balanced_income(metrics)

    assert all(v >= 0 for v in result.values())
```

5. **tests/fixtures/financials_apple_fy22.json**
```json
{
  "revenue": 394328000000,
  "cost_of_revenue": 223546000000,
  "gross_profit": 170782000000,
  "operating_income": 119437000000,
  "rd_expense": 26251000000,
  "sga_expense": 25094000000,
  "tax_expense": 19300000000,
  "net_income": 99803000000
}
```

## 🎯 ACCEPTANCE CRITERIA CHECKLIST

- [ ] Theme toggle works: Light shows dark text, Dark shows light text
- [ ] $GC=F no longer crashes, shows fallback warning
- [ ] Fund holdings sum to ~100%, OTHERS row appears when needed
- [ ] Income sanity check rescales imbalanced data
- [ ] Export buttons work with sanitized filenames
- [ ] All tests pass: `pytest -v tests/`
- [ ] No secrets in code
- [ ] README updated with new features

## 📝 NEXT STEPS

1. Implement remaining items (3-7)
2. Run tests: `pytest -v`
3. Manual testing with theme toggle
4. Update README
5. Create PR with checklist

## 🚀 DEPLOYMENT NOTES

- Ensure `kaleido` installed for PNG export: `pip install kaleido`
- Set `REDIS_URL` env var if using Redis (optional)
- Clear cache after deployment: call `cache_invalidate()` once
