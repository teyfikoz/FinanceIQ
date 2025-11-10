#!/usr/bin/env python3
"""
Entropy Metrics - Usage Examples
=================================

This script demonstrates how to use the entropy metrics module
for financial market analysis.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from app.analytics.entropy_metrics import (
    EntropyCalculator,
    quick_entropy_analysis,
    compare_assets_entropy
)


def example_1_basic_shannon_entropy():
    """Example 1: Basic Shannon Entropy for single asset."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Shannon Entropy - Bitcoin Predictability")
    print("="*70)

    # Download Bitcoin data
    btc = yf.download('BTC-USD', period='1y', progress=False)['Close']

    calc = EntropyCalculator()
    entropy = calc.shannon_entropy(btc.pct_change().dropna())

    print(f"\nBitcoin (1 Year)")
    print(f"Shannon Entropy: {entropy:.4f}")
    print(f"Complexity Score: {entropy * 100:.1f}/100")
    print(f"Predictability Score: {(1-entropy) * 100:.1f}/100")

    if entropy < 0.5:
        print("✅ Status: Relatively predictable - Good for trend following")
    elif entropy < 0.7:
        print("⚠️  Status: Moderate complexity - Use caution")
    else:
        print("❌ Status: High complexity - Very unpredictable")


def example_2_regime_detection():
    """Example 2: Regime detection with Approximate Entropy."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Regime Detection - ApEn Analysis")
    print("="*70)

    # Download S&P 500 data
    spy = yf.download('SPY', period='2y', progress=False)['Close']
    returns = spy.pct_change().dropna()

    calc = EntropyCalculator()

    # Calculate ApEn for different periods
    periods = {
        'Last 3 months': returns[-63:],
        'Last 6 months': returns[-126:],
        'Last 1 year': returns[-252:],
        'Full period': returns
    }

    print("\nS&P 500 Approximate Entropy by Period:")
    print("-" * 50)

    for period_name, period_data in periods.items():
        apen = calc.approximate_entropy(period_data)
        regime = "Trending" if apen < 0.5 else "Mixed" if apen < 1.0 else "Volatile"
        print(f"{period_name:15s}: ApEn={apen:.4f}  [{regime}]")


def example_3_multi_asset_comparison():
    """Example 3: Compare entropy across multiple assets."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Multi-Asset Entropy Comparison")
    print("="*70)

    # Define assets to compare
    assets = {
        'Bitcoin': 'BTC-USD',
        'Ethereum': 'ETH-USD',
        'S&P 500': 'SPY',
        'Nasdaq': 'QQQ',
        'Gold': 'GC=F',
        'US Dollar': 'DX-Y.NYB'
    }

    print("\nDownloading data...")
    asset_data = {}
    for name, ticker in assets.items():
        try:
            data = yf.download(ticker, period='6mo', progress=False)['Close']
            asset_data[name] = data
        except:
            print(f"⚠️  Could not download {name}")

    # Compare using convenience function
    print("\nEntropy Comparison (Shannon):")
    print("-" * 70)

    comparison = compare_assets_entropy(asset_data, metric='shannon')
    print(comparison.to_string(index=False))

    print("\n💡 Insight: Lower entropy = More predictable = Better for trend following")


def example_4_transfer_entropy_causality():
    """Example 4: Transfer entropy for causality analysis."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Transfer Entropy - BTC → ETH Causality")
    print("="*70)

    # Download data
    btc = yf.download('BTC-USD', period='6mo', progress=False)['Close']
    eth = yf.download('ETH-USD', period='6mo', progress=False)['Close']

    # Align data
    df = pd.DataFrame({'BTC': btc, 'ETH': eth}).dropna()

    calc = EntropyCalculator()

    # Calculate transfer entropy both directions
    print("\nCalculating information flow...")

    te_btc_to_eth = calc.transfer_entropy(df['BTC'], df['ETH'])
    te_eth_to_btc = calc.transfer_entropy(df['ETH'], df['BTC'])

    print(f"\nTransfer Entropy Results:")
    print(f"BTC → ETH: {te_btc_to_eth:.4f} bits")
    print(f"ETH → BTC: {te_eth_to_btc:.4f} bits")
    print(f"Net Flow:  {te_btc_to_eth - te_eth_to_btc:+.4f} bits")

    if te_btc_to_eth > te_eth_to_btc + 0.05:
        print("\n✅ Bitcoin is leading Ethereum (BTC provides more information about future ETH)")
    elif te_eth_to_btc > te_btc_to_eth + 0.05:
        print("\n✅ Ethereum is leading Bitcoin (ETH provides more information about future BTC)")
    else:
        print("\n⚖️  Balanced relationship - No clear leader")


def example_5_multiscale_analysis():
    """Example 5: Multiscale entropy for complexity at different timescales."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Multiscale Entropy - Bitcoin Complexity")
    print("="*70)

    # Download Bitcoin
    btc = yf.download('BTC-USD', period='1y', progress=False)['Close']
    returns = btc.pct_change().dropna()

    calc = EntropyCalculator()

    # Calculate multiscale entropy
    print("\nCalculating multiscale entropy (this may take a moment)...")
    mse = calc.multiscale_entropy(returns, max_scale=10)

    print("\nMultiscale Entropy Results:")
    print("-" * 40)
    print(f"{'Scale':<10} {'SampEn':<10} {'Interpretation'}")
    print("-" * 40)

    for scale, entropy in mse.items():
        if scale == 1:
            interp = "Intraday"
        elif scale <= 3:
            interp = "Short-term"
        elif scale <= 7:
            interp = "Medium-term"
        else:
            interp = "Long-term"

        print(f"{scale:<10} {entropy:<10.4f} {interp}")

    # Analysis
    entropy_values = list(mse.values())
    trend = "Increasing" if entropy_values[-1] > entropy_values[0] else "Decreasing"

    print(f"\n💡 Trend: {trend}")
    if trend == "Increasing":
        print("   → Complexity increases at longer timescales (long-range correlations)")
    else:
        print("   → Complexity decreases at longer timescales (white noise characteristics)")


