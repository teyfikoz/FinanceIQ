"""
Test Suite for Institutional Event Reaction Lab
Validates event reaction analysis and whale positioning tracking
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from modules.institutional_event_reaction_lab import (
    InstitutionalEventReactionLab,
    EconomicEvent,
    quick_event_reaction_analysis
)


def test_event_generation():
    """Test synthetic event generation"""
    print("\n" + "="*70)
    print("TEST 1: Event Generation")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    events = lab.generate_synthetic_events(start_date, end_date)

    print(f"✅ Generated {len(events)} events in 2024")

    # Count by type
    event_counts = {}
    for event in events:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

    print(f"✅ Event breakdown:")
    for event_type, count in event_counts.items():
        print(f"   - {event_type}: {count}")

    # Check event properties
    assert len(events) > 0, "No events generated"
    assert all(hasattr(e, 'event_type') for e in events), "Events missing event_type"
    assert all(hasattr(e, 'date') for e in events), "Events missing date"
    assert all(hasattr(e, 'impact') for e in events), "Events missing impact"

    print("\n✅ TEST 1 PASSED: Events generated successfully")
    return events


def test_portfolio_before_after_analysis():
    """Test before/after portfolio comparison"""
    print("\n" + "="*70)
    print("TEST 2: Portfolio Before/After Analysis")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    # Create mock portfolio
    portfolio_before = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'GOOGL', 'XLP', 'XLU'],
        'portfolio_weight': [10.0, 8.0, 6.0, 3.0, 2.0],
        'sector': ['XLK', 'XLK', 'XLC', 'XLP', 'XLU']
    })

    # Simulate rotation to defensive
    portfolio_after = portfolio_before.copy()
    portfolio_after.loc[portfolio_after['ticker'] == 'AAPL', 'portfolio_weight'] = 7.0  # Reduced tech
    portfolio_after.loc[portfolio_after['ticker'] == 'XLP', 'portfolio_weight'] = 5.0  # Increased defensive
    portfolio_after.loc[portfolio_after['ticker'] == 'XLU', 'portfolio_weight'] = 4.0  # Increased defensive

    # Mock event (hawkish FOMC)
    event = EconomicEvent(
        event_type='FOMC',
        date=datetime(2024, 9, 18),
        description="FOMC Meeting - Hawkish stance",
        impact='HAWKISH',
        magnitude=8.5
    )

    result = lab.analyze_portfolio_before_after(
        portfolio_before,
        portfolio_after,
        event,
        "Warren Buffett"
    )

    print(f"✅ Whale: {result['whale_name']}")
    print(f"✅ Event: {result['event'].description}")
    print(f"✅ Reaction Score: {result['reaction_score']:.1f}")
    print(f"✅ Rotation: {result['rotation']}")
    print(f"✅ Number of Changes: {result['num_changes']}")
    print(f"✅ Defensive Change: {result['defensive_change']:+.1f}%")
    print(f"✅ Growth Change: {result['growth_change']:+.1f}%")

    assert result['rotation'] in ['DEFENSIVE', 'GROWTH', 'NEUTRAL']
    assert -100 <= result['reaction_score'] <= 100

    print("\n✅ TEST 2 PASSED: Before/after analysis working")
    return result


def test_anticipatory_moves_detection():
    """Test detection of anticipatory positioning"""
    print("\n" + "="*70)
    print("TEST 3: Anticipatory Moves Detection")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    # Create mock whale moves
    whale_moves = pd.DataFrame({
        'date': [
            datetime(2024, 9, 10),  # 8 days before FOMC
            datetime(2024, 9, 15),  # 3 days before FOMC
            datetime(2024, 9, 20),  # 2 days after FOMC
        ],
        'whale': ['Buffett', 'Gates', 'Dalio'],
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'action': ['REDUCED', 'REDUCED', 'INCREASED'],
        'portfolio_weight': [8.0, 7.0, 5.0]
    })

    # Mock event (hawkish FOMC = bearish for stocks)
    events = [
        EconomicEvent(
            event_type='FOMC',
            date=datetime(2024, 9, 18),
            description="FOMC - Hawkish",
            impact='HAWKISH',
            magnitude=8.0
        )
    ]

    anticipatory = lab.detect_anticipatory_moves(whale_moves, events, lookback_days=7)

    print(f"✅ Detected {len(anticipatory)} anticipatory moves")

    for move in anticipatory:
        print(f"   - {move['whale']}: {move['action']} {move['ticker']} {move['days_before_event']} days before")

    # Both Buffett and Gates reduced tech before hawkish FOMC = anticipatory
    assert len(anticipatory) >= 1, "Should detect at least 1 anticipatory move"

    print("\n✅ TEST 3 PASSED: Anticipatory moves detected")
    return anticipatory


def test_reaction_latency_calculation():
    """Test reaction latency calculation"""
    print("\n" + "="*70)
    print("TEST 4: Reaction Latency Calculation")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    # Create mock whale moves
    whale_moves = pd.DataFrame({
        'date': [
            datetime(2024, 9, 20),  # 2 days after FOMC
            datetime(2024, 9, 22),  # 4 days after FOMC
            datetime(2024, 9, 25),  # 7 days after FOMC
        ],
        'whale': ['Buffett', 'Gates', 'Dalio'],
        'ticker': ['AAPL', 'MSFT', 'GOOGL'],
        'action': ['INCREASED', 'INCREASED', 'INCREASED'],
        'portfolio_weight': [12.0, 10.0, 8.0]
    })

    # Mock event
    events = [
        EconomicEvent(
            event_type='FOMC',
            date=datetime(2024, 9, 18),
            description="FOMC - Dovish",
            impact='DOVISH',
            magnitude=7.0
        )
    ]

    latencies = lab.calculate_reaction_latency(whale_moves, events)

    print(f"✅ Calculated latencies for {len(latencies)} whales")

    for _, row in latencies.iterrows():
        print(f"   - {row['whale']}: avg {row['avg_latency']:.1f} days, median {row['median_latency']:.1f} days")

    assert len(latencies) > 0, "Should calculate latencies"
    assert 'avg_latency' in latencies.columns

    print("\n✅ TEST 4 PASSED: Latency calculation working")
    return latencies


def test_whale_reaction_comparison():
    """Test comparison of whale reactions to same event"""
    print("\n" + "="*70)
    print("TEST 5: Whale Reaction Comparison")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    # Create mock reactions
    event = EconomicEvent(
        event_type='FOMC',
        date=datetime(2024, 9, 18),
        description="FOMC - Hawkish",
        impact='HAWKISH',
        magnitude=8.0
    )

    reactions = [
        {
            'whale_name': 'Buffett',
            'event': event,
            'reaction_score': -45.0,  # Bearish
            'rotation': 'DEFENSIVE',
            'num_changes': 8
        },
        {
            'whale_name': 'Gates',
            'event': event,
            'reaction_score': -40.0,  # Bearish
            'rotation': 'DEFENSIVE',
            'num_changes': 6
        },
        {
            'whale_name': 'Dalio',
            'event': event,
            'reaction_score': -38.0,  # Bearish
            'rotation': 'DEFENSIVE',
            'num_changes': 7
        }
    ]

    comparison = lab.compare_whale_reactions(reactions)

    print(f"✅ Event: {comparison['event'].description}")
    print(f"✅ Whales Analyzed: {comparison['num_whales']}")
    print(f"✅ Average Reaction Score: {comparison['avg_reaction_score']:.1f}")
    print(f"✅ Consensus: {comparison['consensus']}")
    print(f"✅ Most Bullish: {comparison['most_bullish_whale']} ({comparison['most_bullish_score']:.1f})")
    print(f"✅ Most Bearish: {comparison['most_bearish_whale']} ({comparison['most_bearish_score']:.1f})")

    assert comparison['consensus'] in ['STRONG_CONSENSUS', 'MODERATE_CONSENSUS', 'DIVERGENCE']
    assert comparison['num_whales'] == 3

    print("\n✅ TEST 5 PASSED: Whale comparison working")
    return comparison


def test_event_timeline_generation():
    """Test event timeline generation"""
    print("\n" + "="*70)
    print("TEST 6: Event Timeline Generation")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    # Generate events
    events = lab.generate_synthetic_events(datetime(2024, 1, 1), datetime(2024, 3, 31))

    # Create mock whale moves
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
    n_dates = len(dates)

    whale_moves = pd.DataFrame({
        'date': dates,
        'whale': np.random.choice(['Buffett', 'Gates', 'Dalio'], size=n_dates),
        'ticker': np.random.choice(['AAPL', 'MSFT', 'GOOGL'], size=n_dates),
        'action': np.random.choice(['NEW', 'INCREASED', 'REDUCED'], size=n_dates),
        'portfolio_weight': np.random.uniform(1, 10, size=n_dates)
    })

    timeline = lab.generate_event_timeline(events, whale_moves, window_days=7)

    print(f"✅ Generated timeline with {len(timeline)} events")
    print(f"✅ Columns: {list(timeline.columns)}")

    if len(timeline) > 0:
        print(f"✅ Sample event:")
        sample = timeline.iloc[0]
        print(f"   - Type: {sample['event_type']}")
        print(f"   - Date: {sample['date']}")
        print(f"   - Pre-event moves: {sample['pre_event_moves']}")
        print(f"   - Post-event moves: {sample['post_event_moves']}")

    assert len(timeline) > 0, "Timeline should have events"
    assert 'total_whale_activity' in timeline.columns

    print("\n✅ TEST 6 PASSED: Event timeline generated")
    return timeline


def test_event_sensitivity_score():
    """Test event sensitivity scoring"""
    print("\n" + "="*70)
    print("TEST 7: Event Sensitivity Score")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    # Create mock reactions for multiple events
    reactions = []

    for i in range(5):
        event = EconomicEvent(
            event_type=np.random.choice(['FOMC', 'CPI', 'JOBS']),
            date=datetime(2024, i+1, 15),
            description=f"Event {i+1}",
            impact='HAWKISH',
            magnitude=7.0
        )

        reactions.append({
            'whale_name': 'Buffett',
            'event': event,
            'reaction_score': np.random.uniform(-50, 50),
            'rotation': 'DEFENSIVE',
            'num_changes': 5
        })

    sensitivity = lab.calculate_event_sensitivity_score('Buffett', reactions)

    print(f"✅ Whale: {sensitivity['whale_name']}")
    print(f"✅ Overall Sensitivity: {sensitivity['overall_sensitivity']:.1f}")
    print(f"✅ Total Events Reacted: {sensitivity['total_events_reacted']}")
    print(f"✅ Event Type Sensitivity:")
    for event_type, scores in sensitivity['event_type_sensitivity'].items():
        print(f"   - {event_type}: {scores['avg_sensitivity']:.1f} (n={scores['num_events']})")

    assert 0 <= sensitivity['overall_sensitivity'] <= 100

    print("\n✅ TEST 7 PASSED: Event sensitivity calculated")
    return sensitivity


def test_sector_rotation_detection():
    """Test sector rotation detection"""
    print("\n" + "="*70)
    print("TEST 8: Sector Rotation Detection")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    # Portfolio with growth sectors
    portfolio_before = pd.DataFrame({
        'ticker': ['AAPL', 'MSFT', 'TSLA', 'XLP', 'XLU'],
        'portfolio_weight': [15.0, 12.0, 8.0, 2.0, 1.0],
        'sector': ['XLK', 'XLK', 'XLY', 'XLP', 'XLU']  # Growth heavy
    })

    # Rotate to defensive
    portfolio_after = portfolio_before.copy()
    portfolio_after.loc[portfolio_after['ticker'] == 'AAPL', 'portfolio_weight'] = 10.0  # -5%
    portfolio_after.loc[portfolio_after['ticker'] == 'MSFT', 'portfolio_weight'] = 8.0   # -4%
    portfolio_after.loc[portfolio_after['ticker'] == 'TSLA', 'portfolio_weight'] = 5.0   # -3%
    portfolio_after.loc[portfolio_after['ticker'] == 'XLP', 'portfolio_weight'] = 7.0    # +5%
    portfolio_after.loc[portfolio_after['ticker'] == 'XLU', 'portfolio_weight'] = 6.0    # +5%

    event = EconomicEvent(
        event_type='FOMC',
        date=datetime.now(),
        description="Hawkish FOMC",
        impact='HAWKISH',
        magnitude=9.0
    )

    result = lab.analyze_portfolio_before_after(
        portfolio_before,
        portfolio_after,
        event,
        "Test Whale"
    )

    print(f"✅ Rotation Detected: {result['rotation']}")
    print(f"✅ Defensive Change: {result['defensive_change']:+.1f}%")
    print(f"✅ Growth Change: {result['growth_change']:+.1f}%")
    print(f"✅ Reaction Score: {result['reaction_score']:.1f}")

    # Should detect defensive rotation (negative reaction score)
    assert result['rotation'] in ['DEFENSIVE', 'GROWTH', 'NEUTRAL']
    assert result['defensive_change'] > 0, "Defensive sectors should increase"
    assert result['reaction_score'] < 0, "Should be negative (risk-off)"

    print("\n✅ TEST 8 PASSED: Sector rotation detected correctly")
    return result


def test_quick_event_reaction_analysis():
    """Test quick analysis wrapper"""
    print("\n" + "="*70)
    print("TEST 9: Quick Event Reaction Analysis")
    print("="*70)

    # Create mock whale portfolios
    whale_portfolios = {}

    for whale_name in ['Buffett', 'Gates', 'Dalio']:
        portfolio = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT', 'GOOGL', 'XLP', 'XLU', 'XLV'],
            'portfolio_weight': np.random.uniform(2, 15, 6),
            'sector': ['XLK', 'XLK', 'XLC', 'XLP', 'XLU', 'XLV']
        })
        whale_portfolios[whale_name] = portfolio

    # Generate events
    events = [
        EconomicEvent(
            event_type='FOMC',
            date=datetime(2024, 9, 18),
            description="FOMC - Hawkish",
            impact='HAWKISH',
            magnitude=8.5
        ),
        EconomicEvent(
            event_type='CPI',
            date=datetime(2024, 10, 13),
            description="CPI - Beat expectations",
            impact='BEAT',
            magnitude=7.0
        )
    ]

    results = quick_event_reaction_analysis(whale_portfolios, events)

    print(f"✅ Analysis complete")
    print(f"✅ Events Analyzed: {results['num_events']}")
    print(f"✅ Whales Analyzed: {results['num_whales']}")
    print(f"✅ Event Analyses: {len(results['event_analyses'])}")

    assert results['num_events'] == 2
    assert results['num_whales'] == 3
    assert len(results['event_analyses']) == 2

    print("\n✅ TEST 9 PASSED: Quick analysis wrapper working")
    return results


def test_consensus_vs_divergence():
    """Test consensus vs divergence detection"""
    print("\n" + "="*70)
    print("TEST 10: Consensus vs Divergence Detection")
    print("="*70)

    lab = InstitutionalEventReactionLab()

    event = EconomicEvent(
        event_type='FOMC',
        date=datetime.now(),
        description="Test FOMC",
        impact='HAWKISH',
        magnitude=8.0
    )

    # Test 1: Strong consensus (all similar)
    consensus_reactions = [
        {'whale_name': 'W1', 'event': event, 'reaction_score': -42.0, 'rotation': 'DEFENSIVE', 'num_changes': 5},
        {'whale_name': 'W2', 'event': event, 'reaction_score': -40.0, 'rotation': 'DEFENSIVE', 'num_changes': 4},
        {'whale_name': 'W3', 'event': event, 'reaction_score': -38.0, 'rotation': 'DEFENSIVE', 'num_changes': 6}
    ]

    result1 = lab.compare_whale_reactions(consensus_reactions)
    print(f"✅ Test 1 - Similar reactions: {result1['consensus']} (std={result1['std_reaction_score']:.1f})")
    assert result1['consensus'] in ['STRONG_CONSENSUS', 'MODERATE_CONSENSUS']

    # Test 2: Divergence (very different)
    divergence_reactions = [
        {'whale_name': 'W1', 'event': event, 'reaction_score': +60.0, 'rotation': 'GROWTH', 'num_changes': 5},
        {'whale_name': 'W2', 'event': event, 'reaction_score': -10.0, 'rotation': 'NEUTRAL', 'num_changes': 2},
        {'whale_name': 'W3', 'event': event, 'reaction_score': -70.0, 'rotation': 'DEFENSIVE', 'num_changes': 8}
    ]

    result2 = lab.compare_whale_reactions(divergence_reactions)
    print(f"✅ Test 2 - Different reactions: {result2['consensus']} (std={result2['std_reaction_score']:.1f})")
    assert result2['consensus'] == 'DIVERGENCE'

    print("\n✅ TEST 10 PASSED: Consensus/divergence detection working")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("🚀 INSTITUTIONAL EVENT REACTION LAB - COMPREHENSIVE TEST SUITE")
    print("="*70)

    try:
        # Run all tests
        test_event_generation()
        test_portfolio_before_after_analysis()
        test_anticipatory_moves_detection()
        test_reaction_latency_calculation()
        test_whale_reaction_comparison()
        test_event_timeline_generation()
        test_event_sensitivity_score()
        test_sector_rotation_detection()
        test_quick_event_reaction_analysis()
        test_consensus_vs_divergence()

        print("\n" + "="*70)
        print("✅ ALL 10 TESTS PASSED!")
        print("="*70)
        print("\n🎉 Institutional Event Reaction Lab is working correctly!")
        print("📅 Event generation validated")
        print("📊 Before/after portfolio analysis validated")
        print("🔮 Anticipatory move detection validated")
        print("⏱️ Reaction latency calculation validated")
        print("🔄 Sector rotation detection validated")
        print("🤝 Consensus vs divergence detection validated")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
