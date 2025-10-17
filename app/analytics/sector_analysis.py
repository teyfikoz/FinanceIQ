#!/usr/bin/env python3
"""
Sektör Analizi ve Karşılaştırma Modülü
Sektör performansı, hisse karşılaştırmaları ve peer analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class SectorAnalyzer:
    """Sektör analizi ve karşılaştırma aracı"""

    # Sektör ETF'leri
    SECTOR_ETFS = {
        'Technology': 'XLK',
        'Healthcare': 'XLV',
        'Financials': 'XLF',
        'Consumer Discretionary': 'XLY',
        'Consumer Staples': 'XLP',
        'Energy': 'XLE',
        'Utilities': 'XLU',
        'Real Estate': 'XLRE',
        'Materials': 'XLB',
        'Industrials': 'XLI',
        'Communication Services': 'XLC'
    }

    def __init__(self, symbol: str):
        """
        Args:
            symbol: Analiz edilecek hisse sembolü
        """
        self.symbol = symbol.upper()
        self.stock = yf.Ticker(self.symbol)
        self.info = self.stock.info
        self.sector = self.info.get('sector', 'Unknown')

    def get_comprehensive_sector_analysis(self) -> Dict[str, Any]:
        """Kapsamlı sektör analizi"""
        try:
            return {
                "stock_info": self.get_stock_sector_info(),
                "sector_performance": self.analyze_sector_performance(),
                "peer_comparison": self.compare_with_peers(),
                "sector_metrics": self.calculate_sector_metrics(),
                "relative_strength": self.calculate_relative_strength(),
                "sector_trends": self.analyze_sector_trends(),
                "market_share": self.estimate_market_position(),
                "recommendation": self.generate_sector_recommendation()
            }
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def get_stock_sector_info(self) -> Dict[str, Any]:
        """Hisse sektör bilgileri"""
        return {
            "symbol": self.symbol,
            "company_name": self.info.get('longName', 'N/A'),
            "sector": self.sector,
            "industry": self.info.get('industry', 'N/A'),
            "market_cap": self.info.get('marketCap', 0),
            "current_price": self.info.get('currentPrice', 0)
        }

    def analyze_sector_performance(self, period: str = "1y") -> Dict[str, Any]:
        """Sektör performans analizi"""
        try:
            # Sektör ETF'i
            sector_etf = self.SECTOR_ETFS.get(self.sector)

            if not sector_etf:
                return {"error": "Sector ETF not found"}

            # ETF ve hisse verilerini çek
            etf = yf.Ticker(sector_etf)
            etf_hist = etf.history(period=period)
            stock_hist = self.stock.history(period=period)

            if etf_hist.empty or stock_hist.empty:
                return {"error": "Insufficient data"}

            # Performans hesapla
            etf_return = ((etf_hist['Close'].iloc[-1] - etf_hist['Close'].iloc[0]) /
                         etf_hist['Close'].iloc[0] * 100)
            stock_return = ((stock_hist['Close'].iloc[-1] - stock_hist['Close'].iloc[0]) /
                           stock_hist['Close'].iloc[0] * 100)

            # S&P 500 ile karşılaştır
            spy = yf.Ticker('SPY')
            spy_hist = spy.history(period=period)
            spy_return = ((spy_hist['Close'].iloc[-1] - spy_hist['Close'].iloc[0]) /
                         spy_hist['Close'].iloc[0] * 100) if not spy_hist.empty else 0

            return {
                "sector": self.sector,
                "sector_etf": sector_etf,
                "sector_return": float(etf_return),
                "stock_return": float(stock_return),
                "market_return": float(spy_return),
                "outperformance_vs_sector": float(stock_return - etf_return),
                "outperformance_vs_market": float(stock_return - spy_return),
                "sector_rank": self._calculate_sector_rank(etf_return, spy_return),
                "stock_rank": self._calculate_stock_rank(stock_return, etf_return)
            }

        except Exception as e:
            return {"error": str(e)}

    def _calculate_sector_rank(self, sector_return: float, market_return: float) -> str:
        """Sektör sıralaması"""
        outperformance = sector_return - market_return

        if outperformance > 10:
            return "top_performer"
        elif outperformance > 0:
            return "above_market"
        elif outperformance > -10:
            return "below_market"
        else:
            return "underperformer"

    def _calculate_stock_rank(self, stock_return: float, sector_return: float) -> str:
        """Hisse sektör içi sıralaması"""
        outperformance = stock_return - sector_return

        if outperformance > 10:
            return "sector_leader"
        elif outperformance > 0:
            return "above_sector"
        elif outperformance > -10:
            return "below_sector"
        else:
            return "sector_laggard"

    def compare_with_peers(self, peer_symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Rakip şirketlerle karşılaştır"""
        try:
            # Eğer peer listesi verilmemişse, sektörden örnekler al
            if not peer_symbols:
                peer_symbols = self._get_peer_symbols()

            if not peer_symbols:
                return {"error": "No peers found"}

            comparisons = []

            # Ana hisse
            main_data = self._get_comparison_data(self.symbol)
            if main_data:
                comparisons.append(main_data)

            # Rakipler
            for peer in peer_symbols[:10]:  # Max 10 peer
                if peer != self.symbol:
                    peer_data = self._get_comparison_data(peer)
                    if peer_data:
                        comparisons.append(peer_data)

            if not comparisons:
                return {"error": "No comparison data available"}

            # Ranking hesapla
            rankings = self._calculate_rankings(comparisons)

            return {
                "main_stock": self.symbol,
                "peers": [c['symbol'] for c in comparisons if c['symbol'] != self.symbol],
                "comparison_data": comparisons,
                "rankings": rankings,
                "percentile_rank": self._calculate_percentile_rank(comparisons, self.symbol)
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_peer_symbols(self) -> List[str]:
        """Sektör bazlı peer semboller (örnek liste)"""
        peers_by_sector = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'ADBE', 'CRM', 'ORCL'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'MRK', 'LLY'],
            'Financials': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO'],
            'Consumer Discretionary': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW'],
            'Consumer Staples': ['PG', 'KO', 'PEP', 'WMT', 'COST', 'MDLZ', 'CL', 'KHC'],
            'Industrials': ['BA', 'HON', 'UNP', 'CAT', 'RTX', 'LMT', 'GE', 'MMM'],
            'Materials': ['LIN', 'APD', 'SHW', 'ECL', 'DD', 'NEM', 'FCX', 'NUE'],
            'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL'],
            'Real Estate': ['AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'SPG', 'O', 'WELL'],
            'Communication Services': ['GOOGL', 'META', 'DIS', 'NFLX', 'T', 'VZ', 'CMCSA', 'TMUS']
        }

        return peers_by_sector.get(self.sector, [])

    def _get_comparison_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Karşılaştırma verilerini çek"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="1y")

            if hist.empty:
                return None

            price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) /
                          hist['Close'].iloc[0] * 100) if len(hist) > 0 else 0

            return {
                "symbol": symbol,
                "name": info.get('shortName', symbol),
                "market_cap": info.get('marketCap', 0),
                "pe_ratio": info.get('trailingPE', 0),
                "forward_pe": info.get('forwardPE', 0),
                "pb_ratio": info.get('priceToBook', 0),
                "dividend_yield": info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                "profit_margin": info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                "roe": info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                "revenue_growth": info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                "price_change_1y": float(price_change),
                "beta": info.get('beta', 1)
            }

        except:
            return None

    def _calculate_rankings(self, comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Metrik bazında sıralama"""
        if not comparisons:
            return {}

        df = pd.DataFrame(comparisons)

        rankings = {}
        main_symbol = self.symbol

        # Her metrik için ranking
        metrics = ['market_cap', 'pe_ratio', 'pb_ratio', 'dividend_yield',
                  'profit_margin', 'roe', 'revenue_growth', 'price_change_1y']

        for metric in metrics:
            if metric in df.columns:
                # P/E ve P/B için düşük daha iyi, diğerleri için yüksek
                ascending = metric in ['pe_ratio', 'pb_ratio']

                df_sorted = df.sort_values(metric, ascending=ascending)
                rank = df_sorted[df_sorted['symbol'] == main_symbol].index[0] + 1 if main_symbol in df_sorted['symbol'].values else 0

                rankings[metric] = {
                    "rank": int(rank),
                    "total": len(df),
                    "percentile": float(rank / len(df) * 100) if len(df) > 0 else 0
                }

        return rankings

    def _calculate_percentile_rank(self, comparisons: List[Dict[str, Any]], symbol: str) -> float:
        """Genel yüzdelik sıralama"""
        if not comparisons:
            return 50.0

        # Çoklu metrik skoru
        scores = []

        for comp in comparisons:
            score = 0
            # ROE (yüksek = iyi)
            score += comp.get('roe', 0)
            # Profit margin (yüksek = iyi)
            score += comp.get('profit_margin', 0) * 2
            # Price change (yüksek = iyi)
            score += comp.get('price_change_1y', 0) * 0.5
            # Dividend yield (yüksek = iyi)
            score += comp.get('dividend_yield', 0) * 5

            # P/E (düşük = iyi)
            pe = comp.get('pe_ratio', 20)
            if pe > 0:
                score += max(0, 50 - pe)

            scores.append({"symbol": comp['symbol'], "score": score})

        # Sırala
        scores.sort(key=lambda x: x['score'], reverse=True)

        # Percentile hesapla
        rank = next((i for i, s in enumerate(scores) if s['symbol'] == symbol), -1)

        if rank == -1:
            return 50.0

        percentile = (1 - rank / len(scores)) * 100 if len(scores) > 0 else 50.0
        return float(percentile)

    def calculate_sector_metrics(self) -> Dict[str, Any]:
        """Sektör metrikleri"""
        try:
            # Sektör ortalamaları (yaklaşık değerler)
            sector_averages = {
                'Technology': {'pe': 25, 'pb': 6, 'roe': 20, 'profit_margin': 20},
                'Healthcare': {'pe': 20, 'pb': 4, 'roe': 15, 'profit_margin': 15},
                'Financials': {'pe': 12, 'pb': 1.2, 'roe': 12, 'profit_margin': 25},
                'Energy': {'pe': 15, 'pb': 1.5, 'roe': 10, 'profit_margin': 8},
                'Consumer Discretionary': {'pe': 20, 'pb': 5, 'roe': 18, 'profit_margin': 10},
                'Consumer Staples': {'pe': 18, 'pb': 4, 'roe': 16, 'profit_margin': 7},
                'Industrials': {'pe': 18, 'pb': 3, 'roe': 14, 'profit_margin': 8},
                'Materials': {'pe': 16, 'pb': 2, 'roe': 12, 'profit_margin': 10},
                'Utilities': {'pe': 16, 'pb': 1.5, 'roe': 9, 'profit_margin': 12},
                'Real Estate': {'pe': 30, 'pb': 2, 'roe': 8, 'profit_margin': 15},
                'Communication Services': {'pe': 20, 'pb': 3, 'roe': 12, 'profit_margin': 15}
            }

            sector_avg = sector_averages.get(self.sector, {'pe': 20, 'pb': 3, 'roe': 15, 'profit_margin': 12})

            # Hisse metrikleri
            stock_pe = self.info.get('trailingPE', 0)
            stock_pb = self.info.get('priceToBook', 0)
            stock_roe = self.info.get('returnOnEquity', 0) * 100 if self.info.get('returnOnEquity') else 0
            stock_margin = self.info.get('profitMargins', 0) * 100 if self.info.get('profitMargins') else 0

            return {
                "sector": self.sector,
                "stock_pe": float(stock_pe),
                "sector_avg_pe": sector_avg['pe'],
                "pe_vs_sector": float(stock_pe - sector_avg['pe']) if stock_pe else 0,
                "stock_pb": float(stock_pb),
                "sector_avg_pb": sector_avg['pb'],
                "pb_vs_sector": float(stock_pb - sector_avg['pb']) if stock_pb else 0,
                "stock_roe": float(stock_roe),
                "sector_avg_roe": sector_avg['roe'],
                "roe_vs_sector": float(stock_roe - sector_avg['roe']),
                "stock_margin": float(stock_margin),
                "sector_avg_margin": sector_avg['profit_margin'],
                "margin_vs_sector": float(stock_margin - sector_avg['profit_margin'])
            }

        except Exception as e:
            return {"error": str(e)}

    def calculate_relative_strength(self, period: str = "3mo") -> Dict[str, Any]:
        """Relative Strength Index (RSI) - Sektöre göre"""
        try:
            stock_hist = self.stock.history(period=period)

            sector_etf = self.SECTOR_ETFS.get(self.sector)
            if not sector_etf:
                return {"error": "Sector ETF not found"}

            etf = yf.Ticker(sector_etf)
            etf_hist = etf.history(period=period)

            if stock_hist.empty or etf_hist.empty:
                return {"error": "Insufficient data"}

            # Relative strength = Stock / Sector ETF
            # Align dates
            merged = pd.merge(stock_hist[['Close']], etf_hist[['Close']],
                            left_index=True, right_index=True,
                            suffixes=('_stock', '_etf'))

            merged['RS'] = merged['Close_stock'] / merged['Close_etf']

            # RS trend
            rs_current = merged['RS'].iloc[-1]
            rs_start = merged['RS'].iloc[0]
            rs_change = ((rs_current - rs_start) / rs_start * 100) if rs_start > 0 else 0

            # RS moving average
            merged['RS_MA'] = merged['RS'].rolling(window=20).mean()

            rs_trend = "strengthening" if rs_current > merged['RS_MA'].iloc[-1] else "weakening"

            return {
                "relative_strength": float(rs_current),
                "rs_change": float(rs_change),
                "rs_trend": rs_trend,
                "interpretation": self._interpret_rs(rs_change, rs_trend)
            }

        except Exception as e:
            return {"error": str(e)}

    def _interpret_rs(self, rs_change: float, rs_trend: str) -> str:
        """RS yorumlama"""
        if rs_change > 10 and rs_trend == "strengthening":
            return "Strong outperformance vs sector"
        elif rs_change > 0 and rs_trend == "strengthening":
            return "Outperforming sector"
        elif rs_change < -10 and rs_trend == "weakening":
            return "Strong underperformance vs sector"
        elif rs_change < 0 and rs_trend == "weakening":
            return "Underperforming sector"
        else:
            return "In line with sector"

    def analyze_sector_trends(self) -> Dict[str, Any]:
        """Sektör trendleri"""
        try:
            sector_etf = self.SECTOR_ETFS.get(self.sector)
            if not sector_etf:
                return {"error": "Sector ETF not found"}

            etf = yf.Ticker(sector_etf)
            etf_hist = etf.history(period="1y")

            if etf_hist.empty:
                return {"error": "No data"}

            # Moving averages
            etf_hist['MA_50'] = etf_hist['Close'].rolling(window=50).mean()
            etf_hist['MA_200'] = etf_hist['Close'].rolling(window=200).mean()

            current = etf_hist.iloc[-1]

            # Trend
            if current['Close'] > current['MA_50'] > current['MA_200']:
                trend = "strong_uptrend"
            elif current['Close'] > current['MA_50']:
                trend = "uptrend"
            elif current['Close'] < current['MA_50'] < current['MA_200']:
                trend = "strong_downtrend"
            elif current['Close'] < current['MA_50']:
                trend = "downtrend"
            else:
                trend = "neutral"

            return {
                "sector": self.sector,
                "sector_etf": sector_etf,
                "current_price": float(current['Close']),
                "ma_50": float(current['MA_50']),
                "ma_200": float(current['MA_200']) if not pd.isna(current['MA_200']) else None,
                "trend": trend,
                "momentum": "bullish" if trend in ['uptrend', 'strong_uptrend'] else "bearish"
            }

        except Exception as e:
            return {"error": str(e)}

    def estimate_market_position(self) -> Dict[str, Any]:
        """Pazar pozisyonu tahmini"""
        market_cap = self.info.get('marketCap', 0)

        if market_cap > 200_000_000_000:
            size = "mega_cap"
            position = "market_leader"
        elif market_cap > 10_000_000_000:
            size = "large_cap"
            position = "major_player"
        elif market_cap > 2_000_000_000:
            size = "mid_cap"
            position = "established_company"
        elif market_cap > 300_000_000:
            size = "small_cap"
            position = "emerging_player"
        else:
            size = "micro_cap"
            position = "niche_player"

        return {
            "market_cap": market_cap,
            "size_category": size,
            "estimated_position": position,
            "sector": self.sector
        }

    def generate_sector_recommendation(self) -> Dict[str, Any]:
        """Sektör bazlı öneri"""
        try:
            performance = self.analyze_sector_performance()
            metrics = self.calculate_sector_metrics()
            relative_strength = self.calculate_relative_strength()

            score = 0

            # Sector performance
            if performance.get('sector_rank') == 'top_performer':
                score += 2
            elif performance.get('sector_rank') == 'above_market':
                score += 1

            # Stock vs sector
            if performance.get('stock_rank') == 'sector_leader':
                score += 2
            elif performance.get('stock_rank') == 'above_sector':
                score += 1

            # Relative strength
            if relative_strength.get('rs_trend') == 'strengthening':
                score += 1

            # Valuation
            pe_vs_sector = metrics.get('pe_vs_sector', 0)
            if pe_vs_sector < -5:  # Undervalued vs sector
                score += 1

            # ROE
            roe_vs_sector = metrics.get('roe_vs_sector', 0)
            if roe_vs_sector > 0:
                score += 1

            # Recommendation
            if score >= 5:
                recommendation = "strong_buy"
                explanation = "Sektör lideri, güçlü performans ve değerleme avantajı"
            elif score >= 3:
                recommendation = "buy"
                explanation = "Sektörde iyi pozisyon, olumlu göstergeler"
            elif score >= 1:
                recommendation = "hold"
                explanation = "Orta seviye performans, seçici yaklaşım gerekir"
            else:
                recommendation = "avoid"
                explanation = "Sektör ve şirket performansı zayıf"

            return {
                "recommendation": recommendation,
                "score": score,
                "max_score": 7,
                "explanation": explanation,
                "sector_outlook": performance.get('sector_rank', 'unknown'),
                "stock_position": performance.get('stock_rank', 'unknown')
            }

        except Exception as e:
            return {"error": str(e)}
