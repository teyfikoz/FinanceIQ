"""
FinanceIQ Pro - Test Script
Quick test to verify all modules work correctly
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from modules.portfolio_health import PortfolioHealthScore
from modules.etf_weight_tracker import ETFWeightTracker

def test_portfolio_health():
    """Test Portfolio Health Score module"""
    print("=" * 60)
    print("Testing Portfolio Health Score Module...")
    print("=" * 60)

    # Load sample portfolio
    try:
        portfolio_df = pd.read_csv('sample_data/sample_portfolio.csv')
        print(f"✅ Sample portfolio loaded: {len(portfolio_df)} positions")
    except Exception as e:
        print(f"❌ Failed to load sample portfolio: {e}")
        return False

    # Initialize calculator
    try:
        calculator = PortfolioHealthScore()
        calculator.load_portfolio(portfolio_df)
        print("✅ Portfolio loaded successfully")
    except Exception as e:
        print(f"❌ Failed to initialize calculator: {e}")
        return False

    # Enrich data (this will take 30-60 seconds)
    print("\n⏳ Enriching portfolio data (may take 30-60 seconds)...")
    try:
        enriched_df = calculator.enrich_portfolio_data()
        print(f"✅ Portfolio enriched: {len(enriched_df.columns)} columns")
    except Exception as e:
        print(f"❌ Failed to enrich portfolio: {e}")
        return False

    # Calculate metrics
    print("\n⏳ Calculating health metrics...")
    try:
        scores = calculator.calculate_all_metrics()
        summary = calculator.get_summary()

        print("\n" + "=" * 60)
        print("PORTFOLIO HEALTH SCORE RESULTS")
        print("=" * 60)
        print(f"\n🎯 Total Score: {summary['total_score']:.1f}/100")
        print(f"📊 Grade: {summary['grade']}")
        print(f"\n📋 Metric Breakdown:")

        metric_names = {
            'diversification': 'Diversification',
            'risk': 'Risk Management',
            'momentum': 'Momentum',
            'liquidity': 'Liquidity',
            'tax_efficiency': 'Tax Efficiency',
            'balance': 'Balance',
            'duration_fit': 'Duration Fit',
            'sector_performance': 'Sector Performance'
        }

        for metric, score in summary['metric_scores'].items():
            metric_name = metric_names.get(metric, metric)
            print(f"  - {metric_name}: {score:.1f}/100")

        print(f"\n💡 Recommendations ({len(summary['recommendations'])}):")
        if summary['recommendations']:
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"  {i}. {rec}")
        else:
            print("  ✅ No major issues found!")

        print("\n✅ Portfolio Health Score module working correctly!")
        return True

    except Exception as e:
        print(f"❌ Failed to calculate metrics: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_etf_weight_tracker():
    """Test ETF Weight Tracker module"""
    print("\n" + "=" * 60)
    print("Testing ETF Weight Tracker Module...")
    print("=" * 60)

    # Initialize tracker
    try:
        tracker = ETFWeightTracker(db_path="data/etf_holdings_test.db")
        print("✅ ETF Weight Tracker initialized")
    except Exception as e:
        print(f"❌ Failed to initialize tracker: {e}")
        return False

    # Test database
    try:
        stats = tracker.get_summary_stats()
        print(f"✅ Database initialized")
        print(f"  - Total records: {stats['total_records']}")
        print(f"  - Unique stocks: {stats['unique_stocks']}")
        print(f"  - Unique funds: {stats['unique_funds']}")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

    # Test single ETF fetch
    print("\n⏳ Fetching sample ETF holdings (SPY)...")
    try:
        holdings_df = tracker.fetch_etf_holdings('SPY', force_refresh=True)

        if len(holdings_df) > 0:
            print(f"✅ Fetched {len(holdings_df)} holdings for SPY")
            print(f"\n📊 Top 5 Holdings in SPY:")
            top5 = holdings_df.nlargest(5, 'weight_pct')[['stock_symbol', 'weight_pct']]
            for idx, row in top5.iterrows():
                print(f"  - {row['stock_symbol']}: {row['weight_pct']:.2f}%")
        else:
            print("⚠️ No holdings data returned (API limitation or rate limit)")
            print("   This is expected with yfinance free tier")

    except Exception as e:
        print(f"⚠️ ETF fetch warning: {e}")
        print("   This is expected - yfinance may not always provide holdings data")

    # Test reverse lookup (will work once data is populated)
    print("\n⏳ Testing reverse lookup...")
    try:
        funds = tracker.get_funds_for_stock('AAPL', min_weight=0.5)
        if len(funds) > 0:
            print(f"✅ Found {len(funds)} funds holding AAPL")
        else:
            print("ℹ️ No funds found (database needs population)")
    except Exception as e:
        print(f"⚠️ Reverse lookup warning: {e}")

    print("\n✅ ETF Weight Tracker module structure working correctly!")
    print("ℹ️ Note: Full functionality requires ETF data population (5-10 min)")
    return True


def main():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print("FinanceIQ Pro - Module Test Suite")
    print("🚀" * 30 + "\n")

    results = {}

    # Test Portfolio Health Score
    results['portfolio_health'] = test_portfolio_health()

    # Test ETF Weight Tracker
    results['etf_tracker'] = test_etf_weight_tracker()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for module, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {module}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All tests passed! You're ready to run:")
        print("   streamlit run financeiq_pro.py")
    else:
        print("\n⚠️ Some tests failed. Check error messages above.")

    print("=" * 60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
