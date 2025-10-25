"""
Whale Sentiment Engine - Composite sentiment index from 5 institutional data sources
Aggregates whale correlation, fund flow, momentum, activity, and TEFAS to create 0-100 sentiment score
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class WhaleSentimentEngine:
    """
    Composite institutional sentiment engine
    Combines 5 data sources into single 0-100 sentiment score
    """

    def __init__(self):
        """Initialize Whale Sentiment Engine"""
        # Source weights for composite score
        self.source_weights = {
            'whale_correlation': 0.25,      # Whale portfolio overlap
            'fund_flow': 0.20,              # TEFAS net flows
            'momentum': 0.25,               # Whale momentum/consensus
            'activity': 0.20,               # Hedge fund activity
            'event_reaction': 0.10          # Event reaction sentiment
        }

        # Market regime thresholds
        self.regime_thresholds = {
            'EXTREME_FEAR': 20,
            'FEAR': 35,
            'NEUTRAL': 65,
            'GREED': 80,
            'EXTREME_GREED': 100
        }

    def calculate_composite_sentiment(
        self,
        whale_correlation_score: float,  # 0-100
        fund_flow_score: float,          # 0-100
        momentum_score: float,           # 0-100
        activity_score: float,           # -100 to +100, will normalize
        event_reaction_score: float = None  # Optional, -100 to +100
    ) -> Dict:
        """
        Calculate composite sentiment from 5 sources

        Args:
            whale_correlation_score: Avg correlation among whales (0-100)
            fund_flow_score: TEFAS net flow sentiment (0-100)
            momentum_score: Institutional consensus indicator (0-100)
            activity_score: Hedge fund activity composite (-100 to +100)
            event_reaction_score: Optional event reaction sentiment (-100 to +100)

        Returns:
            Dict with composite score, regime, breakdown
        """
        # Normalize activity score (-100 to +100 → 0-100)
        normalized_activity = (activity_score + 100) / 2

        # Normalize event reaction if provided
        if event_reaction_score is not None:
            normalized_event = (event_reaction_score + 100) / 2
        else:
            normalized_event = 50  # Neutral if not provided
            # Rebalance weights if event reaction not available
            self.source_weights['event_reaction'] = 0.0
            # Redistribute weight equally
            total_weight = sum(w for k, w in self.source_weights.items() if k != 'event_reaction')
            for key in self.source_weights:
                if key != 'event_reaction':
                    self.source_weights[key] = self.source_weights[key] / total_weight

        # Weighted composite
        composite_score = (
            whale_correlation_score * self.source_weights['whale_correlation'] +
            fund_flow_score * self.source_weights['fund_flow'] +
            momentum_score * self.source_weights['momentum'] +
            normalized_activity * self.source_weights['activity'] +
            normalized_event * self.source_weights['event_reaction']
        )

        composite_score = np.clip(composite_score, 0, 100)

        # Determine market regime
        regime = self._classify_regime(composite_score)

        # Calculate confidence (lower std = higher confidence)
        scores = [
            whale_correlation_score,
            fund_flow_score,
            momentum_score,
            normalized_activity,
            normalized_event
        ]
        std_scores = np.std(scores)
        confidence = max(0, 100 - std_scores * 2)  # High std = low confidence

        return {
            'composite_score': composite_score,
            'regime': regime,
            'confidence': confidence,
            'breakdown': {
                'whale_correlation': whale_correlation_score,
                'fund_flow': fund_flow_score,
                'momentum': momentum_score,
                'activity': normalized_activity,
                'event_reaction': normalized_event
            },
            'weights': self.source_weights.copy(),
            'timestamp': datetime.now()
        }

    def _classify_regime(self, score: float) -> str:
        """Classify market regime based on sentiment score"""
        if score < self.regime_thresholds['EXTREME_FEAR']:
            return 'EXTREME_FEAR'
        elif score < self.regime_thresholds['FEAR']:
            return 'FEAR'
        elif score < self.regime_thresholds['NEUTRAL']:
            return 'NEUTRAL'
        elif score < self.regime_thresholds['GREED']:
            return 'GREED'
        else:
            return 'EXTREME_GREED'

    def calculate_sentiment_trend(
        self,
        historical_sentiment: pd.DataFrame
    ) -> Dict:
        """
        Calculate sentiment trend from historical data

        Args:
            historical_sentiment: DataFrame with columns [date, composite_score]

        Returns:
            Trend metrics
        """
        if len(historical_sentiment) < 2:
            return {
                'trend': 'NEUTRAL',
                'change_7d': 0,
                'change_30d': 0,
                'momentum': 0
            }

        historical_sentiment = historical_sentiment.sort_values('date')

        latest_score = historical_sentiment.iloc[-1]['composite_score']

        # 7-day change
        seven_days_ago = historical_sentiment.iloc[-1]['date'] - timedelta(days=7)
        past_7d = historical_sentiment[historical_sentiment['date'] <= seven_days_ago]
        change_7d = latest_score - past_7d.iloc[-1]['composite_score'] if len(past_7d) > 0 else 0

        # 30-day change
        thirty_days_ago = historical_sentiment.iloc[-1]['date'] - timedelta(days=30)
        past_30d = historical_sentiment[historical_sentiment['date'] <= thirty_days_ago]
        change_30d = latest_score - past_30d.iloc[-1]['composite_score'] if len(past_30d) > 0 else 0

        # Momentum (rate of change)
        if len(historical_sentiment) >= 5:
            recent_5 = historical_sentiment.tail(5)
            momentum = np.polyfit(range(5), recent_5['composite_score'].values, 1)[0]
        else:
            momentum = 0

        # Trend classification
        if momentum > 2:
            trend = 'STRONG_IMPROVING'
        elif momentum > 0.5:
            trend = 'IMPROVING'
        elif momentum > -0.5:
            trend = 'NEUTRAL'
        elif momentum > -2:
            trend = 'DETERIORATING'
        else:
            trend = 'STRONG_DETERIORATING'

        return {
            'trend': trend,
            'change_7d': change_7d,
            'change_30d': change_30d,
            'momentum': momentum
        }

    def detect_sentiment_divergence(
        self,
        breakdown: Dict
    ) -> Dict:
        """
        Detect divergence among sentiment sources

        Returns:
            Divergence metrics
        """
        scores = list(breakdown.values())
        mean_score = np.mean(scores)
        std_score = np.std(scores)

        # Calculate max divergence
        max_diff = max(scores) - min(scores)

        # Find most bullish/bearish sources
        sorted_sources = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)

        most_bullish = sorted_sources[0]
        most_bearish = sorted_sources[-1]

        # Divergence classification
        if std_score < 10:
            divergence_level = 'LOW'
            interpretation = 'Strong consensus across all sources'
        elif std_score < 20:
            divergence_level = 'MODERATE'
            interpretation = 'Some disagreement among sources'
        else:
            divergence_level = 'HIGH'
            interpretation = 'Significant divergence - mixed signals'

        return {
            'divergence_level': divergence_level,
            'std_score': std_score,
            'max_difference': max_diff,
            'most_bullish_source': most_bullish[0],
            'most_bullish_score': most_bullish[1],
            'most_bearish_source': most_bearish[0],
            'most_bearish_score': most_bearish[1],
            'interpretation': interpretation
        }

    def calculate_risk_appetite_index(
        self,
        sentiment_score: float,
        volatility_score: float  # 0-100, higher = more volatile
    ) -> Dict:
        """
        Calculate Risk Appetite Index combining sentiment and volatility

        High sentiment + Low volatility = High risk appetite
        Low sentiment + High volatility = Low risk appetite

        Returns:
            Risk appetite metrics
        """
        # Risk appetite = sentiment adjusted for volatility
        risk_appetite = sentiment_score * (1 - volatility_score / 200)
        risk_appetite = np.clip(risk_appetite, 0, 100)

        # Classification
        if risk_appetite > 70:
            classification = 'RISK_ON'
            color = 'green'
        elif risk_appetite > 50:
            classification = 'MILD_RISK_ON'
            color = 'lightgreen'
        elif risk_appetite > 30:
            classification = 'NEUTRAL'
            color = 'gray'
        elif risk_appetite > 15:
            classification = 'MILD_RISK_OFF'
            color = 'orange'
        else:
            classification = 'RISK_OFF'
            color = 'red'

        return {
            'risk_appetite': risk_appetite,
            'classification': classification,
            'color': color,
            'sentiment_component': sentiment_score,
            'volatility_component': volatility_score
        }

    def generate_sentiment_signal(
        self,
        sentiment_result: Dict
    ) -> Dict:
        """
        Generate actionable trading signal from sentiment

        Returns:
            Trading signal and recommended action
        """
        score = sentiment_result['composite_score']
        regime = sentiment_result['regime']
        confidence = sentiment_result['confidence']

        # Signal logic
        if regime == 'EXTREME_FEAR' and confidence > 60:
            signal = 'STRONG_BUY'
            action = 'Aggressive buying opportunity (contrarian)'
            risk_level = 'HIGH'
        elif regime == 'FEAR':
            signal = 'BUY'
            action = 'Accumulate positions'
            risk_level = 'MODERATE'
        elif regime == 'NEUTRAL':
            signal = 'HOLD'
            action = 'Wait for clearer signals'
            risk_level = 'LOW'
        elif regime == 'GREED':
            signal = 'SELL'
            action = 'Take profits, reduce exposure'
            risk_level = 'MODERATE'
        elif regime == 'EXTREME_GREED' and confidence > 60:
            signal = 'STRONG_SELL'
            action = 'Heavy profit-taking (contrarian)'
            risk_level = 'HIGH'
        else:
            signal = 'NEUTRAL'
            action = 'No clear signal'
            risk_level = 'LOW'

        return {
            'signal': signal,
            'action': action,
            'risk_level': risk_level,
            'confidence': confidence,
            'regime': regime,
            'score': score
        }


def quick_sentiment_analysis(
    whale_correlation: float = None,
    fund_flow: float = None,
    momentum: float = None,
    activity: float = None,
    event_reaction: float = None
) -> Dict:
    """
    Quick sentiment analysis with synthetic data if not provided

    Args:
        whale_correlation: 0-100 (optional, will use synthetic if None)
        fund_flow: 0-100 (optional)
        momentum: 0-100 (optional)
        activity: -100 to +100 (optional)
        event_reaction: -100 to +100 (optional)

    Returns:
        Complete sentiment analysis
    """
    engine = WhaleSentimentEngine()

    # Use synthetic data if not provided
    if whale_correlation is None:
        whale_correlation = np.random.uniform(40, 80)
    if fund_flow is None:
        fund_flow = np.random.uniform(35, 75)
    if momentum is None:
        momentum = np.random.uniform(40, 70)
    if activity is None:
        activity = np.random.uniform(-30, 40)
    # event_reaction can be None (optional)

    # Calculate composite sentiment
    sentiment_result = engine.calculate_composite_sentiment(
        whale_correlation,
        fund_flow,
        momentum,
        activity,
        event_reaction
    )

    # Detect divergence
    divergence = engine.detect_sentiment_divergence(sentiment_result['breakdown'])

    # Generate signal
    signal = engine.generate_sentiment_signal(sentiment_result)

    # Risk appetite (synthetic volatility)
    volatility_score = np.random.uniform(20, 60)
    risk_appetite = engine.calculate_risk_appetite_index(
        sentiment_result['composite_score'],
        volatility_score
    )

    return {
        'sentiment': sentiment_result,
        'divergence': divergence,
        'signal': signal,
        'risk_appetite': risk_appetite,
        'timestamp': datetime.now()
    }
