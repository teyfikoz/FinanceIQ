#!/usr/bin/env python3
"""
Temettü Analizi Modülü
Temettü ödemeleri, verimi, büyümesi ve sürdürülebilirlik analizi
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class DividendAnalyzer:
    """Temettü analizi ve değerlendirme aracı"""

    def __init__(self, symbol: str):
        """
        Args:
            symbol: Hisse senedi sembolü
        """
        self.symbol = symbol.upper()
        self.stock = yf.Ticker(self.symbol)
        self.info = self.stock.info

    def get_comprehensive_dividend_analysis(self) -> Dict[str, Any]:
        """Kapsamlı temettü analizi"""
        try:
            return {
                "basic_info": self.get_basic_dividend_info(),
                "dividend_history": self.get_dividend_history(),
                "dividend_metrics": self.calculate_dividend_metrics(),
                "dividend_growth": self.analyze_dividend_growth(),
                "sustainability": self.assess_dividend_sustainability(),
                "yield_analysis": self.analyze_yield_metrics(),
                "comparison": self.compare_to_benchmarks(),
                "forecast": self.forecast_future_dividends(),
                "rating": self.calculate_dividend_score()
            }
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def get_basic_dividend_info(self) -> Dict[str, Any]:
        """Temel temettü bilgileri"""
        try:
            return {
                "symbol": self.symbol,
                "company_name": self.info.get('longName', 'N/A'),
                "current_price": self.info.get('currentPrice', 0),
                "dividend_rate": self.info.get('dividendRate', 0),
                "dividend_yield": self.info.get('dividendYield', 0) * 100 if self.info.get('dividendYield') else 0,
                "ex_dividend_date": self.info.get('exDividendDate', None),
                "payout_ratio": self.info.get('payoutRatio', 0) * 100 if self.info.get('payoutRatio') else 0,
                "five_year_avg_yield": self.info.get('fiveYearAvgDividendYield', 0),
                "trailing_annual_dividend_rate": self.info.get('trailingAnnualDividendRate', 0),
                "trailing_annual_dividend_yield": self.info.get('trailingAnnualDividendYield', 0) * 100 if self.info.get('trailingAnnualDividendYield') else 0
            }
        except Exception as e:
            return {"error": str(e)}

    def get_dividend_history(self, years: int = 10) -> List[Dict[str, Any]]:
        """Temettü geçmişi"""
        try:
            dividends = self.stock.dividends
            if dividends.empty:
                return []

            # Son X yılın verileri
            cutoff_date = datetime.now() - timedelta(days=years*365)
            recent_dividends = dividends[dividends.index >= cutoff_date]

            history = []
            for date, amount in recent_dividends.items():
                history.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "amount": float(amount),
                    "year": date.year,
                    "quarter": (date.month - 1) // 3 + 1
                })

            return history

        except Exception as e:
            return []

    def calculate_dividend_metrics(self) -> Dict[str, Any]:
        """Temettü metrikleri"""
        try:
            dividends = self.stock.dividends
            if dividends.empty:
                return {"error": "No dividend history"}

            # Yıllık temettüler
            annual_dividends = dividends.resample('Y').sum()

            # Son 5 yıl
            last_5_years = annual_dividends.tail(5)

            if len(last_5_years) == 0:
                return {"error": "Insufficient data"}

            return {
                "total_dividends_paid": float(dividends.sum()),
                "last_dividend": float(dividends.iloc[-1]),
                "last_dividend_date": dividends.index[-1].strftime('%Y-%m-%d'),
                "annual_dividend_current": float(last_5_years.iloc[-1]) if len(last_5_years) > 0 else 0,
                "annual_dividend_avg_5y": float(last_5_years.mean()),
                "dividend_frequency": self._estimate_dividend_frequency(dividends),
                "consecutive_years": self._calculate_consecutive_years(annual_dividends),
                "dividend_stability": self._calculate_stability(annual_dividends)
            }

        except Exception as e:
            return {"error": str(e)}

    def _estimate_dividend_frequency(self, dividends: pd.Series) -> str:
        """Temettü ödeme sıklığını tahmin et"""
        # Son 2 yılda kaç ödeme yapılmış
        recent = dividends.tail(24)  # Son 24 ay
        payments_per_year = len(recent) / 2

        if payments_per_year >= 11:
            return "monthly"
        elif payments_per_year >= 3.5:
            return "quarterly"
        elif payments_per_year >= 1.5:
            return "semi-annual"
        elif payments_per_year >= 0.8:
            return "annual"
        else:
            return "irregular"

    def _calculate_consecutive_years(self, annual_dividends: pd.Series) -> int:
        """Kesintisiz temettü ödeme yılları"""
        if len(annual_dividends) == 0:
            return 0

        consecutive = 0
        for i in range(len(annual_dividends) - 1, -1, -1):
            if annual_dividends.iloc[i] > 0:
                consecutive += 1
            else:
                break

        return consecutive

    def _calculate_stability(self, annual_dividends: pd.Series) -> float:
        """Temettü istikrar skoru (0-100)"""
        if len(annual_dividends) < 3:
            return 0.0

        # Son 5 yıl
        recent = annual_dividends.tail(5)

        # Standart sapma / ortalama (düşük = istikrarlı)
        cv = recent.std() / recent.mean() if recent.mean() > 0 else 1

        # İstikrar skoru (düşük CV = yüksek skor)
        stability = max(0, 100 - (cv * 100))

        return float(stability)

    def analyze_dividend_growth(self) -> Dict[str, Any]:
        """Temettü büyüme analizi"""
        try:
            dividends = self.stock.dividends
            if dividends.empty:
                return {"error": "No dividend history"}

            annual_dividends = dividends.resample('Y').sum()

            if len(annual_dividends) < 2:
                return {"error": "Insufficient data"}

            # Büyüme oranları
            growth_rates = annual_dividends.pct_change() * 100

            # 1, 3, 5, 10 yıllık CAGR
            cagr_1y = self._calculate_cagr(annual_dividends, 1)
            cagr_3y = self._calculate_cagr(annual_dividends, 3)
            cagr_5y = self._calculate_cagr(annual_dividends, 5)
            cagr_10y = self._calculate_cagr(annual_dividends, 10)

            return {
                "cagr_1y": cagr_1y,
                "cagr_3y": cagr_3y,
                "cagr_5y": cagr_5y,
                "cagr_10y": cagr_10y,
                "avg_growth_rate": float(growth_rates.mean()) if not growth_rates.empty else 0,
                "growth_consistency": self._assess_growth_consistency(growth_rates),
                "growth_trend": self._determine_growth_trend(annual_dividends),
                "years_of_growth": self._count_growth_years(annual_dividends)
            }

        except Exception as e:
            return {"error": str(e)}

    def _calculate_cagr(self, series: pd.Series, years: int) -> Optional[float]:
        """CAGR hesapla"""
        if len(series) < years + 1:
            return None

        recent = series.tail(years + 1)
        if recent.iloc[0] == 0:
            return None

        cagr = ((recent.iloc[-1] / recent.iloc[0]) ** (1 / years) - 1) * 100
        return float(cagr)

    def _assess_growth_consistency(self, growth_rates: pd.Series) -> str:
        """Büyüme tutarlılığı"""
        if len(growth_rates) < 3:
            return "insufficient_data"

        positive_years = (growth_rates > 0).sum()
        total_years = len(growth_rates.dropna())

        if total_years == 0:
            return "insufficient_data"

        consistency_ratio = positive_years / total_years

        if consistency_ratio >= 0.9:
            return "very_consistent"
        elif consistency_ratio >= 0.7:
            return "consistent"
        elif consistency_ratio >= 0.5:
            return "moderate"
        else:
            return "inconsistent"

    def _determine_growth_trend(self, annual_dividends: pd.Series) -> str:
        """Büyüme trendi"""
        if len(annual_dividends) < 3:
            return "unknown"

        recent = annual_dividends.tail(5)

        # Linear regression
        x = np.arange(len(recent))
        y = recent.values

        if len(x) < 2:
            return "unknown"

        slope = np.polyfit(x, y, 1)[0]

        if slope > recent.mean() * 0.1:
            return "accelerating"
        elif slope > 0:
            return "growing"
        elif slope > -recent.mean() * 0.1:
            return "stable"
        else:
            return "declining"

    def _count_growth_years(self, annual_dividends: pd.Series) -> int:
        """Ardışık büyüme yılları"""
        if len(annual_dividends) < 2:
            return 0

        count = 0
        for i in range(len(annual_dividends) - 1, 0, -1):
            if annual_dividends.iloc[i] > annual_dividends.iloc[i-1]:
                count += 1
            else:
                break

        return count

    def assess_dividend_sustainability(self) -> Dict[str, Any]:
        """Temettü sürdürülebilirlik değerlendirmesi"""
        try:
            # Payout ratio
            payout_ratio = self.info.get('payoutRatio', 0)

            # Free cash flow
            financials = self.stock.cashflow
            if not financials.empty and 'Free Cash Flow' in financials.index:
                fcf = financials.loc['Free Cash Flow'].iloc[0]
            else:
                fcf = None

            # Debt levels
            balance_sheet = self.stock.balance_sheet
            if not balance_sheet.empty:
                total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0
                total_equity = balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in balance_sheet.index else 1
                debt_to_equity = (total_debt / total_equity) if total_equity > 0 else 0
            else:
                debt_to_equity = None

            # Sustainability assessment
            sustainability_score = self._calculate_sustainability_score(payout_ratio, debt_to_equity)

            return {
                "payout_ratio": float(payout_ratio * 100) if payout_ratio else 0,
                "payout_status": self._assess_payout_ratio(payout_ratio),
                "debt_to_equity": float(debt_to_equity) if debt_to_equity else None,
                "sustainability_score": sustainability_score,
                "sustainability_rating": self._get_sustainability_rating(sustainability_score),
                "risk_level": self._assess_risk_level(payout_ratio, debt_to_equity)
            }

        except Exception as e:
            return {"error": str(e)}

    def _assess_payout_ratio(self, payout_ratio: float) -> str:
        """Payout ratio değerlendirmesi"""
        if not payout_ratio:
            return "unknown"

        payout_pct = payout_ratio * 100

        if payout_pct < 30:
            return "conservative"
        elif payout_pct < 60:
            return "sustainable"
        elif payout_pct < 80:
            return "moderate_risk"
        else:
            return "high_risk"

    def _calculate_sustainability_score(self, payout_ratio: float, debt_to_equity: Optional[float]) -> float:
        """Sürdürülebilirlik skoru (0-100)"""
        score = 50.0  # Base score

        # Payout ratio contribution (0-50)
        if payout_ratio:
            if payout_ratio < 0.3:
                score += 30
            elif payout_ratio < 0.6:
                score += 20
            elif payout_ratio < 0.8:
                score += 10
            else:
                score -= 10

        # Debt contribution (0-20)
        if debt_to_equity is not None:
            if debt_to_equity < 0.5:
                score += 20
            elif debt_to_equity < 1.0:
                score += 10
            elif debt_to_equity < 2.0:
                score += 0
            else:
                score -= 10

        return max(0, min(100, float(score)))

    def _get_sustainability_rating(self, score: float) -> str:
        """Sürdürülebilirlik derecesi"""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "fair"
        else:
            return "poor"

    def _assess_risk_level(self, payout_ratio: float, debt_to_equity: Optional[float]) -> str:
        """Risk seviyesi"""
        risk_factors = 0

        if payout_ratio and payout_ratio > 0.8:
            risk_factors += 2
        elif payout_ratio and payout_ratio > 0.6:
            risk_factors += 1

        if debt_to_equity and debt_to_equity > 2.0:
            risk_factors += 2
        elif debt_to_equity and debt_to_equity > 1.0:
            risk_factors += 1

        if risk_factors >= 3:
            return "high"
        elif risk_factors >= 2:
            return "moderate"
        else:
            return "low"

    def analyze_yield_metrics(self) -> Dict[str, Any]:
        """Verim metrikleri"""
        try:
            current_price = self.info.get('currentPrice', 0)
            dividend_rate = self.info.get('dividendRate', 0)

            # Current yield
            current_yield = (dividend_rate / current_price * 100) if current_price > 0 else 0

            # Yield on cost (5 years ago)
            hist = self.stock.history(period="5y")
            if not hist.empty:
                price_5y_ago = hist['Close'].iloc[0]
                yield_on_cost_5y = (dividend_rate / price_5y_ago * 100) if price_5y_ago > 0 else 0
            else:
                yield_on_cost_5y = 0

            return {
                "current_yield": float(current_yield),
                "yield_on_cost_5y": float(yield_on_cost_5y),
                "yield_category": self._categorize_yield(current_yield),
                "yield_vs_market": self._compare_yield_to_market(current_yield)
            }

        except Exception as e:
            return {"error": str(e)}

    def _categorize_yield(self, yield_pct: float) -> str:
        """Verim kategorisi"""
        if yield_pct < 1:
            return "very_low"
        elif yield_pct < 2:
            return "low"
        elif yield_pct < 4:
            return "moderate"
        elif yield_pct < 6:
            return "high"
        else:
            return "very_high"

    def _compare_yield_to_market(self, yield_pct: float) -> str:
        """Piyasa ortalamasıyla karşılaştır (S&P 500 ortalama ~1.5%)"""
        market_avg = 1.5

        if yield_pct > market_avg * 2:
            return "significantly_above"
        elif yield_pct > market_avg * 1.2:
            return "above"
        elif yield_pct > market_avg * 0.8:
            return "in_line"
        else:
            return "below"

    def compare_to_benchmarks(self) -> Dict[str, Any]:
        """Benchmark karşılaştırması"""
        try:
            current_yield = self.info.get('dividendYield', 0) * 100 if self.info.get('dividendYield') else 0
            sector = self.info.get('sector', 'Unknown')

            # Sector averages (approximate)
            sector_yields = {
                'Utilities': 3.5,
                'Real Estate': 3.0,
                'Energy': 2.8,
                'Consumer Staples': 2.5,
                'Financials': 2.3,
                'Healthcare': 1.5,
                'Industrials': 1.8,
                'Materials': 2.0,
                'Communication Services': 1.0,
                'Technology': 0.8,
                'Consumer Discretionary': 1.2
            }

            sector_avg = sector_yields.get(sector, 1.5)

            return {
                "sector": sector,
                "stock_yield": float(current_yield),
                "sector_avg_yield": float(sector_avg),
                "vs_sector": float(current_yield - sector_avg),
                "vs_sp500": float(current_yield - 1.5),
                "percentile_rank": self._estimate_percentile(current_yield, sector)
            }

        except Exception as e:
            return {"error": str(e)}

    def _estimate_percentile(self, yield_pct: float, sector: str) -> int:
        """Yüzdelik dilim tahmini"""
        # Simplified estimation
        if yield_pct > 5:
            return 95
        elif yield_pct > 4:
            return 80
        elif yield_pct > 3:
            return 60
        elif yield_pct > 2:
            return 40
        else:
            return 20

    def forecast_future_dividends(self, years: int = 3) -> List[Dict[str, Any]]:
        """Gelecek temettü tahmini"""
        try:
            dividends = self.stock.dividends
            if dividends.empty:
                return []

            annual_dividends = dividends.resample('Y').sum()

            if len(annual_dividends) < 3:
                return []

            # Son 5 yıl CAGR
            growth_rate = self._calculate_cagr(annual_dividends, min(5, len(annual_dividends)-1))

            if growth_rate is None:
                growth_rate = 0

            # Conservative growth assumption (max 10% annually)
            growth_rate = min(growth_rate, 10)

            current_dividend = annual_dividends.iloc[-1]

            forecasts = []
            for year in range(1, years + 1):
                forecasted_dividend = current_dividend * ((1 + growth_rate/100) ** year)
                forecasts.append({
                    "year": datetime.now().year + year,
                    "forecasted_dividend": float(forecasted_dividend),
                    "growth_rate_used": float(growth_rate)
                })

            return forecasts

        except Exception as e:
            return []

    def calculate_dividend_score(self) -> Dict[str, Any]:
        """Genel temettü skoru"""
        try:
            # Get all analyses
            metrics = self.calculate_dividend_metrics()
            growth = self.analyze_dividend_growth()
            sustainability = self.assess_dividend_sustainability()
            yield_analysis = self.analyze_yield_metrics()

            score = 0
            max_score = 100

            # Yield (0-25 points)
            current_yield = yield_analysis.get('current_yield', 0)
            if current_yield > 4:
                score += 25
            elif current_yield > 3:
                score += 20
            elif current_yield > 2:
                score += 15
            elif current_yield > 1:
                score += 10

            # Growth (0-25 points)
            cagr_5y = growth.get('cagr_5y', 0)
            if cagr_5y and cagr_5y > 10:
                score += 25
            elif cagr_5y and cagr_5y > 5:
                score += 20
            elif cagr_5y and cagr_5y > 0:
                score += 15

            # Sustainability (0-25 points)
            sustainability_score = sustainability.get('sustainability_score', 0)
            score += sustainability_score * 0.25

            # Consistency (0-25 points)
            consecutive_years = metrics.get('consecutive_years', 0)
            if consecutive_years >= 25:
                score += 25
            elif consecutive_years >= 10:
                score += 20
            elif consecutive_years >= 5:
                score += 15
            elif consecutive_years >= 3:
                score += 10

            # Overall rating
            if score >= 80:
                rating = "excellent"
            elif score >= 60:
                rating = "good"
            elif score >= 40:
                rating = "fair"
            else:
                rating = "poor"

            return {
                "total_score": float(score),
                "max_score": max_score,
                "rating": rating,
                "recommendation": self._get_dividend_recommendation(rating, current_yield)
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_dividend_recommendation(self, rating: str, yield_pct: float) -> str:
        """Temettü yatırım tavsiyesi"""
        if rating == "excellent" and yield_pct > 3:
            return "Mükemmel temettü hissesi. Uzun vadeli gelir yatırımcıları için ideal."
        elif rating == "good":
            return "İyi temettü hissesi. Gelir portföyüne eklenebilir."
        elif rating == "fair":
            return "Orta seviye temettü hissesi. Dikkatli değerlendirme gerekir."
        else:
            return "Temettü yatırımı için uygun değil. Diğer seçenekleri değerlendirin."
