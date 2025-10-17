"""Financial Modeling Prep API integration"""
import os
import requests
import streamlit as st
from typing import Dict, Optional


class FMPAPI:
    """Financial Modeling Prep API wrapper"""

    def __init__(self):
        self.api_key = os.getenv('FMP_API_KEY', None)
        self.base_url = 'https://financialmodelingprep.com/api/v3'

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_company_profile(_self, symbol: str) -> Optional[Dict]:
        """Get company profile and fundamental data

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with company data or None if error
        """
        if not _self.api_key:
            return None

        try:
            url = f'{_self.base_url}/profile/{symbol}'
            params = {'apikey': _self.api_key}

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data and len(data) > 0:
                company = data[0]
                return {
                    'symbol': company.get('symbol'),
                    'company_name': company.get('companyName'),
                    'price': company.get('price'),
                    'market_cap': company.get('mktCap'),
                    'beta': company.get('beta'),
                    'volume_avg': company.get('volAvg'),
                    'last_div': company.get('lastDiv'),
                    'range': company.get('range'),
                    'changes': company.get('changes'),
                    'sector': company.get('sector'),
                    'industry': company.get('industry'),
                    'ceo': company.get('ceo'),
                    'website': company.get('website'),
                    'description': company.get('description'),
                    'exchange': company.get('exchangeShortName'),
                    'country': company.get('country'),
                    'ipo_date': company.get('ipoDate')
                }

            return None

        except Exception as e:
            print(f"FMP API error: {str(e)}")
            return None

    @st.cache_data(ttl=3600)
    def get_financial_ratios(_self, symbol: str) -> Optional[Dict]:
        """Get financial ratios

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with financial ratios
        """
        if not _self.api_key:
            return None

        try:
            url = f'{_self.base_url}/ratios/{symbol}'
            params = {'apikey': _self.api_key, 'limit': 1}

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data and len(data) > 0:
                ratios = data[0]
                return {
                    'pe_ratio': ratios.get('priceEarningsRatio'),
                    'pb_ratio': ratios.get('priceToBookRatio'),
                    'ps_ratio': ratios.get('priceToSalesRatio'),
                    'roe': ratios.get('returnOnEquity'),
                    'roa': ratios.get('returnOnAssets'),
                    'debt_equity': ratios.get('debtEquityRatio'),
                    'current_ratio': ratios.get('currentRatio'),
                    'quick_ratio': ratios.get('quickRatio'),
                    'gross_margin': ratios.get('grossProfitMargin'),
                    'operating_margin': ratios.get('operatingProfitMargin'),
                    'net_margin': ratios.get('netProfitMargin'),
                    'dividend_yield': ratios.get('dividendYield')
                }

            return None

        except Exception as e:
            print(f"FMP ratios error: {str(e)}")
            return None

    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def get_earnings_calendar(_self, limit: int = 20) -> Optional[list]:
        """Get earnings calendar

        Args:
            limit: Number of earnings to return

        Returns:
            List of upcoming earnings
        """
        if not _self.api_key:
            return None

        try:
            url = f'{_self.base_url}/earning_calendar'
            params = {'apikey': _self.api_key, 'limit': limit}

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data:
                return [
                    {
                        'symbol': item.get('symbol'),
                        'date': item.get('date'),
                        'eps_estimated': item.get('epsEstimated'),
                        'eps': item.get('eps'),
                        'revenue_estimated': item.get('revenueEstimated'),
                        'revenue': item.get('revenue'),
                        'fiscal_date': item.get('fiscalDateEnding'),
                        'updated': item.get('updatedFromDate')
                    }
                    for item in data[:limit]
                ]

            return None

        except Exception as e:
            print(f"FMP earnings calendar error: {str(e)}")
            return None

    @st.cache_data(ttl=3600)
    def get_stock_news(_self, symbol: str, limit: int = 10) -> Optional[list]:
        """Get stock news

        Args:
            symbol: Stock symbol
            limit: Number of news items

        Returns:
            List of news items
        """
        if not _self.api_key:
            return None

        try:
            url = f'{_self.base_url}/stock_news'
            params = {'apikey': _self.api_key, 'tickers': symbol, 'limit': limit}

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data:
                return [
                    {
                        'title': item.get('title'),
                        'text': item.get('text', '')[:200] + '...' if len(item.get('text', '')) > 200 else item.get('text', ''),
                        'url': item.get('url'),
                        'image': item.get('image'),
                        'site': item.get('site'),
                        'published_date': item.get('publishedDate'),
                        'symbol': item.get('symbol')
                    }
                    for item in data[:limit]
                ]

            return None

        except Exception as e:
            print(f"FMP news error: {str(e)}")
            return None