def example_6_portfolio_diversification():
    """Example 6: Portfolio entropy for diversification analysis."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Portfolio Entropy - Diversification Analysis")
    print("="*70)

    calc = EntropyCalculator()

    # Example portfolios
    portfolios = {
        "Concentrated": {
            'AAPL': 0.70,
            'MSFT': 0.20,
            'GOOGL': 0.10
        },
        "Balanced": {
            'AAPL': 0.20,
            'MSFT': 0.20,
            'GOOGL': 0.20,
            'AMZN': 0.20,
            'NVDA': 0.20
        },
        "Over-diversified": {
            f'Stock_{i}': 1.0/20 for i in range(20)
        }
    }

    print("\nPortfolio Diversification Analysis:")
    print("-" * 60)

    for name, weights in portfolios.items():
        entropy = calc.portfolio_entropy(weights)
        max_entropy = np.log(len(weights))
        diversification = (entropy / max_entropy) * 100

        print(f"\n{name} Portfolio:")
        print(f"  Assets: {len(weights)}")
        print(f"  Entropy: {entropy:.4f}")
        print(f"  Diversification Score: {diversification:.1f}%")

        if diversification > 90:
            print(f"  Status: ✅ Excellent diversification")
        elif diversification > 70:
            print(f"  Status: ℹ️  Good diversification")
        else:
            print(f"  Status: ⚠️  Poor diversification - High concentration risk")


def example_7_comprehensive_report():
    """Example 7: Generate comprehensive entropy report."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Comprehensive Entropy Report")
    print("="*70)

    # Download data
    btc = yf.download('BTC-USD', period='1y', progress=False)['Close']

    calc = EntropyCalculator()

    # Generate comprehensive report
    print("\nGenerating comprehensive entropy analysis...")
    report = calc.comprehensive_entropy_report(btc, asset_name='Bitcoin')

    # Display report
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE ENTROPY REPORT: {report['asset_name']}")
    print(f"{'='*60}")

    print(f"\nData: {report['data_points']} observations")
    print(f"Timestamp: {report['timestamp']}")

    print(f"\n{'─'*60}")
    print("ENTROPY METRICS")
    print(f"{'─'*60}")
    print(f"Shannon Entropy:      {report['shannon_entropy']:.4f}")
    print(f"Sample Entropy:       {report['sample_entropy']:.4f}")
    print(f"Approximate Entropy:  {report['approximate_entropy']:.4f}")
    print(f"Permutation Entropy:  {report['permutation_entropy']:.4f}")
    print(f"Spectral Entropy:     {report['spectral_entropy']:.4f}")
    print(f"Fuzzy Entropy:        {report['fuzzy_entropy']:.4f}")

    print(f"\n{'─'*60}")
    print("DERIVED SCORES")
    print(f"{'─'*60}")
    print(f"Complexity Score:     {report['complexity_score']:.1f}/100")
    print(f"Predictability Score: {report['predictability_score']:.1f}/100")

    print(f"\n{'─'*60}")
    print("INTERPRETATION")
    print(f"{'─'*60}")
    print(f"Market Regime:        {report['market_regime']}")
    print(f"Risk Level:           {report['risk_level']}")

    # Multiscale
    print(f"\n{'─'*60}")
    print("MULTISCALE ENTROPY (Sample Entropy at different scales)")
    print(f"{'─'*60}")
    mse = report['multiscale_entropy']
    for scale in [1, 2, 3, 5]:
        if scale in mse:
            print(f"Scale {scale}: {mse[scale]:.4f}")

    print(f"\n{'='*60}\n")


