"""
🔑 Unified API Manager
Centralized API management with rate limiting, caching, and fallback strategies
Zero-cost operation with free tier APIs
"""

import os
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import hashlib
from collections import defaultdict
import threading
from .secret_utils import get_secret


class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self):
        self.locks = defaultdict(threading.Lock)
        self.call_times = defaultdict(list)

    def can_call(self, api_name: str, max_calls: int, time_window: int) -> bool:
        """
        Check if API call is allowed

        Args:
            api_name: Name of the API
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        with self.locks[api_name]:
            now = time.time()
            # Remove old calls outside the window
            self.call_times[api_name] = [
                t for t in self.call_times[api_name]
                if now - t < time_window
            ]

            # Check if we can make another call
            if len(self.call_times[api_name]) < max_calls:
                self.call_times[api_name].append(now)
                return True
            return False

    def wait_until_ready(self, api_name: str, max_calls: int, time_window: int, timeout: int = 60):
        """Wait until API call is allowed"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.can_call(api_name, max_calls, time_window):
                return True
            time.sleep(0.5)
        return False


class APICache:
    """Simple in-memory cache for API responses"""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def get(self, key: str, max_age: int = 300) -> Optional[Any]:
        """Get cached value if not expired"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]['data'], self.cache[key]['timestamp']
                if time.time() - timestamp < max_age:
                    return data
                else:
                    # Expired, remove from cache
                    del self.cache[key]
            return None

    def set(self, key: str, value: Any):
        """Set cache value"""
        with self.lock:
            self.cache[key] = {
                'data': value,
                'timestamp': time.time()
            }

    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()

    def get_cache_key(self, api_name: str, endpoint: str, params: Dict = None) -> str:
        """Generate unique cache key"""
        param_str = json.dumps(params, sort_keys=True) if params else ""
        raw_key = f"{api_name}:{endpoint}:{param_str}"
        return hashlib.md5(raw_key.encode()).hexdigest()


class UnifiedAPIManager:
    """
    Unified API Manager for all data sources
    Handles rate limiting, caching, and fallback strategies
    """

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.cache = APICache()
        self.api_keys = self._load_api_keys()

        self.tefas_session = requests.Session()
        self.tefas_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Referer': 'https://www.tefas.gov.tr/FonKarsilastirma.aspx',
            'Origin': 'https://www.tefas.gov.tr',
            'X-Requested-With': 'XMLHttpRequest'
        })

        # API rate limits (calls, time_window_seconds)
        self.rate_limits = {
            'alpha_vantage': (25, 86400),  # 25 calls per day
            'finnhub': (60, 60),  # 60 calls per minute
            'binance': (1200, 60),  # 1200 calls per minute
            'okx': (1200, 60),  # 1200 calls per minute (public)
            'coingecko': (50, 60),  # 50 calls per minute
            'newsapi': (100, 86400),  # 100 calls per day
            'polygon': (5, 60),  # 5 calls per minute
            'tradingeconomics': (500, 2592000),  # 500 calls per month
            'fmp': (250, 86400),  # 250 calls per day (free tier)
            # Unlimited APIs
            'yahoo': (None, None),
            'fred': (None, None),
            'tefas': (None, None),
            'worldbank': (None, None),
        }

        # Cache durations (seconds)
        self.cache_durations = {
            'stock_price': 60,  # 1 minute
            'crypto_price': 30,  # 30 seconds
            'macro_data': 86400,  # 24 hours
            'funds': 3600,  # 1 hour
            'news': 900,  # 15 minutes
            'economic_calendar': 43200,  # 12 hours
            'company_info': 86400,  # 24 hours
            'historical': 3600,  # 1 hour
        }

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment or config"""
        keys = {
            'alpha_vantage': get_secret('ALPHA_VANTAGE_KEY', 'ALPHA_VANTAGE_API_KEY', 'alpha_vantage', default=''),
            'fred': get_secret('FRED_API_KEY', 'fred', default=''),
            'finnhub': get_secret('FINNHUB_API_KEY', 'finnhub', default=''),
            'binance_key': get_secret('BINANCE_API_KEY', 'binance_key', default=''),
            'binance_secret': get_secret('BINANCE_SECRET_KEY', 'binance_secret', default=''),
            'tradingeconomics': get_secret('TRADINGECONOMICS_KEY', 'tradingeconomics', default=''),
            'newsapi': get_secret('NEWSAPI_KEY', 'newsapi', default=''),
            'polygon': get_secret('POLYGON_API_KEY', 'polygon', default=''),
            'fmp': get_secret('FMP_API_KEY', 'fmp', default=''),
        }

        # Try loading from config file if env vars not set
        try:
            config_path = 'config/api_keys.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    file_keys = json.load(f)
                    # Update keys that are not empty from file
                    for k, v in file_keys.items():
                        if v:  # Only update if value is not empty
                            keys[k] = v
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")

        return keys

    def _make_request(self, api_name: str, url: str, params: Dict = None,
                     headers: Dict = None, data_type: str = 'stock_price') -> Optional[Any]:
        """
        Make API request with rate limiting and caching

        Args:
            api_name: Name of the API
            url: API endpoint URL
            params: Query parameters
            headers: Request headers
            data_type: Type of data for cache duration
        """
        # Generate cache key
        cache_key = self.cache.get_cache_key(api_name, url, params)

        # Check cache first
        cached_data = self.cache.get(cache_key, self.cache_durations.get(data_type, 300))
        if cached_data is not None:
            return cached_data

        # Check rate limit
        max_calls, time_window = self.rate_limits.get(api_name, (None, None))
        if max_calls is not None:
            if not self.rate_limiter.wait_until_ready(api_name, max_calls, time_window, timeout=5):
                print(f"⚠️ Rate limit reached for {api_name}")
                return None

        # Make request
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Cache the result
            self.cache.set(cache_key, data)

            return data

        except Exception as e:
            print(f"❌ Error calling {api_name}: {e}")
            return None

    # ========== ALPHA VANTAGE ==========

    def get_alpha_vantage_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time quote from Alpha Vantage"""
        if not self.api_keys.get('alpha_vantage'):
            return None

        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_keys['alpha_vantage']
        }

        return self._make_request('alpha_vantage', url, params, data_type='stock_price')

    def get_alpha_vantage_technical(self, symbol: str, indicator: str = 'RSI') -> Optional[Dict]:
        """Get technical indicator from Alpha Vantage"""
        if not self.api_keys.get('alpha_vantage'):
            return None

        url = "https://www.alphavantage.co/query"
        params = {
            'function': indicator,
            'symbol': symbol,
            'interval': 'daily',
            'time_period': 14,
            'series_type': 'close',
            'apikey': self.api_keys['alpha_vantage']
        }

        return self._make_request('alpha_vantage', url, params, data_type='stock_price')

    # ========== FRED ==========

    def get_fred_series(self, series_id: str) -> Optional[Dict]:
        """Get economic data from FRED"""
        if not self.api_keys.get('fred'):
            return None

        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': series_id,
            'api_key': self.api_keys['fred'],
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 100
        }

        return self._make_request('fred', url, params, data_type='macro_data')

    # ========== FINNHUB ==========

    def get_finnhub_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Finnhub"""
        if not self.api_keys.get('finnhub'):
            return None

        url = f"https://finnhub.io/api/v1/quote"
        params = {
            'symbol': symbol,
            'token': self.api_keys['finnhub']
        }

        return self._make_request('finnhub', url, params, data_type='stock_price')

    def get_finnhub_news(self, symbol: str) -> Optional[List[Dict]]:
        """Get company news from Finnhub"""
        if not self.api_keys.get('finnhub'):
            return None

        url = "https://finnhub.io/api/v1/company-news"
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        params = {
            'symbol': symbol,
            'from': week_ago,
            'to': today,
            'token': self.api_keys['finnhub']
        }

        return self._make_request('finnhub', url, params, data_type='news')

    def get_finnhub_sentiment(self, symbol: str) -> Optional[Dict]:
        """Get social sentiment from Finnhub"""
        if not self.api_keys.get('finnhub'):
            return None

        url = "https://finnhub.io/api/v1/stock/social-sentiment"
        params = {
            'symbol': symbol,
            'token': self.api_keys['finnhub']
        }

        return self._make_request('finnhub', url, params, data_type='news')

    # ========== BINANCE ==========

    def get_binance_ticker(self, symbol: str = 'BTCUSDT') -> Optional[Dict]:
        """Get crypto ticker from Binance"""
        url = "https://api.binance.com/api/v3/ticker/24hr"
        params = {'symbol': symbol}

        return self._make_request('binance', url, params, data_type='crypto_price')

    def get_binance_klines(self, symbol: str = 'BTCUSDT', interval: str = '1h', limit: int = 100) -> Optional[List]:
        """Get historical klines from Binance"""
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }

        return self._make_request('binance', url, params, data_type='historical')

    # ========== OKX (PUBLIC) ==========

    def get_okx_ticker(self, inst_id: str = 'BTC-USDT') -> Optional[Dict]:
        """Get crypto ticker from OKX (public)"""
        url = "https://www.okx.com/api/v5/market/ticker"
        params = {'instId': inst_id}

        data = self._make_request('okx', url, params, data_type='crypto_price')
        if not data or data.get('code') != '0':
            return None

        entries = data.get('data', [])
        if not entries:
            return None

        return entries[0]

    def get_okx_candles(self, inst_id: str = 'BTC-USDT', bar: str = '1H', limit: int = 100) -> Optional[List]:
        """Get historical candles from OKX (public)"""
        url = "https://www.okx.com/api/v5/market/candles"
        params = {
            'instId': inst_id,
            'bar': bar,
            'limit': limit
        }

        data = self._make_request('okx', url, params, data_type='historical')
        if not data or data.get('code') != '0':
            return None

        return data.get('data')

    # ========== TEFAS ==========

    def get_tefas_fund_history(self, fund_code: str, start_date: str = "2010-01-01",
                               end_date: str = None) -> Optional[Dict]:
        """
        Get Turkish fund history from TEFAS

        Args:
            fund_code: TEFAS fund code (e.g., 'TCD', 'AKG')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            Dict with 'data' list containing date and price info
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Check cache first
        cache_key = self.cache.get_cache_key('tefas', fund_code, {'start': start_date, 'end': end_date})
        cached = self.cache.get(cache_key, self.cache_durations['funds'])
        if cached is not None:
            return cached

        try:
            url = "https://www.tefas.gov.tr/api/DB/BindComparisonFundReturn"
            payload = {
                "startDate": start_date,
                "endDate": end_date,
                "fundCodes": [fund_code]
            }

            response = self.tefas_session.post(url, json=payload, timeout=15)
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError:
                body = response.text.strip()
                preview = body[:200] if body else "<empty response>"
                print(f"Error getting TEFAS data for {fund_code}: Invalid JSON response: {preview}")
                return None

            # Parse response
            if 'data' in data and 'comparisonReturnList' in data['data']:
                fund_data = data['data']['comparisonReturnList']

                # Format data
                formatted_data = {
                    'fund_code': fund_code,
                    'data': []
                }

                for item in fund_data:
                    formatted_data['data'].append({
                        'date': item.get('tarih'),
                        'price': float(item.get('birimPayDegeri', 0)),
                        'daily_return': float(item.get('gunlukGetiri', 0))
                    })

                # Cache result
                self.cache.set(cache_key, formatted_data)
                return formatted_data

            return None

        except Exception as e:
            print(f"Error getting TEFAS data for {fund_code}: {e}")
            return None

    def get_tefas_fund_info(self, fund_code: str) -> Optional[Dict]:
        """Get current TEFAS fund info (latest price and details)"""
        # Get last 7 days of data
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        history = self.get_tefas_fund_history(fund_code, start_date, end_date)

        if history and history.get('data'):
            latest = history['data'][-1]  # Most recent data
            return {
                'fund_code': fund_code,
                'current_price': latest['price'],
                'date': latest['date'],
                'daily_return': latest.get('daily_return', 0),
                'source': 'tefas'
            }

        return None

    # ========== NEWS API ==========

    def get_news_headlines(self, query: str = 'finance', language: str = 'en') -> Optional[Dict]:
        """Get news headlines from NewsAPI"""
        if not self.api_keys.get('newsapi'):
            return None

        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'language': language,
            'sortBy': 'publishedAt',
            'pageSize': 20,
            'apiKey': self.api_keys['newsapi']
        }

        return self._make_request('newsapi', url, params, data_type='news')

    # ========== POLYGON ==========

    def get_polygon_quote(self, symbol: str) -> Optional[Dict]:
        """Get quote from Polygon"""
        if not self.api_keys.get('polygon'):
            return None

        url = f"https://api.polygon.io/v2/last/trade/{symbol}"
        params = {'apiKey': self.api_keys['polygon']}

        return self._make_request('polygon', url, params, data_type='stock_price')

    # ========== FMP (Financial Modeling Prep) ==========

    def get_fmp_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get stock/ETF quote from FMP
        Free tier: 15min delayed, 250 calls/day
        """
        if not self.api_keys.get('fmp'):
            return None

        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
        params = {'apikey': self.api_keys['fmp']}

        return self._make_request('fmp', url, params, data_type='stock_price')

    def get_fmp_profile(self, symbol: str) -> Optional[Dict]:
        """Get company profile from FMP"""
        if not self.api_keys.get('fmp'):
            return None

        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
        params = {'apikey': self.api_keys['fmp']}

        return self._make_request('fmp', url, params, data_type='company_info')

    def get_fmp_historical(self, symbol: str, from_date: str = None,
                          to_date: str = None) -> Optional[Dict]:
        """Get historical prices from FMP"""
        if not self.api_keys.get('fmp'):
            return None

        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
        params = {'apikey': self.api_keys['fmp']}

        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date

        return self._make_request('fmp', url, params, data_type='historical')

    def get_fmp_etf_holdings(self, symbol: str) -> Optional[List]:
        """Get ETF holdings from FMP"""
        if not self.api_keys.get('fmp'):
            return None

        url = f"https://financialmodelingprep.com/api/v3/etf-holder/{symbol}"
        params = {'apikey': self.api_keys['fmp']}

        return self._make_request('fmp', url, params, data_type='etf_composition')

    def get_fmp_crypto_quote(self, symbol: str = 'BTCUSD') -> Optional[List]:
        """Get crypto quote from FMP"""
        if not self.api_keys.get('fmp'):
            return None

        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
        params = {'apikey': self.api_keys['fmp']}

        return self._make_request('fmp', url, params, data_type='crypto_price')

    def get_fmp_market_hours(self) -> Optional[Dict]:
        """Get market hours and status from FMP"""
        if not self.api_keys.get('fmp'):
            return None

        url = "https://financialmodelingprep.com/api/v3/market-hours"
        params = {'apikey': self.api_keys['fmp']}

        return self._make_request('fmp', url, params, data_type='macro_data')

    def get_fmp_earnings_calendar(self, from_date: str = None, to_date: str = None) -> Optional[List]:
        """Get earnings calendar from FMP"""
        if not self.api_keys.get('fmp'):
            return None

        url = "https://financialmodelingprep.com/api/v3/earning_calendar"
        params = {'apikey': self.api_keys['fmp']}

        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date

        return self._make_request('fmp', url, params, data_type='economic_calendar')

    # ========== WORLD BANK ==========

    def get_worldbank_indicator(self, indicator: str = 'NY.GDP.MKTP.CD',
                                country: str = 'all') -> Optional[List]:
        """Get indicator from World Bank"""
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        params = {
            'format': 'json',
            'per_page': 100,
            'date': '2010:2024'
        }

        return self._make_request('worldbank', url, params, data_type='macro_data')

    # ========== TRADING ECONOMICS ==========

    def get_trading_economics_calendar(self, country: str = 'united states') -> Optional[List]:
        """Get economic calendar from TradingEconomics"""
        if not self.api_keys.get('tradingeconomics'):
            return None

        url = f"https://api.tradingeconomics.com/calendar/country/{country}"
        headers = {
            'Authorization': f"Client {self.api_keys['tradingeconomics']}"
        }

        return self._make_request('tradingeconomics', url, headers=headers,
                                 data_type='economic_calendar')

    def _get_stooq_quote(self, symbol: str) -> Optional[Dict[str, float]]:
        """Fetch last price from Stooq (public)"""
        try:
            from pandas_datareader import data as pdr
        except Exception:
            return None

        symbol_upper = symbol.upper()
        if symbol_upper.startswith('^'):
            candidates = [symbol_upper]
        else:
            base = symbol_upper.replace('-', '.')
            candidates = []
            if '.' not in base:
                candidates.append(f"{base}.US")
            candidates.append(base)

        start = datetime.utcnow() - timedelta(days=10)
        end = datetime.utcnow()

        for candidate in candidates:
            try:
                df = pdr.DataReader(candidate, 'stooq', start, end)
            except Exception:
                continue

            if df is None or df.empty:
                continue

            df = df.sort_index()
            last_close = float(df['Close'].iloc[-1])
            if len(df) > 1:
                prev_close = float(df['Close'].iloc[-2])
                change_pct = ((last_close / prev_close) - 1) * 100 if prev_close else 0.0
            else:
                change_pct = 0.0

            return {'price': last_close, 'change': change_pct}

        return None

    # ========== UTILITY METHODS ==========

    def get_stock_price_with_fallback(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock price with fallback strategy
        Priority: Yahoo Finance → Alpha Vantage → Finnhub → Polygon
        """
        result = {
            'symbol': symbol,
            'price': None,
            'change': None,
            'source': None,
            'timestamp': datetime.now().isoformat()
        }

        # Try Yahoo Finance first (unlimited, free)
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period='1d')

            if not hist.empty:
                result['price'] = hist['Close'].iloc[-1]
                result['change'] = info.get('regularMarketChangePercent', 0)
                result['source'] = 'yahoo'
                return result
        except:
            pass

        # Try Stooq public data (no key required)
        stooq_data = self._get_stooq_quote(symbol)
        if stooq_data:
            result['price'] = stooq_data['price']
            result['change'] = stooq_data['change']
            result['source'] = 'stooq'
            return result

        # Try Alpha Vantage
        av_data = self.get_alpha_vantage_quote(symbol)
        if av_data and 'Global Quote' in av_data:
            quote = av_data['Global Quote']
            result['price'] = float(quote.get('05. price', 0))
            result['change'] = float(quote.get('10. change percent', '0').replace('%', ''))
            result['source'] = 'alpha_vantage'
            return result

        # Try Finnhub
        fh_data = self.get_finnhub_quote(symbol)
        if fh_data and fh_data.get('c'):
            result['price'] = fh_data['c']
            result['change'] = fh_data.get('dp', 0)
            result['source'] = 'finnhub'
            return result

        # Try Polygon
        poly_data = self.get_polygon_quote(symbol)
        if poly_data and poly_data.get('results'):
            res = poly_data['results']
            result['price'] = res.get('p')
            result['source'] = 'polygon'
            return result

        return result

    def get_crypto_price_with_fallback(self, symbol: str = 'bitcoin') -> Dict[str, Any]:
        """
        Get crypto price with fallback
        Priority: CoinGecko (already integrated) → Binance
        """
        result = {
            'symbol': symbol,
            'price': None,
            'change_24h': None,
            'source': None,
            'timestamp': datetime.now().isoformat()
        }

        # Try Binance
        binance_symbol = symbol.upper() + 'USDT' if not symbol.endswith('USDT') else symbol
        binance_data = self.get_binance_ticker(binance_symbol)

        if binance_data:
            result['price'] = float(binance_data.get('lastPrice', 0))
            result['change_24h'] = float(binance_data.get('priceChangePercent', 0))
            result['source'] = 'binance'
            return result

        # Try OKX public ticker
        symbol_upper = symbol.upper()
        base_symbol = symbol_upper[:-4] if symbol_upper.endswith('USDT') else symbol_upper
        if base_symbol.isalpha():
            okx_inst = f"{base_symbol}-USDT"
            okx_data = self.get_okx_ticker(okx_inst)
            if okx_data:
                last_price = float(okx_data.get('last', 0))
                open_24h = float(okx_data.get('open24h', 0))
                change_pct = ((last_price - open_24h) / open_24h * 100) if open_24h else 0.0
                result['price'] = last_price
                result['change_24h'] = change_pct
                result['source'] = 'okx'
                return result

        return result

    def get_economic_indicator_with_fallback(self, indicator: str) -> Dict[str, Any]:
        """
        Get economic indicator with fallback
        Priority: FRED → World Bank → TradingEconomics
        """
        result = {
            'indicator': indicator,
            'value': None,
            'date': None,
            'source': None
        }

        # Map common indicators to FRED series IDs
        fred_series_map = {
            'gdp': 'GDP',
            'cpi': 'CPIAUCSL',
            'unemployment': 'UNRATE',
            'm2': 'M2SL',
            'fed_funds': 'DFF',
            'treasury_10y': 'DGS10'
        }

        series_id = fred_series_map.get(indicator.lower(), indicator)

        # Try FRED
        fred_data = self.get_fred_series(series_id)
        if fred_data and 'observations' in fred_data:
            obs = fred_data['observations']
            if obs:
                latest = obs[0]
                result['value'] = float(latest['value']) if latest['value'] != '.' else None
                result['date'] = latest['date']
                result['source'] = 'fred'
                return result

        # Try World Bank
        wb_indicator_map = {
            'gdp': 'NY.GDP.MKTP.CD',
            'inflation': 'FP.CPI.TOTL.ZG',
            'unemployment': 'SL.UEM.TOTL.ZS'
        }

        wb_indicator = wb_indicator_map.get(indicator.lower())
        if wb_indicator:
            wb_data = self.get_worldbank_indicator(wb_indicator, 'USA')
            if wb_data and len(wb_data) > 1:
                for item in wb_data[1]:
                    if item.get('value'):
                        result['value'] = item['value']
                        result['date'] = item['date']
                        result['source'] = 'worldbank'
                        return result

        return result

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()

    def get_api_status(self) -> Dict[str, Any]:
        """Get status of all APIs"""
        status = {}

        for api_name, (max_calls, time_window) in self.rate_limits.items():
            api_key_name = api_name
            if api_name == 'binance':
                api_key_name = 'binance_key'

            has_key = bool(self.api_keys.get(api_key_name))

            if max_calls is None:
                limit_str = "Unlimited"
            else:
                limit_str = f"{max_calls} calls per {time_window}s"

            status[api_name] = {
                'configured': has_key,
                'rate_limit': limit_str,
                'calls_made': len(self.rate_limiter.call_times.get(api_name, []))
            }

        return status


# Global instance
api_manager = UnifiedAPIManager()
