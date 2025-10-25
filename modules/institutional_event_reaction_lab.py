"""
Institutional Event Reaction Lab - Track how whales react to major economic events
Analyzes before/after portfolio changes during FOMC, CPI, Jobs Reports, etc.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class EconomicEvent:
    """Economic event data structure"""
    event_type: str  # FOMC, CPI, JOBS, EARNINGS, FED_SPEECH
    date: datetime
    description: str
    impact: str  # HAWKISH, DOVISH, NEUTRAL, BEAT, MISS
    magnitude: float  # 0-10 scale


class InstitutionalEventReactionLab:
    """
    Analyzes how institutional investors react to major economic events
    Tracks portfolio changes before/after FOMC, CPI releases, etc.
    """

    def __init__(self):
        """Initialize Event Reaction Lab"""
        self.event_types = ['FOMC', 'CPI', 'JOBS', 'GDP', 'EARNINGS', 'FED_SPEECH']

        # Event impact categories
        self.impact_categories = {
            'HAWKISH': -1.0,  # Bearish for stocks (rate hikes)
            'DOVISH': +1.0,   # Bullish for stocks (rate cuts)
            'BEAT': +0.8,     # Better than expected
            'MISS': -0.8,     # Worse than expected
            'NEUTRAL': 0.0
        }

        # Sector rotation patterns during events
        self.defensive_sectors = ['XLP', 'XLU', 'XLV']  # Consumer Staples, Utilities, Healthcare
        self.growth_sectors = ['XLK', 'XLY', 'XLC']     # Tech, Consumer Discretionary, Communication

    def generate_synthetic_events(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[EconomicEvent]:
        """
        Generate synthetic economic events for testing

        In production: Use Fed calendar API, BLS API, etc.
        """
        events = []
        current_date = start_date

        while current_date <= end_date:
            # FOMC meetings (8 per year, roughly every 6 weeks)
            if np.random.random() < 0.15:  # ~15% chance per month
                impact = np.random.choice(['HAWKISH', 'DOVISH', 'NEUTRAL'], p=[0.3, 0.3, 0.4])
                events.append(EconomicEvent(
                    event_type='FOMC',
                    date=current_date,
                    description=f"FOMC Meeting - {impact.title()} stance",
                    impact=impact,
                    magnitude=np.random.uniform(5, 9)
                ))

            # CPI releases (monthly, around 13th)
            if current_date.day == 13:
                impact = np.random.choice(['BEAT', 'MISS', 'NEUTRAL'], p=[0.35, 0.35, 0.3])
                events.append(EconomicEvent(
                    event_type='CPI',
                    date=current_date,
                    description=f"CPI Release - {impact}",
                    impact=impact,
                    magnitude=np.random.uniform(6, 10)
                ))

            # Jobs Report (first Friday of month)
            if current_date.weekday() == 4 and current_date.day <= 7:  # First Friday
                impact = np.random.choice(['BEAT', 'MISS', 'NEUTRAL'], p=[0.4, 0.3, 0.3])
                events.append(EconomicEvent(
                    event_type='JOBS',
                    date=current_date,
                    description=f"Nonfarm Payrolls - {impact}",
                    impact=impact,
                    magnitude=np.random.uniform(5, 9)
                ))

            current_date += timedelta(days=1)

        return sorted(events, key=lambda x: x.date)

    def analyze_portfolio_before_after(
        self,
        whale_portfolio_before: pd.DataFrame,
        whale_portfolio_after: pd.DataFrame,
        event: EconomicEvent,
        whale_name: str
    ) -> Dict:
        """
        Analyze portfolio changes before/after an event

        Args:
            whale_portfolio_before: Portfolio snapshot before event (ticker, portfolio_weight, sector)
            whale_portfolio_after: Portfolio snapshot after event
            event: Economic event
            whale_name: Name of whale investor

        Returns:
            Dict with reaction metrics
        """
        # Merge before/after
        before = whale_portfolio_before.set_index('ticker')
        after = whale_portfolio_after.set_index('ticker')

        # Calculate weight changes
        all_tickers = set(before.index) | set(after.index)

        changes = []
        for ticker in all_tickers:
            weight_before = before.loc[ticker, 'portfolio_weight'] if ticker in before.index else 0
            weight_after = after.loc[ticker, 'portfolio_weight'] if ticker in after.index else 0

            change = weight_after - weight_before

            if abs(change) > 0.1:  # Only significant changes (>0.1%)
                sector = before.loc[ticker, 'sector'] if ticker in before.index else \
                         after.loc[ticker, 'sector'] if ticker in after.index else 'Unknown'

                changes.append({
                    'ticker': ticker,
                    'weight_before': weight_before,
                    'weight_after': weight_after,
                    'change': change,
                    'change_pct': (change / weight_before * 100) if weight_before > 0 else 0,
                    'sector': sector,
                    'action': 'INCREASED' if change > 0 else 'DECREASED'
                })

        changes_df = pd.DataFrame(changes)

        # Sector rotation analysis
        sector_changes = {}
        if len(changes_df) > 0:
            sector_changes = changes_df.groupby('sector')['change'].sum().to_dict()

        # Detect defensive vs growth rotation
        defensive_change = sum(sector_changes.get(s, 0) for s in self.defensive_sectors)
        growth_change = sum(sector_changes.get(s, 0) for s in self.growth_sectors)

        if defensive_change > 1.0:
            rotation = 'DEFENSIVE'
        elif growth_change > 1.0:
            rotation = 'GROWTH'
        else:
            rotation = 'NEUTRAL'

        # Calculate reaction score (-100 to +100)
        # Positive = risk-on (buying growth), Negative = risk-off (buying defensive)
        reaction_score = (growth_change - defensive_change) * 10
        reaction_score = np.clip(reaction_score, -100, 100)

        return {
            'whale_name': whale_name,
            'event': event,
            'changes': changes_df.sort_values('change', ascending=False) if len(changes_df) > 0 else pd.DataFrame(),
            'sector_changes': sector_changes,
            'rotation': rotation,
            'reaction_score': reaction_score,
            'num_changes': len(changes_df),
            'defensive_change': defensive_change,
            'growth_change': growth_change
        }

    def detect_anticipatory_moves(
        self,
        whale_moves: pd.DataFrame,
        events: List[EconomicEvent],
        lookback_days: int = 7
    ) -> List[Dict]:
        """
        Detect if whales made moves BEFORE events (anticipatory positioning)

        Args:
            whale_moves: DataFrame with columns [date, whale, ticker, action, portfolio_weight]
            events: List of economic events
            lookback_days: Days before event to check

        Returns:
            List of anticipatory moves
        """
        anticipatory_moves = []

        for event in events:
            window_start = event.date - timedelta(days=lookback_days)
            window_end = event.date - timedelta(days=1)

            # Get moves in window before event
            pre_event_moves = whale_moves[
                (whale_moves['date'] >= window_start) &
                (whale_moves['date'] <= window_end)
            ]

            if len(pre_event_moves) == 0:
                continue

            # Check if moves align with event impact
            event_impact_sign = self.impact_categories.get(event.impact, 0)

            for _, move in pre_event_moves.iterrows():
                move_sign = 1 if move['action'] in ['NEW', 'INCREASED'] else -1

                # Anticipatory = move aligns with eventual event impact
                if move_sign * event_impact_sign > 0:
                    anticipatory_moves.append({
                        'whale': move['whale'],
                        'ticker': move['ticker'],
                        'action': move['action'],
                        'days_before_event': (event.date - move['date']).days,
                        'event': event,
                        'alignment': 'CORRECT' if event_impact_sign > 0 else 'CORRECT_SHORT'
                    })

        return anticipatory_moves

    def calculate_reaction_latency(
        self,
        whale_moves: pd.DataFrame,
        events: List[EconomicEvent],
        lookafter_days: int = 14
    ) -> pd.DataFrame:
        """
        Calculate how quickly whales react to events (latency in days)

        Returns:
            DataFrame with whale, avg_latency, median_latency
        """
        latencies = []

        for event in events:
            window_end = event.date + timedelta(days=lookafter_days)

            post_event_moves = whale_moves[
                (whale_moves['date'] > event.date) &
                (whale_moves['date'] <= window_end)
            ]

            for whale in post_event_moves['whale'].unique():
                whale_post_moves = post_event_moves[post_event_moves['whale'] == whale]

                # First move after event
                first_move_date = whale_post_moves['date'].min()
                latency = (first_move_date - event.date).days

                latencies.append({
                    'whale': whale,
                    'event_type': event.event_type,
                    'event_date': event.date,
                    'first_move_date': first_move_date,
                    'latency_days': latency
                })

        latency_df = pd.DataFrame(latencies)

        if len(latency_df) == 0:
            return pd.DataFrame()

        # Aggregate by whale
        whale_latencies = latency_df.groupby('whale')['latency_days'].agg([
            ('avg_latency', 'mean'),
            ('median_latency', 'median'),
            ('min_latency', 'min'),
            ('max_latency', 'max')
        ]).reset_index()

        return whale_latencies.sort_values('avg_latency')

    def compare_whale_reactions(
        self,
        reactions: List[Dict]
    ) -> Dict:
        """
        Compare how different whales reacted to the same event

        Args:
            reactions: List of reaction dicts from analyze_portfolio_before_after

        Returns:
            Comparison metrics
        """
        if len(reactions) == 0:
            return {}

        # Extract reaction scores
        reaction_scores = {r['whale_name']: r['reaction_score'] for r in reactions}

        # Consensus or divergence?
        scores = list(reaction_scores.values())
        avg_score = np.mean(scores)
        std_score = np.std(scores)

        if std_score < 20:
            consensus = 'STRONG_CONSENSUS'
        elif std_score < 40:
            consensus = 'MODERATE_CONSENSUS'
        else:
            consensus = 'DIVERGENCE'

        # Most bullish/bearish
        most_bullish = max(reaction_scores.items(), key=lambda x: x[1])
        most_bearish = min(reaction_scores.items(), key=lambda x: x[1])

        return {
            'event': reactions[0]['event'],
            'num_whales': len(reactions),
            'avg_reaction_score': avg_score,
            'std_reaction_score': std_score,
            'consensus': consensus,
            'most_bullish_whale': most_bullish[0],
            'most_bullish_score': most_bullish[1],
            'most_bearish_whale': most_bearish[0],
            'most_bearish_score': most_bearish[1],
            'reactions': reactions
        }

    def generate_event_timeline(
        self,
        events: List[EconomicEvent],
        whale_moves: pd.DataFrame,
        window_days: int = 7
    ) -> pd.DataFrame:
        """
        Generate event timeline with whale activity markers

        Returns:
            DataFrame with date, event, whale_activity_count
        """
        timeline = []

        for event in events:
            # Count whale activity around event
            window_start = event.date - timedelta(days=window_days)
            window_end = event.date + timedelta(days=window_days)

            activity = whale_moves[
                (whale_moves['date'] >= window_start) &
                (whale_moves['date'] <= window_end)
            ]

            timeline.append({
                'date': event.date,
                'event_type': event.event_type,
                'description': event.description,
                'impact': event.impact,
                'magnitude': event.magnitude,
                'pre_event_moves': len(activity[activity['date'] < event.date]),
                'post_event_moves': len(activity[activity['date'] >= event.date]),
                'total_whale_activity': len(activity)
            })

        return pd.DataFrame(timeline)

    def calculate_event_sensitivity_score(
        self,
        whale_name: str,
        reactions: List[Dict]
    ) -> Dict:
        """
        Calculate how sensitive a whale is to different event types

        Returns:
            Dict with event_type sensitivity scores
        """
        event_type_reactions = {}

        for reaction in reactions:
            if reaction['whale_name'] != whale_name:
                continue

            event_type = reaction['event'].event_type
            reaction_score = abs(reaction['reaction_score'])  # Magnitude matters

            if event_type not in event_type_reactions:
                event_type_reactions[event_type] = []

            event_type_reactions[event_type].append(reaction_score)

        # Average sensitivity per event type
        sensitivity_scores = {}
        for event_type, scores in event_type_reactions.items():
            sensitivity_scores[event_type] = {
                'avg_sensitivity': np.mean(scores),
                'max_sensitivity': np.max(scores),
                'num_events': len(scores)
            }

        # Overall sensitivity (0-100)
        all_scores = [s for scores in event_type_reactions.values() for s in scores]
        overall_sensitivity = np.mean(all_scores) if len(all_scores) > 0 else 0

        return {
            'whale_name': whale_name,
            'overall_sensitivity': overall_sensitivity,
            'event_type_sensitivity': sensitivity_scores,
            'total_events_reacted': len(all_scores)
        }


def quick_event_reaction_analysis(
    whale_portfolios: Dict[str, pd.DataFrame],
    events: List[EconomicEvent],
    whale_moves: pd.DataFrame = None
) -> Dict:
    """
    Quick event reaction analysis across multiple whales

    Args:
        whale_portfolios: Dict of {whale_name: portfolio_df}
        events: List of economic events
        whale_moves: Optional DataFrame of whale moves

    Returns:
        Dict with all analysis results
    """
    lab = InstitutionalEventReactionLab()

    # Analyze each event
    event_analyses = []

    for event in events:
        event_reactions = []

        for whale_name, portfolio in whale_portfolios.items():
            # Simulate before/after portfolios (in production, use actual snapshots)
            # For now, add random noise to simulate portfolio changes
            portfolio_before = portfolio.copy()
            portfolio_after = portfolio.copy()

            # Random weight changes
            noise = np.random.normal(0, 0.5, len(portfolio_after))
            portfolio_after['portfolio_weight'] = portfolio_after['portfolio_weight'] + noise
            portfolio_after['portfolio_weight'] = portfolio_after['portfolio_weight'].clip(lower=0)

            reaction = lab.analyze_portfolio_before_after(
                portfolio_before,
                portfolio_after,
                event,
                whale_name
            )
            event_reactions.append(reaction)

        # Compare reactions
        comparison = lab.compare_whale_reactions(event_reactions)
        event_analyses.append(comparison)

    # Reaction latencies
    latencies = pd.DataFrame()
    if whale_moves is not None:
        latencies = lab.calculate_reaction_latency(whale_moves, events)

    # Event timeline
    timeline = pd.DataFrame()
    if whale_moves is not None:
        timeline = lab.generate_event_timeline(events, whale_moves)

    # Anticipatory moves
    anticipatory = []
    if whale_moves is not None:
        anticipatory = lab.detect_anticipatory_moves(whale_moves, events)

    return {
        'event_analyses': event_analyses,
        'reaction_latencies': latencies,
        'event_timeline': timeline,
        'anticipatory_moves': anticipatory,
        'num_events': len(events),
        'num_whales': len(whale_portfolios),
        'timestamp': datetime.now()
    }
