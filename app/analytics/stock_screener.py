#!/usr/bin/env python3
"""
Hisse Senedi Tarayıcı (Stock Screener)
Kriterlere göre hisse filtreleme ve tarama
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class StockScreener:
    """Hisse senedi tarayıcı ve filtreleme aracı"""

    def __init__(self):
        """Tarayıcıyı başlat"""
        self.results = []

    def screen_stocks(self, symbols: List[str], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Hisseleri kriterlere göre tara

        Args:
            symbols: Taranacak hisse listesi
            criteria: Filtreleme kriterleri
                - market_cap_min: Minimum piyasa değeri
                - market_cap_max: Maximum piyasa değeri
                - pe_ratio_min: Minimum P/E oranı
                - pe_ratio_max: Maximum P/E oranı
                - dividend_yield_min: Minimum temettü verimi
                - price_change_min: Minimum fiyat değişimi (%)
                - price_change_max: Maximum fiyat değişimi (%)
                - volume_min: Minimum hacim
                - rsi_min: Minimum RSI
                - rsi_max: Maximum RSI
                - sector: Sektör filtresi
        """
        results = []

        for symbol in symbols:
            try:
                stock_data = self._get_stock_data(symbol)
                if self._meets_criteria(stock_data, criteria):
                    results.append(stock_data)
            except Exception as e:
                continue

        self.results = results
        return self._sort_results(results, criteria.get('sort_by', 'market_cap'))

    def _get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Hisse verilerini çek"""
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="3mo")

        if hist.empty:
            raise ValueError("No data")

        # RSI hesapla
        rsi = self._calculate_rsi(hist['Close'])

        # Price change
        price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100

        return {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'current_price': info.get('currentPrice', hist['Close'].iloc[-1]),
            'pe_ratio': info.get('trailingPE', 0),
            'forward_pe': info.get('forwardPE', 0),
            'pb_ratio': info.get('priceToBook', 0),
            'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            'volume': int(hist['Volume'].iloc[-1]),
            'avg_volume': info.get('averageVolume', 0),
            'price_change_3m': float(price_change),
            'rsi': float(rsi),
            'beta': info.get('beta', 0),
            'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
            'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
            'debt_to_equity': info.get('debtToEquity', 0),
            'week_52_high': info.get('fiftyTwoWeekHigh', 0),
            'week_52_low': info.get('fiftyTwoWeekLow', 0)
        }

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI hesapla"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        if loss.iloc[-1] == 0:
            return 100.0

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

    def _meets_criteria(self, stock_data: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Hisse kriterlere uygun mu kontrol et"""

        # Market cap
        if 'market_cap_min' in criteria:
            if stock_data['market_cap'] < criteria['market_cap_min']:
                return False

        if 'market_cap_max' in criteria:
            if stock_data['market_cap'] > criteria['market_cap_max']:
                return False

        # P/E Ratio
        if 'pe_ratio_min' in criteria:
            if stock_data['pe_ratio'] < criteria['pe_ratio_min']:
                return False

        if 'pe_ratio_max' in criteria:
            if stock_data['pe_ratio'] > criteria['pe_ratio_max']:
                return False

        # Dividend Yield
        if 'dividend_yield_min' in criteria:
            if stock_data['dividend_yield'] < criteria['dividend_yield_min']:
                return False

        # Price Change
        if 'price_change_min' in criteria:
            if stock_data['price_change_3m'] < criteria['price_change_min']:
                return False

        if 'price_change_max' in criteria:
            if stock_data['price_change_3m'] > criteria['price_change_max']:
                return False

        # Volume
        if 'volume_min' in criteria:
            if stock_data['volume'] < criteria['volume_min']:
                return False

        # RSI
        if 'rsi_min' in criteria:
            if stock_data['rsi'] < criteria['rsi_min']:
                return False

        if 'rsi_max' in criteria:
            if stock_data['rsi'] > criteria['rsi_max']:
                return False

        # Sector
        if 'sector' in criteria and criteria['sector'] != 'All':
            if stock_data['sector'] != criteria['sector']:
                return False

        # ROE
        if 'roe_min' in criteria:
            if stock_data['roe'] < criteria['roe_min']:
                return False

        # P/B Ratio
        if 'pb_ratio_max' in criteria:
            if stock_data['pb_ratio'] > criteria['pb_ratio_max']:
                return False

        # Debt to Equity
        if 'debt_to_equity_max' in criteria:
            if stock_data['debt_to_equity'] > criteria['debt_to_equity_max']:
                return False

        return True

    def _sort_results(self, results: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sonuçları sırala"""
        if not results:
            return []

        reverse = True  # Çoğu metrik için büyükten küçüğe

        if sort_by == 'market_cap':
            key = 'market_cap'
        elif sort_by == 'price_change':
            key = 'price_change_3m'
        elif sort_by == 'dividend_yield':
            key = 'dividend_yield'
        elif sort_by == 'pe_ratio':
            key = 'pe_ratio'
            reverse = False  # P/E için küçükten büyüğe
        elif sort_by == 'rsi':
            key = 'rsi'
            reverse = False
        elif sort_by == 'volume':
            key = 'volume'
        else:
            key = 'market_cap'

        return sorted(results, key=lambda x: x.get(key, 0), reverse=reverse)

    def get_predefined_screens(self) -> Dict[str, Dict[str, Any]]:
        """Önceden tanımlı tarama kriterleri"""
        return {
            "value_stocks": {
                "name": "Değer Hisseleri",
                "description": "Düşük P/E, yüksek temettü",
                "criteria": {
                    "pe_ratio_max": 15,
                    "dividend_yield_min": 3,
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "dividend_yield"
                }
            },
            "growth_stocks": {
                "name": "Büyüme Hisseleri",
                "description": "Yüksek büyüme potansiyeli",
                "criteria": {
                    "price_change_min": 20,
                    "roe_min": 15,
                    "market_cap_min": 500_000_000,
                    "sort_by": "price_change"
                }
            },
            "dividend_stocks": {
                "name": "Temettü Hisseleri",
                "description": "Yüksek temettü verimi",
                "criteria": {
                    "dividend_yield_min": 4,
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "dividend_yield"
                }
            },
            "oversold_stocks": {
                "name": "Aşırı Satım Bölgesi",
                "description": "RSI < 30 (potansiyel alım)",
                "criteria": {
                    "rsi_max": 30,
                    "market_cap_min": 500_000_000,
                    "sort_by": "rsi"
                }
            },
            "overbought_stocks": {
                "name": "Aşırı Alım Bölgesi",
                "description": "RSI > 70 (potansiyel satım)",
                "criteria": {
                    "rsi_min": 70,
                    "market_cap_min": 500_000_000,
                    "sort_by": "rsi"
                }
            },
            "momentum_stocks": {
                "name": "Momentum Hisseleri",
                "description": "Güçlü yükseliş trendi",
                "criteria": {
                    "price_change_min": 15,
                    "rsi_min": 50,
                    "rsi_max": 70,
                    "volume_min": 1_000_000,
                    "sort_by": "price_change"
                }
            },
            "quality_stocks": {
                "name": "Kaliteli Hisseler",
                "description": "Yüksek ROE, düşük borç",
                "criteria": {
                    "roe_min": 15,
                    "debt_to_equity_max": 50,
                    "market_cap_min": 1_000_000_000,
                    "sort_by": "market_cap"
                }
            },
            "large_cap": {
                "name": "Büyük Şirketler",
                "description": "10B+ piyasa değeri",
                "criteria": {
                    "market_cap_min": 10_000_000_000,
                    "sort_by": "market_cap"
                }
            }
        }

    def export_results(self, format: str = 'dataframe') -> Any:
        """Sonuçları export et"""
        if not self.results:
            return None

        if format == 'dataframe':
            return pd.DataFrame(self.results)
        elif format == 'dict':
            return self.results
        elif format == 'csv':
            df = pd.DataFrame(self.results)
            return df.to_csv(index=False)
        else:
            return self.results


# Örnek hisse listeleri
def get_bist_stocks() -> List[str]:
    """BIST hisse listesi"""
    return [
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'EREGL.IS', 'SAHOL.IS',
        'SISE.IS', 'PETKM.IS', 'KCHOL.IS', 'TUPRS.IS', 'ISCTR.IS',
        'VAKBN.IS', 'EKGYO.IS', 'ASELS.IS', 'TAVHL.IS', 'KRDMD.IS',
        'TCELL.IS', 'KOZAL.IS', 'BIMAS.IS', 'PGSUS.IS', 'ARCLK.IS',
        'TOASO.IS', 'HALKB.IS', 'ENKA.IS', 'KOZAA.IS', 'OYAKC.IS'
    ]


def get_sp500_sample() -> List[str]:
    """S&P 500 örnek hisseler"""
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B',
        'JPM', 'JNJ', 'V', 'WMT', 'PG', 'MA', 'HD', 'DIS', 'BAC', 'XOM',
        'ABBV', 'KO', 'PFE', 'CSCO', 'PEP', 'AVGO', 'COST', 'TMO', 'MRK',
        'NFLX', 'ABT', 'ACN', 'CVX', 'ADBE', 'NKE', 'LLY', 'ORCL', 'CRM',
        'DHR', 'MDT', 'NEE', 'VZ', 'UNP', 'TXN', 'UNH', 'RTX', 'PM', 'LOW',
        'QCOM', 'BMY', 'HON', 'INTU'
    ]


def get_nasdaq_sample() -> List[str]:
    """NASDAQ örnek hisseler"""
    return [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'TSLA', 'AVGO',
        'COST', 'NFLX', 'ADBE', 'CSCO', 'PEP', 'AMD', 'INTC', 'QCOM',
        'TXN', 'CMCSA', 'HON', 'INTU', 'AMAT', 'PYPL', 'BKNG', 'SBUX',
        'GILD', 'ADP', 'MDLZ', 'ISRG', 'VRTX', 'FISV', 'ADI', 'REGN'
    ]
