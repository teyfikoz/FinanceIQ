#!/usr/bin/env python3
"""
Takas Analizi Modülü (Settlement Analysis)
Yurt içi (BIST) ve yurt dışı hisse senetleri için takas hacmi ve akış analizi
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class SettlementAnalyzer:
    """Hisse senetleri için takas analizi ve hacim takibi"""

    def __init__(self, symbol: str, market: str = "auto"):
        """
        Args:
            symbol: Hisse senedi sembolü (örn: THYAO.IS, AAPL)
            market: 'bist' veya 'global' (auto otomatik algılar)
        """
        self.symbol = symbol.upper()
        self.market = self._detect_market(symbol) if market == "auto" else market
        self.stock = yf.Ticker(self.symbol)

    def _detect_market(self, symbol: str) -> str:
        """Sembolden piyasa türünü algıla"""
        if '.IS' in symbol.upper():
            return 'bist'
        return 'global'

    def get_settlement_analysis(self, period: str = "1mo") -> Dict[str, Any]:
        """Kapsamlı takas analizi"""
        try:
            hist = self.stock.history(period=period)

            if hist.empty:
                return self._empty_result()

            analysis = {
                "summary": self._calculate_summary_metrics(hist),
                "daily_settlement": self._analyze_daily_settlements(hist),
                "volume_profile": self._analyze_volume_profile(hist),
                "price_impact": self._analyze_price_impact(hist),
                "liquidity_metrics": self._calculate_liquidity_metrics(hist),
                "settlement_trends": self._identify_settlement_trends(hist),
                "anomalies": self._detect_settlement_anomalies(hist),
                "market_depth": self._estimate_market_depth(hist),
                "settlement_efficiency": self._calculate_settlement_efficiency(hist)
            }

            if self.market == 'bist':
                analysis["bist_specific"] = self._bist_specific_metrics(hist)

            return analysis

        except Exception as e:
            return {"error": str(e)}

    def _calculate_summary_metrics(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Özet takas metrikleri"""
        total_volume = hist['Volume'].sum()
        total_value = (hist['Close'] * hist['Volume']).sum()
        avg_daily_volume = hist['Volume'].mean()
        avg_daily_value = (hist['Close'] * hist['Volume']).mean()

        return {
            "total_volume": int(total_volume),
            "total_value": float(total_value),
            "avg_daily_volume": int(avg_daily_volume),
            "avg_daily_value": float(avg_daily_value),
            "trading_days": len(hist),
            "volume_std": float(hist['Volume'].std()),
            "value_std": float((hist['Close'] * hist['Volume']).std())
        }

    def _analyze_daily_settlements(self, hist: pd.DataFrame) -> List[Dict[str, Any]]:
        """Günlük takas detayları"""
        settlements = []

        for idx, row in hist.iterrows():
            daily_value = row['Close'] * row['Volume']

            settlement = {
                "date": idx.strftime('%Y-%m-%d'),
                "volume": int(row['Volume']),
                "value": float(daily_value),
                "price": float(row['Close']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "price_change": float(row['Close'] - row['Open']),
                "price_change_pct": float((row['Close'] - row['Open']) / row['Open'] * 100) if row['Open'] > 0 else 0
            }
            settlements.append(settlement)

        return settlements[-10:]  # Son 10 gün

    def _analyze_volume_profile(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Hacim profili analizi"""
        volumes = hist['Volume'].values

        return {
            "min_volume": int(volumes.min()),
            "max_volume": int(volumes.max()),
            "median_volume": int(np.median(volumes)),
            "q1_volume": int(np.percentile(volumes, 25)),
            "q3_volume": int(np.percentile(volumes, 75)),
            "volume_volatility": float(volumes.std() / volumes.mean() if volumes.mean() > 0 else 0),
            "high_volume_days": int(np.sum(volumes > np.percentile(volumes, 75))),
            "low_volume_days": int(np.sum(volumes < np.percentile(volumes, 25)))
        }

    def _analyze_price_impact(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Hacim-fiyat etkisi analizi"""
        hist_copy = hist.copy()
        hist_copy['price_change'] = hist_copy['Close'].pct_change()
        hist_copy['volume_change'] = hist_copy['Volume'].pct_change()

        # Korelasyon hesapla
        correlation = hist_copy[['price_change', 'volume_change']].corr().iloc[0, 1]

        # Yüksek hacimli günlerde fiyat hareketi
        high_volume_mask = hist_copy['Volume'] > hist_copy['Volume'].median()
        high_vol_price_change = hist_copy.loc[high_volume_mask, 'price_change'].mean()
        low_vol_price_change = hist_copy.loc[~high_volume_mask, 'price_change'].mean()

        return {
            "volume_price_correlation": float(correlation) if not np.isnan(correlation) else 0,
            "high_volume_avg_price_change": float(high_vol_price_change) if not np.isnan(high_vol_price_change) else 0,
            "low_volume_avg_price_change": float(low_vol_price_change) if not np.isnan(low_vol_price_change) else 0,
            "impact_ratio": float(abs(high_vol_price_change / low_vol_price_change)) if low_vol_price_change != 0 else 1
        }

    def _calculate_liquidity_metrics(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Likidite metrikleri"""
        # Turnover ratio (hacim / ortalama piyasa değeri tahmini)
        avg_price = hist['Close'].mean()
        avg_volume = hist['Volume'].mean()

        # Bid-Ask spread tahmini (High-Low / Close)
        avg_spread = ((hist['High'] - hist['Low']) / hist['Close']).mean()

        # Amihud illiquidity measure
        price_impact = (hist['Close'].pct_change().abs() / (hist['Volume'] * hist['Close'])).mean()

        return {
            "avg_daily_turnover": float(avg_volume * avg_price),
            "estimated_spread_pct": float(avg_spread * 100),
            "illiquidity_measure": float(price_impact * 1e6) if not np.isnan(price_impact) else 0,
            "zero_volume_days": int((hist['Volume'] == 0).sum())
        }

    def _identify_settlement_trends(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Takas trendlerini tespit et"""
        # Son 7 gün vs önceki 7 gün karşılaştırması
        if len(hist) < 14:
            return {"trend": "insufficient_data"}

        recent_volume = hist['Volume'].iloc[-7:].mean()
        previous_volume = hist['Volume'].iloc[-14:-7].mean()

        volume_change = (recent_volume - previous_volume) / previous_volume * 100 if previous_volume > 0 else 0

        # Trend yönü
        if volume_change > 20:
            trend = "increasing"
        elif volume_change < -20:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "recent_avg_volume": int(recent_volume),
            "previous_avg_volume": int(previous_volume),
            "change_pct": float(volume_change),
            "momentum": "bullish" if volume_change > 0 else "bearish"
        }

    def _detect_settlement_anomalies(self, hist: pd.DataFrame) -> List[Dict[str, Any]]:
        """Olağandışı takas aktivitelerini tespit et"""
        anomalies = []

        mean_volume = hist['Volume'].mean()
        std_volume = hist['Volume'].std()
        threshold = mean_volume + 2 * std_volume

        for idx, row in hist.iterrows():
            if row['Volume'] > threshold:
                anomalies.append({
                    "date": idx.strftime('%Y-%m-%d'),
                    "volume": int(row['Volume']),
                    "normal_volume": int(mean_volume),
                    "deviation_pct": float((row['Volume'] - mean_volume) / mean_volume * 100),
                    "price_change": float((row['Close'] - row['Open']) / row['Open'] * 100) if row['Open'] > 0 else 0,
                    "type": "spike"
                })

        return anomalies[-5:]  # Son 5 anomali

    def _estimate_market_depth(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Piyasa derinliği tahmini"""
        # Volume-weighted average price (VWAP)
        vwap = (hist['Close'] * hist['Volume']).sum() / hist['Volume'].sum()

        # Price range analizi
        price_range = hist['High'].max() - hist['Low'].min()
        price_range_pct = (price_range / hist['Close'].mean()) * 100

        return {
            "vwap": float(vwap),
            "price_range": float(price_range),
            "price_range_pct": float(price_range_pct),
            "avg_daily_range": float(((hist['High'] - hist['Low']) / hist['Close']).mean() * 100),
            "depth_score": self._calculate_depth_score(hist)
        }

    def _calculate_depth_score(self, hist: pd.DataFrame) -> float:
        """Piyasa derinlik skoru (0-100)"""
        # Yüksek hacim, düşük volatilite = yüksek derinlik
        avg_volume = hist['Volume'].mean()
        volume_stability = 1 - (hist['Volume'].std() / avg_volume) if avg_volume > 0 else 0

        price_stability = 1 - hist['Close'].pct_change().std()

        score = (volume_stability * 0.6 + price_stability * 0.4) * 100
        return max(0, min(100, float(score)))

    def _calculate_settlement_efficiency(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """Takas verimliliği metrikleri"""
        # Tutarlı hacim = verimli takas
        volume_cv = hist['Volume'].std() / hist['Volume'].mean() if hist['Volume'].mean() > 0 else 0

        # Fiyat istikrarı
        price_volatility = hist['Close'].pct_change().std()

        # Verimlilik skoru
        efficiency = (1 - min(volume_cv, 1)) * 0.5 + (1 - min(price_volatility * 10, 1)) * 0.5

        return {
            "volume_consistency": float(1 - volume_cv) if volume_cv < 1 else 0,
            "price_stability": float(1 - price_volatility) if price_volatility < 1 else 0,
            "efficiency_score": float(efficiency * 100),
            "rating": self._get_efficiency_rating(efficiency)
        }

    def _get_efficiency_rating(self, score: float) -> str:
        """Verimlilik derecesi"""
        if score > 0.8:
            return "excellent"
        elif score > 0.6:
            return "good"
        elif score > 0.4:
            return "moderate"
        else:
            return "poor"

    def _bist_specific_metrics(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """BIST'e özel takas metrikleri"""
        try:
            # BIST için özel hesaplamalar
            info = self.stock.info

            return {
                "market_cap_try": info.get('marketCap', 0),
                "free_float_pct": info.get('floatShares', 0) / info.get('sharesOutstanding', 1) * 100 if info.get('sharesOutstanding') else 0,
                "avg_daily_try_volume": float((hist['Close'] * hist['Volume']).mean()),
                "bist_liquidity_rank": self._calculate_bist_liquidity_rank(hist)
            }
        except:
            return {}

    def _calculate_bist_liquidity_rank(self, hist: pd.DataFrame) -> str:
        """BIST likidite sıralaması"""
        avg_value = (hist['Close'] * hist['Volume']).mean()

        # Basit sınıflandırma (gerçek uygulamada BIST ortalamalarıyla karşılaştırılır)
        if avg_value > 50_000_000:  # 50M TL
            return "high"
        elif avg_value > 10_000_000:  # 10M TL
            return "medium"
        else:
            return "low"

    def _empty_result(self) -> Dict[str, Any]:
        """Veri yoksa boş sonuç"""
        return {
            "error": "No settlement data available",
            "symbol": self.symbol,
            "market": self.market
        }

    def get_settlement_comparison(self, comparison_symbols: List[str], period: str = "1mo") -> Dict[str, Any]:
        """Birden fazla hisse arasında takas karşılaştırması"""
        results = {}

        # Ana hisse
        results[self.symbol] = self.get_settlement_analysis(period)

        # Karşılaştırma hisseleri
        for symbol in comparison_symbols:
            try:
                analyzer = SettlementAnalyzer(symbol)
                results[symbol] = analyzer.get_settlement_analysis(period)
            except:
                results[symbol] = {"error": "Failed to fetch data"}

        # Karşılaştırma özeti
        comparison_summary = self._create_comparison_summary(results)

        return {
            "individual_results": results,
            "comparison_summary": comparison_summary
        }

    def _create_comparison_summary(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Karşılaştırma özeti oluştur"""
        summary = {
            "symbols": list(results.keys()),
            "highest_volume": None,
            "most_liquid": None,
            "most_efficient": None
        }

        # En yüksek hacim
        max_volume = 0
        for symbol, data in results.items():
            if 'summary' in data and data['summary'].get('avg_daily_volume', 0) > max_volume:
                max_volume = data['summary']['avg_daily_volume']
                summary['highest_volume'] = symbol

        # En likit
        max_liquidity = 0
        for symbol, data in results.items():
            if 'market_depth' in data and data['market_depth'].get('depth_score', 0) > max_liquidity:
                max_liquidity = data['market_depth']['depth_score']
                summary['most_liquid'] = symbol

        # En verimli
        max_efficiency = 0
        for symbol, data in results.items():
            if 'settlement_efficiency' in data and data['settlement_efficiency'].get('efficiency_score', 0) > max_efficiency:
                max_efficiency = data['settlement_efficiency']['efficiency_score']
                summary['most_efficient'] = symbol

        return summary


def get_bist_top_settlements(limit: int = 10) -> List[Dict[str, Any]]:
    """BIST'te en yüksek takas hacimli hisseler"""
    # BIST 100 örnek hisseler (gerçek uygulamada API'den çekilir)
    bist_symbols = [
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'EREGL.IS', 'SAHOL.IS',
        'SISE.IS', 'PETKM.IS', 'KCHOL.IS', 'TUPRS.IS', 'ISCTR.IS'
    ]

    results = []

    for symbol in bist_symbols[:limit]:
        try:
            analyzer = SettlementAnalyzer(symbol)
            analysis = analyzer.get_settlement_analysis(period="1d")

            if 'summary' in analysis:
                results.append({
                    'symbol': symbol,
                    'volume': analysis['summary']['total_volume'],
                    'value': analysis['summary']['total_value']
                })
        except:
            continue

    # Hacme göre sırala
    results.sort(key=lambda x: x['value'], reverse=True)
    return results


def get_global_top_settlements(limit: int = 10) -> List[Dict[str, Any]]:
    """Küresel piyasalarda en yüksek takas hacimli hisseler"""
    # Örnek global hisseler
    global_symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
        'TSLA', 'META', 'JPM', 'V', 'WMT'
    ]

    results = []

    for symbol in global_symbols[:limit]:
        try:
            analyzer = SettlementAnalyzer(symbol)
            analysis = analyzer.get_settlement_analysis(period="1d")

            if 'summary' in analysis:
                results.append({
                    'symbol': symbol,
                    'volume': analysis['summary']['total_volume'],
                    'value': analysis['summary']['total_value']
                })
        except:
            continue

    # Değere göre sırala
    results.sort(key=lambda x: x['value'], reverse=True)
    return results
