# 🎲 Entropy Metrics for Financial Markets

## Overview

The Entropy Metrics module provides advanced **information-theoretic** measures to quantify market complexity, predictability, and information flow. These metrics go beyond traditional volatility analysis to provide deep insights into market dynamics.

## 📚 Table of Contents

1. [What is Entropy in Finance?](#what-is-entropy-in-finance)
2. [Available Entropy Metrics](#available-entropy-metrics)
3. [Quick Start](#quick-start)
4. [Detailed Metric Descriptions](#detailed-metric-descriptions)
5. [Practical Applications](#practical-applications)
6. [API Reference](#api-reference)
7. [Best Practices](#best-practices)

---

## What is Entropy in Finance?

**Entropy** is a measure of uncertainty, randomness, or disorder in a system. In financial markets:

- **Low Entropy** = Predictable, trending, ordered behavior
- **High Entropy** = Unpredictable, random, chaotic behavior

Entropy metrics help answer critical questions:
- Is the market trending or random?
- When is a regime change occurring?
- How diversified is my portfolio?
- Are whale movements leading the market?

---

## Available Entropy Metrics

### 1. **Shannon Entropy** 🎯
- **What**: Measures information content and randomness in price returns
- **Range**: 0 to 1 (normalized)
- **Interpretation**:
  - < 0.3: Strong trend, highly predictable
  - 0.3-0.7: Mixed market
  - > 0.7: Highly chaotic, unpredictable
- **Best for**: Market regime identification, trend detection

### 2. **Approximate Entropy (ApEn)** 📊
- **What**: Quantifies regularity and predictability of time series
- **Range**: 0 to 2+ (typical)
- **Interpretation**:
  - < 0.5: Very regular (strong trend)
  - 0.5-1.0: Moderate complexity
  - > 1.0: High complexity (volatile)
- **Best for**: Bull/bear market transitions, volatility regime changes

### 3. **Sample Entropy (SampEn)** 🔬
- **What**: Improved version of ApEn, more consistent
- **Range**: 0 to infinity (lower = more regular)
- **Interpretation**: Lower values indicate more predictable patterns
- **Best for**: Time series complexity measurement, pattern recognition

### 4. **Permutation Entropy** ⚡
- **What**: Fast entropy based on ordinal patterns
- **Range**: 0 to 1 (normalized)
- **Interpretation**: Measures complexity of ordering patterns
- **Best for**: High-frequency data, real-time analysis, flash crash detection

### 5. **Spectral Entropy** 🌊
- **What**: Entropy in frequency domain
- **Range**: 0 to 1 (normalized)
- **Interpretation**: Higher = more frequency components (complex cycles)
- **Best for**: Identifying cyclical patterns, seasonality

### 6. **Transfer Entropy** 🔄
- **What**: Information flow from one asset to another
- **Range**: 0 to infinity (higher = stronger influence)
- **Interpretation**: Quantifies causal relationships
- **Best for**: Whale influence analysis, market leadership detection

### 7. **Cross-Entropy** 🎭
- **What**: Difference between two probability distributions
- **Range**: 0 to infinity
- **Interpretation**: Higher = more different distributions
- **Best for**: Anomaly detection, distribution shifts

### 8. **KL Divergence (Relative Entropy)** 📏
- **What**: Measures divergence between two distributions
- **Range**: 0 to infinity (0 = identical)
- **Interpretation**: Quantifies distribution change
- **Best for**: Regime change detection, model validation

### 9. **Conditional Entropy** 🔗
- **What**: Uncertainty of Y given X
- **Range**: Varies
- **Interpretation**: Information gain from indicators
- **Best for**: Feature selection, indicator quality assessment

### 10. **Fuzzy Entropy** 🌫️
- **What**: Noise-resistant complexity measure
- **Range**: Similar to ApEn
- **Interpretation**: Robust to noise
- **Best for**: Noisy data, high-frequency analysis

### 11. **Multiscale Entropy** 📐
- **What**: Complexity across multiple timescales
- **Range**: Multiple values (one per scale)
- **Interpretation**: Reveals scale-dependent patterns
- **Best for**: Multi-timeframe analysis, fractal markets

### 12. **Portfolio Entropy** 💼
- **What**: Diversification measure
- **Range**: 0 to log(N) where N = number of assets
- **Interpretation**: Higher = better diversified
- **Best for**: Portfolio optimization, concentration risk

---

## Quick Start

### Installation

```python
from app.analytics.entropy_metrics import EntropyCalculator, quick_entropy_analysis
import yfinance as yf
```

### Example 1: Quick Analysis

```python
# Download Bitcoin data
btc = yf.download('BTC-USD', period='6mo')['Close']

# Quick analysis
result = quick_entropy_analysis(btc, 'Bitcoin')

print(f"Complexity: {result['complexity_score']:.1f}/100")
print(f"Market Regime: {result['market_regime']}")
```

### Example 2: Comprehensive Report

```python
calc = EntropyCalculator()
prices = yf.download('SPY', period='1y')['Close']

# Generate full report
report = calc.comprehensive_entropy_report(prices, asset_name='S&P 500')

print(f"Shannon Entropy: {report['shannon_entropy']:.4f}")
print(f"Market Regime: {report['market_regime']}")
print(f"Risk Level: {report['risk_level']}")
```

### Example 3: Compare Assets

```python
from app.analytics.entropy_metrics import compare_assets_entropy

assets = {
    'BTC': yf.download('BTC-USD', period='3mo')['Close'],
    'ETH': yf.download('ETH-USD', period='3mo')['Close'],
    'SPY': yf.download('SPY', period='3mo')['Close']
}

comparison = compare_assets_entropy(assets, metric='shannon')
print(comparison)
```

---

## Detailed Metric Descriptions

### Shannon Entropy

**Formula**: H(X) = -Σ p(x) * log₂(p(x))

**Python Example**:
```python
calc = EntropyCalculator()
returns = prices.pct_change().dropna()
shannon = calc.shannon_entropy(returns, bins=50, normalize=True)

if shannon < 0.3:
    print("Low entropy - Strong trend expected")
elif shannon < 0.7:
    print("Medium entropy - Mixed market")
else:
    print("High entropy - Chaotic, avoid trend strategies")
```

**Trading Application**:
- **Low Entropy (< 0.4)**: Use trend-following strategies (moving averages, breakouts)
- **Medium Entropy (0.4-0.7)**: Use adaptive strategies, shorter timeframes
- **High Entropy (> 0.7)**: Reduce position sizes, use mean reversion

---

### Approximate Entropy (ApEn)

**Python Example**:
```python
apen = calc.approximate_entropy(returns, m=2, r=None)

# Detect regime changes
if apen < 0.5:
    regime = "Trending"
elif apen < 1.0:
    regime = "Transitional"
else:
    regime = "Volatile"
```

**Use Cases**:
- Detect bull → bear transitions
- Identify volatility clustering
- Signal crisis periods

---

### Transfer Entropy

**Python Example**:
```python
# Measure BTC influence on altcoins
btc = yf.download('BTC-USD', period='6mo')['Close']
eth = yf.download('ETH-USD', period='6mo')['Close']

te_btc_to_eth = calc.transfer_entropy(btc, eth, k=1, l=1)
te_eth_to_btc = calc.transfer_entropy(eth, btc, k=1, l=1)

net_influence = te_btc_to_eth - te_eth_to_btc

if net_influence > 0.1:
    print("BTC is leading ETH - watch BTC for ETH signals")
else:
    print("Independent movements")
```

**Whale Tracking Application**:
```python
whale_activity = df['whale_volume']
market_price = df['price']

result = calc.whale_influence_entropy(whale_activity, market_price)
print(f"Whale Influence: {result['interpretation']}")
```

---

### Multiscale Entropy

**Python Example**:
```python
mse = calc.multiscale_entropy(returns, max_scale=10)

# Plot to see complexity at different timescales
import matplotlib.pyplot as plt
plt.plot(mse.keys(), mse.values())
plt.xlabel('Scale')
plt.ylabel('Sample Entropy')
plt.title('Multiscale Entropy Analysis')
```

**Interpretation**:
- **Increasing**: Long-range correlations (fractal market)
- **Decreasing**: White noise characteristics
- **U-shaped**: Both short and long-term structure

---

### Portfolio Entropy

**Python Example**:
```python
# Your portfolio weights
weights = {
    'AAPL': 0.30,
    'MSFT': 0.25,
    'GOOGL': 0.20,
    'AMZN': 0.15,
    'NVDA': 0.10
}

portfolio_ent = calc.portfolio_entropy(weights)
max_entropy = np.log(len(weights))
diversification_score = (portfolio_ent / max_entropy) * 100

print(f"Diversification: {diversification_score:.1f}%")

if diversification_score > 90:
    print("✅ Excellent diversification")
elif diversification_score > 70:
    print("ℹ️ Good diversification")
else:
    print("⚠️ High concentration risk")
```

---

## Practical Applications

### 1. Trading Strategy Selection

```python
def select_strategy(entropy):
    """Select trading strategy based on entropy."""
    if entropy < 0.3:
        return "Trend Following (MA crossover, breakouts)"
    elif entropy < 0.5:
        return "Hybrid (Trend + filters)"
    elif entropy < 0.7:
        return "Mean Reversion (Bollinger Bands, RSI)"
    else:
        return "Stay Out / Reduce Risk"

entropy = calc.shannon_entropy(returns)
strategy = select_strategy(entropy)
print(f"Recommended: {strategy}")
```

### 2. Position Sizing

```python
def position_size_multiplier(entropy):
    """Adjust position size based on market entropy."""
    if entropy < 0.4:
        return 1.0  # Full size
    elif entropy < 0.6:
        return 0.7  # 70% size
    elif entropy < 0.75:
        return 0.4  # 40% size
    else:
        return 0.0  # No position

multiplier = position_size_multiplier(entropy)
position_size = base_position * multiplier
```

### 3. Regime Detection System

```python
def detect_market_regime(prices):
    """Complete regime detection system."""
    calc = EntropyCalculator()
    returns = prices.pct_change().dropna()

    shannon = calc.shannon_entropy(returns)
    apen = calc.approximate_entropy(returns)
    sampen = calc.sample_entropy(returns)

    # Composite score
    regime_score = (shannon + apen/2 + sampen/2) / 3

    if regime_score < 0.3:
        return "STRONG_TREND"
    elif regime_score < 0.5:
        return "WEAK_TREND"
    elif regime_score < 0.7:
        return "MIXED"
    else:
        return "CHAOTIC"

regime = detect_market_regime(spy_prices)
print(f"Current Regime: {regime}")
```

### 4. Whale Alert System

```python
def whale_alert_system(whale_data, price_data):
    """Alert when whales are leading the market."""
    calc = EntropyCalculator()

    result = calc.whale_influence_entropy(whale_data, price_data)

    if result['net_whale_influence'] > 0.2:
        return {
            'alert': True,
            'message': '🐋 WHALE ALERT: Large holders are leading the market',
            'action': 'Watch whale movements for price signals'
        }
    return {'alert': False}
```

### 5. Portfolio Rebalancing Signal

```python
def check_rebalancing_needed(portfolio_weights):
    """Check if portfolio needs rebalancing based on entropy."""
    calc = EntropyCalculator()

    current_entropy = calc.portfolio_entropy(portfolio_weights)
    n_assets = len(portfolio_weights)
    max_entropy = np.log(n_assets)

    diversification_ratio = current_entropy / max_entropy

    if diversification_ratio < 0.7:
        return {
            'rebalance': True,
            'reason': 'Low diversification detected',
            'target': 'Move towards equal weights'
        }
    return {'rebalance': False}
```

---

## API Reference

### EntropyCalculator Class

```python
calc = EntropyCalculator()
```

#### Main Methods

```python
# Shannon Entropy
calc.shannon_entropy(data, bins=50, normalize=True)

# Approximate Entropy
calc.approximate_entropy(data, m=2, r=None)

# Sample Entropy
calc.sample_entropy(data, m=2, r=None)

# Permutation Entropy
calc.permutation_entropy(data, order=3, delay=1, normalize=True)

# Spectral Entropy
calc.spectral_entropy(data, method='welch', normalize=True)

# Transfer Entropy
calc.transfer_entropy(source, target, k=1, l=1, bins=10)

# Cross-Entropy
calc.cross_entropy(observed, expected, bins=50)

# KL Divergence
calc.kl_divergence(p, q, bins=50)

# Conditional Entropy
calc.conditional_entropy(X, Y, bins=20)

# Fuzzy Entropy
calc.fuzzy_entropy(data, m=2, r=None, n=2.0)

# Multiscale Entropy
calc.multiscale_entropy(data, max_scale=10, method='sample')

# Portfolio Entropy
calc.portfolio_entropy(weights)

# Whale Influence
calc.whale_influence_entropy(whale_activity, market_price, window=20)

# Comprehensive Report
calc.comprehensive_entropy_report(prices, reference_data=None, asset_name="Asset")
```

### Convenience Functions

```python
# Quick analysis
quick_entropy_analysis(data, asset_name="Asset")

# Compare assets
compare_assets_entropy(assets_dict, metric='shannon')
```

---

## Best Practices

### 1. Data Preparation
- Use **clean, continuous data** without gaps
- For prices: Convert to returns first (most metrics work better with returns)
- Remove outliers if necessary (especially for entropy calculations)

### 2. Parameter Selection
- **Shannon Entropy**: Use 50-100 bins for daily data
- **ApEn/SampEn**: m=2 or m=3, r=0.2*std is standard
- **Permutation Entropy**: order=3 to 5 for financial data
- **Transfer Entropy**: k=1, l=1 for daily data; increase for lower frequency

### 3. Interpretation Guidelines
- **Combine multiple entropy measures** for robust signals
- Use **rolling windows** to detect changes over time
- **Compare to historical values** rather than absolute thresholds
- Consider **market context** (crypto vs stocks behave differently)

### 4. Computational Considerations
- **Shannon, Permutation**: Very fast, suitable for real-time
- **ApEn, SampEn**: Moderate speed
- **Transfer Entropy, Multiscale**: Slower, use for periodic analysis
- Cache results when possible

### 5. Integration with Other Metrics
```python
# Combine with traditional risk metrics
from app.analytics.risk_metrics import RiskCalculator

risk_calc = RiskCalculator()
entropy_calc = EntropyCalculator()

# Get both perspectives
risk_report = risk_calc.comprehensive_risk_report(prices)
entropy_report = entropy_calc.comprehensive_entropy_report(prices)

# Compare volatility with entropy
vol = risk_report['return_statistics']['volatility']
entropy = entropy_report['shannon_entropy']

print(f"Volatility: {vol:.2f}% | Entropy: {entropy:.4f}")
```

---

## Use in Dashboard

### Streamlit Integration

The entropy metrics are integrated into the dashboard at:
**`dashboard/pages/entropy_analysis.py`**

Run the dashboard:
```bash
streamlit run main.py
```

Then navigate to the **Entropy Analysis** page for:
- Single asset analysis with rolling entropy
- Multi-asset comparison
- Whale influence detection
- Portfolio diversification analysis

---

## Examples

Run comprehensive examples:
```bash
python examples/entropy_usage_examples.py
```

This includes 10 practical examples covering all entropy metrics.

---

## References & Further Reading

### Academic Papers
1. Shannon, C.E. (1948). "A Mathematical Theory of Communication"
2. Pincus, S.M. (1991). "Approximate Entropy as a Measure of System Complexity"
3. Richman, J.S. & Moorman, J.R. (2000). "Physiological Time-Series Analysis Using Approximate Entropy and Sample Entropy"
4. Schreiber, T. (2000). "Measuring Information Transfer"
5. Bandt, C. & Pompe, B. (2002). "Permutation Entropy: A Natural Complexity Measure for Time Series"

### Financial Applications
- Peters, E.E. (1994). "Fractal Market Analysis"
- Gulko, L. (1999). "The Entropy Theory of Stock Option Pricing"
- Zhou, R. et al. (2013). "Applications of Entropy in Finance"

---

## Support & Contributing

For questions or contributions:
- 📧 GitHub Issues
- 📚 See main project README
- 💡 Feature requests welcome

---

## Summary

Entropy metrics provide a **powerful complement** to traditional financial analysis:

✅ **Quantify predictability** beyond simple volatility
✅ **Detect regime changes** before traditional indicators
✅ **Measure information flow** between assets
✅ **Optimize diversification** scientifically
✅ **Validate trading strategies** based on market complexity

**When to use each metric:**

| Metric | Use Case |
|--------|----------|
| Shannon | General complexity, regime identification |
| ApEn/SampEn | Regime transitions, volatility clustering |
| Permutation | HFT, real-time analysis |
| Spectral | Cyclical patterns, seasonality |
| Transfer | Causality, whale influence |
| KL Divergence | Anomaly detection, distribution shifts |
| Portfolio | Diversification optimization |
| Multiscale | Multi-timeframe complexity |

**Start with Shannon Entropy and expand from there!**

---

*Last updated: 2025*
*Part of Global Liquidity Dashboard*
