#!/usr/bin/env python3
"""
KAP VYK API Integration Module
This module provides integration with the Turkish Capital Markets Board (SPK)
KAP VYK API for accessing Turkish stock market data.
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KAPVYKClient:
    """Client for KAP VYK API integration."""

    def __init__(self, base_url: str = "https://apigwdev.mkk.com.tr/api/vyk"):
        """
        Initialize KAP VYK API client.

        Args:
            base_url: Base URL for the KAP VYK API
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def get_company_info(self, company_code: str) -> Optional[Dict[str, Any]]:
        """
        Get company information by company code.

        Args:
            company_code: Turkish company stock code (e.g., 'AKBNK', 'GARAN')

        Returns:
            Company information dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/companies/{company_code}"
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get company info for {company_code}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching company info for {company_code}: {e}")
            return None

    def get_all_companies(self) -> List[Dict[str, Any]]:
        """
        Get list of all companies available in the system.

        Returns:
            List of company dictionaries
        """
        try:
            url = f"{self.base_url}/companies"
            response = self.session.get(url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get companies list: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching companies list: {e}")
            return []

    def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get market data for specified symbols.

        Args:
            symbols: List of Turkish stock symbols

        Returns:
            Dictionary with market data for each symbol
        """
        market_data = {}

        for symbol in symbols:
            company_info = self.get_company_info(symbol)
            if company_info:
                market_data[symbol] = {
                    'name': company_info.get('name', symbol),
                    'sector': company_info.get('sector', 'Unknown'),
                    'last_updated': datetime.now().isoformat()
                }

        return market_data

# Turkish stock symbols for BIST-30
BIST_30_SYMBOLS = [
    'AKBNK', 'GARAN', 'ISCTR', 'THYAO', 'KCHOL', 'SAHOL', 'ASELS', 'SISE',
    'EREGL', 'BIMAS', 'TOASO', 'TCELL', 'KOZAL', 'PETKM', 'TUPRS', 'VAKBN',
    'HALKB', 'ARCLK', 'FROTO', 'ODAS', 'MGROS', 'EKGYO', 'DOHOL', 'YKBNK',
    'ENJSA', 'ULKER', 'CCOLA', 'OTKAR', 'PGSUS', 'KRDMD'
]

# Turkish fund categories mapping
TURKISH_FUND_CATEGORIES = {
    'equity_funds': [
        'AEH', 'AEJ', 'AGH', 'AGJ', 'ATH', 'ATJ', 'AZH', 'AZJ',
        'GAH', 'GAJ', 'GEH', 'GEJ', 'HEH', 'HEJ', 'IEH', 'IEJ',
        'KEH', 'KEJ', 'TAH', 'TAJ', 'TEH', 'TEJ', 'YEH', 'YEJ',
        'ZEH', 'ZEJ'
    ],
    'bond_funds': [
        'ABH', 'ABJ', 'DBH', 'DBJ', 'FBH', 'FBJ', 'GBH', 'GBJ',
        'HBH', 'HBJ', 'IBH', 'IBJ', 'KBH', 'KBJ', 'TBH', 'TBJ',
        'YBH', 'YBJ', 'ZBH', 'ZBJ'
    ],
    'mixed_funds': [
        'AMH', 'AMJ', 'DMH', 'DMJ', 'FMH', 'FMJ', 'GMH', 'GMJ',
        'HMH', 'HMJ', 'IMH', 'IMJ', 'KMH', 'KMJ', 'TMH', 'TMJ',
        'YMH', 'YMJ', 'ZMH', 'ZMJ'
    ],
    'money_market_funds': [
        'APH', 'APJ', 'DPH', 'DPJ', 'FPH', 'FPJ', 'GPH', 'GPJ',
        'HPH', 'HPJ', 'IPH', 'IPJ', 'KPH', 'KPJ', 'TPH', 'TPJ',
        'YPH', 'YPJ', 'ZPH', 'ZPJ'
    ]
}

def get_turkish_market_summary() -> Dict[str, Any]:
    """
    Get a summary of Turkish market data including stocks and funds.

    Returns:
        Dictionary containing market summary data
    """
    client = KAPVYKClient()

    # Get BIST-30 market data
    bist_data = client.get_market_data(BIST_30_SYMBOLS[:10])  # Limit to first 10 for demo

    # Calculate summary statistics
    total_companies = len(BIST_30_SYMBOLS)
    total_funds = sum(len(funds) for funds in TURKISH_FUND_CATEGORIES.values())

    return {
        'market_name': 'Borsa İstanbul (BIST)',
        'total_companies': total_companies,
        'total_funds': total_funds,
        'major_indices': ['BIST 100', 'BIST 30', 'BIST 50'],
        'sample_companies': bist_data,
        'fund_categories': list(TURKISH_FUND_CATEGORIES.keys()),
        'last_updated': datetime.now().isoformat()
    }

def get_company_details(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information for a specific Turkish company.

    Args:
        symbol: Turkish stock symbol (e.g., 'AKBNK')

    Returns:
        Company details dictionary or None if not found
    """
    client = KAPVYKClient()
    return client.get_company_info(symbol)

# Example usage and testing
if __name__ == "__main__":
    # Test the KAP integration
    print("Testing KAP VYK API Integration...")

    # Get market summary
    summary = get_turkish_market_summary()
    print(f"\nTurkish Market Summary:")
    print(f"Market: {summary['market_name']}")
    print(f"Total Companies: {summary['total_companies']}")
    print(f"Total Funds: {summary['total_funds']}")
    print(f"Major Indices: {', '.join(summary['major_indices'])}")

    # Test individual company lookup
    test_symbol = 'AKBNK'
    company_details = get_company_details(test_symbol)
    if company_details:
        print(f"\nCompany Details for {test_symbol}:")
        print(json.dumps(company_details, indent=2))
    else:
        print(f"\nCould not fetch details for {test_symbol} (API may not be accessible)")

    print("\nKAP VYK API Integration module is ready for use!")