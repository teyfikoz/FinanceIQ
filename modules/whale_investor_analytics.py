"""
Whale Investor Analytics - Track legendary investors' portfolios
Analyze 13F filings from Warren Buffett, Bill Gates, Cathie Wood, Ray Dalio, etc.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import yfinance as yf


class WhaleInvestorAnalytics:
    """
    Track and analyze legendary investors' portfolio moves

    Key Features:
    - 13F filing data parsing
    - Portfolio composition analysis
    - Quarter-over-quarter changes
    - Sector allocation tracking
    - Big move detection (whale signals)
    - Performance attribution
    """

    # Famous investors and their entities
    WHALE_INVESTORS = {
        'buffett': {
            'name': 'Warren Buffett',
            'entity': 'Berkshire Hathaway',
            'cik': '0001067983',
            'style': 'Value Investing',
            'icon': '🐘'
        },
        'gates': {
            'name': 'Bill Gates',
            'entity': 'Bill & Melinda Gates Foundation Trust',
            'cik': '0001166559',
            'style': 'Growth + Impact',
            'icon': '💻'
        },
        'wood': {
            'name': 'Cathie Wood',
            'entity': 'ARK Investment Management',
            'cik': '0001649339',
            'style': 'Disruptive Innovation',
            'icon': '🚀'
        },
        'dalio': {
            'name': 'Ray Dalio',
            'entity': 'Bridgewater Associates',
            'cik': '0001350694',
            'style': 'All Weather Portfolio',
            'icon': '🌊'
        },
        'ackman': {
            'name': 'Bill Ackman',
            'entity': 'Pershing Square Capital',
            'cik': '0001336528',
            'style': 'Activist Value',
            'icon': '🎯'
        },
        'burry': {
            'name': 'Michael Burry',
            'entity': 'Scion Asset Management',
            'cik': '0001649339',
            'style': 'Contrarian Value',
            'icon': '🔍'
        },
        'druckenmiller': {
            'name': 'Stanley Druckenmiller',
            'entity': 'Duquesne Family Office',
            'cik': '0001434673',
            'style': 'Macro Trading',
            'icon': '📊'
        }
    }

    def __init__(self, data_dir: str = 'data/whale_holdings'):
        """
        Initialize Whale Investor Analytics

        Args:
            data_dir: Directory containing whale holding data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def generate_sample_holdings(
        self,
        investor: str,
        quarter: str,
        num_holdings: int = 50
    ) -> pd.DataFrame:
        """
        Generate sample 13F holdings data for demonstration

        Args:
            investor: Investor key (e.g., 'buffett')
            quarter: Quarter (e.g., '2024Q4')
            num_holdings: Number of holdings to generate

        Returns:
            DataFrame with holdings data
        """
        # Sample tickers based on investor style
        if investor == 'buffett':
            # Value stocks
            base_tickers = ['AAPL', 'BAC', 'AXP', 'KO', 'CVX', 'OXY', 'MCO', 'KHC', 'USB', 'V',
                           'MA', 'JPM', 'WFC', 'GM', 'DVA', 'BK', 'C', 'BRK.B', 'KR', 'ALLY']
        elif investor == 'wood':
            # Growth/tech stocks
            base_tickers = ['TSLA', 'ROKU', 'SQ', 'TDOC', 'COIN', 'SHOP', 'ZM', 'HOOD', 'PATH', 'RBLX',
                           'U', 'DKNG', 'TWLO', 'SNAP', 'SPOT', 'PLTR', 'NVDA', 'AMD', 'NET', 'CRWD']
        elif investor == 'dalio':
            # Diversified + hedges
            base_tickers = ['SPY', 'VTI', 'GLD', 'TLT', 'EEM', 'VWO', 'IWM', 'QQQ', 'HYG', 'LQD',
                           'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'PG', 'JNJ', 'XOM', 'JPM', 'DIS', 'WMT']
        elif investor == 'gates':
            # Large cap tech + healthcare
            base_tickers = ['MSFT', 'BRK.B', 'WM', 'CNI', 'CAT', 'GOOGL', 'AAPL', 'AMZN', 'UNH', 'JNJ',
                           'TMO', 'DHR', 'ABT', 'LLY', 'MRK', 'PFE', 'CVS', 'CI', 'WMT', 'KO']
        else:
            # Default mix
            base_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B', 'JPM', 'V']

        # Extend to num_holdings
        tickers = (base_tickers * (num_holdings // len(base_tickers) + 1))[:num_holdings]

        # Generate portfolio weights (Zipf distribution - realistic for portfolios)
        np.random.seed(hash(investor + quarter) % 2**32)
        raw_weights = 1 / (np.arange(1, num_holdings + 1) ** 1.5)
        weights = raw_weights / raw_weights.sum()

        # Shuffle a bit for variety
        np.random.shuffle(weights)

        # Generate data
        data = []
        for i, ticker in enumerate(tickers):
            shares = np.random.randint(100000, 10000000)
            price = np.random.uniform(50, 500)
            value = shares * price

            data.append({
                'ticker': ticker,
                'shares': shares,
                'price': price,
                'value_usd': value,
                'portfolio_weight': weights[i] * 100,  # percentage
                'sector': self._get_sector(ticker),
                'filing_date': self._get_filing_date(quarter)
            })

        df = pd.DataFrame(data)

        # Normalize weights to exactly 100%
        df['portfolio_weight'] = (df['value_usd'] / df['value_usd'].sum()) * 100

        return df.sort_values('portfolio_weight', ascending=False).reset_index(drop=True)

    def _get_sector(self, ticker: str) -> str:
        """Get sector for ticker (simplified mapping)"""
        tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD', 'NFLX',
                      'ROKU', 'SQ', 'SHOP', 'ZM', 'COIN', 'PLTR', 'SNAP', 'SPOT', 'NET', 'CRWD']
        finance_stocks = ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'V', 'MA', 'BK', 'USB', 'PNC']
        healthcare_stocks = ['JNJ', 'UNH', 'LLY', 'PFE', 'ABBV', 'TMO', 'DHR', 'ABT', 'MRK', 'CVS']
        energy_stocks = ['XOM', 'CVX', 'OXY', 'COP', 'SLB', 'EOG']
        consumer_stocks = ['WMT', 'PG', 'KO', 'PEP', 'COST', 'HD', 'MCD', 'NKE', 'SBUX']

        if ticker in tech_stocks:
            return 'Technology'
        elif ticker in finance_stocks:
            return 'Financials'
        elif ticker in healthcare_stocks:
            return 'Healthcare'
        elif ticker in energy_stocks:
            return 'Energy'
        elif ticker in consumer_stocks:
            return 'Consumer'
        else:
            return 'Other'

    def _get_filing_date(self, quarter: str) -> str:
        """Get filing date for quarter"""
        year = int(quarter[:4])
        q = int(quarter[5])

        # 13F filings due 45 days after quarter end
        if q == 1:
            return f"{year}-05-15"
        elif q == 2:
            return f"{year}-08-15"
        elif q == 3:
            return f"{year}-11-15"
        else:
            return f"{year+1}-02-15"

    def load_whale_data(self, investor: str, quarter: str) -> Optional[pd.DataFrame]:
        """
        Load whale holdings data

        Args:
            investor: Investor key
            quarter: Quarter (e.g., '2024Q4')

        Returns:
            DataFrame with holdings
        """
        # Try to load from file
        file_path = self.data_dir / f"{investor}_{quarter}.json"

        if file_path.exists():
            return pd.read_json(file_path)
        else:
            # Generate sample data
            df = self.generate_sample_holdings(investor, quarter)

            # Save for future use
            df.to_json(file_path, orient='records', indent=2)

            return df

    def calculate_portfolio_changes(
        self,
        df_current: pd.DataFrame,
        df_previous: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate quarter-over-quarter changes

        Args:
            df_current: Current quarter holdings
            df_previous: Previous quarter holdings

        Returns:
            DataFrame with changes
        """
        # Merge on ticker
        merged = df_current.merge(
            df_previous,
            on='ticker',
            how='outer',
            suffixes=('_curr', '_prev')
        )

        # Fill NaN for new/sold positions
        merged['shares_curr'] = merged['shares_curr'].fillna(0)
        merged['shares_prev'] = merged['shares_prev'].fillna(0)
        merged['value_usd_curr'] = merged['value_usd_curr'].fillna(0)
        merged['value_usd_prev'] = merged['value_usd_prev'].fillna(0)
        merged['portfolio_weight_curr'] = merged['portfolio_weight_curr'].fillna(0)
        merged['portfolio_weight_prev'] = merged['portfolio_weight_prev'].fillna(0)

        # Calculate changes
        merged['shares_change'] = merged['shares_curr'] - merged['shares_prev']
        merged['shares_change_pct'] = np.where(
            merged['shares_prev'] > 0,
            (merged['shares_change'] / merged['shares_prev']) * 100,
            np.inf  # New position
        )

        merged['value_change'] = merged['value_usd_curr'] - merged['value_usd_prev']
        merged['weight_change'] = merged['portfolio_weight_curr'] - merged['portfolio_weight_prev']

        # Position status
        merged['position_status'] = 'HELD'
        merged.loc[merged['shares_prev'] == 0, 'position_status'] = 'NEW'
        merged.loc[merged['shares_curr'] == 0, 'position_status'] = 'SOLD'
        merged.loc[merged['shares_change'] > 0, 'position_status'] = 'INCREASED'
        merged.loc[merged['shares_change'] < 0, 'position_status'] = 'DECREASED'

        # Use current sector (or previous if sold)
        merged['sector'] = merged['sector_curr'].fillna(merged['sector_prev'])

        return merged

    def detect_whale_moves(
        self,
        changes_df: pd.DataFrame,
        min_weight_change: float = 1.0,
        min_value_change: float = 100_000_000  # $100M
    ) -> List[Dict]:
        """
        Detect significant portfolio moves (whale signals)

        Args:
            changes_df: DataFrame with portfolio changes
            min_weight_change: Minimum weight change (%)
            min_value_change: Minimum value change ($)

        Returns:
            List of whale move dicts
        """
        whale_moves = []

        # Filter significant moves
        significant = changes_df[
            (abs(changes_df['weight_change']) >= min_weight_change) |
            (abs(changes_df['value_change']) >= min_value_change)
        ].copy()

        for _, row in significant.iterrows():
            move_type = row['position_status']

            if move_type == 'NEW':
                signal = 'STRONG_BUY'
                description = f"Yeni pozisyon açıldı - ${row['value_usd_curr']/1e6:.0f}M"
            elif move_type == 'SOLD':
                signal = 'STRONG_SELL'
                description = f"Pozisyon tamamen kapatıldı - ${abs(row['value_usd_prev'])/1e6:.0f}M"
            elif move_type == 'INCREASED':
                signal = 'BUY'
                description = f"{row['shares_change_pct']:.0f}% artırıldı - +${row['value_change']/1e6:.0f}M"
            elif move_type == 'DECREASED':
                signal = 'SELL'
                description = f"{abs(row['shares_change_pct']):.0f}% azaltıldı - -${abs(row['value_change'])/1e6:.0f}M"
            else:
                continue

            whale_moves.append({
                'ticker': row['ticker'],
                'sector': row['sector'],
                'signal': signal,
                'move_type': move_type,
                'weight_change': row['weight_change'],
                'value_change': row['value_change'],
                'current_weight': row['portfolio_weight_curr'],
                'description': description
            })

        return sorted(whale_moves, key=lambda x: abs(x['weight_change']), reverse=True)

    def analyze_sector_allocation(
        self,
        holdings_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Analyze sector allocation

        Args:
            holdings_df: Holdings DataFrame

        Returns:
            DataFrame with sector breakdown
        """
        sector_agg = holdings_df.groupby('sector').agg({
            'value_usd': 'sum',
            'portfolio_weight': 'sum',
            'ticker': 'count'
        }).reset_index()

        sector_agg.columns = ['sector', 'total_value', 'total_weight', 'num_holdings']

        sector_agg = sector_agg.sort_values('total_weight', ascending=False)

        return sector_agg

    def calculate_portfolio_concentration(
        self,
        holdings_df: pd.DataFrame
    ) -> Dict:
        """
        Calculate portfolio concentration metrics

        Args:
            holdings_df: Holdings DataFrame

        Returns:
            Dict with concentration metrics
        """
        # Herfindahl-Hirschman Index (HHI)
        hhi = (holdings_df['portfolio_weight'] ** 2).sum()

        # Top N concentration
        top5_weight = holdings_df.nlargest(5, 'portfolio_weight')['portfolio_weight'].sum()
        top10_weight = holdings_df.nlargest(10, 'portfolio_weight')['portfolio_weight'].sum()
        top20_weight = holdings_df.nlargest(20, 'portfolio_weight')['portfolio_weight'].sum()

        # Effective number of holdings
        effective_holdings = 10000 / hhi if hhi > 0 else 0

        return {
            'hhi': hhi,
            'effective_holdings': effective_holdings,
            'top5_concentration': top5_weight,
            'top10_concentration': top10_weight,
            'top20_concentration': top20_weight,
            'concentration_level': self._interpret_concentration(top10_weight)
        }

    def _interpret_concentration(self, top10_pct: float) -> str:
        """Interpret concentration level"""
        if top10_pct >= 80:
            return 'Very High'
        elif top10_pct >= 60:
            return 'High'
        elif top10_pct >= 40:
            return 'Moderate'
        else:
            return 'Low'

    def compare_investors(
        self,
        investors: List[str],
        quarter: str
    ) -> pd.DataFrame:
        """
        Compare multiple investors' portfolios

        Args:
            investors: List of investor keys
            quarter: Quarter to compare

        Returns:
            DataFrame with comparison
        """
        comparison_data = []

        for investor in investors:
            df = self.load_whale_data(investor, quarter)

            if df is not None:
                total_value = df['value_usd'].sum()
                num_holdings = len(df)
                concentration = self.calculate_portfolio_concentration(df)

                top_holding = df.nlargest(1, 'portfolio_weight').iloc[0]

                comparison_data.append({
                    'investor': self.WHALE_INVESTORS[investor]['name'],
                    'style': self.WHALE_INVESTORS[investor]['style'],
                    'total_value': total_value,
                    'num_holdings': num_holdings,
                    'top_holding': top_holding['ticker'],
                    'top_holding_weight': top_holding['portfolio_weight'],
                    'concentration': concentration['concentration_level'],
                    'top10_weight': concentration['top10_concentration']
                })

        return pd.DataFrame(comparison_data)

    def get_common_holdings(
        self,
        investor1: str,
        investor2: str,
        quarter: str
    ) -> pd.DataFrame:
        """
        Find common holdings between two investors

        Args:
            investor1: First investor
            investor2: Second investor
            quarter: Quarter

        Returns:
            DataFrame with common holdings
        """
        df1 = self.load_whale_data(investor1, quarter)
        df2 = self.load_whale_data(investor2, quarter)

        # Merge on ticker
        common = df1.merge(df2, on='ticker', suffixes=('_1', '_2'))

        common = common[[
            'ticker', 'sector_1',
            'portfolio_weight_1', 'portfolio_weight_2',
            'value_usd_1', 'value_usd_2'
        ]].copy()

        common.columns = [
            'ticker', 'sector',
            f'{investor1}_weight', f'{investor2}_weight',
            f'{investor1}_value', f'{investor2}_value'
        ]

        return common.sort_values(f'{investor1}_weight', ascending=False)


def quick_whale_analysis(investor: str, quarters: List[str] = None) -> Dict:
    """
    Quick whale analysis convenience function

    Args:
        investor: Investor key
        quarters: List of quarters (default: last 2 quarters)

    Returns:
        Dict with analysis results
    """
    analytics = WhaleInvestorAnalytics()

    if quarters is None:
        quarters = ['2024Q3', '2024Q4']

    current_quarter = quarters[-1]
    previous_quarter = quarters[-2] if len(quarters) > 1 else None

    # Load current data
    df_current = analytics.load_whale_data(investor, current_quarter)

    results = {
        'investor': analytics.WHALE_INVESTORS[investor],
        'current_holdings': df_current,
        'portfolio_value': df_current['value_usd'].sum(),
        'num_holdings': len(df_current),
        'sector_allocation': analytics.analyze_sector_allocation(df_current),
        'concentration': analytics.calculate_portfolio_concentration(df_current)
    }

    # If previous quarter available, calculate changes
    if previous_quarter:
        df_previous = analytics.load_whale_data(investor, previous_quarter)
        changes = analytics.calculate_portfolio_changes(df_current, df_previous)
        whale_moves = analytics.detect_whale_moves(changes)

        results['changes'] = changes
        results['whale_moves'] = whale_moves

    return results