def example_8_kl_divergence_anomaly():
    """Example 8: KL divergence for anomaly detection."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Anomaly Detection with KL Divergence")
    print("="*70)

    # Download S&P 500
    spy = yf.download('SPY', period='2y', progress=False)['Close']
    returns = spy.pct_change().dropna()

    calc = EntropyCalculator()

    # Split into reference and recent period
    reference_period = returns[:-63]  # All but last 3 months
    recent_period = returns[-63:]      # Last 3 months

    # Calculate KL divergence
    kl_div = calc.kl_divergence(recent_period, reference_period)

    print(f"\nS&P 500 Distribution Comparison:")
    print(f"Reference Period: {len(reference_period)} days")
    print(f"Recent Period:    {len(recent_period)} days")
    print(f"\nKL Divergence:    {kl_div:.4f}")

    if kl_div < 0.1:
        print("✅ Status: Normal - Distribution unchanged")
    elif kl_div < 0.3:
        print("ℹ️  Status: Slight change detected")
    elif kl_div < 0.5:
        print("⚠️  Status: Significant change - Market regime shift possible")
    else:
        print("❌ Status: Major distribution shift - Anomaly detected!")


def example_9_quick_analysis():
    """Example 9: Quick analysis using convenience function."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Quick Entropy Analysis (Convenience Function)")
    print("="*70)

    symbols = ['BTC-USD', 'ETH-USD', 'SPY', 'QQQ', 'GLD']

    print("\nQuick Entropy Analysis:")
    print("-" * 70)

    for symbol in symbols:
        try:
            data = yf.download(symbol, period='3mo', progress=False)['Close']
            result = quick_entropy_analysis(data, symbol)

            print(f"\n{result['asset']:10s}")
            print(f"  Shannon:      {result['shannon_entropy']:.4f}")
            print(f"  Sample:       {result['sample_entropy']:.4f}")
            print(f"  Complexity:   {result['complexity_score']:.1f}/100")
            print(f"  Regime:       {result['market_regime']}")
        except Exception as e:
            print(f"\n{symbol:10s}: Error - {e}")


def example_10_trading_signals():
    """Example 10: Generate trading signals based on entropy."""
    print("\n" + "="*70)
    print("EXAMPLE 10: Trading Signals from Entropy")
    print("="*70)

    # Download Bitcoin
    btc = yf.download('BTC-USD', period='6mo', progress=False)['Close']
    returns = btc.pct_change().dropna()

    calc = EntropyCalculator()

    # Calculate rolling entropy
    window = 30
    rolling_entropy = []

    print("\nCalculating rolling entropy signals...")

    for i in range(window, len(returns), 5):  # Every 5 days
        window_returns = returns.iloc[i-window:i]
        entropy = calc.shannon_entropy(window_returns)
        rolling_entropy.append({
            'date': returns.index[i],
            'price': btc.iloc[i],
            'entropy': entropy
        })

    df_signals = pd.DataFrame(rolling_entropy)

    # Generate signals
    df_signals['signal'] = 'HOLD'
    df_signals.loc[df_signals['entropy'] < 0.4, 'signal'] = 'STRONG BUY (Trending)'
    df_signals.loc[df_signals['entropy'] > 0.7, 'signal'] = 'REDUCE (Chaotic)'

    print("\nRecent Entropy-Based Trading Signals:")
    print("-" * 80)
    print(df_signals.tail(10).to_string(index=False))

    # Current recommendation
    current = df_signals.iloc[-1]
    print(f"\n📊 CURRENT STATUS:")
    print(f"Date:    {current['date'].strftime('%Y-%m-%d')}")
    print(f"Price:   ${current['price']:.2f}")
    print(f"Entropy: {current['entropy']:.4f}")
    print(f"Signal:  {current['signal']}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("ENTROPY METRICS - COMPREHENSIVE USAGE EXAMPLES")
    print("Financial Market Analysis with Information Theory")
    print("="*70)

    examples = [
        example_1_basic_shannon_entropy,
        example_2_regime_detection,
        example_3_multi_asset_comparison,
        example_4_transfer_entropy_causality,
        example_5_multiscale_analysis,
        example_6_portfolio_diversification,
        example_7_comprehensive_report,
        example_8_kl_divergence_anomaly,
        example_9_quick_analysis,
        example_10_trading_signals
    ]

    print("\nAvailable Examples:")
    for i, example in enumerate(examples, 1):
        print(f"{i:2d}. {example.__doc__.split('.')[0].replace('Example ' + str(i) + ':', '').strip()}")

    print("\n" + "-"*70)
    choice = input("\nSelect example (1-10) or 'all' to run all examples: ").strip().lower()

    if choice == 'all':
        for example in examples:
            try:
                example()
            except Exception as e:
                print(f"\n❌ Error in example: {e}")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        try:
            examples[int(choice) - 1]()
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("Invalid choice. Running Example 1 by default.")
        example_1_basic_shannon_entropy()

    print("\n" + "="*70)
    print("EXAMPLES COMPLETED")
    print("="*70)
    print("\n💡 For more information, see: app/analytics/entropy_metrics.py")
    print("📊 To use in dashboard, run: streamlit run main.py")
    print("\n")


if __name__ == "__main__":
    main()
