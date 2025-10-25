"""
ETF Holdings Weight Tracker Module
Track ETF/Fund holdings and weight changes over time
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import sqlite3
import warnings
warnings.filterwarnings('ignore')


class ETFWeightTracker:
    """
    ETF/Fund Holdings Weight Tracker

    Features:
    1. Get all funds/ETFs that hold a specific stock
    2. Track weight changes over time
    3. Detect fund manager actions (buy/sell signals)
    4. Reverse lookup: Which funds hold this stock?
    """

    def __init__(self, db_path: str = "data/etf_holdings.db"):
        self.db_path = db_path
        self._init_database()

        # Popular ETFs to track
        self.TRACKED_ETFS = {
            # US Market
            'SPY': 'SPDR S&P 500 ETF',
            'QQQ': 'Invesco QQQ (Nasdaq 100)',
            'IWM': 'iShares Russell 2000',
            'DIA': 'SPDR Dow Jones Industrial',
            'VTI': 'Vanguard Total Stock Market',
            'VOO': 'Vanguard S&P 500',

            # Sector ETFs
            'XLK': 'Technology Select Sector',
            'XLF': 'Financial Select Sector',
            'XLE': 'Energy Select Sector',
            'XLV': 'Health Care Select Sector',
            'XLI': 'Industrial Select Sector',
            'XLP': 'Consumer Staples Select',
            'XLY': 'Consumer Discretionary Select',
            'XLU': 'Utilities Select Sector',
            'XLRE': 'Real Estate Select Sector',
            'XLC': 'Communication Services Select',

            # Tech-focused
            'ARKK': 'ARK Innovation ETF',
            'ARKW': 'ARK Next Generation Internet',
            'WCLD': 'WisdomTree Cloud Computing',
            'SKYY': 'First Trust Cloud Computing',

            # Growth
            'VUG': 'Vanguard Growth ETF',
            'IWF': 'iShares Russell 1000 Growth',
            'MTUM': 'iShares Edge MSCI USA Momentum'
        }

    def _init_database(self):
        """Initialize SQLite database for holdings storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create holdings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fund_code TEXT NOT NULL,
                fund_name TEXT,
                stock_symbol TEXT NOT NULL,
                weight_pct REAL,
                shares REAL,
                market_value REAL,
                report_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(fund_code, stock_symbol, report_date)
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_symbol
            ON holdings(stock_symbol)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fund_code
            ON holdings(fund_code)
        """)

        conn.commit()
        conn.close()

    def fetch_etf_holdings(self, etf_ticker: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetch current holdings for an ETF from yfinance

        Args:
            etf_ticker: ETF ticker symbol (e.g., 'SPY', 'QQQ')
            force_refresh: Force fetch from API even if cached

        Returns:
            DataFrame with holdings data
        """
        # Check if we have recent data (< 7 days old)
        if not force_refresh:
            cached_data = self._get_cached_holdings(etf_ticker, days=7)
            if cached_data is not None and len(cached_data) > 0:
                return cached_data

        # Fetch from yfinance
        try:
            etf = yf.Ticker(etf_ticker)
            holdings_data = etf.get_holdings()

            if holdings_data is not None and not holdings_data.empty:
                # Process holdings
                df = holdings_data.copy()

                # Rename columns to standard format
                if 'symbol' in df.columns:
                    df.rename(columns={'symbol': 'stock_symbol'}, inplace=True)
                if 'holdingPercent' in df.columns:
                    df.rename(columns={'holdingPercent': 'weight_pct'}, inplace=True)
                elif 'weight' in df.columns:
                    df.rename(columns={'weight': 'weight_pct'}, inplace=True)

                # Add metadata
                df['fund_code'] = etf_ticker
                df['fund_name'] = self.TRACKED_ETFS.get(etf_ticker, etf_ticker)
                df['report_date'] = datetime.now().strftime('%Y-%m-%d')

                # Ensure weight is percentage (0-100)
                if df['weight_pct'].max() <= 1.0:
                    df['weight_pct'] = df['weight_pct'] * 100

                # Save to database
                self._save_holdings_to_db(df)

                return df

        except Exception as e:
            print(f"Warning: Could not fetch holdings for {etf_ticker}: {e}")

        return pd.DataFrame()

    def _get_cached_holdings(self, fund_code: str, days: int = 7) -> Optional[pd.DataFrame]:
        """Get cached holdings from database"""
        conn = sqlite3.connect(self.db_path)

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = """
            SELECT * FROM holdings
            WHERE fund_code = ? AND report_date >= ?
            ORDER BY report_date DESC
        """

        df = pd.read_sql_query(query, conn, params=(fund_code, cutoff_date))
        conn.close()

        return df if len(df) > 0 else None

    def _save_holdings_to_db(self, holdings_df: pd.DataFrame):
        """Save holdings to database"""
        conn = sqlite3.connect(self.db_path)

        # Select only relevant columns
        cols_to_save = ['fund_code', 'fund_name', 'stock_symbol', 'weight_pct', 'report_date']
        df_to_save = holdings_df[[col for col in cols_to_save if col in holdings_df.columns]]

        # Use replace to handle duplicates
        df_to_save.to_sql('holdings', conn, if_exists='append', index=False)

        conn.commit()
        conn.close()

    def get_funds_for_stock(self, stock_symbol: str, min_weight: float = 0.1) -> pd.DataFrame:
        """
        Find all ETFs/funds that hold a specific stock

        Args:
            stock_symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
            min_weight: Minimum weight percentage to include (default 0.1%)

        Returns:
            DataFrame with fund holdings sorted by weight
        """
        # Clean symbol (remove exchange suffix if present)
        clean_symbol = stock_symbol.split('.')[0].upper()

        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT
                fund_code,
                fund_name,
                stock_symbol,
                weight_pct,
                report_date,
                MAX(report_date) as latest_date
            FROM holdings
            WHERE stock_symbol = ?
            AND weight_pct >= ?
            GROUP BY fund_code, stock_symbol
            ORDER BY weight_pct DESC
        """

        df = pd.read_sql_query(query, conn, params=(clean_symbol, min_weight))
        conn.close()

        return df

    def get_weight_history(self, stock_symbol: str, fund_code: str) -> pd.DataFrame:
        """
        Get historical weight changes for a stock in a specific fund

        Args:
            stock_symbol: Stock ticker
            fund_code: ETF ticker

        Returns:
            DataFrame with historical weights
        """
        clean_symbol = stock_symbol.split('.')[0].upper()

        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT
                report_date,
                weight_pct,
                fund_code,
                fund_name
            FROM holdings
            WHERE stock_symbol = ? AND fund_code = ?
            ORDER BY report_date ASC
        """

        df = pd.read_sql_query(query, conn, params=(clean_symbol, fund_code))
        conn.close()

        if len(df) > 0:
            df['report_date'] = pd.to_datetime(df['report_date'])

            # Calculate weight change
            df['weight_change'] = df['weight_pct'].diff()
            df['weight_change_pct'] = df['weight_pct'].pct_change() * 100

        return df

    def get_weight_changes(self, stock_symbol: str, period_days: int = 30) -> pd.DataFrame:
        """
        Calculate recent weight changes across all funds

        Args:
            stock_symbol: Stock ticker
            period_days: Period to analyze (default 30 days)

        Returns:
            DataFrame with weight changes
        """
        clean_symbol = stock_symbol.split('.')[0].upper()

        conn = sqlite3.connect(self.db_path)

        cutoff_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')

        query = """
            WITH latest_holdings AS (
                SELECT
                    fund_code,
                    stock_symbol,
                    weight_pct as current_weight,
                    report_date as current_date
                FROM holdings
                WHERE stock_symbol = ?
                AND report_date >= ?
            ),
            previous_holdings AS (
                SELECT
                    fund_code,
                    stock_symbol,
                    weight_pct as previous_weight,
                    report_date as previous_date
                FROM holdings
                WHERE stock_symbol = ?
                AND report_date < ?
            )
            SELECT
                l.fund_code,
                l.stock_symbol,
                l.current_weight,
                l.current_date,
                p.previous_weight,
                p.previous_date,
                (l.current_weight - COALESCE(p.previous_weight, 0)) as weight_change,
                CASE
                    WHEN p.previous_weight > 0
                    THEN ((l.current_weight - p.previous_weight) / p.previous_weight * 100)
                    ELSE NULL
                END as weight_change_pct
            FROM latest_holdings l
            LEFT JOIN previous_holdings p
                ON l.fund_code = p.fund_code AND l.stock_symbol = p.stock_symbol
            ORDER BY weight_change DESC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(clean_symbol, cutoff_date, clean_symbol, cutoff_date)
        )

        conn.close()

        return df

    def get_top_weight_changes(self, period_days: int = 30, limit: int = 20) -> pd.DataFrame:
        """
        Get stocks with biggest weight changes across all funds

        Args:
            period_days: Analysis period
            limit: Number of results to return

        Returns:
            DataFrame with top weight changes
        """
        conn = sqlite3.connect(self.db_path)

        cutoff_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')

        query = f"""
            WITH recent_changes AS (
                SELECT
                    h1.stock_symbol,
                    h1.fund_code,
                    h1.weight_pct as current_weight,
                    h2.weight_pct as previous_weight,
                    (h1.weight_pct - h2.weight_pct) as weight_change,
                    h1.report_date
                FROM holdings h1
                INNER JOIN holdings h2
                    ON h1.fund_code = h2.fund_code
                    AND h1.stock_symbol = h2.stock_symbol
                WHERE h1.report_date >= ?
                AND h2.report_date < ?
                AND ABS(h1.weight_pct - h2.weight_pct) > 0.5
            )
            SELECT
                stock_symbol,
                COUNT(*) as num_funds_changed,
                AVG(weight_change) as avg_weight_change,
                SUM(CASE WHEN weight_change > 0 THEN 1 ELSE 0 END) as funds_increased,
                SUM(CASE WHEN weight_change < 0 THEN 1 ELSE 0 END) as funds_decreased
            FROM recent_changes
            GROUP BY stock_symbol
            ORDER BY ABS(avg_weight_change) DESC
            LIMIT ?
        """

        df = pd.read_sql_query(query, conn, params=(cutoff_date, cutoff_date, limit))
        conn.close()

        return df

    def detect_fund_manager_actions(self, stock_symbol: str, threshold: float = 1.0) -> Dict:
        """
        Detect significant fund manager actions (buy/sell)

        Args:
            stock_symbol: Stock ticker
            threshold: Minimum weight change to flag (default 1%)

        Returns:
            Dictionary with action signals
        """
        changes_df = self.get_weight_changes(stock_symbol, period_days=30)

        if len(changes_df) == 0:
            return {
                'signal': 'NEUTRAL',
                'confidence': 0,
                'details': 'No recent data available'
            }

        # Count significant increases/decreases
        increases = (changes_df['weight_change'] >= threshold).sum()
        decreases = (changes_df['weight_change'] <= -threshold).sum()
        total_funds = len(changes_df)

        # Calculate signal
        if increases > decreases and increases >= total_funds * 0.6:
            signal = 'BULLISH'
            confidence = (increases / total_funds) * 100
            details = f"{increases}/{total_funds} fonunda ağırlık artışı"
        elif decreases > increases and decreases >= total_funds * 0.6:
            signal = 'BEARISH'
            confidence = (decreases / total_funds) * 100
            details = f"{decreases}/{total_funds} fonunda ağırlık azalışı"
        else:
            signal = 'NEUTRAL'
            confidence = 50
            details = f"Karışık sinyaller: {increases} artış, {decreases} azalış"

        return {
            'signal': signal,
            'confidence': round(confidence, 1),
            'details': details,
            'increases': int(increases),
            'decreases': int(decreases),
            'total_funds': int(total_funds)
        }

    def bulk_fetch_etf_holdings(self, etf_list: List[str] = None, force_refresh: bool = False):
        """
        Fetch holdings for multiple ETFs

        Args:
            etf_list: List of ETF tickers (default: all tracked ETFs)
            force_refresh: Force refresh from API
        """
        if etf_list is None:
            etf_list = list(self.TRACKED_ETFS.keys())

        results = {}

        for etf in etf_list:
            print(f"Fetching holdings for {etf}...")
            holdings = self.fetch_etf_holdings(etf, force_refresh=force_refresh)

            if len(holdings) > 0:
                results[etf] = {
                    'success': True,
                    'num_holdings': len(holdings),
                    'top_holding': holdings.iloc[0]['stock_symbol'] if len(holdings) > 0 else None
                }
            else:
                results[etf] = {
                    'success': False,
                    'error': 'No holdings data available'
                }

        return results

    def get_summary_stats(self) -> Dict:
        """Get summary statistics of the database"""
        conn = sqlite3.connect(self.db_path)

        stats = {}

        # Total holdings records
        stats['total_records'] = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM holdings", conn
        ).iloc[0]['count']

        # Unique stocks
        stats['unique_stocks'] = pd.read_sql_query(
            "SELECT COUNT(DISTINCT stock_symbol) as count FROM holdings", conn
        ).iloc[0]['count']

        # Unique funds
        stats['unique_funds'] = pd.read_sql_query(
            "SELECT COUNT(DISTINCT fund_code) as count FROM holdings", conn
        ).iloc[0]['count']

        # Latest update date
        latest_date = pd.read_sql_query(
            "SELECT MAX(report_date) as date FROM holdings", conn
        ).iloc[0]['date']
        stats['latest_update'] = latest_date

        conn.close()

        return stats
