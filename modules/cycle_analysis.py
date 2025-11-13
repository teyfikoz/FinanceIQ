"""
🌀 Cycle Analysis Engine
Core intelligence engine for analyzing market, economic, liquidity, and sentiment cycles
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .cycle_indicators import CycleIndicators


class CycleAnalysisEngine:
    """
    Main cycle intelligence engine
    Combines multiple cycle indicators to provide comprehensive analysis
    """

    def __init__(self, fred_api=None, alpha_vantage_api=None):
        self.fred_api = fred_api
        self.alpha_vantage_api = alpha_vantage_api
        self.indicators = CycleIndicators()
        self.cache = {}

    def get_comprehensive_analysis(self):
        """
        Get comprehensive cycle analysis across all dimensions
        Returns: dict with all cycle phases and composite score
        """
        try:
            # Get all cycle phases
            market_cycle = self.indicators.get_market_cycle_phase(self.fred_api)
            economic_cycle = self.indicators.get_economic_cycle_phase(self.fred_api)
            liquidity_cycle = self.indicators.get_liquidity_cycle_phase()
            sentiment_cycle = self.indicators.get_sentiment_volatility_phase()

            # Calculate composite score
            composite_score = (
                market_cycle['score'] * 0.35 +
                economic_cycle['score'] * 0.25 +
                liquidity_cycle['score'] * 0.25 +
                sentiment_cycle['score'] * 0.15
            )

            # Overall market condition
            overall_condition = self._determine_overall_condition(composite_score)

            # Get ETF recommendations
            etf_recommendations = self.indicators.get_etf_allocation_recommendation(
                market_cycle['phase'],
                economic_cycle['phase'],
                liquidity_cycle['phase']
            )

            # Generate AI commentary
            ai_commentary = self._generate_ai_commentary(
                market_cycle,
                economic_cycle,
                liquidity_cycle,
                sentiment_cycle,
                overall_condition
            )

            # Risk assessment
            risk_level = self._calculate_risk_level(
                market_cycle,
                sentiment_cycle,
                liquidity_cycle
            )

            return {
                'timestamp': datetime.now(),
                'cycles': {
                    'market': market_cycle,
                    'economic': economic_cycle,
                    'liquidity': liquidity_cycle,
                    'sentiment': sentiment_cycle
                },
                'composite_score': composite_score,
                'overall_condition': overall_condition,
                'etf_recommendations': etf_recommendations,
                'ai_commentary': ai_commentary,
                'risk_level': risk_level,
                'key_signals': self._identify_key_signals(
                    market_cycle,
                    economic_cycle,
                    liquidity_cycle,
                    sentiment_cycle
                )
            }

        except Exception as e:
            print(f"Error in get_comprehensive_analysis: {e}")
            return self._get_default_analysis()

    def _determine_overall_condition(self, composite_score):
        """Determine overall market condition from composite score"""
        if composite_score < 0.25:
            return {
                'condition': 'Bear Market / Crisis',
                'color': '#E74C3C',
                'emoji': '🐻',
                'description': 'Defensive posture recommended'
            }
        elif composite_score < 0.45:
            return {
                'condition': 'Transitional / Recovery',
                'color': '#E67E22',
                'emoji': '🔄',
                'description': 'Selective opportunities emerging'
            }
        elif composite_score < 0.65:
            return {
                'condition': 'Bull Market / Growth',
                'color': '#2ECC71',
                'emoji': '🐂',
                'description': 'Favorable risk-on environment'
            }
        else:
            return {
                'condition': 'Late Cycle / Caution',
                'color': '#3498DB',
                'emoji': '⚠️',
                'description': 'Consider taking profits'
            }

    def _calculate_risk_level(self, market_cycle, sentiment_cycle, liquidity_cycle):
        """Calculate overall market risk level"""
        risk_score = 0

        # Market cycle risk
        if market_cycle['phase'] == 'Recession':
            risk_score += 40
        elif market_cycle['phase'] == 'Distribution':
            risk_score += 30
        elif market_cycle['phase'] == 'Accumulation':
            risk_score += 15
        else:
            risk_score += 20

        # Sentiment risk (extreme readings)
        if sentiment_cycle['phase'] in ['Euphoria', 'Capitulation']:
            risk_score += 30
        elif sentiment_cycle['phase'] in ['Optimism', 'Panic']:
            risk_score += 20
        else:
            risk_score += 10

        # Liquidity risk
        if liquidity_cycle['phase'] == 'Tightening':
            risk_score += 25
        elif liquidity_cycle['phase'] == 'Neutral':
            risk_score += 15
        else:
            risk_score += 5

        # Normalize to 0-100
        risk_score = min(100, risk_score)

        if risk_score < 30:
            risk_category = 'Low Risk'
            risk_color = '#2ECC71'
        elif risk_score < 50:
            risk_category = 'Moderate Risk'
            risk_color = '#F39C12'
        elif risk_score < 70:
            risk_category = 'Elevated Risk'
            risk_color = '#E67E22'
        else:
            risk_category = 'High Risk'
            risk_color = '#E74C3C'

        return {
            'score': risk_score,
            'category': risk_category,
            'color': risk_color
        }

    def _generate_ai_commentary(self, market_cycle, economic_cycle, liquidity_cycle, sentiment_cycle, overall_condition):
        """Generate intelligent commentary based on cycle analysis"""
        commentary = []

        # Overall assessment
        commentary.append(f"**Genel Durum:** {overall_condition['condition']} {overall_condition['emoji']}")
        commentary.append(f"*{overall_condition['description']}*")
        commentary.append("")

        # Market cycle commentary
        market_phase = market_cycle['phase']
        market_conf = market_cycle['confidence']
        commentary.append(f"**Piyasa Döngüsü:** {market_phase}")

        if market_phase == "Accumulation":
            commentary.append("📈 Dip bölgede konumlanma fırsatı. Value ve defensive ETF'lere odaklanın.")
        elif market_phase == "Expansion":
            commentary.append("🚀 Büyüme fazında. Growth ve technology ETF'leri güçlü performans gösteriyor.")
        elif market_phase == "Distribution":
            commentary.append("⚠️ Zirve bölgede. Kısmi kar realizasyonu ve defensive rotasyon öneriliyor.")
        elif market_phase == "Recession":
            commentary.append("🛡️ Durgunluk fazı. Bonds, cash ve defensive pozisyonlar tercih edilmeli.")

        commentary.append(f"*Güven: {market_conf*100:.0f}%*")
        commentary.append("")

        # Economic cycle
        econ_phase = economic_cycle['phase']
        commentary.append(f"**Ekonomik Döngü:** {econ_phase}")

        if econ_phase == "Recovery":
            commentary.append("💚 Ekonomi toparlanıyor. Small cap ve cyclical sektörler avantajlı.")
        elif econ_phase == "Boom":
            commentary.append("🔥 Zirve büyüme. Commodities ve value hisseleri tercih edilebilir.")
        elif econ_phase == "Slowdown":
            commentary.append("📉 Yavaşlama başladı. Bonds ve defensive pozisyonlar güvenli liman.")
        elif econ_phase == "Recession":
            commentary.append("❄️ Durgunluk. Kaliteli tahvil ve nakit pozisyonları korunmalı.")

        commentary.append("")

        # Liquidity cycle
        liq_phase = liquidity_cycle['phase']
        commentary.append(f"**Likidite Döngüsü:** {liq_phase}")

        if liq_phase == "Loose":
            commentary.append("💰 Bol likidite ortamı. Risk varlıkları destekleniyor.")
        elif liq_phase == "Easing":
            commentary.append("💵 Para politikası gevşiyor. Risk iştahı artıyor.")
        elif liq_phase == "Neutral":
            commentary.append("⚖️ Dengeli likidite. Seçici olun.")
        elif liq_phase == "Tightening":
            commentary.append("🔒 Likidite daralıyor. Savunma moduna geçin.")

        commentary.append("")

        # Sentiment
        sent_phase = sentiment_cycle['phase']
        commentary.append(f"**Yatırımcı Duygusu:** {sent_phase}")

        if sent_phase in ["Euphoria", "Optimism"]:
            commentary.append("⚠️ Aşırı iyimserlik! Contrarian sinyaller dikkat çekiyor.")
        elif sent_phase in ["Capitulation", "Panic"]:
            commentary.append("💎 Aşırı kötümserlik! Uzun vadeli alım fırsatı oluşabilir.")
        elif sent_phase in ["Hope", "Anxiety"]:
            commentary.append("🎯 Dengeli duygusal ortam. Normal pozisyon alımları uygun.")

        return "\n".join(commentary)

    def _identify_key_signals(self, market_cycle, economic_cycle, liquidity_cycle, sentiment_cycle):
        """Identify key actionable signals"""
        signals = []

        # Extreme sentiment warnings
        if sentiment_cycle['phase'] == 'Euphoria':
            signals.append({
                'type': 'warning',
                'title': 'Aşırı İyimserlik',
                'message': 'VIX çok düşük, piyasa complacent. Kar realizasyonu düşünülebilir.',
                'icon': '⚠️'
            })
        elif sentiment_cycle['phase'] == 'Capitulation':
            signals.append({
                'type': 'opportunity',
                'title': 'Aşırı Kötümserlik',
                'message': 'Korku zirvede. Contrarian alım fırsatı yakın olabilir.',
                'icon': '💎'
            })

        # Cycle transition warnings
        if market_cycle['phase'] == 'Distribution' and economic_cycle['phase'] == 'Slowdown':
            signals.append({
                'type': 'warning',
                'title': 'Döngü Geçişi',
                'message': 'Hem piyasa hem ekonomi zirvede. Durgunluk riski artıyor.',
                'icon': '🔴'
            })

        if market_cycle['phase'] == 'Accumulation' and liquidity_cycle['phase'] in ['Easing', 'Loose']:
            signals.append({
                'type': 'opportunity',
                'title': 'Alım Fırsatı',
                'message': 'Dip bölge + bol likidite = güçlü yükseliş potansiyeli.',
                'icon': '🟢'
            })

        # Liquidity warnings
        if liquidity_cycle['phase'] == 'Tightening' and sentiment_cycle['score'] > 0.7:
            signals.append({
                'type': 'warning',
                'title': 'Likidite Riski',
                'message': 'Para politikası sıkılaşıyor ancak piyasa hala aşırı iyimser.',
                'icon': '⚠️'
            })

        return signals

    def get_historical_phases(self, lookback_months=24):
        """
        Get historical cycle phases for timeline visualization
        (Simplified version - would need historical data storage)
        """
        # This is a simplified mock - in production you'd query historical data
        phases = []

        current_date = datetime.now()
        for i in range(lookback_months):
            month_date = current_date - timedelta(days=30 * i)

            # Mock historical phases (would be real historical data)
            phases.append({
                'date': month_date,
                'market_phase': 'Expansion' if i < 12 else 'Accumulation',
                'composite_score': 0.6 if i < 12 else 0.4
            })

        return list(reversed(phases))

    def get_phase_probabilities(self):
        """
        Calculate probability of transitioning to different phases
        """
        current_analysis = self.get_comprehensive_analysis()
        current_score = current_analysis['composite_score']

        # Simple probability model based on current position
        if current_score < 0.3:
            probabilities = {
                'Remain in Recession': 40,
                'Move to Recovery': 35,
                'Stay Depressed': 25
            }
        elif current_score < 0.5:
            probabilities = {
                'Enter Expansion': 45,
                'Remain Recovery': 30,
                'Return to Recession': 25
            }
        elif current_score < 0.7:
            probabilities = {
                'Continue Expansion': 40,
                'Move to Distribution': 35,
                'Correction Risk': 25
            }
        else:
            probabilities = {
                'Enter Correction': 45,
                'Remain Distribution': 30,
                'Continued Rally': 25
            }

        return probabilities

    def _get_default_analysis(self):
        """Return default analysis if errors occur"""
        return {
            'timestamp': datetime.now(),
            'cycles': {
                'market': self.indicators._get_default_market_cycle(),
                'economic': self.indicators._get_default_economic_cycle(),
                'liquidity': self.indicators._get_default_liquidity_cycle(),
                'sentiment': self.indicators._get_default_sentiment_cycle()
            },
            'composite_score': 0.5,
            'overall_condition': {
                'condition': 'Neutral',
                'color': '#F39C12',
                'emoji': '⚖️',
                'description': 'Data unavailable'
            },
            'etf_recommendations': {
                'allocations': {},
                'recommendations': []
            },
            'ai_commentary': 'Analiz şu anda kullanılamıyor.',
            'risk_level': {
                'score': 50,
                'category': 'Moderate Risk',
                'color': '#F39C12'
            },
            'key_signals': []
        }
