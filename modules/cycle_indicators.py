"""
🌀 Cycle Indicators Module
Calculates various economic and market cycle indicators
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf


class CycleIndicators:
    """Calculate cycle phase indicators"""

    def __init__(self):
        self.cache = {}
        self.cache_timestamp = {}
        self.cache_duration = 300  # 5 minutes

    def _is_cache_valid(self, key):
        """Check if cache is still valid"""
        if key not in self.cache_timestamp:
            return False
        elapsed = (datetime.now() - self.cache_timestamp[key]).total_seconds()
        return elapsed < self.cache_duration

    def _set_cache(self, key, value):
        """Store value in cache"""
        self.cache[key] = value
        self.cache_timestamp[key] = datetime.now()

    def get_market_cycle_phase(self, fred_api=None):
        """
        Calculate Market Cycle Phase (4 stages)
        Returns: phase_name, phase_score (0-1), indicators dict
        """
        try:
            # Get market data
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period="2y")

            if spy_hist.empty:
                return self._get_default_market_cycle()

            # Calculate indicators
            current_price = spy_hist['Close'].iloc[-1]
            sma_50 = spy_hist['Close'].rolling(50).mean().iloc[-1]
            sma_200 = spy_hist['Close'].rolling(200).mean().iloc[-1]

            # Price momentum
            returns_3m = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[-63] - 1) * 100

            # Volatility (20-day)
            volatility = spy_hist['Close'].pct_change().rolling(20).std().iloc[-1] * np.sqrt(252) * 100

            # VIX for fear gauge
            try:
                vix = yf.Ticker("^VIX")
                vix_hist = vix.history(period="5d")
                vix_level = vix_hist['Close'].iloc[-1] if not vix_hist.empty else 20
            except:
                vix_level = 20

            # Volume trend
            volume_avg = spy_hist['Volume'].rolling(50).mean().iloc[-1]
            volume_recent = spy_hist['Volume'].iloc[-5:].mean()
            volume_trend = (volume_recent / volume_avg - 1) * 100

            # Phase determination logic
            indicators = {
                'price_vs_sma50': ((current_price / sma_50 - 1) * 100),
                'price_vs_sma200': ((current_price / sma_200 - 1) * 100),
                'returns_3m': returns_3m,
                'volatility': volatility,
                'vix': vix_level,
                'volume_trend': volume_trend
            }

            # Scoring system
            score = 0

            # Positive factors
            if current_price > sma_50:
                score += 1
            if current_price > sma_200:
                score += 1
            if returns_3m > 5:
                score += 1
            elif returns_3m < -5:
                score -= 1

            if volatility < 15:
                score += 0.5
            elif volatility > 25:
                score -= 0.5

            if vix_level < 15:
                score += 1
            elif vix_level > 25:
                score -= 1

            if volume_trend > 10:
                score += 0.5
            elif volume_trend < -10:
                score -= 0.5

            # Normalize score to 0-1
            normalized_score = (score + 3) / 6  # Range: -3 to +3 → 0 to 1
            normalized_score = max(0, min(1, normalized_score))

            # Determine phase
            if normalized_score < 0.25:
                phase = "Recession"
                phase_color = "#E74C3C"
            elif normalized_score < 0.5:
                phase = "Accumulation"
                phase_color = "#F39C12"
            elif normalized_score < 0.75:
                phase = "Expansion"
                phase_color = "#2ECC71"
            else:
                phase = "Distribution"
                phase_color = "#3498DB"

            return {
                'phase': phase,
                'score': normalized_score,
                'indicators': indicators,
                'color': phase_color,
                'confidence': min(abs(normalized_score - 0.5) * 2, 1.0)  # Distance from center
            }

        except Exception as e:
            print(f"Error in get_market_cycle_phase: {e}")
            return self._get_default_market_cycle()

    def get_economic_cycle_phase(self, fred_api=None):
        """
        Calculate Economic Cycle Phase
        Returns: phase_name, phase_score, indicators dict
        """
        try:
            # Default values if FRED API not available
            gdp_growth = 2.5
            unemployment = 4.0
            inflation = 3.0
            pmi = 52.0

            # Try to get real data from FRED API if available
            if fred_api:
                try:
                    # Get latest economic indicators from FRED
                    # This would require FRED API implementation
                    pass
                except:
                    pass

            # Scoring logic
            indicators = {
                'gdp_growth': gdp_growth,
                'unemployment': unemployment,
                'inflation': inflation,
                'pmi': pmi
            }

            score = 0

            # GDP
            if gdp_growth > 3:
                score += 1.5
            elif gdp_growth > 2:
                score += 1
            elif gdp_growth < 0:
                score -= 1.5

            # Unemployment
            if unemployment < 4:
                score += 1
            elif unemployment > 6:
                score -= 1

            # Inflation
            if 2 < inflation < 3:
                score += 0.5
            elif inflation > 5:
                score -= 1

            # PMI
            if pmi > 55:
                score += 1
            elif pmi < 50:
                score -= 1

            # Normalize
            normalized_score = (score + 3) / 6
            normalized_score = max(0, min(1, normalized_score))

            # Determine phase
            if normalized_score < 0.25:
                phase = "Recession"
                phase_color = "#E74C3C"
            elif normalized_score < 0.5:
                phase = "Recovery"
                phase_color = "#F39C12"
            elif normalized_score < 0.75:
                phase = "Boom"
                phase_color = "#2ECC71"
            else:
                phase = "Slowdown"
                phase_color = "#3498DB"

            return {
                'phase': phase,
                'score': normalized_score,
                'indicators': indicators,
                'color': phase_color,
                'confidence': 0.7  # Lower confidence without real-time data
            }

        except Exception as e:
            print(f"Error in get_economic_cycle_phase: {e}")
            return self._get_default_economic_cycle()

    def get_liquidity_cycle_phase(self):
        """
        Calculate Liquidity Cycle Phase
        Based on Fed balance sheet, M2, and global liquidity proxies
        """
        try:
            # Use proxies: Treasury yields, Dollar index, Gold
            tlt = yf.Ticker("TLT")  # 20Y Treasury Bond ETF
            uup = yf.Ticker("UUP")  # Dollar Index
            gld = yf.Ticker("GLD")  # Gold

            tlt_hist = tlt.history(period="6mo")
            uup_hist = uup.history(period="6mo")
            gld_hist = gld.history(period="6mo")

            # Calculate trends
            tlt_return = (tlt_hist['Close'].iloc[-1] / tlt_hist['Close'].iloc[0] - 1) * 100 if not tlt_hist.empty else 0
            uup_return = (uup_hist['Close'].iloc[-1] / uup_hist['Close'].iloc[0] - 1) * 100 if not uup_hist.empty else 0
            gld_return = (gld_hist['Close'].iloc[-1] / gld_hist['Close'].iloc[0] - 1) * 100 if not gld_hist.empty else 0

            indicators = {
                'bond_trend': tlt_return,
                'dollar_trend': uup_return,
                'gold_trend': gld_return
            }

            # Scoring
            score = 0

            # Rising bonds (falling yields) = easing = +score
            if tlt_return > 5:
                score += 1.5
            elif tlt_return < -5:
                score -= 1

            # Falling dollar = easing = +score
            if uup_return < -2:
                score += 1
            elif uup_return > 5:
                score -= 1

            # Rising gold = easing = +score
            if gld_return > 10:
                score += 1
            elif gld_return < -5:
                score -= 0.5

            normalized_score = (score + 2.5) / 5
            normalized_score = max(0, min(1, normalized_score))

            if normalized_score < 0.3:
                phase = "Tightening"
                phase_color = "#E74C3C"
            elif normalized_score < 0.5:
                phase = "Neutral"
                phase_color = "#F39C12"
            elif normalized_score < 0.7:
                phase = "Easing"
                phase_color = "#2ECC71"
            else:
                phase = "Loose"
                phase_color = "#27AE60"

            return {
                'phase': phase,
                'score': normalized_score,
                'indicators': indicators,
                'color': phase_color,
                'confidence': 0.75
            }

        except Exception as e:
            print(f"Error in get_liquidity_cycle_phase: {e}")
            return self._get_default_liquidity_cycle()

    def get_sentiment_volatility_phase(self):
        """
        Calculate Sentiment + Volatility Cycle Phase
        Based on VIX and market breadth
        """
        try:
            # VIX
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="1mo")
            vix_level = vix_hist['Close'].iloc[-1] if not vix_hist.empty else 20
            vix_ma = vix_hist['Close'].mean() if not vix_hist.empty else 20

            # Market breadth: SPY vs equal-weight RSP
            spy = yf.Ticker("SPY")
            rsp = yf.Ticker("RSP")

            spy_hist = spy.history(period="3mo")
            rsp_hist = rsp.history(period="3mo")

            spy_return = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[0] - 1) * 100 if not spy_hist.empty else 0
            rsp_return = (rsp_hist['Close'].iloc[-1] / rsp_hist['Close'].iloc[0] - 1) * 100 if not rsp_hist.empty else 0

            breadth_diff = rsp_return - spy_return  # Positive = healthy breadth

            indicators = {
                'vix_level': vix_level,
                'vix_vs_ma': vix_level - vix_ma,
                'breadth_diff': breadth_diff
            }

            # Scoring
            score = 0

            # Low VIX = complacency/optimism
            if vix_level < 12:
                score += 2  # Extreme optimism
            elif vix_level < 15:
                score += 1.5  # Optimism
            elif vix_level < 20:
                score += 0.5  # Neutral
            elif vix_level < 30:
                score -= 1  # Anxiety
            else:
                score -= 2  # Panic

            # Breadth
            if breadth_diff > 2:
                score += 1
            elif breadth_diff < -2:
                score -= 0.5

            normalized_score = (score + 2.5) / 5
            normalized_score = max(0, min(1, normalized_score))

            # Phases
            if normalized_score < 0.2:
                phase = "Capitulation"
                phase_color = "#C0392B"
            elif normalized_score < 0.35:
                phase = "Panic"
                phase_color = "#E74C3C"
            elif normalized_score < 0.5:
                phase = "Anxiety"
                phase_color = "#E67E22"
            elif normalized_score < 0.65:
                phase = "Hope"
                phase_color = "#F39C12"
            elif normalized_score < 0.8:
                phase = "Optimism"
                phase_color = "#2ECC71"
            else:
                phase = "Euphoria"
                phase_color = "#27AE60"

            return {
                'phase': phase,
                'score': normalized_score,
                'indicators': indicators,
                'color': phase_color,
                'confidence': 0.85
            }

        except Exception as e:
            print(f"Error in get_sentiment_volatility_phase: {e}")
            return self._get_default_sentiment_cycle()

    def get_etf_allocation_recommendation(self, market_phase, economic_phase, liquidity_phase):
        """
        Generate ETF allocation recommendations based on cycle phases
        """
        allocations = {
            'Growth': 0,
            'Value': 0,
            'Bonds': 0,
            'Commodities': 0,
            'Cash': 0,
            'Defensive': 0
        }

        # Market cycle influence
        if market_phase == "Accumulation":
            allocations['Value'] += 30
            allocations['Bonds'] += 25
            allocations['Cash'] += 20
            allocations['Growth'] += 15
            allocations['Defensive'] += 10
        elif market_phase == "Expansion":
            allocations['Growth'] += 45
            allocations['Value'] += 20
            allocations['Commodities'] += 15
            allocations['Bonds'] += 10
            allocations['Defensive'] += 10
        elif market_phase == "Distribution":
            allocations['Defensive'] += 30
            allocations['Value'] += 25
            allocations['Bonds'] += 20
            allocations['Growth'] += 15
            allocations['Cash'] += 10
        else:  # Recession
            allocations['Bonds'] += 35
            allocations['Cash'] += 25
            allocations['Defensive'] += 20
            allocations['Value'] += 10
            allocations['Growth'] += 10

        # Economic cycle adjustment
        if economic_phase == "Boom":
            allocations['Growth'] += 10
            allocations['Commodities'] += 10
            allocations['Bonds'] -= 10
            allocations['Cash'] -= 10
        elif economic_phase == "Recession":
            allocations['Bonds'] += 15
            allocations['Defensive'] += 10
            allocations['Growth'] -= 15
            allocations['Commodities'] -= 10

        # Liquidity cycle adjustment
        if liquidity_phase == "Loose":
            allocations['Growth'] += 10
            allocations['Bonds'] -= 10
        elif liquidity_phase == "Tightening":
            allocations['Cash'] += 10
            allocations['Bonds'] += 5
            allocations['Growth'] -= 15

        # Normalize to 100%
        total = sum(allocations.values())
        if total > 0:
            allocations = {k: max(0, round(v * 100 / total, 1)) for k, v in allocations.items()}

        # ETF recommendations
        etf_map = {
            'Growth': ['QQQ', 'ARKK', 'XLK', 'VUG'],
            'Value': ['VTV', 'VYM', 'SCHD', 'IWD'],
            'Bonds': ['AGG', 'TLT', 'BND', 'VCIT'],
            'Commodities': ['DBC', 'GLD', 'USO', 'PDBC'],
            'Cash': ['SHV', 'SGOV', 'BIL'],
            'Defensive': ['XLP', 'XLU', 'VDC', 'XLRE']
        }

        # Top 3 allocations
        top_allocations = sorted(allocations.items(), key=lambda x: x[1], reverse=True)[:3]

        recommendations = []
        for category, weight in top_allocations:
            if weight > 5:
                recommendations.append({
                    'category': category,
                    'weight': weight,
                    'etfs': etf_map.get(category, [])
                })

        return {
            'allocations': allocations,
            'recommendations': recommendations
        }

    # Default fallback methods
    def _get_default_market_cycle(self):
        return {
            'phase': 'Expansion',
            'score': 0.6,
            'indicators': {},
            'color': '#2ECC71',
            'confidence': 0.5
        }

    def _get_default_economic_cycle(self):
        return {
            'phase': 'Recovery',
            'score': 0.5,
            'indicators': {},
            'color': '#F39C12',
            'confidence': 0.5
        }

    def _get_default_liquidity_cycle(self):
        return {
            'phase': 'Neutral',
            'score': 0.5,
            'indicators': {},
            'color': '#F39C12',
            'confidence': 0.5
        }

    def _get_default_sentiment_cycle(self):
        return {
            'phase': 'Hope',
            'score': 0.55,
            'indicators': {},
            'color': '#F39C12',
            'confidence': 0.5
        }
