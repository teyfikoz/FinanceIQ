"""
TEFAS Portfolio Tracker
=======================
Tracks Turkish fund portfolio changes over time.
Analyzes monthly portfolio composition and identifies changes.
"""

import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time


class TEFASPortfolioTracker:
    """
    Track TEFAS fund portfolio changes over time.
    """

    def __init__(self):
        self.base_url = "https://www.tefas.gov.tr/api/DB"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def get_fund_portfolio(self, fund_code: str, date: str = None) -> Optional[Dict]:
        """
        Get fund portfolio for a specific date.

        Args:
            fund_code: TEFAS fund code (e.g., 'TCD', 'AKG')
            date: Date in YYYY-MM-DD format, defaults to today

        Returns:
            Dictionary with portfolio holdings
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            # TEFAS Portfolio endpoint
            endpoint = f"{self.base_url}/BindHistoryInfo"
            payload = {
                "fontip": "YAT",
                "fonkod": fund_code,
                "bastarih": date,
                "bittarih": date
            }

            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data or 'data' not in data:
                return None

            portfolio_data = data.get('data', [])

            if not portfolio_data:
                return None

            latest = portfolio_data[0] if portfolio_data else {}

            return {
                'fund_code': fund_code,
                'date': date,
                'portfolio_value': latest.get('toplam_deger', 0),
                'number_of_investors': latest.get('kisi_sayisi', 0),
                'number_of_shares': latest.get('tedpaysay', 0),
                'holdings': self._parse_holdings(latest),
                'asset_allocation': self._parse_asset_allocation(latest)
            }

        except Exception as e:
            print(f"Error getting portfolio for {fund_code} on {date}: {e}")
            return None

    def _parse_holdings(self, data: Dict) -> List[Dict]:
        """Parse individual holdings from TEFAS data."""
        holdings = []

        # TEFAS provides holdings in different fields
        # This is a simplified version - actual structure may vary
        portfolio_items = data.get('portfolio', [])

        for item in portfolio_items:
            holdings.append({
                'security_name': item.get('name', ''),
                'security_code': item.get('code', ''),
                'weight': float(item.get('weight', 0)),
                'value': float(item.get('value', 0)),
                'quantity': float(item.get('quantity', 0)),
                'sector': item.get('sector', 'Unknown')
            })

        return holdings

    def _parse_asset_allocation(self, data: Dict) -> Dict[str, float]:
        """Parse asset allocation percentages."""
        return {
            'stocks': float(data.get('hisse_oran', 0)),
            'bonds': float(data.get('tahvil_oran', 0)),
            'bills': float(data.get('bono_oran', 0)),
            'repo': float(data.get('repo_oran', 0)),
            'fx': float(data.get('doviz_oran', 0)),
            'participation': float(data.get('katilma_oran', 0)),
            'precious_metals': float(data.get('kiymetli_maden_oran', 0)),
            'other': float(data.get('diger_oran', 0))
        }

    def get_monthly_portfolio_changes(self, fund_code: str, months: int = 12) -> pd.DataFrame:
        """
        Get portfolio changes over the specified number of months.

        Args:
            fund_code: TEFAS fund code
            months: Number of months to track (default 12)

        Returns:
            DataFrame with monthly portfolio data
        """
        try:
            monthly_data = []
            end_date = datetime.now()

            for i in range(months):
                # Get last day of each month
                target_date = end_date - relativedelta(months=i)
                # Set to last day of month
                next_month = target_date.replace(day=28) + timedelta(days=4)
                last_day = next_month - timedelta(days=next_month.day)

                date_str = last_day.strftime("%Y-%m-%d")

                portfolio = self.get_fund_portfolio(fund_code, date_str)

                if portfolio:
                    monthly_data.append({
                        'date': date_str,
                        'month': last_day.strftime("%Y-%m"),
                        'portfolio_value': portfolio['portfolio_value'],
                        'num_investors': portfolio['number_of_investors'],
                        'asset_allocation': portfolio['asset_allocation'],
                        'holdings': portfolio['holdings']
                    })

                # Rate limiting
                time.sleep(0.5)

            df = pd.DataFrame(monthly_data)
            df = df.sort_values('date')

            return df

        except Exception as e:
            print(f"Error getting monthly changes for {fund_code}: {e}")
            return pd.DataFrame()

    def calculate_allocation_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate month-over-month allocation changes.

        Args:
            df: DataFrame from get_monthly_portfolio_changes

        Returns:
            DataFrame with allocation changes
        """
        if df.empty:
            return pd.DataFrame()

        try:
            changes = []

            for i in range(1, len(df)):
                prev_month = df.iloc[i - 1]
                curr_month = df.iloc[i]

                prev_alloc = prev_month['asset_allocation']
                curr_alloc = curr_month['asset_allocation']

                month_changes = {
                    'month': curr_month['month'],
                    'date': curr_month['date']
                }

                # Calculate changes for each asset class
                for asset_class in prev_alloc.keys():
                    prev_val = prev_alloc[asset_class]
                    curr_val = curr_alloc[asset_class]
                    change = curr_val - prev_val

                    month_changes[f'{asset_class}_prev'] = prev_val
                    month_changes[f'{asset_class}_curr'] = curr_val
                    month_changes[f'{asset_class}_change'] = change

                changes.append(month_changes)

            return pd.DataFrame(changes)

        except Exception as e:
            print(f"Error calculating allocation changes: {e}")
            return pd.DataFrame()

    def identify_new_and_removed_holdings(self, df: pd.DataFrame) -> Dict[str, List]:
        """
        Identify securities added or removed from portfolio.

        Args:
            df: DataFrame from get_monthly_portfolio_changes

        Returns:
            Dictionary with new and removed holdings per month
        """
        if df.empty or len(df) < 2:
            return {}

        try:
            changes_by_month = {}

            for i in range(1, len(df)):
                prev_month = df.iloc[i - 1]
                curr_month = df.iloc[i]

                prev_holdings = {h['security_code']: h for h in prev_month['holdings']}
                curr_holdings = {h['security_code']: h for h in curr_month['holdings']}

                # Find new holdings
                new_codes = set(curr_holdings.keys()) - set(prev_holdings.keys())
                new_holdings = [curr_holdings[code] for code in new_codes]

                # Find removed holdings
                removed_codes = set(prev_holdings.keys()) - set(curr_holdings.keys())
                removed_holdings = [prev_holdings[code] for code in removed_codes]

                # Find weight changes for existing holdings
                weight_changes = []
                common_codes = set(curr_holdings.keys()) & set(prev_holdings.keys())

                for code in common_codes:
                    prev_weight = prev_holdings[code]['weight']
                    curr_weight = curr_holdings[code]['weight']
                    weight_change = curr_weight - prev_weight

                    if abs(weight_change) > 0.5:  # Significant change (>0.5%)
                        weight_changes.append({
                            'security_code': code,
                            'security_name': curr_holdings[code]['security_name'],
                            'prev_weight': prev_weight,
                            'curr_weight': curr_weight,
                            'change': weight_change
                        })

                changes_by_month[curr_month['month']] = {
                    'new_holdings': new_holdings,
                    'removed_holdings': removed_holdings,
                    'weight_changes': sorted(weight_changes, key=lambda x: abs(x['change']), reverse=True)
                }

            return changes_by_month

        except Exception as e:
            print(f"Error identifying holdings changes: {e}")
            return {}

    def get_top_holdings_over_time(self, fund_code: str, months: int = 6, top_n: int = 10) -> pd.DataFrame:
        """
        Track top N holdings over time.

        Args:
            fund_code: TEFAS fund code
            months: Number of months to track
            top_n: Number of top holdings to track

        Returns:
            DataFrame with top holdings evolution
        """
        try:
            monthly_df = self.get_monthly_portfolio_changes(fund_code, months)

            if monthly_df.empty:
                return pd.DataFrame()

            # Extract top holdings for each month
            top_holdings_data = []

            for _, row in monthly_df.iterrows():
                holdings = row['holdings']

                # Sort by weight
                sorted_holdings = sorted(holdings, key=lambda x: x['weight'], reverse=True)[:top_n]

                for rank, holding in enumerate(sorted_holdings, 1):
                    top_holdings_data.append({
                        'month': row['month'],
                        'rank': rank,
                        'security_name': holding['security_name'],
                        'security_code': holding['security_code'],
                        'weight': holding['weight'],
                        'value': holding['value']
                    })

            return pd.DataFrame(top_holdings_data)

        except Exception as e:
            print(f"Error getting top holdings: {e}")
            return pd.DataFrame()

    def generate_portfolio_summary(self, fund_code: str, months: int = 12) -> Dict[str, Any]:
        """
        Generate comprehensive portfolio change summary.

        Args:
            fund_code: TEFAS fund code
            months: Number of months to analyze

        Returns:
            Dictionary with summary statistics
        """
        try:
            monthly_df = self.get_monthly_portfolio_changes(fund_code, months)

            if monthly_df.empty:
                return {}

            allocation_changes = self.calculate_allocation_changes(monthly_df)
            holdings_changes = self.identify_new_and_removed_holdings(monthly_df)
            top_holdings = self.get_top_holdings_over_time(fund_code, months)

            # Calculate summary statistics
            latest = monthly_df.iloc[-1]
            oldest = monthly_df.iloc[0]

            summary = {
                'fund_code': fund_code,
                'period': f"{oldest['month']} to {latest['month']}",
                'total_months': len(monthly_df),
                'latest_portfolio_value': latest['portfolio_value'],
                'portfolio_value_change': latest['portfolio_value'] - oldest['portfolio_value'],
                'latest_num_investors': latest['num_investors'],
                'investor_change': latest['num_investors'] - oldest['num_investors'],
                'asset_allocation_current': latest['asset_allocation'],
                'asset_allocation_initial': oldest['asset_allocation'],
                'monthly_allocation_changes': allocation_changes.to_dict('records'),
                'holdings_changes_by_month': holdings_changes,
                'top_holdings_evolution': top_holdings.to_dict('records'),
                'total_new_holdings': sum(len(m['new_holdings']) for m in holdings_changes.values()),
                'total_removed_holdings': sum(len(m['removed_holdings']) for m in holdings_changes.values())
            }

            return summary

        except Exception as e:
            print(f"Error generating portfolio summary: {e}")
            return {}
