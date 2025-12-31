"""
🚀 MarketDataEngine - Unified Market Data Interface
Single class to access all market data sources
"""

from typing import Dict, Any, Optional, List
from .unified_api_manager import api_manager
import pandas as pd


class MarketDataEngine:
    """
    Unified interface for all market data
    Simplifies access to stocks, ETFs, crypto, funds, and macro data
    """

    def __init__(self):
        self.api = api_manager

    # ========== STOCKS & ETFs ==========

    def get_stock(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock price with automatic fallback
        Priority: Yahoo → FMP → Alpha Vantage → Finnhub → Polygon
        """
        return self.api.get_stock_price_with_fallback(symbol)

    def get_etf(self, symbol: str) -> Dict[str, Any]:
        """Get ETF price (same as stock)"""
        return self.get_stock(symbol)

    def get_stock_profile(self, symbol: str) -> Optional[Dict]:
        """Get detailed company profile"""
        # Try FMP first (comprehensive)
        profile = self.api.get_fmp_profile(symbol)
        if profile and isinstance(profile, list) and len(profile) > 0:
            return profile[0]
        return None

    def get_etf_holdings(self, symbol: str) -> Optional[List]:
        """Get ETF composition/holdings"""
        return self.api.get_fmp_etf_holdings(symbol)

    def get_stock_historical(self, symbol: str, from_date: str = None,
                            to_date: str = None) -> Optional[Dict]:
        """Get historical price data"""
        return self.api.get_fmp_historical(symbol, from_date, to_date)

    # ========== CRYPTOCURRENCY ==========

    def get_crypto(self, symbol: str = 'bitcoin') -> Dict[str, Any]:
        """
        Get crypto price with fallback
        Priority: CoinGecko (already integrated) → Binance → FMP
        """
        # Try Binance for common pairs
        if symbol.upper() in ['BTC', 'ETH', 'BNB', 'XRP', 'ADA']:
            binance_symbol = symbol.upper() + 'USDT'
            result = self.api.get_binance_ticker(binance_symbol)
            if result:
                return {
                    'symbol': symbol,
                    'price': float(result.get('lastPrice', 0)),
                    'change_24h': float(result.get('priceChangePercent', 0)),
                    'volume': float(result.get('volume', 0)),
                    'source': 'binance'
                }

        # Try OKX public ticker
        okx_inst = symbol.upper() + '-USDT'
        okx_data = self.api.get_okx_ticker(okx_inst)
        if okx_data:
            last_price = float(okx_data.get('last', 0))
            open_24h = float(okx_data.get('open24h', 0))
            change_pct = ((last_price - open_24h) / open_24h * 100) if open_24h else 0.0
            return {
                'symbol': symbol,
                'price': last_price,
                'change_24h': change_pct,
                'volume': float(okx_data.get('vol24h', 0)),
                'source': 'okx'
            }

        # Fallback to FMP
        fmp_symbol = symbol.upper() + 'USD'
        fmp_data = self.api.get_fmp_crypto_quote(fmp_symbol)
        if fmp_data and isinstance(fmp_data, list) and len(fmp_data) > 0:
            item = fmp_data[0]
            return {
                'symbol': symbol,
                'price': item.get('price', 0),
                'change_24h': item.get('changesPercentage', 0),
                'source': 'fmp'
            }

        # Ultimate fallback
        return self.api.get_crypto_price_with_fallback(symbol)

    def get_crypto_historical(self, symbol: str = 'BTCUSDT',
                             interval: str = '1h', limit: int = 100) -> Optional[List]:
        """Get crypto historical klines from Binance with OKX fallback"""
        data = self.api.get_binance_klines(symbol, interval, limit)
        if data:
            return data

        interval_map = {
            '1m': '1m',
            '3m': '3m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1H',
            '2h': '2H',
            '4h': '4H',
            '6h': '6H',
            '12h': '12H',
            '1d': '1D',
            '1w': '1W',
            '1M': '1M'
        }
        okx_bar = interval_map.get(interval, '1H')

        symbol_upper = symbol.upper()
        if '-' in symbol_upper:
            okx_inst = symbol_upper
        elif symbol_upper.endswith('USDT'):
            okx_inst = f"{symbol_upper[:-4]}-USDT"
        else:
            okx_inst = f"{symbol_upper}-USDT"

        return self.api.get_okx_candles(okx_inst, bar=okx_bar, limit=limit)

    # ========== TURKISH FUNDS (TEFAS) ==========

    def get_fund(self, fund_code: str) -> Optional[Dict]:
        """
        Get Turkish fund current price
        Example: get_fund('TCD'), get_fund('AKG')
        """
        return self.api.get_tefas_fund_info(fund_code)

    def get_fund_history(self, fund_code: str, start_date: str = "2020-01-01",
                        end_date: str = None) -> Optional[Dict]:
        """
        Get Turkish fund historical data
        Returns: {'fund_code': str, 'data': [{'date', 'price', 'daily_return'}]}
        """
        return self.api.get_tefas_fund_history(fund_code, start_date, end_date)

    def get_fund_dataframe(self, fund_code: str, start_date: str = "2020-01-01",
                          end_date: str = None) -> Optional[pd.DataFrame]:
        """Get fund history as pandas DataFrame"""
        history = self.get_fund_history(fund_code, start_date, end_date)

        if history and history.get('data'):
            df = pd.DataFrame(history['data'])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df

        return None

    # ========== MACRO & ECONOMIC DATA ==========

    def get_macro(self, indicator: str) -> Dict[str, Any]:
        """
        Get macro indicator with fallback
        Examples: 'gdp', 'cpi', 'unemployment', 'm2', 'fed_funds', 'treasury_10y'
        """
        return self.api.get_economic_indicator_with_fallback(indicator)

    def get_fred_series(self, series_id: str) -> Optional[Dict]:
        """
        Get FRED economic series
        Examples: 'GDP', 'CPIAUCSL', 'UNRATE', 'M2SL', 'DFF', 'DGS10'
        """
        return self.api.get_fred_series(series_id)

    def get_economic_calendar(self, country: str = 'united states') -> Optional[List]:
        """Get economic calendar from TradingEconomics"""
        return self.api.get_trading_economics_calendar(country)

    def get_earnings_calendar(self, from_date: str = None, to_date: str = None) -> Optional[List]:
        """Get earnings calendar from FMP"""
        return self.api.get_fmp_earnings_calendar(from_date, to_date)

    def get_market_hours(self) -> Optional[Dict]:
        """Get market hours and status"""
        return self.api.get_fmp_market_hours()

    # ========== NEWS & SENTIMENT ==========

    def get_news(self, symbol: str = None, query: str = None) -> Optional[List]:
        """
        Get news with fallback
        If symbol provided: Get company-specific news from Finnhub
        If query provided: Get general news from NewsAPI
        """
        if symbol:
            # Company-specific news from Finnhub
            return self.api.get_finnhub_news(symbol)

        if query:
            # General news from NewsAPI
            news_data = self.api.get_news_headlines(query)
            if news_data and 'articles' in news_data:
                return news_data['articles']

        return None

    def get_sentiment(self, symbol: str) -> Optional[Dict]:
        """Get social sentiment for a stock"""
        return self.api.get_finnhub_sentiment(symbol)

    # ========== UTILITIES ==========

    def get_api_status(self) -> Dict[str, Any]:
        """Get status of all configured APIs"""
        return self.api.get_api_status()

    def clear_cache(self):
        """Clear all cached data"""
        self.api.clear_cache()

    # ========== BATCH OPERATIONS ==========

    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get multiple stock prices efficiently"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock(symbol)
        return results

    def get_multiple_cryptos(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get multiple crypto prices"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_crypto(symbol)
        return results

    def get_multiple_funds(self, fund_codes: List[str]) -> Dict[str, Dict]:
        """Get multiple TEFAS funds"""
        results = {}
        for code in fund_codes:
            results[code] = self.get_fund(code)
        return results

    # ========== HELPER METHODS ==========

    def search_stock(self, query: str) -> List[Dict]:
        """
        Search for stocks (placeholder - would need search API)
        For now returns empty list
        """
        # Future: Implement search using FMP search endpoint
        return []

    def get_top_movers(self, market: str = 'US') -> Dict[str, List]:
        """
        Get top gainers/losers (placeholder)
        Future: Implement using FMP or Finnhub
        """
        return {
            'gainers': [],
            'losers': [],
            'most_active': []
        }


# Global instance
market = MarketDataEngine()


# ========== CONVENIENCE FUNCTIONS ==========

def get_stock(symbol: str) -> Dict:
    """Quick function to get stock price"""
    return market.get_stock(symbol)


def get_crypto(symbol: str) -> Dict:
    """Quick function to get crypto price"""
    return market.get_crypto(symbol)


def get_fund(fund_code: str) -> Optional[Dict]:
    """Quick function to get TEFAS fund"""
    return market.get_fund(fund_code)


def get_macro(indicator: str) -> Dict:
    """Quick function to get macro data"""
    return market.get_macro(indicator)


# ========== EXAMPLE USAGE ==========

if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("MarketDataEngine - Example Usage")
    print("=" * 60)

    # Stock
    print("\n1. Get Stock Price (AAPL):")
    stock = market.get_stock('AAPL')
    print(f"   Price: ${stock.get('price'):.2f}")
    print(f"   Change: {stock.get('change'):.2f}%")
    print(f"   Source: {stock.get('source')}")

    # Crypto
    print("\n2. Get Crypto Price (BTC):")
    crypto = market.get_crypto('BTC')
    print(f"   Price: ${crypto.get('price'):.2f}")
    print(f"   24h Change: {crypto.get('change_24h'):.2f}%")
    print(f"   Source: {crypto.get('source')}")

    # TEFAS Fund
    print("\n3. Get TEFAS Fund (TCD):")
    fund = market.get_fund('TCD')
    if fund:
        print(f"   Price: {fund.get('current_price'):.4f}")
        print(f"   Date: {fund.get('date')}")
        print(f"   Daily Return: {fund.get('daily_return'):.2f}%")

    # Macro data
    print("\n4. Get Macro Indicator (GDP):")
    gdp = market.get_macro('gdp')
    if gdp.get('value'):
        print(f"   Value: {gdp.get('value')}")
        print(f"   Date: {gdp.get('date')}")
        print(f"   Source: {gdp.get('source')}")

    # API Status
    print("\n5. API Status:")
    status = market.get_api_status()
    configured_count = sum(1 for v in status.values() if v['configured'])
    print(f"   Configured APIs: {configured_count}/{len(status)}")

    print("\n" + "=" * 60)
    print("✅ MarketDataEngine Ready!")
    print("=" * 60)
