"""
ETF-Whale Linkage - Analyze overlap between ETF holdings and whale portfolios
Identifies passive vs active investment intensity in user portfolios
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class ETFWhaleLinkage:
    """
    Analyzes relationships between ETF holdings and whale investor portfolios
    Calculates overlap, influence scores, and passive/active investment ratios
    """

    def __init__(self):
        """Initialize ETF-Whale Linkage analyzer"""
        self.major_etfs = {
            'QQQ': {'name': 'Invesco QQQ', 'category': 'Tech', 'aum': 200e9},
            'SPY': {'name': 'SPDR S&P 500', 'category': 'Large Cap', 'aum': 400e9},
            'VOO': {'name': 'Vanguard S&P 500', 'category': 'Large Cap', 'aum': 300e9},
            'IWM': {'name': 'iShares Russell 2000', 'category': 'Small Cap', 'aum': 60e9},
            'VTI': {'name': 'Vanguard Total Market', 'category': 'Total Market', 'aum': 350e9},
            'ARKK': {'name': 'ARK Innovation', 'category': 'Innovation', 'aum': 8e9},
            'XLF': {'name': 'Financial Select', 'category': 'Financials', 'aum': 40e9},
            'XLE': {'name': 'Energy Select', 'category': 'Energy', 'aum': 30e9},
            'XLK': {'name': 'Technology Select', 'category': 'Technology', 'aum': 50e9},
            'XLV': {'name': 'Health Care Select', 'category': 'Healthcare', 'aum': 35e9}
        }

    def generate_etf_holdings(self, etf_ticker: str, num_holdings: int = 50) -> pd.DataFrame:
        """
        Generate synthetic ETF holdings based on ETF type

        Args:
            etf_ticker: ETF ticker symbol
            num_holdings: Number of holdings to generate

        Returns:
            DataFrame with ETF holdings
        """
        if etf_ticker not in self.major_etfs:
            return pd.DataFrame()

        etf_info = self.major_etfs[etf_ticker]
        category = etf_info['category']

        # Define stock universe by category
        stock_universe = {
            'Tech': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX', 'ADBE', 'CRM',
                    'ORCL', 'CSCO', 'INTC', 'QCOM', 'AMD', 'AVGO', 'TXN', 'AMAT', 'LRCX', 'KLAC'],
            'Large Cap': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'BRK.B', 'JNJ', 'V', 'WMT', 'PG', 'JPM',
                         'UNH', 'HD', 'MA', 'BAC', 'XOM', 'CVX', 'PFE', 'ABBV', 'KO', 'PEP'],
            'Total Market': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'BRK.B', 'UNH', 'JNJ', 'XOM', 'V',
                           'WMT', 'PG', 'MA', 'HD', 'CVX', 'ABBV', 'BAC', 'PFE', 'KO', 'MRK'],
            'Small Cap': ['ROKU', 'ZM', 'SQ', 'SHOP', 'PINS', 'SNAP', 'TWLO', 'DDOG', 'CRWD', 'NET',
                         'SNOW', 'PLTR', 'COIN', 'RBLX', 'DASH', 'ABNB', 'UBER', 'LYFT', 'DOCU', 'ZS'],
            'Innovation': ['TSLA', 'ROKU', 'SQ', 'SHOP', 'COIN', 'RBLX', 'PLTR', 'CRWD', 'SNOW', 'NET',
                          'ZM', 'TWLO', 'DDOG', 'PINS', 'SNAP', 'PATH', 'U', 'DKNG', 'TDOC', 'EXAS'],
            'Financials': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BK', 'AXP', 'USB', 'PNC',
                          'SCHW', 'BLK', 'CB', 'MMC', 'ICE', 'CME', 'SPGI', 'MCO', 'AON', 'TRV'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PXD', 'MPC', 'PSX', 'VLO', 'OXY',
                      'HAL', 'BKR', 'WMB', 'KMI', 'OKE', 'DVN', 'FANG', 'HES', 'MRO', 'APA'],
            'Technology': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CSCO', 'ADBE', 'CRM', 'INTC', 'AMD',
                          'QCOM', 'TXN', 'AMAT', 'LRCX', 'KLAC', 'SNPS', 'CDNS', 'MCHP', 'FTNT', 'PANW'],
            'Healthcare': ['UNH', 'JNJ', 'PFE', 'ABBV', 'TMO', 'MRK', 'ABT', 'LLY', 'DHR', 'BMY',
                          'AMGN', 'GILD', 'CVS', 'CI', 'ISRG', 'VRTX', 'REGN', 'HUM', 'ZTS', 'BIIB']
        }

        tickers = stock_universe.get(category, stock_universe['Large Cap'])

        # Generate holdings
        holdings = []

        # Use exponential distribution for weights (top-heavy like real ETFs)
        weights = np.random.exponential(2, num_holdings)
        weights = (weights / weights.sum()) * 100  # Normalize to 100%
        weights = np.sort(weights)[::-1]  # Sort descending

        for i in range(min(num_holdings, len(tickers))):
            holdings.append({
                'etf_ticker': etf_ticker,
                'ticker': tickers[i % len(tickers)],
                'weight': weights[i],
                'shares': np.random.randint(1000, 100000),
                'value_usd': weights[i] * etf_info['aum'] / 100
            })

        return pd.DataFrame(holdings)

    def calculate_etf_whale_overlap(
        self,
        etf_holdings: pd.DataFrame,
        whale_holdings: pd.DataFrame,
        etf_ticker: str,
        whale_name: str
    ) -> Dict:
        """
        Calculate overlap between ETF holdings and whale portfolio

        Args:
            etf_holdings: ETF holdings DataFrame
            whale_holdings: Whale portfolio DataFrame
            etf_ticker: ETF ticker
            whale_name: Whale investor name

        Returns:
            Dict with overlap metrics
        """
        # Find common tickers
        etf_tickers = set(etf_holdings['ticker'].unique())
        whale_tickers = set(whale_holdings['ticker'].unique())

        common_tickers = etf_tickers.intersection(whale_tickers)

        if len(common_tickers) == 0:
            return {
                'etf_ticker': etf_ticker,
                'whale_name': whale_name,
                'num_common': 0,
                'overlap_pct': 0.0,
                'whale_exposure_to_etf': 0.0,
                'etf_representation_in_whale': 0.0,
                'common_tickers': []
            }

        # Calculate overlap percentage
        total_unique = len(etf_tickers.union(whale_tickers))
        overlap_pct = (len(common_tickers) / total_unique) * 100

        # Calculate whale's exposure to this ETF's top holdings
        etf_top10 = set(etf_holdings.nlargest(10, 'weight')['ticker'])
        whale_in_etf_top10 = etf_top10.intersection(whale_tickers)

        whale_weight_in_etf_top10 = whale_holdings[
            whale_holdings['ticker'].isin(whale_in_etf_top10)
        ]['portfolio_weight'].sum()

        # Calculate how much of whale's portfolio overlaps with ETF
        whale_weight_in_common = whale_holdings[
            whale_holdings['ticker'].isin(common_tickers)
        ]['portfolio_weight'].sum()

        return {
            'etf_ticker': etf_ticker,
            'whale_name': whale_name,
            'num_common': len(common_tickers),
            'overlap_pct': overlap_pct,
            'whale_exposure_to_etf_top10': whale_weight_in_etf_top10,
            'whale_exposure_to_all_etf': whale_weight_in_common,
            'common_tickers': list(common_tickers)
        }

    def analyze_whale_etf_alignment(
        self,
        whale_holdings_dict: Dict[str, pd.DataFrame],
        etf_list: List[str] = None
    ) -> pd.DataFrame:
        """
        Analyze alignment between multiple whales and multiple ETFs

        Args:
            whale_holdings_dict: Dict mapping whale names to their portfolios
            etf_list: List of ETF tickers to analyze

        Returns:
            DataFrame with all whale-ETF overlaps
        """
        if etf_list is None:
            etf_list = ['QQQ', 'SPY', 'ARKK', 'XLF', 'XLE']

        results = []

        for etf_ticker in etf_list:
            etf_holdings = self.generate_etf_holdings(etf_ticker, num_holdings=50)

            if len(etf_holdings) == 0:
                continue

            for whale_name, whale_holdings in whale_holdings_dict.items():
                overlap = self.calculate_etf_whale_overlap(
                    etf_holdings,
                    whale_holdings,
                    etf_ticker,
                    whale_name
                )
                results.append(overlap)

        return pd.DataFrame(results)

    def calculate_passive_active_ratio(
        self,
        user_portfolio: pd.DataFrame,
        whale_holdings_dict: Dict[str, pd.DataFrame],
        major_etfs: List[str] = None
    ) -> Dict:
        """
        Calculate passive vs active investment ratio in user portfolio

        Passive = overlaps with major ETFs
        Active = overlaps with whale picks (unique to whales, not in major ETFs)

        Args:
            user_portfolio: User's portfolio
            whale_holdings_dict: Whale portfolios
            major_etfs: List of major ETF tickers

        Returns:
            Dict with passive/active metrics
        """
        if major_etfs is None:
            major_etfs = ['SPY', 'QQQ', 'VTI']

        user_tickers = set(user_portfolio['ticker'].unique())

        # Get all ETF holdings
        etf_tickers_combined = set()
        for etf in major_etfs:
            etf_holdings = self.generate_etf_holdings(etf)
            etf_tickers_combined.update(etf_holdings['ticker'].unique())

        # Get all whale holdings
        whale_tickers_combined = set()
        for whale_holdings in whale_holdings_dict.values():
            whale_tickers_combined.update(whale_holdings['ticker'].unique())

        # Passive stocks: in user portfolio AND in major ETFs
        passive_stocks = user_tickers.intersection(etf_tickers_combined)

        # Active stocks: in user portfolio AND in whale portfolios BUT NOT in major ETFs
        active_stocks = user_tickers.intersection(whale_tickers_combined - etf_tickers_combined)

        # ETF-only stocks: in user AND ETF but NOT in whale portfolios
        etf_only = user_tickers.intersection(etf_tickers_combined - whale_tickers_combined)

        # Whale-only stocks: in user AND whale but NOT in ETFs
        whale_only = user_tickers.intersection(whale_tickers_combined - etf_tickers_combined)

        # Calculate weights
        passive_weight = user_portfolio[
            user_portfolio['ticker'].isin(passive_stocks)
        ]['portfolio_weight'].sum() if 'portfolio_weight' in user_portfolio.columns else 0

        active_weight = user_portfolio[
            user_portfolio['ticker'].isin(active_stocks)
        ]['portfolio_weight'].sum() if 'portfolio_weight' in user_portfolio.columns else 0

        total_analyzed_weight = passive_weight + active_weight

        passive_ratio = (passive_weight / total_analyzed_weight * 100) if total_analyzed_weight > 0 else 0
        active_ratio = (active_weight / total_analyzed_weight * 100) if total_analyzed_weight > 0 else 0

        return {
            'num_passive_stocks': len(passive_stocks),
            'num_active_stocks': len(active_stocks),
            'num_etf_only': len(etf_only),
            'num_whale_only': len(whale_only),
            'passive_weight': passive_weight,
            'active_weight': active_weight,
            'passive_ratio': passive_ratio,
            'active_ratio': active_ratio,
            'investment_style': 'Passive-Heavy' if passive_ratio > 60 else 'Active-Heavy' if active_ratio > 60 else 'Balanced',
            'passive_stocks': list(passive_stocks),
            'active_stocks': list(active_stocks)
        }

    def get_top_etf_whale_overlaps(
        self,
        analysis_df: pd.DataFrame,
        n: int = 10
    ) -> pd.DataFrame:
        """
        Get top N ETF-whale overlaps by exposure

        Args:
            analysis_df: Result from analyze_whale_etf_alignment
            n: Number of top overlaps

        Returns:
            DataFrame with top overlaps
        """
        df = analysis_df.copy()
        df = df.sort_values('whale_exposure_to_all_etf', ascending=False)
        return df.head(n)

    def identify_etf_concentrated_whales(
        self,
        analysis_df: pd.DataFrame,
        etf_ticker: str
    ) -> List[Dict]:
        """
        Identify whales with high concentration in specific ETF's holdings

        Args:
            analysis_df: ETF-whale alignment analysis
            etf_ticker: Target ETF

        Returns:
            List of whale concentration metrics
        """
        etf_data = analysis_df[analysis_df['etf_ticker'] == etf_ticker]

        concentrations = []

        for _, row in etf_data.iterrows():
            if row['whale_exposure_to_all_etf'] > 30:  # >30% threshold
                concentrations.append({
                    'whale_name': row['whale_name'],
                    'exposure': row['whale_exposure_to_all_etf'],
                    'num_common': row['num_common'],
                    'concentration_level': 'HIGH' if row['whale_exposure_to_all_etf'] > 50 else 'MODERATE'
                })

        return sorted(concentrations, key=lambda x: x['exposure'], reverse=True)


def quick_etf_whale_linkage(
    whale_holdings_dict: Dict[str, pd.DataFrame],
    user_portfolio: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Quick ETF-whale linkage analysis

    Args:
        whale_holdings_dict: Whale portfolios
        user_portfolio: Optional user portfolio

    Returns:
        Dict with all analysis results
    """
    linkage = ETFWhaleLinkage()

    # Analyze whale-ETF alignment
    alignment = linkage.analyze_whale_etf_alignment(
        whale_holdings_dict,
        etf_list=['QQQ', 'SPY', 'ARKK', 'XLF', 'XLE', 'XLK', 'XLV']
    )

    # Get top overlaps
    top_overlaps = linkage.get_top_etf_whale_overlaps(alignment, n=15)

    # Identify concentrated whales for each ETF
    etf_concentrations = {}
    for etf in ['QQQ', 'SPY', 'ARKK']:
        concentrations = linkage.identify_etf_concentrated_whales(alignment, etf)
        if concentrations:
            etf_concentrations[etf] = concentrations

    results = {
        'alignment_analysis': alignment,
        'top_overlaps': top_overlaps,
        'etf_concentrations': etf_concentrations
    }

    # User portfolio analysis (if provided)
    if user_portfolio is not None:
        passive_active = linkage.calculate_passive_active_ratio(
            user_portfolio,
            whale_holdings_dict
        )
        results['user_passive_active'] = passive_active

    return results
