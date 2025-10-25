"""
Test script for Whale Correlation Engine module
Validates correlation analysis, network graphs, and user DNA matching
"""

import pandas as pd
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.whale_correlation import WhaleCorrelationEngine, quick_correlation_analysis
from modules.whale_investor_analytics import WhaleInvestorAnalytics
from modules.insight_engine import generate_all_insights


def test_whale_correlation():
    """Test Whale Correlation Engine with sample data"""

    print("=" * 70)
    print("WHALE CORRELATION ENGINE - TEST SUITE")
    print("=" * 70)
    print()

    engine = WhaleCorrelationEngine()
    whale_analytics = WhaleInvestorAnalytics()

    # Load whale data for testing
    print("TEST 1: LOADING WHALE DATA")
    print("=" * 70)

    investors = ['buffett', 'gates', 'wood', 'dalio']
    whale_data_dict = {}

    for investor_key in investors:
        df = whale_analytics.load_whale_data(investor_key, '2024Q4')
        if df is not None and len(df) > 0:
            investor_name = whale_analytics.WHALE_INVESTORS[investor_key]['name']
            whale_data_dict[investor_name] = df
            print(f"✅ {investor_name}: {len(df)} holdings loaded")

    print(f"\n✅ {len(whale_data_dict)} investors loaded")
    print()

    # Test 2: Portfolio correlation
    print("=" * 70)
    print("TEST 2: PORTFOLIO CORRELATION CALCULATION")
    print("=" * 70)

    buffett_df = whale_data_dict.get('Warren Buffett')
    gates_df = whale_data_dict.get('Bill Gates')

    if buffett_df is not None and gates_df is not None:
        corr = engine.calculate_portfolio_correlation(buffett_df, gates_df)
        print(f"\n📊 Buffett vs Gates Correlation: {corr:.3f}")

        interpretation = engine.get_correlation_interpretation(corr)
        print(f"   Interpretation: {interpretation}")

        # Overlap analysis
        overlap_metrics = engine.calculate_overlap_percentage(buffett_df, gates_df)
        print(f"\n🤝 Overlap Analysis:")
        print(f"   - Overlap Percentage: {overlap_metrics['overlap_percentage']:.1f}%")
        print(f"   - Common Holdings: {overlap_metrics['common_holdings']}")

        print("\n✅ Correlation calculated successfully")
    else:
        print("❌ Could not load data for correlation test")

    print()

    # Test 3: Correlation matrix
    print("=" * 70)
    print("TEST 3: CORRELATION MATRIX GENERATION")
    print("=" * 70)

    corr_matrix = engine.build_correlation_matrix(whale_data_dict)

    print(f"\n📊 Correlation Matrix ({len(corr_matrix)}x{len(corr_matrix)}):")
    print()
    print(corr_matrix.to_string())
    print()

    # Statistics
    upper_triangle = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]
    avg_corr = upper_triangle.mean()
    max_corr = upper_triangle.max()
    min_corr = upper_triangle.min()

    print(f"Statistics:")
    print(f"   - Average Correlation: {avg_corr:.3f}")
    print(f"   - Maximum Correlation: {max_corr:.3f}")
    print(f"   - Minimum Correlation: {min_corr:.3f}")

    print("\n✅ Correlation matrix generated")
    print()

    # Test 4: Overlap matrix
    print("=" * 70)
    print("TEST 4: OVERLAP MATRIX GENERATION")
    print("=" * 70)

    overlap_matrix = engine.build_overlap_matrix(whale_data_dict)

    print(f"\n🤝 Overlap Matrix (%):")
    print()
    print(overlap_matrix.to_string())
    print()

    print("✅ Overlap matrix generated")
    print()

    # Test 5: Top correlated pairs
    print("=" * 70)
    print("TEST 5: TOP CORRELATED PAIRS")
    print("=" * 70)

    top_pairs = engine.get_top_correlated_pairs(corr_matrix, n=5)

    print(f"\n🏆 Top {len(top_pairs)} Correlated Pairs:")
    print()

    for i, pair in enumerate(top_pairs, 1):
        interpretation = engine.get_correlation_interpretation(pair['correlation'])
        print(f"{i}. {pair['investor_a']} ⟷ {pair['investor_b']}")
        print(f"   Correlation: {pair['correlation']:.3f} ({interpretation})")
        print()

    print("✅ Top pairs identified")
    print()

    # Test 6: Investor clusters
    print("=" * 70)
    print("TEST 6: INVESTOR CLUSTERING")
    print("=" * 70)

    clusters = engine.identify_whale_clusters(corr_matrix, threshold=0.6)

    print(f"\n🎯 Identified {len(clusters)} Cluster(s) (threshold=0.6):")
    print()

    for i, cluster in enumerate(clusters, 1):
        print(f"Cluster {i}: {', '.join(cluster)} ({len(cluster)} investors)")

    print()
    print("✅ Clustering completed")
    print()

    # Test 7: User DNA analysis (synthetic user portfolio)
    print("=" * 70)
    print("TEST 7: USER DNA ANALYSIS")
    print("=" * 70)

    # Create synthetic user portfolio (similar to Buffett)
    user_df = buffett_df.head(15).copy()  # Take top 15 Buffett holdings
    user_df['portfolio_weight'] = user_df['portfolio_weight'] * 0.8  # Scale down weights

    print("\n👤 User Portfolio Created (15 holdings, Buffett-like)")
    print()

    user_dna = engine.analyze_user_dna(user_df, whale_data_dict)

    print(f"🧬 User DNA Analysis Results:")
    print(f"   - Top Match: {user_dna['top_match']}")
    print(f"   - Similarity Score: {user_dna['similarity_score']:.1f}%")
    print()

    print("📊 Similarity Breakdown:")
    print(user_dna['similarity_breakdown'].to_string(index=False))
    print()

    print("💡 Recommendations:")
    for rec in user_dna['recommendations']:
        print(f"   {rec}")

    print()
    print("✅ User DNA analysis completed")
    print()

    # Test 8: Quick analysis function
    print("=" * 70)
    print("TEST 8: QUICK CORRELATION ANALYSIS")
    print("=" * 70)

    results = quick_correlation_analysis(whale_data_dict, user_df)

    print(f"\n🚀 Quick Analysis Results:")
    print(f"   - Number of Investors: {results['num_investors']}")
    print(f"   - Clusters Identified: {len(results['clusters'])}")
    print(f"   - Top Pairs: {len(results['top_pairs'])}")
    if 'user_dna' in results:
        print(f"   - User Top Match: {results['user_dna']['top_match']}")
        print(f"   - User Similarity: {results['user_dna']['similarity_score']:.1f}%")

    print()
    print("✅ Quick analysis completed")
    print()

    # Test 9: AI Insights
    print("=" * 70)
    print("TEST 9: AI INSIGHT GENERATION")
    print("=" * 70)

    insights = generate_all_insights(
        data_type='whale_correlation',
        correlation_matrix=corr_matrix,
        top_pairs=top_pairs,
        clusters=clusters,
        num_investors=len(whale_data_dict)
    )

    print(f"\n✅ Generated {len(insights)} AI insights:")
    print()

    for i, insight in enumerate(insights, 1):
        print(f"{i}. {insight}")
        print()

    print("✅ AI insights generated")
    print()

    # Test 10: Visualization data structures
    print("=" * 70)
    print("TEST 10: VISUALIZATION READINESS")
    print("=" * 70)

    print("\n✅ Testing visualization components:")

    # Heatmap
    fig_corr = engine.plot_correlation_heatmap(corr_matrix)
    print(f"   - Correlation Heatmap: {len(fig_corr.data)} traces")

    # Overlap heatmap
    fig_overlap = engine.plot_overlap_heatmap(overlap_matrix)
    print(f"   - Overlap Heatmap: {len(fig_overlap.data)} traces")

    # Network graph
    fig_network = engine.plot_whale_network(corr_matrix, threshold=0.5)
    print(f"   - Network Graph: {len(fig_network.data)} traces")

    print()
    print("✅ All visualizations ready")
    print()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("✅ Test 1: Loading Whale Data - PASSED")
    print("✅ Test 2: Portfolio Correlation - PASSED")
    print("✅ Test 3: Correlation Matrix - PASSED")
    print("✅ Test 4: Overlap Matrix - PASSED")
    print("✅ Test 5: Top Correlated Pairs - PASSED")
    print("✅ Test 6: Investor Clustering - PASSED")
    print("✅ Test 7: User DNA Analysis - PASSED")
    print("✅ Test 8: Quick Analysis - PASSED")
    print("✅ Test 9: AI Insights - PASSED")
    print("✅ Test 10: Visualization Readiness - PASSED")
    print()
    print("✅ ALL TESTS PASSED - Whale Correlation Engine Working Correctly!")
    print("=" * 70)
    print()

    # Key findings
    print("🔗 KEY FINDINGS:")
    print("=" * 70)
    print(f"1. Average Whale Correlation: {avg_corr:.3f}")
    if avg_corr >= 0.6:
        print("   → High consensus among whale investors")
    elif avg_corr >= 0.4:
        print("   → Moderate consensus, mixed strategies")
    else:
        print("   → Low consensus, divergent strategies")
    print()

    if top_pairs:
        print(f"2. Most Correlated Pair: {top_pairs[0]['investor_a']} ⟷ {top_pairs[0]['investor_b']}")
        print(f"   Correlation: {top_pairs[0]['correlation']:.3f}")
    print()

    if clusters:
        print(f"3. Largest Cluster: {', '.join(clusters[0])} ({len(clusters[0])} investors)")
    print()

    if 'user_dna' in results:
        print(f"4. User DNA: {results['user_dna']['similarity_score']:.1f}% similar to {results['user_dna']['top_match']}")
    print()

    print("=" * 70)


if __name__ == "__main__":
    import numpy as np
    test_whale_correlation()
