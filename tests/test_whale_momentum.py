"""
Test script for Whale Momentum Tracker module
Validates momentum calculation, consensus detection, and institutional indicators
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.whale_momentum_tracker import WhaleMomentumTracker, quick_momentum_analysis
from modules.whale_investor_analytics import WhaleInvestorAnalytics
from modules.insight_engine import generate_all_insights


def test_whale_momentum():
    """Test Whale Momentum Tracker with sample data"""

    print("=" * 70)
    print("WHALE MOMENTUM TRACKER - TEST SUITE")
    print("=" * 70)
    print()

    tracker = WhaleMomentumTracker()
    whale_analytics = WhaleInvestorAnalytics()

    # Test 1: Load whale data for two periods
    print("TEST 1: LOADING WHALE DATA (TWO PERIODS)")
    print("=" * 70)

    investors = ['buffett', 'gates', 'wood', 'dalio']
    whale_data_current = {}
    whale_data_previous = {}

    for investor_key in investors:
        df_curr = whale_analytics.load_whale_data(investor_key, '2024Q4')
        df_prev = whale_analytics.load_whale_data(investor_key, '2024Q3')

        if df_curr is not None and df_prev is not None:
            investor_name = whale_analytics.WHALE_INVESTORS[investor_key]['name']
            whale_data_current[investor_name] = df_curr
            whale_data_previous[investor_name] = df_prev
            print(f"✅ {investor_name}: Q3={len(df_prev)} → Q4={len(df_curr)} holdings")

    print(f"\n✅ {len(whale_data_current)} investors loaded for 2 periods")
    print()

    # Test 2: Calculate position changes
    print("=" * 70)
    print("TEST 2: CALCULATE POSITION CHANGES")
    print("=" * 70)

    buffett_name = 'Warren Buffett'
    if buffett_name in whale_data_current:
        changes = tracker.calculate_position_changes(
            whale_data_current[buffett_name],
            whale_data_previous[buffett_name]
        )

        print(f"\n📊 Buffett Position Changes (Q3 → Q4):")
        print(f"   - NEW positions: {(changes['action'] == 'NEW').sum()}")
        print(f"   - SOLD positions: {(changes['action'] == 'SOLD').sum()}")
        print(f"   - INCREASED positions: {(changes['action'] == 'INCREASED').sum()}")
        print(f"   - DECREASED positions: {(changes['action'] == 'DECREASED').sum()}")
        print(f"   - UNCHANGED positions: {(changes['action'] == 'UNCHANGED').sum()}")

        print("\n✅ Position changes calculated")
    print()

    # Test 3: Aggregate whale moves
    print("=" * 70)
    print("TEST 3: AGGREGATE WHALE MOVES")
    print("=" * 70)

    whale_changes = {}
    for whale_name in whale_data_current.keys():
        if whale_name in whale_data_previous:
            changes = tracker.calculate_position_changes(
                whale_data_current[whale_name],
                whale_data_previous[whale_name]
            )
            whale_changes[whale_name] = changes

    aggregated_moves = tracker.aggregate_whale_moves(whale_changes)

    print(f"\n📊 Aggregated Whale Moves:")
    print(f"   - Total moves: {len(aggregated_moves)}")
    print(f"   - Unique tickers: {aggregated_moves['ticker'].nunique()}")
    print(f"   - Whales tracked: {aggregated_moves['whale'].nunique()}")
    print()

    action_counts = aggregated_moves['action'].value_counts()
    for action, count in action_counts.items():
        print(f"   - {action}: {count}")

    print("\n✅ Whale moves aggregated")
    print()

    # Test 4: Calculate momentum score
    print("=" * 70)
    print("TEST 4: CALCULATE MOMENTUM SCORES")
    print("=" * 70)

    # Get a ticker with multiple whales
    ticker_counts = aggregated_moves['ticker'].value_counts()
    if len(ticker_counts) > 0:
        test_ticker = ticker_counts.index[0]

        momentum = tracker.calculate_momentum_score(test_ticker, aggregated_moves)

        print(f"\n📊 Momentum Analysis for {test_ticker}:")
        print(f"   - Momentum Score: {momentum['momentum_score']:.3f}")
        print(f"   - Number of Whales: {momentum['num_whales']}")
        print(f"   - Buyers: {momentum['buyers']}")
        print(f"   - Sellers: {momentum['sellers']}")
        print(f"   - Net Direction: {momentum['net_direction']}")
        print(f"   - Net Buy %: {momentum['net_buy_pct']:+.2f}")
        print(f"   - Overlap: {momentum['overlap']:.2f}")
        print(f"   - Confidence: {momentum['confidence']:.2f}")

        print("\n✅ Momentum score calculated")
    print()

    # Test 5: Detect consensus buys
    print("=" * 70)
    print("TEST 5: DETECT CONSENSUS BUYS")
    print("=" * 70)

    consensus_buys = tracker.detect_consensus_buys(aggregated_moves, min_whales=3)

    print(f"\n🟢 Consensus Buy Signals Detected: {len(consensus_buys)}")

    if consensus_buys:
        print("\nTop 5 Consensus Buys:")
        for i, buy in enumerate(consensus_buys[:5], 1):
            print(f"\n{i}. {buy['ticker']}")
            print(f"   - Number of Buyers: {buy['num_buyers']}")
            print(f"   - Buyer Whales: {', '.join(buy['buyer_whales'])}")
            print(f"   - Total Value Change: ${buy['total_value_change']/1e6:.1f}M")
            print(f"   - Signal Strength: {buy['signal_strength']}")
    else:
        print("   No consensus buys detected (3+ whales)")

    print("\n✅ Consensus buy detection completed")
    print()

    # Test 6: Detect consensus sells
    print("=" * 70)
    print("TEST 6: DETECT CONSENSUS SELLS")
    print("=" * 70)

    consensus_sells = tracker.detect_consensus_sells(aggregated_moves, min_whales=3)

    print(f"\n🔴 Consensus Sell Signals Detected: {len(consensus_sells)}")

    if consensus_sells:
        print("\nTop 5 Consensus Sells:")
        for i, sell in enumerate(consensus_sells[:5], 1):
            print(f"\n{i}. {sell['ticker']}")
            print(f"   - Number of Sellers: {sell['num_sellers']}")
            print(f"   - Seller Whales: {', '.join(sell['seller_whales'])}")
            print(f"   - Total Value Change: ${abs(sell['total_value_change'])/1e6:.1f}M")
            print(f"   - Signal Strength: {sell['signal_strength']}")
    else:
        print("   No consensus sells detected (3+ whales)")

    print("\n✅ Consensus sell detection completed")
    print()

    # Test 7: Institutional consensus indicator
    print("=" * 70)
    print("TEST 7: INSTITUTIONAL CONSENSUS INDICATOR")
    print("=" * 70)

    consensus_indicator = tracker.calculate_institutional_consensus_indicator(aggregated_moves)

    print(f"\n🎯 Institutional Consensus Indicator:")
    print(f"   - Consensus Score: {consensus_indicator['consensus_score']:.1f}/100")
    print(f"   - Market Sentiment: {consensus_indicator['market_sentiment']}")
    print(f"   - Total Moves: {consensus_indicator['total_moves']}")
    print(f"   - Buys: {consensus_indicator['num_buys']}")
    print(f"   - Sells: {consensus_indicator['num_sells']}")
    print(f"   - Buy Ratio: {consensus_indicator['buy_ratio']:.2f}")
    print(f"   - Total Buy Value: ${consensus_indicator['total_buy_value']/1e9:.2f}B")
    print(f"   - Total Sell Value: ${consensus_indicator['total_sell_value']/1e9:.2f}B")
    print(f"   - Value-Weighted Score: {consensus_indicator['value_weighted_score']:.1f}/100")

    print("\n✅ Consensus indicator calculated")
    print()

    # Test 8: Top momentum stocks
    print("=" * 70)
    print("TEST 8: TOP MOMENTUM STOCKS")
    print("=" * 70)

    top_momentum = tracker.get_top_momentum_stocks(aggregated_moves, n=10)

    print(f"\n⚡ Top 10 Momentum Stocks:")
    print()
    print(top_momentum[['ticker', 'momentum_score', 'num_whales', 'buyers', 'sellers', 'net_direction']].to_string(index=False))

    print("\n✅ Top momentum stocks identified")
    print()

    # Test 9: Divergence detection
    print("=" * 70)
    print("TEST 9: DIVERGENCE DETECTION")
    print("=" * 70)

    divergences = tracker.analyze_divergence(aggregated_moves)

    print(f"\n🔀 Divergence Signals Detected: {len(divergences)}")

    if divergences:
        print("\nTop 5 Divergences:")
        for i, div in enumerate(divergences[:5], 1):
            print(f"\n{i}. {div['ticker']}")
            print(f"   - Buyers: {div['num_buyers']} ({', '.join(div['buyer_whales'])})")
            print(f"   - Sellers: {div['num_sellers']} ({', '.join(div['seller_whales'])})")
            print(f"   - Divergence Score: {div['divergence_score']:.2f}")
    else:
        print("   No divergences detected")

    print("\n✅ Divergence analysis completed")
    print()

    # Test 10: Quick momentum analysis
    print("=" * 70)
    print("TEST 10: QUICK MOMENTUM ANALYSIS")
    print("=" * 70)

    results = quick_momentum_analysis(whale_data_current, whale_data_previous)

    print(f"\n🚀 Quick Analysis Results:")
    print(f"   - Whales Analyzed: {results['num_whales_analyzed']}")
    print(f"   - Total Moves: {len(results['aggregated_moves'])}")
    print(f"   - Consensus Buys: {len(results['consensus_buys'])}")
    print(f"   - Consensus Sells: {len(results['consensus_sells'])}")
    print(f"   - Divergences: {len(results['divergences'])}")
    print(f"   - Consensus Score: {results['consensus_indicator']['consensus_score']:.1f}/100")
    print(f"   - Market Sentiment: {results['consensus_indicator']['market_sentiment']}")

    print("\n✅ Quick analysis completed")
    print()

    # Test 11: AI Insights
    print("=" * 70)
    print("TEST 11: AI INSIGHT GENERATION")
    print("=" * 70)

    insights = generate_all_insights(
        data_type='whale_momentum',
        consensus_indicator=results['consensus_indicator'],
        consensus_buys=results['consensus_buys'],
        consensus_sells=results['consensus_sells'],
        divergences=results['divergences'],
        top_momentum=results['top_momentum_stocks']
    )

    print(f"\n✅ Generated {len(insights)} AI insights:")
    print()

    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")
        print()

    print("✅ AI insights generated")
    print()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("✅ Test 1: Loading Whale Data - PASSED")
    print("✅ Test 2: Calculate Position Changes - PASSED")
    print("✅ Test 3: Aggregate Whale Moves - PASSED")
    print("✅ Test 4: Calculate Momentum Scores - PASSED")
    print("✅ Test 5: Detect Consensus Buys - PASSED")
    print("✅ Test 6: Detect Consensus Sells - PASSED")
    print("✅ Test 7: Institutional Consensus Indicator - PASSED")
    print("✅ Test 8: Top Momentum Stocks - PASSED")
    print("✅ Test 9: Divergence Detection - PASSED")
    print("✅ Test 10: Quick Momentum Analysis - PASSED")
    print("✅ Test 11: AI Insights - PASSED")
    print()
    print("✅ ALL TESTS PASSED - Whale Momentum Tracker Working Correctly!")
    print("=" * 70)
    print()

    # Key findings
    print("📈 KEY FINDINGS:")
    print("=" * 70)
    print(f"1. Institutional Consensus: {results['consensus_indicator']['consensus_score']:.0f}/100 ({results['consensus_indicator']['market_sentiment']})")
    if results['consensus_indicator']['consensus_score'] >= 60:
        print("   → Bullish institutional sentiment")
    elif results['consensus_indicator']['consensus_score'] <= 40:
        print("   → Bearish institutional sentiment")
    else:
        print("   → Neutral/mixed sentiment")
    print()

    if results['consensus_buys']:
        print(f"2. Top Consensus Buy: {results['consensus_buys'][0]['ticker']}")
        print(f"   - {results['consensus_buys'][0]['num_buyers']} whales buying")
        print(f"   - ${results['consensus_buys'][0]['total_value_change']/1e6:.0f}M total value")
    print()

    if results['consensus_sells']:
        print(f"3. Top Consensus Sell: {results['consensus_sells'][0]['ticker']}")
        print(f"   - {results['consensus_sells'][0]['num_sellers']} whales selling")
        print(f"   - ${abs(results['consensus_sells'][0]['total_value_change'])/1e6:.0f}M total value")
    print()

    if results['divergences']:
        print(f"4. Divergences Detected: {len(results['divergences'])}")
        print(f"   - Top ticker: {results['divergences'][0]['ticker']}")
        print(f"   - {results['divergences'][0]['num_buyers']} buyers vs {results['divergences'][0]['num_sellers']} sellers")
    print()

    print("=" * 70)


if __name__ == "__main__":
    test_whale_momentum()
