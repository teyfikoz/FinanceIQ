"""
Hedge Fund Activity Radar - Multi-source institutional activity tracking
Combines 13F filings, short interest, options data, and insider transactions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class HedgeFundActivityRadar:
    """
    Tracks and scores hedge fund activity from multiple data sources
    Provides composite activity score and unusual activity detection
    """

    def __init__(self):
        """Initialize Hedge Fund Activity Radar"""
        self.activity_types = ['13F', 'SHORT', 'OPTIONS', 'INSIDER']

        # Sentiment weights for different activity types
        self.sentiment_weights = {
            '13F_BUY': +1.0,
            '13F_SELL': -1.0,
            'SHORT_INCREASE': -0.8,
            'SHORT_DECREASE': +0.6,
            'PUT_CALL_HIGH': -0.7,  # >1.0 ratio
            'PUT_CALL_LOW': +0.5,   # <0.7 ratio
            'INSIDER_BUY': +0.9,
            'INSIDER_SELL': -0.4
        }

    def generate_synthetic_short_interest(self, ticker: str) -> pd.DataFrame:
        """
        Generate synthetic short interest data for testing

        In production: Use FINRA API or Yahoo Finance
        """
        dates = pd.date_range(end=datetime.now(), periods=26, freq='2W')

        # Random walk for short interest %
        base_short = np.random.uniform(2, 15)
        changes = np.random.normal(0, 1, len(dates))
        short_pct = base_short + np.cumsum(changes)
        short_pct = np.clip(short_pct, 0.5, 30)

        return pd.DataFrame({
            'date': dates,
            'ticker': ticker,
            'short_interest_pct': short_pct,
            'days_to_cover': short_pct / np.random.uniform(10, 50, len(dates))
        })

    def generate_synthetic_options_data(self, ticker: str) -> pd.DataFrame:
        """
        Generate synthetic put/call ratio data

        In production: Use CBOE API
        """
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')

        # Random walk for put/call ratio
        base_ratio = 0.8
        changes = np.random.normal(0, 0.1, len(dates))
        put_call_ratio = base_ratio + np.cumsum(changes)
        put_call_ratio = np.clip(put_call_ratio, 0.3, 2.5)

        return pd.DataFrame({
            'date': dates,
            'ticker': ticker,
            'put_call_ratio': put_call_ratio,
            'put_volume': np.random.randint(1000, 50000, len(dates)),
            'call_volume': np.random.randint(1000, 50000, len(dates))
        })

    def generate_synthetic_insider_transactions(self, ticker: str) -> pd.DataFrame:
        """
        Generate synthetic insider transaction data

        In production: Use SEC Form 4 API
        """
        num_transactions = np.random.randint(5, 20)

        transactions = []
        for _ in range(num_transactions):
            date = datetime.now() - timedelta(days=np.random.randint(1, 90))
            transaction_type = np.random.choice(['BUY', 'SELL'], p=[0.4, 0.6])

            transactions.append({
                'date': date,
                'ticker': ticker,
                'insider_name': f"Insider_{np.random.randint(1, 10)}",
                'transaction_type': transaction_type,
                'shares': np.random.randint(1000, 100000),
                'value': np.random.uniform(50000, 5000000)
            })

        return pd.DataFrame(transactions).sort_values('date', ascending=False)

    def calculate_activity_score(
        self,
        ticker: str,
        thirteenf_data: Dict,
        timeframe: str = '30d'
    ) -> Dict:
        """
        Calculate composite activity score from all sources

        Score: -100 (extreme bearish) to +100 (extreme bullish)

        Args:
            ticker: Stock ticker
            thirteenf_data: 13F data (whale moves)
            timeframe: Analysis timeframe

        Returns:
            Dict with activity score and breakdown
        """
        scores = {
            '13f_score': 0.0,
            'short_score': 0.0,
            'options_score': 0.0,
            'insider_score': 0.0
        }

        # 1. 13F Score (from whale moves)
        if thirteenf_data and 'net_buyers' in thirteenf_data:
            net = thirteenf_data['net_buyers'] - thirteenf_data['net_sellers']
            total = thirteenf_data['net_buyers'] + thirteenf_data['net_sellers']

            if total > 0:
                scores['13f_score'] = (net / total) * 40  # Max ±40 points

        # 2. Short Interest Score
        short_data = self.generate_synthetic_short_interest(ticker)
        if len(short_data) >= 2:
            latest = short_data.iloc[-1]['short_interest_pct']
            previous = short_data.iloc[-2]['short_interest_pct']
            change_pct = ((latest - previous) / previous) * 100

            if change_pct > 20:  # >20% increase = bearish
                scores['short_score'] = -25
            elif change_pct < -20:  # >20% decrease = bullish
                scores['short_score'] = +20
            else:
                scores['short_score'] = -change_pct * 0.5  # Linear scaling

        # 3. Options Score (Put/Call ratio)
        options_data = self.generate_synthetic_options_data(ticker)
        if len(options_data) > 0:
            latest_ratio = options_data.iloc[-1]['put_call_ratio']

            if latest_ratio > 1.5:  # High put/call = bearish
                scores['options_score'] = -20
            elif latest_ratio < 0.7:  # Low put/call = bullish
                scores['options_score'] = +15
            else:
                scores['options_score'] = (1.0 - latest_ratio) * 10

        # 4. Insider Score
        insider_data = self.generate_synthetic_insider_transactions(ticker)
        if len(insider_data) > 0:
            recent = insider_data[insider_data['date'] > (datetime.now() - timedelta(days=30))]

            if len(recent) > 0:
                buys = (recent['transaction_type'] == 'BUY').sum()
                sells = (recent['transaction_type'] == 'SELL').sum()

                if buys + sells > 0:
                    net_ratio = (buys - sells) / (buys + sells)
                    scores['insider_score'] = net_ratio * 25  # Max ±25 points

        # Composite score
        activity_score = sum(scores.values())
        activity_score = np.clip(activity_score, -100, 100)

        # Signal classification
        if activity_score > 50:
            signal = 'STRONG_BULLISH'
        elif activity_score > 20:
            signal = 'BULLISH'
        elif activity_score > -20:
            signal = 'NEUTRAL'
        elif activity_score > -50:
            signal = 'BEARISH'
        else:
            signal = 'STRONG_BEARISH'

        return {
            'ticker': ticker,
            'activity_score': activity_score,
            'signal': signal,
            'breakdown': scores,
            'timestamp': datetime.now()
        }

    def detect_unusual_activity(
        self,
        ticker: str,
        lookback_days: int = 30
    ) -> List[Dict]:
        """
        Detect unusual institutional activity (>2σ anomalies)

        Returns:
            List of unusual activity signals
        """
        anomalies = []

        # 1. Check short interest spike
        short_data = self.generate_synthetic_short_interest(ticker)
        if len(short_data) >= 5:
            recent_change = short_data.iloc[-1]['short_interest_pct'] - short_data.iloc[-2]['short_interest_pct']
            historical_changes = short_data['short_interest_pct'].diff().dropna()

            mean_change = historical_changes.mean()
            std_change = historical_changes.std()

            if abs(recent_change - mean_change) > 2 * std_change:
                anomalies.append({
                    'ticker': ticker,
                    'activity_type': 'SHORT_SPIKE' if recent_change > 0 else 'SHORT_COVER',
                    'magnitude': abs(recent_change),
                    'z_score': (recent_change - mean_change) / std_change if std_change > 0 else 0,
                    'description': f"Short interest {'increased' if recent_change > 0 else 'decreased'} by {abs(recent_change):.1f}% (>{2:.1f}σ)"
                })

        # 2. Check put/call ratio spike
        options_data = self.generate_synthetic_options_data(ticker)
        if len(options_data) >= 5:
            recent_ratio = options_data.iloc[-1]['put_call_ratio']
            mean_ratio = options_data['put_call_ratio'].mean()
            std_ratio = options_data['put_call_ratio'].std()

            z_score = (recent_ratio - mean_ratio) / std_ratio if std_ratio > 0 else 0

            if abs(z_score) > 2.5:
                anomalies.append({
                    'ticker': ticker,
                    'activity_type': 'PUT_CALL_ANOMALY',
                    'magnitude': recent_ratio,
                    'z_score': z_score,
                    'description': f"Put/Call ratio at {recent_ratio:.2f} ({z_score:.1f}σ from mean)"
                })

        # 3. Check insider buying cluster
        insider_data = self.generate_synthetic_insider_transactions(ticker)
        recent_insiders = insider_data[insider_data['date'] > (datetime.now() - timedelta(days=7))]

        buy_cluster = recent_insiders[recent_insiders['transaction_type'] == 'BUY']

        if len(buy_cluster) >= 3:
            anomalies.append({
                'ticker': ticker,
                'activity_type': 'INSIDER_BUY_CLUSTER',
                'magnitude': len(buy_cluster),
                'z_score': len(buy_cluster) / 2,  # Pseudo z-score
                'description': f"{len(buy_cluster)} insiders bought in last 7 days"
            })

        return anomalies

    def correlate_tefas_with_activity(
        self,
        tefas_flows: pd.DataFrame,
        activity_scores: pd.DataFrame
    ) -> Dict:
        """
        Analyze correlation between TEFAS flows and hedge fund activity

        Returns:
            Correlation metrics and lead/lag analysis
        """
        if len(tefas_flows) == 0 or len(activity_scores) == 0:
            return {
                'correlation_score': 0.0,
                'lead_lag_days': 0,
                'sector_correlations': {}
            }

        # Simple correlation calculation
        # In production: Use cross-correlation with different lags

        correlation = np.random.uniform(0.3, 0.7)  # Synthetic
        lead_lag = np.random.randint(-5, 5)  # Negative = TEFAS leads

        sector_correlations = {
            'Technology': np.random.uniform(0.4, 0.8),
            'Financials': np.random.uniform(0.2, 0.6),
            'Healthcare': np.random.uniform(0.3, 0.7),
            'Energy': np.random.uniform(0.1, 0.5)
        }

        return {
            'correlation_score': correlation,
            'lead_lag_days': lead_lag,
            'sector_correlations': sector_correlations,
            'interpretation': 'TEFAS leads' if lead_lag < 0 else 'Hedge funds lead' if lead_lag > 0 else 'Synchronous'
        }

    def generate_activity_heatmap_data(
        self,
        tickers: List[str],
        date_range: Tuple[datetime, datetime]
    ) -> pd.DataFrame:
        """
        Generate time × ticker heatmap data

        Returns:
            DataFrame with dates, tickers, and activity scores
        """
        start_date, end_date = date_range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        heatmap_data = []

        for ticker in tickers:
            for date in dates:
                # Synthetic activity score (random walk)
                score = np.random.normal(0, 30)

                heatmap_data.append({
                    'date': date,
                    'ticker': ticker,
                    'activity_score': score
                })

        return pd.DataFrame(heatmap_data)

    def calculate_market_activity_index(
        self,
        activity_scores: List[Dict]
    ) -> Dict:
        """
        Calculate overall market activity index (0-100)

        Aggregates activity across all tracked tickers

        Returns:
            Market-wide activity metrics
        """
        if not activity_scores:
            return {
                'market_activity_index': 50,
                'sentiment': 'NEUTRAL',
                'bullish_stocks': 0,
                'bearish_stocks': 0
            }

        scores = [s['activity_score'] for s in activity_scores]
        avg_score = np.mean(scores)

        # Normalize to 0-100
        market_index = (avg_score + 100) / 2

        bullish_count = sum(1 for s in scores if s > 20)
        bearish_count = sum(1 for s in scores if s < -20)

        if market_index > 65:
            sentiment = 'BULLISH'
        elif market_index > 55:
            sentiment = 'MILDLY_BULLISH'
        elif market_index > 45:
            sentiment = 'NEUTRAL'
        elif market_index > 35:
            sentiment = 'MILDLY_BEARISH'
        else:
            sentiment = 'BEARISH'

        return {
            'market_activity_index': market_index,
            'sentiment': sentiment,
            'bullish_stocks': bullish_count,
            'bearish_stocks': bearish_count,
            'total_analyzed': len(activity_scores),
            'avg_activity_score': avg_score
        }


def quick_activity_radar_analysis(
    tickers: List[str],
    thirteenf_data_dict: Dict[str, Dict] = None
) -> Dict:
    """
    Quick hedge fund activity analysis across multiple tickers

    Args:
        tickers: List of tickers to analyze
        thirteenf_data_dict: Optional 13F data per ticker

    Returns:
        Dict with all activity metrics
    """
    radar = HedgeFundActivityRadar()

    # Calculate activity scores
    activity_scores = []
    unusual_activities = []

    for ticker in tickers:
        thirteenf = thirteenf_data_dict.get(ticker, {}) if thirteenf_data_dict else {}

        score = radar.calculate_activity_score(ticker, thirteenf)
        activity_scores.append(score)

        # Detect anomalies
        anomalies = radar.detect_unusual_activity(ticker)
        unusual_activities.extend(anomalies)

    # Market activity index
    market_index = radar.calculate_market_activity_index(activity_scores)

    # Generate heatmap data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    heatmap_data = radar.generate_activity_heatmap_data(tickers[:10], (start_date, end_date))

    return {
        'activity_scores': pd.DataFrame(activity_scores),
        'unusual_activities': unusual_activities,
        'market_activity_index': market_index,
        'heatmap_data': heatmap_data,
        'num_tickers_analyzed': len(tickers),
        'timestamp': datetime.now()
    }
