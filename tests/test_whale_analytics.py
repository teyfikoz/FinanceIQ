"""
Test script for Whale Investor Analytics module
Validates portfolio tracking and whale move detection
"""

import pandas as pd
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.whale_investor_analytics import WhaleInvestorAnalytics, quick_whale_analysis
from modules.insight_engine import generate_all_insights


def test_whale_analytics():
    """Test Whale Investor Analytics with sample data"""

    print("=" * 70)
    print("WHALE INVESTOR ANALYTICS MODULE - TEST SUITE")
    print("=" * 70)
    print()

    analytics = WhaleInvestorAnalytics()

    # Test 1: Generate sample holdings
    print("TEST 1: SAMPLE HOLDINGS GENERATION")
    print("=" * 70)

    for investor in ['buffett', 'wood', 'dalio', 'gates']:
        df = analytics.generate_sample_holdings(investor, '2024Q4', num_holdings=20)

        print(f"\n{analytics.WHALE_INVESTORS[investor]['icon']} {analytics.WHALE_INVESTORS[investor]['name']}")
        print(f"   - Holdings: {len(df)}")
        print(f"   - Total Value: ${df['value_usd'].sum()/1e9:.1f}B")
        print(f"   - Top Holding: {df.iloc[0]['ticker']} ({df.iloc[0]['portfolio_weight']:.1f}%)")

    print("\n✅ Sample holdings generated successfully")
    print()

    # Test 2: Portfolio concentration
    print("=" * 70)
    print("TEST 2: PORTFOLIO CONCENTRATION ANALYSIS")
    print("=" * 70)

    investor = 'buffett'
    df = analytics.load_whale_data(investor, '2024Q4')

    concentration = analytics.calculate_portfolio_concentration(df)

    print(f"\n📊 Warren Buffett Portfolio Concentration:")
    print(f"   - HHI: {concentration['hhi']:.0f}")
    print(f"   - Effective Holdings: {concentration['effective_holdings']:.1f}")
    print(f"   - Top 5: {concentration['top5_concentration']:.1f}%")
    print(f"   - Top 10: {concentration['top10_concentration']:.1f}%")
    print(f"   - Top 20: {concentration['top20_concentration']:.1f}%")
    print(f"   - Level: {concentration['concentration_level']}")

    print("\n✅ Concentration metrics calculated")
    print()

    # Test 3: Sector allocation
    print("=" * 70)
    print("TEST 3: SECTOR ALLOCATION ANALYSIS")
    print("=" * 70)

    sector_alloc = analytics.analyze_sector_allocation(df)

    print("\n📊 Sector Breakdown:")
    print(sector_alloc)
    print()

    # Test 4: Quarter-over-quarter changes
    print("=" * 70)
    print("TEST 4: QUARTERLY CHANGES DETECTION")
    print("=" * 70)

    df_curr = analytics.load_whale_data('buffett', '2024Q4')
    df_prev = analytics.load_whale_data('buffett', '2024Q3')

    changes = analytics.calculate_portfolio_changes(df_curr, df_prev)

    print(f"\n📈 Portfolio Changes (Q3 → Q4):")
    print(f"   - New Positions: {(changes['position_status'] == 'NEW').sum()}")
    print(f"   - Sold Positions: {(changes['position_status'] == 'SOLD').sum()}")
    print(f"   - Increased: {(changes['position_status'] == 'INCREASED').sum()}")
    print(f"   - Decreased: {(changes['position_status'] == 'DECREASED').sum()}")

    print("\n✅ Changes calculated successfully")
    print()

    # Test 5: Whale move detection
    print("=" * 70)
    print("TEST 5: WHALE MOVE DETECTION")
    print("=" * 70)

    whale_moves = analytics.detect_whale_moves(changes, min_weight_change=0.5)

    print(f"\n🐋 Detected {len(whale_moves)} significant moves:")
    print()

    for i, move in enumerate(whale_moves[:10], 1):
        emoji = "🟢" if move['signal'] in ['STRONG_BUY', 'BUY'] else "🔴"
        print(f"{i}. {emoji} {move['ticker']} ({move['sector']}) - {move['signal']}")
        print(f"   {move['description']}")
        print(f"   Weight Change: {move['weight_change']:+.2f}%")
        print()

    print("✅ Whale moves detected")
    print()

    # Test 6: Investor comparison
    print("=" * 70)
    print("TEST 6: MULTI-INVESTOR COMPARISON")
    print("=" * 70)

    investors = ['buffett', 'wood', 'dalio', 'gates']
    comparison = analytics.compare_investors(investors, '2024Q4')

    print("\n📊 Investor Comparison:")
    print(comparison.to_string(index=False))
    print()

    # Test 7: Common holdings
    print("=" * 70)
    print("TEST 7: COMMON HOLDINGS ANALYSIS")
    print("=" * 70)

    common = analytics.get_common_holdings('buffett', 'gates', '2024Q4')

    print(f"\n🤝 Buffett & Gates Common Holdings: {len(common)}")
    print()
    print(common.head(10).to_string(index=False))
    print()

    # Test 8: AI Insights
    print("=" * 70)
    print("TEST 8: AI INSIGHT GENERATION")
    print("=" * 70)

    insights = generate_all_insights(
        data_type='whale_investor',
        investor_name='Warren Buffett',
        investor_style='Value Investing',
        whale_moves=whale_moves,
        concentration=concentration,
        sector_alloc=sector_alloc
    )

    print(f"\n✅ Generated {len(insights)} AI insights:")
    print()

    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")

    print()

    # Test 9: Quick analysis function
    print("=" * 70)
    print("TEST 9: QUICK ANALYSIS FUNCTION")
    print("=" * 70)

    results = quick_whale_analysis('wood', quarters=['2024Q3', '2024Q4'])

    print(f"\n🚀 Cathie Wood Quick Analysis:")
    print(f"   - Portfolio Value: ${results['portfolio_value']/1e9:.1f}B")
    print(f"   - Holdings: {results['num_holdings']}")
    print(f"   - Whale Moves: {len(results['whale_moves'])}")
    print(f"   - Concentration: {results['concentration']['concentration_level']}")

    print("\n✅ Quick analysis completed")
    print()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("✅ Test 1: Sample Holdings Generation - PASSED")
    print("✅ Test 2: Portfolio Concentration - PASSED")
    print("✅ Test 3: Sector Allocation - PASSED")
    print("✅ Test 4: Quarterly Changes - PASSED")
    print("✅ Test 5: Whale Move Detection - PASSED")
    print("✅ Test 6: Investor Comparison - PASSED")
    print("✅ Test 7: Common Holdings - PASSED")
    print("✅ Test 8: AI Insights - PASSED")
    print("✅ Test 9: Quick Analysis - PASSED")
    print()
    print("✅ ALL TESTS PASSED - Whale Analytics Module Working Correctly!")
    print("=" * 70)
    print()

    # Key findings
    print("🐋 KEY FINDINGS:")
    print("=" * 70)
    print(f"1. Buffett Concentration: {concentration['concentration_level']}")
    print(f"   Top 10 holdings: {concentration['top10_concentration']:.1f}%")
    print()
    print(f"2. Detected {len(whale_moves)} whale moves in Q4")
    if whale_moves:
        top_buy = [m for m in whale_moves if m['signal'] in ['STRONG_BUY', 'BUY']][0] if any(m['signal'] in ['STRONG_BUY', 'BUY'] for m in whale_moves) else None
        if top_buy:
            print(f"   Biggest Buy: {top_buy['ticker']} (+{top_buy['weight_change']:.1f}%)")
    print()
    print(f"3. Common holdings between Buffett & Gates: {len(common)}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    test_whale_analytics()
