"""FRED API integration for macroeconomic indicators"""
import streamlit as st
from .secret_utils import get_secret
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional


class FREDAPI:
    """FRED API wrapper for macroeconomic data"""

    def __init__(self):
        self.api_key = get_secret('FRED_API_KEY', 'fred', default=None)
        self.fred = None

        # Try to import fredapi
        try:
            from fredapi import Fred
            if self.api_key:
                self.fred = Fred(api_key=self.api_key)
        except ImportError:
            print("fredapi not installed. Run: pip install fredapi")

    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def get_global_liquidity_index(_self) -> Optional[Dict]:
        """Get global liquidity index data

        Returns:
            Dictionary with liquidity data or None if error
        """
        if not _self.fred:
            return None

        try:
            # Get M2 Money Supply
            m2 = _self.fred.get_series('M2SL', observation_start='2020-01-01')

            # Get Federal Reserve Balance Sheet
            fed_balance = _self.fred.get_series('WALCL', observation_start='2020-01-01')

            # Normalize and combine (simple liquidity proxy)
            # Convert to billions and align dates
            m2_billions = m2 / 1000  # M2 is in billions
            fed_billions = fed_balance / 1000  # WALCL is in millions, convert to billions

            # Align the series
            combined = pd.DataFrame({
                'M2': m2_billions,
                'FED': fed_billions
            }).fillna(method='ffill')

            # Simple liquidity index (weighted average)
            combined['Liquidity_Index'] = (combined['M2'] * 0.6 + combined['FED'] * 0.4)

            # Normalize to 100 base
            base_value = combined['Liquidity_Index'].iloc[0]
            combined['Liquidity_Index'] = (combined['Liquidity_Index'] / base_value) * 100

            return {
                'dates': combined.index.tolist(),
                'values': combined['Liquidity_Index'].tolist(),
                'current': combined['Liquidity_Index'].iloc[-1],
                'previous': combined['Liquidity_Index'].iloc[-2],
                'change_pct': ((combined['Liquidity_Index'].iloc[-1] - combined['Liquidity_Index'].iloc[-2]) / combined['Liquidity_Index'].iloc[-2]) * 100,
                'm2': m2_billions.tolist(),
                'fed_balance': fed_billions.tolist()
            }

        except Exception as e:
            print(f"FRED API error: {str(e)}")
            return None

    @st.cache_data(ttl=86400)
    def get_interest_rates(_self) -> Optional[Dict]:
        """Get key interest rate data

        Returns:
            Dictionary with interest rate data
        """
        if not _self.fred:
            return None

        try:
            # Federal Funds Rate
            fed_funds = _self.fred.get_series('DFF')

            # 10-Year Treasury
            treasury_10y = _self.fred.get_series('DGS10')

            # 2-Year Treasury
            treasury_2y = _self.fred.get_series('DGS2')

            return {
                'fed_funds_rate': {
                    'current': fed_funds.iloc[-1],
                    'previous': fed_funds.iloc[-2],
                    'dates': fed_funds.index[-30:].tolist(),
                    'values': fed_funds.iloc[-30:].tolist()
                },
                'treasury_10y': {
                    'current': treasury_10y.iloc[-1],
                    'previous': treasury_10y.iloc[-2],
                    'dates': treasury_10y.index[-30:].tolist(),
                    'values': treasury_10y.iloc[-30:].tolist()
                },
                'treasury_2y': {
                    'current': treasury_2y.iloc[-1],
                    'previous': treasury_2y.iloc[-2],
                    'dates': treasury_2y.index[-30:].tolist(),
                    'values': treasury_2y.iloc[-30:].tolist()
                },
                'yield_curve': treasury_10y.iloc[-1] - treasury_2y.iloc[-1]
            }

        except Exception as e:
            print(f"FRED interest rates error: {str(e)}")
            return None

    @st.cache_data(ttl=86400)
    def get_economic_indicators(_self) -> Optional[Dict]:
        """Get key economic indicators

        Returns:
            Dictionary with economic indicator data
        """
        if not _self.fred:
            return None

        try:
            # GDP
            gdp = _self.fred.get_series('GDP')

            # CPI (Inflation)
            cpi = _self.fred.get_series('CPIAUCSL')

            # Unemployment Rate
            unemployment = _self.fred.get_series('UNRATE')

            # Calculate inflation rate (YoY)
            inflation_rate = ((cpi.iloc[-1] - cpi.iloc[-13]) / cpi.iloc[-13]) * 100 if len(cpi) >= 13 else 0

            return {
                'gdp': {
                    'current': gdp.iloc[-1],
                    'previous': gdp.iloc[-2],
                    'growth_rate': ((gdp.iloc[-1] - gdp.iloc[-5]) / gdp.iloc[-5]) * 100 if len(gdp) >= 5 else 0
                },
                'inflation': {
                    'current': inflation_rate,
                    'cpi': cpi.iloc[-1],
                    'dates': cpi.index[-12:].tolist(),
                    'values': cpi.iloc[-12:].tolist()
                },
                'unemployment': {
                    'current': unemployment.iloc[-1],
                    'previous': unemployment.iloc[-2],
                    'dates': unemployment.index[-12:].tolist(),
                    'values': unemployment.iloc[-12:].tolist()
                }
            }

        except Exception as e:
            print(f"FRED economic indicators error: {str(e)}")
            return None
