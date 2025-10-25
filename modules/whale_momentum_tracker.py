"""
Whale Momentum Tracker - Institutional buying/selling momentum analysis
Tracks which whales are buying/selling the same stocks and calculates momentum scores
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class WhaleMomentumTracker:
    """
    Analyzes whale buying/selling momentum across multiple investors
    Detects institutional consensus and divergence signals
    """

    def __init__(self):
        """Initialize Whale Momentum Tracker"""
        self.momentum_threshold_high = 0.7
        self.momentum_threshold_medium = 0.5
        self.consensus_threshold = 3  # Minimum whales for consensus

    def calculate_position_changes(
        self,
        current_holdings: pd.DataFrame,
        previous_holdings: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate position changes between two periods

        Args:
            current_holdings: Current quarter holdings
            previous_holdings: Previous quarter holdings

        Returns:
            DataFrame with position changes and direction
        """
        # Merge current and previous
        merged = pd.merge(
            current_holdings[['ticker', 'shares', 'value_usd', 'portfolio_weight']],
            previous_holdings[['ticker', 'shares', 'value_usd', 'portfolio_weight']],
            on='ticker',
            how='outer',
            suffixes=('_curr', '_prev')
        ).fillna(0)

        # Calculate changes
        merged['shares_change'] = merged['shares_curr'] - merged['shares_prev']
        merged['value_change'] = merged['value_usd_curr'] - merged['value_usd_prev']
        merged['weight_change'] = merged['portfolio_weight_curr'] - merged['portfolio_weight_prev']

        # Determine action
        def determine_action(row):
            if row['shares_prev'] == 0:
                return 'NEW'
            elif row['shares_curr'] == 0:
                return 'SOLD'
            elif row['shares_change'] > 0:
                return 'INCREASED'
            elif row['shares_change'] < 0:
                return 'DECREASED'
            else:
                return 'UNCHANGED'

        merged['action'] = merged.apply(determine_action, axis=1)

        # Calculate percentage changes
        merged['shares_change_pct'] = np.where(
            merged['shares_prev'] != 0,
            (merged['shares_change'] / merged['shares_prev']) * 100,
            0
        )

        return merged

    def aggregate_whale_moves(
        self,
        whale_changes_dict: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Aggregate position changes across all whales

        Args:
            whale_changes_dict: Dict mapping whale names to their position changes

        Returns:
            DataFrame with aggregated moves per ticker
        """
        all_moves = []

        for whale_name, changes_df in whale_changes_dict.items():
            for _, row in changes_df.iterrows():
                if row['action'] in ['NEW', 'INCREASED', 'SOLD', 'DECREASED']:
                    all_moves.append({
                        'ticker': row['ticker'],
                        'whale': whale_name,
                        'action': row['action'],
                        'shares_change': row['shares_change'],
                        'value_change': row['value_change'],
                        'weight_change': row['weight_change'],
                        'shares_change_pct': row['shares_change_pct']
                    })

        return pd.DataFrame(all_moves)

    def calculate_momentum_score(
        self,
        ticker: str,
        aggregated_moves: pd.DataFrame
    ) -> Dict:
        """
        Calculate momentum score for a specific ticker

        Momentum Score = (Net Buy % + Overlap × Confidence) / 2

        Args:
            ticker: Stock ticker
            aggregated_moves: Aggregated whale moves DataFrame

        Returns:
            Dict with momentum metrics
        """
        ticker_moves = aggregated_moves[aggregated_moves['ticker'] == ticker]

        if len(ticker_moves) == 0:
            return {
                'ticker': ticker,
                'momentum_score': 0,
                'num_whales': 0,
                'buyers': 0,
                'sellers': 0,
                'net_direction': 'NEUTRAL'
            }

        # Count buyers and sellers
        buyers = ticker_moves[ticker_moves['action'].isin(['NEW', 'INCREASED'])]
        sellers = ticker_moves[ticker_moves['action'].isin(['SOLD', 'DECREASED'])]

        num_buyers = len(buyers)
        num_sellers = len(sellers)
        total_whales = num_buyers + num_sellers

        # Net buy percentage
        net_buy_pct = (num_buyers - num_sellers) / total_whales if total_whales > 0 else 0

        # Overlap (how many whales are involved)
        overlap = total_whales / len(aggregated_moves['whale'].unique())

        # Confidence (based on magnitude of changes)
        avg_weight_change = ticker_moves['weight_change'].abs().mean()
        confidence = min(avg_weight_change / 2.0, 1.0)  # Normalize to 0-1

        # Momentum score
        momentum_score = ((net_buy_pct + 1) / 2 * 0.5 + overlap * 0.3 + confidence * 0.2)

        # Net direction
        if net_buy_pct > 0.3:
            net_direction = 'BULLISH'
        elif net_buy_pct < -0.3:
            net_direction = 'BEARISH'
        else:
            net_direction = 'NEUTRAL'

        return {
            'ticker': ticker,
            'momentum_score': momentum_score,
            'num_whales': total_whales,
            'buyers': num_buyers,
            'sellers': num_sellers,
            'net_buy_pct': net_buy_pct,
            'overlap': overlap,
            'confidence': confidence,
            'net_direction': net_direction,
            'avg_weight_change': avg_weight_change,
            'buyer_whales': buyers['whale'].tolist(),
            'seller_whales': sellers['whale'].tolist()
        }

    def detect_consensus_buys(
        self,
        aggregated_moves: pd.DataFrame,
        min_whales: int = 3
    ) -> List[Dict]:
        """
        Detect stocks where multiple whales are buying (consensus)

        Args:
            aggregated_moves: Aggregated whale moves
            min_whales: Minimum number of whales for consensus

        Returns:
            List of consensus buy signals
        """
        # Get unique tickers
        tickers = aggregated_moves['ticker'].unique()

        consensus_buys = []

        for ticker in tickers:
            ticker_moves = aggregated_moves[aggregated_moves['ticker'] == ticker]

            # Count buyers
            buyers = ticker_moves[ticker_moves['action'].isin(['NEW', 'INCREASED'])]

            if len(buyers) >= min_whales:
                # Calculate total value change
                total_value_change = buyers['value_change'].sum()

                consensus_buys.append({
                    'ticker': ticker,
                    'num_buyers': len(buyers),
                    'buyer_whales': buyers['whale'].tolist(),
                    'total_value_change': total_value_change,
                    'avg_weight_change': buyers['weight_change'].mean(),
                    'signal_strength': 'STRONG' if len(buyers) >= 5 else 'MODERATE'
                })

        # Sort by number of buyers
        consensus_buys = sorted(consensus_buys, key=lambda x: x['num_buyers'], reverse=True)

        return consensus_buys

    def detect_consensus_sells(
        self,
        aggregated_moves: pd.DataFrame,
        min_whales: int = 3
    ) -> List[Dict]:
        """
        Detect stocks where multiple whales are selling (consensus)

        Args:
            aggregated_moves: Aggregated whale moves
            min_whales: Minimum number of whales for consensus

        Returns:
            List of consensus sell signals
        """
        tickers = aggregated_moves['ticker'].unique()

        consensus_sells = []

        for ticker in tickers:
            ticker_moves = aggregated_moves[aggregated_moves['ticker'] == ticker]

            # Count sellers
            sellers = ticker_moves[ticker_moves['action'].isin(['SOLD', 'DECREASED'])]

            if len(sellers) >= min_whales:
                total_value_change = sellers['value_change'].sum()

                consensus_sells.append({
                    'ticker': ticker,
                    'num_sellers': len(sellers),
                    'seller_whales': sellers['whale'].tolist(),
                    'total_value_change': total_value_change,
                    'avg_weight_change': sellers['weight_change'].mean(),
                    'signal_strength': 'STRONG' if len(sellers) >= 5 else 'MODERATE'
                })

        consensus_sells = sorted(consensus_sells, key=lambda x: x['num_sellers'], reverse=True)

        return consensus_sells

    def calculate_institutional_consensus_indicator(
        self,
        aggregated_moves: pd.DataFrame
    ) -> Dict:
        """
        Calculate overall institutional consensus indicator (0-100)

        Returns:
            Dict with consensus metrics
        """
        if len(aggregated_moves) == 0:
            return {
                'consensus_score': 50,
                'market_sentiment': 'NEUTRAL',
                'total_moves': 0
            }

        # Count all actions
        buys = aggregated_moves[aggregated_moves['action'].isin(['NEW', 'INCREASED'])]
        sells = aggregated_moves[aggregated_moves['action'].isin(['SOLD', 'DECREASED'])]

        num_buys = len(buys)
        num_sells = len(sells)
        total_moves = num_buys + num_sells

        # Consensus score (0-100)
        # 50 = neutral, >50 = bullish, <50 = bearish
        buy_ratio = num_buys / total_moves if total_moves > 0 else 0.5
        consensus_score = buy_ratio * 100

        # Market sentiment
        if consensus_score >= 65:
            market_sentiment = 'BULLISH'
        elif consensus_score >= 55:
            market_sentiment = 'MILDLY_BULLISH'
        elif consensus_score >= 45:
            market_sentiment = 'NEUTRAL'
        elif consensus_score >= 35:
            market_sentiment = 'MILDLY_BEARISH'
        else:
            market_sentiment = 'BEARISH'

        # Value-weighted sentiment
        total_buy_value = buys['value_change'].sum()
        total_sell_value = abs(sells['value_change'].sum())
        total_value = total_buy_value + total_sell_value

        value_weighted_score = (total_buy_value / total_value * 100) if total_value > 0 else 50

        return {
            'consensus_score': consensus_score,
            'value_weighted_score': value_weighted_score,
            'market_sentiment': market_sentiment,
            'total_moves': total_moves,
            'num_buys': num_buys,
            'num_sells': num_sells,
            'buy_ratio': buy_ratio,
            'total_buy_value': total_buy_value,
            'total_sell_value': total_sell_value
        }

    def get_top_momentum_stocks(
        self,
        aggregated_moves: pd.DataFrame,
        n: int = 20
    ) -> pd.DataFrame:
        """
        Get top N stocks by momentum score

        Args:
            aggregated_moves: Aggregated whale moves
            n: Number of top stocks

        Returns:
            DataFrame with top momentum stocks
        """
        tickers = aggregated_moves['ticker'].unique()

        momentum_scores = []

        for ticker in tickers:
            score_dict = self.calculate_momentum_score(ticker, aggregated_moves)
            momentum_scores.append(score_dict)

        df = pd.DataFrame(momentum_scores)

        # Sort by momentum score
        df = df.sort_values('momentum_score', ascending=False)

        return df.head(n)

    def analyze_divergence(
        self,
        aggregated_moves: pd.DataFrame
    ) -> List[Dict]:
        """
        Find stocks where whales are diverging (some buying, some selling)

        Returns:
            List of divergence signals
        """
        tickers = aggregated_moves['ticker'].unique()

        divergences = []

        for ticker in tickers:
            ticker_moves = aggregated_moves[aggregated_moves['ticker'] == ticker]

            buyers = ticker_moves[ticker_moves['action'].isin(['NEW', 'INCREASED'])]
            sellers = ticker_moves[ticker_moves['action'].isin(['SOLD', 'DECREASED'])]

            # Divergence = both buyers and sellers present
            if len(buyers) >= 2 and len(sellers) >= 2:
                divergences.append({
                    'ticker': ticker,
                    'num_buyers': len(buyers),
                    'num_sellers': len(sellers),
                    'buyer_whales': buyers['whale'].tolist(),
                    'seller_whales': sellers['whale'].tolist(),
                    'total_whales': len(buyers) + len(sellers),
                    'divergence_score': min(len(buyers), len(sellers)) / max(len(buyers), len(sellers))
                })

        # Sort by divergence score (higher = more balanced divergence)
        divergences = sorted(divergences, key=lambda x: x['divergence_score'], reverse=True)

        return divergences


def quick_momentum_analysis(
    whale_data_current: Dict[str, pd.DataFrame],
    whale_data_previous: Dict[str, pd.DataFrame]
) -> Dict:
    """
    Quick momentum analysis wrapper function

    Args:
        whale_data_current: Current quarter whale holdings
        whale_data_previous: Previous quarter whale holdings

    Returns:
        Dict with all momentum metrics
    """
    tracker = WhaleMomentumTracker()

    # Calculate position changes for each whale
    whale_changes = {}

    for whale_name in whale_data_current.keys():
        if whale_name in whale_data_previous:
            changes = tracker.calculate_position_changes(
                whale_data_current[whale_name],
                whale_data_previous[whale_name]
            )
            whale_changes[whale_name] = changes

    # Aggregate all moves
    aggregated_moves = tracker.aggregate_whale_moves(whale_changes)

    # Calculate metrics
    consensus_buys = tracker.detect_consensus_buys(aggregated_moves, min_whales=3)
    consensus_sells = tracker.detect_consensus_sells(aggregated_moves, min_whales=3)
    consensus_indicator = tracker.calculate_institutional_consensus_indicator(aggregated_moves)
    top_momentum = tracker.get_top_momentum_stocks(aggregated_moves, n=20)
    divergences = tracker.analyze_divergence(aggregated_moves)

    return {
        'aggregated_moves': aggregated_moves,
        'consensus_buys': consensus_buys,
        'consensus_sells': consensus_sells,
        'consensus_indicator': consensus_indicator,
        'top_momentum_stocks': top_momentum,
        'divergences': divergences,
        'num_whales_analyzed': len(whale_changes)
    }
