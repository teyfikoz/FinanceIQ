"""
AI Insight Engine
Generate actionable insights from portfolio and ETF data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class InsightEngine:
    """
    Generate rule-based insights for portfolio and ETF analysis

    Insights are categorized by:
    - 🟢 Positive (bullish signal)
    - 🔴 Negative (bearish signal)
    - 🟡 Neutral (informational)
    - ⚠️ Warning (risk alert)
    """

    def __init__(self):
        self.insights = []

    def generate_portfolio_insights(self, enriched_df: pd.DataFrame, summary: Dict) -> List[str]:
        """
        Generate insights for Portfolio Health Score

        Args:
            enriched_df: Enriched portfolio DataFrame
            summary: Health score summary dict

        Returns:
            List of insight strings
        """
        insights = []

        # Insight 1: Overall health assessment
        score = summary['total_score']
        if score >= 90:
            insights.append("🟢 **Mükemmel Portföy**: Skorunuz çok yüksek! Mevcut stratejinizi koruyun.")
        elif score >= 80:
            insights.append("🟢 **Sağlıklı Portföy**: Küçük optimizasyonlarla mükemmelleşebilir.")
        elif score >= 70:
            insights.append("🟡 **İyi Portföy**: Bazı alanlarda iyileştirme gerekiyor.")
        elif score >= 60:
            insights.append("⚠️ **Orta Portföy**: Dikkat gerektiren noktalar var.")
        else:
            insights.append("🔴 **Zayıf Portföy**: Acil revizyonlar gerekiyor.")

        # Insight 2: Diversification analysis
        num_stocks = len(enriched_df)
        num_sectors = enriched_df['Sector'].nunique()

        if num_stocks < 5:
            insights.append(f"⚠️ **Düşük Çeşitlendirme**: Sadece {num_stocks} hisse var. Risk yüksek - en az 7-10 hisseye çıkarın.")
        elif num_stocks >= 15:
            insights.append(f"🟢 **İyi Çeşitlendirme**: {num_stocks} hisse ve {num_sectors} sektör. Riskiniz dağıtılmış.")

        # Insight 3: Sector concentration
        sector_weights = enriched_df.groupby('Sector')['Weight'].sum().sort_values(ascending=False)
        top_sector = sector_weights.index[0]
        top_sector_weight = sector_weights.iloc[0]

        if top_sector_weight > 0.50:
            insights.append(f"🔴 **Sektör Riski**: {top_sector} sektörü portföyün %{top_sector_weight*100:.0f}'ini oluşturuyor. Çok riskli!")
        elif top_sector_weight > 0.35:
            insights.append(f"⚠️ **Sektör Konsantrasyonu**: {top_sector} ağırlığı yüksek (%{top_sector_weight*100:.0f}). Denge için diğer sektörlere ağırlık verin.")

        # Insight 4: Risk assessment
        avg_beta = (enriched_df['Beta'] * enriched_df['Weight']).sum()

        if avg_beta > 1.5:
            insights.append(f"⚠️ **Yüksek Risk**: Portföy betası {avg_beta:.2f} - piyasadan %50 daha volatil. Defansif hisseler ekleyin.")
        elif avg_beta < 0.7:
            insights.append(f"🟡 **Düşük Risk**: Portföy betası {avg_beta:.2f} - konservatif. Daha agresif büyüme için beta>1 hisseler ekleyebilirsiniz.")
        else:
            insights.append(f"🟢 **Dengeli Risk**: Portföy betası {avg_beta:.2f} - piyasa ile uyumlu.")

        # Insight 5: Momentum analysis
        positive_stocks = (enriched_df['Return_3M'] > 0).sum()
        total_stocks = len(enriched_df[enriched_df['Return_3M'].notna()])

        if total_stocks > 0:
            positive_pct = (positive_stocks / total_stocks) * 100

            if positive_pct >= 75:
                insights.append(f"🟢 **Güçlü Momentum**: Hisselerinizin %{positive_pct:.0f}'i pozitif trendde. İyi gidiyorsunuz!")
            elif positive_pct >= 50:
                insights.append(f"🟡 **Karışık Momentum**: Hisselerinizin %{positive_pct:.0f}'i pozitif. Zayıf olanları gözden geçirin.")
            else:
                insights.append(f"🔴 **Zayıf Momentum**: Hisselerinizin %{100-positive_pct:.0f}'i negatif trendde. Portföy revizyonu gerekebilir.")

        # Insight 6: Top position concentration
        top_position = enriched_df.nlargest(1, 'Weight').iloc[0]

        if top_position['Weight'] > 0.25:
            insights.append(f"⚠️ **Pozisyon Riski**: {top_position['Symbol']} portföyün %{top_position['Weight']*100:.0f}'ini oluşturuyor. Tek hisse riski çok yüksek!")

        # Insight 7: Liquidity warning
        enriched_df['Volume_USD'] = enriched_df['Avg_Volume'] * enriched_df['Price']
        low_liquidity = (enriched_df['Volume_USD'] < 100_000).sum()

        if low_liquidity > 0:
            insights.append(f"⚠️ **Likidite Riski**: {low_liquidity} hissenin işlem hacmi düşük. Satışta zorlanabilirsiniz.")

        return insights

    def generate_etf_insights(self, stock_symbol: str, holdings_df: pd.DataFrame,
                             action_signal: Dict) -> List[str]:
        """
        Generate insights for ETF Weight Tracker analysis

        Args:
            stock_symbol: Stock ticker
            holdings_df: DataFrame of funds holding this stock
            action_signal: Fund manager action signal dict

        Returns:
            List of insight strings
        """
        insights = []

        # Insight 1: ETF presence
        num_etfs = len(holdings_df)

        if num_etfs >= 10:
            insights.append(f"🟢 **Geniş ETF Kapsamı**: {stock_symbol}, {num_etfs} farklı ETF'de bulunuyor. Kurumsal ilgi yüksek.")
        elif num_etfs >= 5:
            insights.append(f"🟡 **Orta ETF Kapsamı**: {stock_symbol}, {num_etfs} ETF'de. Ana endekslerde yer alıyor.")
        else:
            insights.append(f"⚠️ **Düşük ETF Kapsamı**: {stock_symbol}, sadece {num_etfs} ETF'de. Niche veya small-cap olabilir.")

        # Insight 2: Weight concentration
        max_weight = holdings_df['weight_pct'].max()
        max_etf = holdings_df.loc[holdings_df['weight_pct'].idxmax(), 'fund_code']

        if max_weight > 10:
            insights.append(f"🟢 **Yüksek Ağırlık**: {max_etf}'da %{max_weight:.1f} ağırlıkla bulunuyor. Core holding olabilir.")
        elif max_weight > 5:
            insights.append(f"🟡 **Orta Ağırlık**: En yüksek ağırlık {max_etf}'da %{max_weight:.1f}.")
        else:
            insights.append(f"🟡 **Düşük Ağırlık**: Tüm ETF'lerde düşük ağırlıkta (max %{max_weight:.1f}).")

        # Insight 3: Fund manager action signal
        signal = action_signal['signal']
        confidence = action_signal['confidence']

        if signal == 'BULLISH' and confidence >= 70:
            insights.append(f"🟢 **Güçlü Alım Sinyali**: Fonların %{confidence:.0f}'i {stock_symbol} ağırlığını artırmış. Kurumsal yatırımcılar biriktiriyor!")
        elif signal == 'BULLISH':
            insights.append(f"🟡 **Zayıf Alım Sinyali**: Bazı fonlar {stock_symbol} ağırlığını artırmış ama net trend belirsiz.")
        elif signal == 'BEARISH' and confidence >= 70:
            insights.append(f"🔴 **Güçlü Satış Sinyali**: Fonların %{confidence:.0f}'i {stock_symbol} ağırlığını azaltmış. Kurumsal çıkış olabilir!")
        elif signal == 'BEARISH':
            insights.append(f"⚠️ **Zayıf Satış Sinyali**: Bazı fonlar {stock_symbol} ağırlığını azaltmış.")
        else:
            insights.append(f"🟡 **Nötr Sinyal**: {stock_symbol} için net bir kurumsal hareket yok.")

        # Insight 4: Top funds holding
        if len(holdings_df) >= 3:
            top3_funds = holdings_df.nlargest(3, 'weight_pct')['fund_code'].tolist()
            insights.append(f"📊 **En Büyük Holderlar**: {', '.join(top3_funds)} - bu fonların hareketlerini izleyin.")

        # Insight 5: Diversification across fund types
        sector_etfs = [etf for etf in holdings_df['fund_code'] if etf.startswith('XL')]
        broad_etfs = [etf for etf in holdings_df['fund_code'] if etf in ['SPY', 'QQQ', 'IWM', 'VTI', 'VOO']]

        if len(broad_etfs) >= 2:
            insights.append(f"🟢 **Ana Endekslerde**: {stock_symbol} major ETF'lerde ({', '.join(broad_etfs)}). Blue-chip veya mega-cap olabilir.")

        if len(sector_etfs) >= 3:
            insights.append(f"🟡 **Sektör ETF'lerinde Yaygın**: {len(sector_etfs)} farklı sektör ETF'de. Sektör lideri olabilir.")

        return insights

    def generate_weight_change_insight(self, stock_symbol: str, history_df: pd.DataFrame,
                                      fund_code: str) -> List[str]:
        """Generate insights from weight history"""
        insights = []

        if len(history_df) < 2:
            insights.append("ℹ️ **Yetersiz Veri**: Trend analizi için en az 2 veri noktası gerekli.")
            return insights

        # Calculate trend
        weights = history_df['weight_pct'].values
        dates = pd.to_datetime(history_df['report_date']).values

        # Simple linear trend
        if len(weights) >= 3:
            trend_slope = np.polyfit(range(len(weights)), weights, 1)[0]

            if trend_slope > 0.5:
                insights.append(f"📈 **Yükselen Trend**: {fund_code}, {stock_symbol} ağırlığını sürekli artırıyor. Pozitif sinyal!")
            elif trend_slope < -0.5:
                insights.append(f"📉 **Düşen Trend**: {fund_code}, {stock_symbol} ağırlığını sürekli azaltıyor. Negatif sinyal!")
            else:
                insights.append(f"➡️ **Stabil**: {fund_code}, {stock_symbol} ağırlığını koruyor.")

        # Latest change
        latest_change = history_df['weight_change'].iloc[-1]

        if pd.notna(latest_change):
            if abs(latest_change) > 2.0:
                severity = "büyük" if abs(latest_change) > 5.0 else "orta"
                direction = "artış" if latest_change > 0 else "azalış"
                insights.append(f"⚡ **Son Hareket**: {severity.capitalize()} {direction} (%{abs(latest_change):.1f}). Fon yöneticisi aktif!")

        # Volatility
        weight_std = weights.std()

        if weight_std > 2.0:
            insights.append(f"⚠️ **Yüksek Volatilite**: Ağırlık çok dalgalanıyor (std: {weight_std:.1f}). Fon yöneticisi kararsız olabilir.")

        return insights

    def generate_scenario_insights(self, result_df: pd.DataFrame, scenario: Dict,
                                   total_impact_pct: float) -> List[str]:
        """
        Generate insights for scenario simulation results

        Args:
            result_df: Scenario results DataFrame
            scenario: Scenario configuration dict
            total_impact_pct: Overall portfolio impact percentage

        Returns:
            List of insight strings
        """
        insights = []

        # Insight 1: Overall scenario impact
        if total_impact_pct < -20:
            insights.append(f"🔴 **Kritik Kayıp**: Portföyünüz bu senaryoda %{abs(total_impact_pct):.1f} değer kaybeder. Acil risk yönetimi gerekli!")
        elif total_impact_pct < -10:
            insights.append(f"⚠️ **Ciddi Kayıp**: Portföyünüz bu senaryoda %{abs(total_impact_pct):.1f} değer kaybeder. Hedge stratejileri düşünün.")
        elif total_impact_pct < -5:
            insights.append(f"🟡 **Orta Kayıp**: Portföyünüz bu senaryoda %{abs(total_impact_pct):.1f} değer kaybeder. Makul risk seviyesi.")
        elif total_impact_pct < 0:
            insights.append(f"🟡 **Hafif Kayıp**: Portföyünüz bu senaryoda %{abs(total_impact_pct):.1f} değer kaybeder. Küçük dalgalanma.")
        elif total_impact_pct < 5:
            insights.append(f"🟢 **Hafif Kazanç**: Portföyünüz bu senaryoda %{total_impact_pct:.1f} değer kazanır. Pozitif etki.")
        elif total_impact_pct < 10:
            insights.append(f"🟢 **İyi Kazanç**: Portföyünüz bu senaryoda %{total_impact_pct:.1f} değer kazanır. Güçlü performans!")
        else:
            insights.append(f"🟢 **Mükemmel Kazanç**: Portföyünüz bu senaryoda %{total_impact_pct:.1f} değer kazanır. Senaryo portföyünüze çok uygun!")

        # Insight 2: Winner/loser ratio
        positive_stocks = (result_df['Impact_Pct'] > 0).sum()
        negative_stocks = (result_df['Impact_Pct'] < 0).sum()
        total_stocks = len(result_df)

        winner_ratio = (positive_stocks / total_stocks) * 100

        if winner_ratio >= 75:
            insights.append(f"🟢 **Kazanan Ağırlıklı**: Hisselerinizin %{winner_ratio:.0f}'i bu senaryoda kazanıyor. Portföy iyi konumlanmış!")
        elif winner_ratio >= 50:
            insights.append(f"🟡 **Dengeli Etki**: Kazanan (%{winner_ratio:.0f}) ve kaybeden (%{100-winner_ratio:.0f}) hisse sayısı dengeli.")
        else:
            insights.append(f"🔴 **Kaybeden Ağırlıklı**: Hisselerinizin %{100-winner_ratio:.0f}'i bu senaryoda kaybediyor. Portföy bu senaryoya karşı savunmasız!")

        # Insight 3: Sector exposure
        sector_impacts = result_df.groupby('Sector')['Impact_Pct'].mean().sort_values()

        worst_sector = sector_impacts.index[0]
        worst_sector_impact = sector_impacts.iloc[0]

        best_sector = sector_impacts.index[-1]
        best_sector_impact = sector_impacts.iloc[-1]

        if abs(worst_sector_impact) > 10:
            insights.append(f"⚠️ **En Kötü Sektör**: {worst_sector} %{worst_sector_impact:.1f} etkileniyor. Bu sektördeki pozisyonları azaltmayı düşünün.")

        if best_sector_impact > 5:
            insights.append(f"🟢 **En İyi Sektör**: {best_sector} %{best_sector_impact:.1f} kazanıyor. Bu sektördeki pozisyonları artırabilirsiniz.")

        # Insight 4: Concentration risk
        worst_stock = result_df.nsmallest(1, 'Impact_Pct').iloc[0]

        if worst_stock['Impact_Pct'] < -20 and worst_stock['Weight'] > 0.15:
            insights.append(f"🔴 **Konsantrasyon Riski**: {worst_stock['Symbol']} hem %{abs(worst_stock['Impact_Pct']):.1f} kaybediyor hem de portföyün %{worst_stock['Weight']*100:.1f}'ini oluşturuyor. Çift risk!")

        # Insight 5: Defensive positions
        defensive_stocks = result_df[result_df['Impact_Pct'] > -2]

        if len(defensive_stocks) > 0:
            defensive_ratio = (len(defensive_stocks) / len(result_df)) * 100
            if defensive_ratio >= 50:
                insights.append(f"🟢 **Defansif Pozisyonlar**: Portföyün %{defensive_ratio:.0f}'i bu senaryodan az etkileniyor veya kazanıyor. İyi korunma!")

        # Insight 6: Scenario-specific insights
        scenario_type = scenario.get('type', '')

        if scenario_type == 'interest_rate':
            params = scenario.get('parameters', {})
            tcmb_change = params.get('tcmb_change_bp', 0)
            if tcmb_change > 0 and total_impact_pct < 0:
                insights.append(f"⚠️ **Faiz Riski**: Portföyünüz faiz artışlarına karşı duyarlı. Düşük beta veya defansif hisseler ekleyin.")
            elif tcmb_change > 0 and total_impact_pct > 0:
                insights.append(f"🟢 **Faiz Koruması**: Portföyünüz faiz artışlarından pozitif etkileniyor. İyi strateji!")

        elif scenario_type == 'currency_shock':
            params = scenario.get('parameters', {})
            usd_change = params.get('usd_try_change_pct', 0)
            if usd_change > 0 and total_impact_pct < -10:
                insights.append(f"⚠️ **Döviz Riski**: Portföyünüz dolar artışlarına çok duyarlı. İhracatçı/dolar gelirli hisseler ekleyin.")
            elif usd_change > 0 and total_impact_pct > 0:
                insights.append(f"🟢 **Döviz Koruması**: Portföyünüz dolar artışlarından faydalanıyor. İhracatçı ağırlıklı!")

        elif scenario_type == 'commodity_price':
            params = scenario.get('parameters', {})
            oil_change = params.get('oil_change_pct', 0)
            if oil_change < 0 and 'Enerji' in worst_sector:
                insights.append(f"⚠️ **Petrol Bağımlılığı**: Enerji sektörü petrol düşüşünden en çok etkileniyor. Çeşitlendirin.")

        return insights

    def generate_fund_flow_insights(
        self,
        sector_flows: pd.DataFrame,
        signals: List[Dict],
        anomalies: List[Dict]
    ) -> List[str]:
        """
        Generate insights for fund flow analysis

        Args:
            sector_flows: Sector-level flow data
            signals: Investment signals
            anomalies: Detected anomalies

        Returns:
            List of insight strings
        """
        insights = []

        # Insight 1: Overall market sentiment
        total_inflow = sector_flows[sector_flows['net_flow'] > 0]['net_flow'].sum()
        total_outflow = abs(sector_flows[sector_flows['net_flow'] < 0]['net_flow'].sum())
        net_flow = sector_flows['net_flow'].sum()

        if net_flow > total_inflow * 0.5:
            insights.append(f"🟢 **Pozitif Piyasa**: Net ₺{net_flow/1_000_000:.0f}M giriş var. Yatırımcılar risk alıyor, piyasa optimist!")
        elif net_flow < -total_outflow * 0.5:
            insights.append(f"🔴 **Negatif Piyasa**: Net ₺{abs(net_flow)/1_000_000:.0f}M çıkış var. Yatırımcılar riskten kaçıyor!")
        else:
            insights.append(f"🟡 **Nötr Piyasa**: Giriş-çıkış dengeli. Piyasa kararsız.")

        # Insight 2: Sector rotation
        if len(sector_flows) > 0:
            top_inflow_sector = sector_flows.nlargest(1, 'net_flow').iloc[0]
            top_outflow_sector = sector_flows.nsmallest(1, 'net_flow').iloc[0]

            if top_inflow_sector['net_flow'] > 0:
                insights.append(f"📈 **Sektör Rotasyonu**: Para {top_inflow_sector['sector']} sektörüne akıyor. "
                              f"₺{top_inflow_sector['net_flow']/1_000_000:.0f}M giriş tespit edildi.")

            if top_outflow_sector['net_flow'] < 0:
                insights.append(f"📉 **Sektörden Çıkış**: {top_outflow_sector['sector']} sektöründen "
                              f"₺{abs(top_outflow_sector['net_flow'])/1_000_000:.0f}M çıkış var. Dikkatli olun!")

        # Insight 3: Signal strength
        strong_bullish = [s for s in signals if s['signal'] == 'BULLISH' and s['strength'] == 'STRONG']
        strong_bearish = [s for s in signals if s['signal'] == 'BEARISH' and s['strength'] == 'STRONG']

        if len(strong_bullish) >= 2:
            sectors = ', '.join([s['sector'] for s in strong_bullish[:3]])
            insights.append(f"🟢 **Çoklu Alış Sinyali**: {sectors} sektörlerinde güçlü giriş var. "
                          f"Kurumsal yatırımcılar biriktiriyor!")

        if len(strong_bearish) >= 2:
            sectors = ', '.join([s['sector'] for s in strong_bearish[:3]])
            insights.append(f"🔴 **Çoklu Satış Sinyali**: {sectors} sektörlerinden güçlü çıkış var. "
                          f"Risk yönetimi yapın!")

        # Insight 4: Flow concentration
        total_abs_flow = sector_flows['net_flow'].abs().sum()
        if len(sector_flows) > 0 and total_abs_flow > 0:
            top_sector_flow = sector_flows.iloc[0]['net_flow']
            concentration = (abs(top_sector_flow) / total_abs_flow) * 100

            if concentration > 50:
                insights.append(f"⚠️ **Yoğunlaşmış Akış**: Toplam akışın %{concentration:.0f}'i "
                              f"{sector_flows.iloc[0]['sector']} sektöründe. Çok konsantre!")

        # Insight 5: Anomalies
        if len(anomalies) > 5:
            insights.append(f"⚠️ **Anormal Hareketler**: {len(anomalies)} anormal akış tespit edildi. "
                          f"Piyasada büyük oyuncular harekete geçiyor!")

        massive_inflows = [a for a in anomalies if a['type'] == 'massive_inflow']
        if len(massive_inflows) >= 3:
            insights.append(f"🟢 **Güçlü Kurumsal Giriş**: {len(massive_inflows)} fondan anormal giriş var. "
                          f"Smart money biriktiriyor olabilir!")

        # Insight 6: Diversification of flows
        num_positive = (sector_flows['net_flow'] > 0).sum()
        num_negative = (sector_flows['net_flow'] < 0).sum()
        total_sectors = len(sector_flows)

        if total_sectors > 0:
            positive_ratio = (num_positive / total_sectors) * 100

            if positive_ratio >= 75:
                insights.append(f"🟢 **Geniş Yükseliş**: Sektörlerin %{positive_ratio:.0f}'ine para giriyor. "
                              f"Bull market sinyali!")
            elif positive_ratio <= 25:
                insights.append(f"🔴 **Geniş Düşüş**: Sektörlerin %{100-positive_ratio:.0f}'inden para çıkıyor. "
                              f"Bear market sinyali!")

        return insights

    def generate_whale_investor_insights(
        self,
        investor_name: str,
        investor_style: str,
        whale_moves: List[Dict],
        concentration: Dict,
        sector_alloc: pd.DataFrame
    ) -> List[str]:
        """
        Generate insights for whale investor analysis

        Args:
            investor_name: Investor name
            investor_style: Investment style
            whale_moves: List of significant moves
            concentration: Portfolio concentration metrics
            sector_alloc: Sector allocation DataFrame

        Returns:
            List of insight strings
        """
        insights = []

        # Insight 1: Investment style consistency
        insights.append(f"📊 **Yatırım Stili**: {investor_name} '{investor_style}' stratejisi izliyor.")

        # Insight 2: Portfolio concentration
        conc_level = concentration['concentration_level']
        top10_conc = concentration['top10_concentration']

        if conc_level == 'Very High':
            insights.append(f"⚠️ **Yüksek Konsantrasyon**: Portföyün %{top10_conc:.0f}'i top 10 hissede. "
                          f"Çok konsantre bir strateji!")
        elif conc_level == 'High':
            insights.append(f"🟡 **Orta Konsantrasyon**: Top 10 hisse %{top10_conc:.0f}. "
                          f"Odaklanmış bir portföy.")
        else:
            insights.append(f"🟢 **Dengeli Dağılım**: Top 10 sadece %{top10_conc:.0f}. "
                          f"İyi çeşitlendirilmiş.")

        # Insight 3: Sector concentration
        if len(sector_alloc) > 0:
            top_sector = sector_alloc.iloc[0]

            if top_sector['total_weight'] > 50:
                insights.append(f"⚠️ **Sektör Riski**: {top_sector['sector']} %{top_sector['total_weight']:.0f} ağırlıkta. "
                              f"Tek sektöre çok bağımlı!")
            elif top_sector['total_weight'] > 30:
                insights.append(f"🟡 **Sektör Odağı**: {top_sector['sector']} en yüksek ağırlık (%{top_sector['total_weight']:.0f}). "
                              f"Bu sektöre inancı yüksek.")

        # Insight 4: Whale moves analysis
        if whale_moves:
            strong_buys = [m for m in whale_moves if m['signal'] in ['STRONG_BUY', 'BUY']]
            strong_sells = [m for m in whale_moves if m['signal'] in ['STRONG_SELL', 'SELL']]

            if len(strong_buys) > len(strong_sells) * 2:
                insights.append(f"🟢 **Aktif Alım Dönemi**: {len(strong_buys)} yeni/artırılan vs {len(strong_sells)} azaltılan pozisyon. "
                              f"{investor_name} fırsat görüyor!")
            elif len(strong_sells) > len(strong_buys) * 2:
                insights.append(f"🔴 **Pozisyon Azaltma**: {len(strong_sells)} azaltma vs {len(strong_buys)} artırma. "
                              f"Risk almaktan kaçınıyor!")
            else:
                insights.append(f"🟡 **Dengeli Hareket**: {len(strong_buys)} alım, {len(strong_sells)} satım. "
                              f"Portföy rebalancing yapıyor.")

            # Top whale move
            if whale_moves:
                top_move = whale_moves[0]

                if top_move['signal'] in ['STRONG_BUY', 'BUY']:
                    insights.append(f"🎯 **En Büyük Alım**: {top_move['ticker']} ({top_move['sector']}) - "
                                  f"{top_move['description']}. "
                                  f"Bu hisseye güveni çok yüksek!")
                else:
                    insights.append(f"🎯 **En Büyük Satış**: {top_move['ticker']} ({top_move['sector']}) - "
                                  f"{top_move['description']}. "
                                  f"Bu hisseden uzaklaşıyor!")

        # Insight 5: Specific investor patterns
        if 'Buffett' in investor_name:
            value_sectors = ['Financials', 'Energy', 'Consumer']
            value_weight = sector_alloc[sector_alloc['sector'].isin(value_sectors)]['total_weight'].sum()

            if value_weight > 60:
                insights.append(f"🐘 **Buffett DNA'sı**: Value sektörleri (%{value_weight:.0f}) dominant. "
                              f"Klasik Buffett stratejisi!")

        elif 'Wood' in investor_name:
            tech_weight = sector_alloc[sector_alloc['sector'] == 'Technology']['total_weight'].sum()

            if tech_weight > 70:
                insights.append(f"🚀 **ARK DNA'sı**: Teknoloji %{tech_weight:.0f}. "
                              f"Disruptive innovation odağı net!")

        elif 'Dalio' in investor_name:
            num_sectors = len(sector_alloc)

            if num_sectors >= 5:
                insights.append(f"🌊 **All Weather**: {num_sectors} farklı sektör. "
                              f"Ray Dalio'nun diversifikasyon prensibi!")

        # Insight 6: Action recommendations
        if whale_moves:
            buy_tickers = [m['ticker'] for m in whale_moves if m['signal'] in ['STRONG_BUY', 'BUY']][:3]

            if buy_tickers:
                insights.append(f"💡 **Takip Listesi**: {investor_name} bu hisseleri alıyor: {', '.join(buy_tickers)}. "
                              f"Araştırmaya değer!")

        return insights

    def generate_whale_correlation_insights(
        self,
        correlation_matrix: pd.DataFrame,
        top_pairs: List[Dict],
        clusters: List[List[str]],
        num_investors: int
    ) -> List[str]:
        """
        Generate insights for whale correlation analysis

        Args:
            correlation_matrix: NxN correlation matrix
            top_pairs: Top correlated pairs
            clusters: Identified clusters
            num_investors: Number of investors analyzed

        Returns:
            List of insight strings
        """
        insights = []

        # Overall market sentiment
        if correlation_matrix is not None and len(correlation_matrix) > 0:
            # Get upper triangle values (excluding diagonal)
            upper_triangle = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)]
            avg_correlation = upper_triangle.mean()

            if avg_correlation >= 0.6:
                insights.append(
                    f"🟢 **Yüksek Konsensus**: Whale yatırımcılar arasında ortalama {avg_correlation:.2f} "
                    f"korelasyon var. Piyasada güçlü bir fikir birliği söz konusu!"
                )
            elif avg_correlation >= 0.4:
                insights.append(
                    f"🟡 **Orta Konsensus**: Whale korelasyonu {avg_correlation:.2f}. "
                    f"Bazı yatırımcılar benzer, bazıları farklı yönde hareket ediyor."
                )
            else:
                insights.append(
                    f"🔴 **Düşük Konsensus**: Ortalama korelasyon {avg_correlation:.2f}. "
                    f"Whale'ler farklı stratejiler izliyor - piyasa belirsiz!"
                )

        # Top correlated pair analysis
        if top_pairs and len(top_pairs) > 0:
            top_pair = top_pairs[0]
            if top_pair['correlation'] >= 0.8:
                insights.append(
                    f"🤝 **Güçlü İkili**: {top_pair['investor_a']} ve {top_pair['investor_b']} "
                    f"arasında {top_pair['correlation']:.2f} korelasyon. Neredeyse aynı pozisyonlar!"
                )
            elif top_pair['correlation'] >= 0.6:
                insights.append(
                    f"💡 **Benzer Stratejiler**: {top_pair['investor_a']} ve {top_pair['investor_b']} "
                    f"benzer yönde hareket ediyor ({top_pair['correlation']:.2f})"
                )

        # Cluster analysis
        if clusters and len(clusters) > 0:
            significant_clusters = [c for c in clusters if len(c) > 2]

            if significant_clusters:
                largest_cluster = significant_clusters[0]
                insights.append(
                    f"🎯 **Dominant Küme**: {', '.join(largest_cluster)} aynı stratejide. "
                    f"Bu grup piyasayı yönlendirebilir!"
                )

            if len(clusters) == 1 and len(clusters[0]) == num_investors:
                insights.append(
                    f"🟢 **Tam Konsensus**: Tüm whale'ler aynı kümede! "
                    f"Güçlü bir yön birliği var."
                )
            elif len(clusters) >= num_investors - 1:
                insights.append(
                    f"⚠️ **Fragmente Piyasa**: Her yatırımcı farklı strateji izliyor. "
                    f"Belirsizlik yüksek - dikkatli olun!"
                )

        # Divergence warnings
        if top_pairs and len(top_pairs) > 0:
            divergent_pairs = [p for p in top_pairs if p['correlation'] < 0.2]
            if divergent_pairs:
                div_pair = divergent_pairs[0]
                insights.append(
                    f"⚠️ **Strateji Çatışması**: {div_pair['investor_a']} ve {div_pair['investor_b']} "
                    f"tamamen farklı yönde ({div_pair['correlation']:.2f}). "
                    f"Kim haklı çıkacak?"
                )

        # Actionable recommendations
        if correlation_matrix is not None and len(correlation_matrix) > 0:
            if avg_correlation >= 0.6:
                insights.append(
                    f"💡 **Yatırım Önerisi**: Yüksek whale konsensusü var. "
                    f"En yüksek korelasyonlu grubu takip etmek iyi bir strateji olabilir."
                )
            elif avg_correlation < 0.3:
                insights.append(
                    f"💡 **Yatırım Önerisi**: Düşük konsensus dönemlerinde kendi araştırmanıza "
                    f"güvenin. Whale'ler de belirsiz!"
                )

        # Style-based insights
        if clusters and len(clusters) > 0:
            for cluster in clusters:
                if len(cluster) >= 2:
                    # Check if value investors cluster together
                    value_investors = [name for name in cluster if 'Buffett' in name or 'Dalio' in name or 'Gates' in name]
                    growth_investors = [name for name in cluster if 'Wood' in name or 'Ackman' in name]

                    if len(value_investors) >= 2:
                        insights.append(
                            f"📊 **Value Cluster**: {', '.join(value_investors)} birlikte hareket ediyor. "
                            f"Value hisseler yükseliş yaşayabilir!"
                        )

                    if len(growth_investors) >= 2:
                        insights.append(
                            f"🚀 **Growth Cluster**: {', '.join(growth_investors)} aynı yönde. "
                            f"Disruptive tech hisselere ilgi artabilir!"
                        )

        return insights

    def generate_whale_momentum_insights(
        self,
        consensus_indicator: Dict,
        consensus_buys: List[Dict],
        consensus_sells: List[Dict],
        divergences: List[Dict],
        top_momentum: pd.DataFrame
    ) -> List[str]:
        """
        Generate insights for whale momentum analysis

        Args:
            consensus_indicator: Institutional consensus metrics
            consensus_buys: List of consensus buy signals
            consensus_sells: List of consensus sell signals
            divergences: List of divergence signals
            top_momentum: Top momentum stocks DataFrame

        Returns:
            List of insight strings
        """
        insights = []

        # Consensus indicator analysis
        if consensus_indicator:
            score = consensus_indicator.get('consensus_score', 50)
            sentiment = consensus_indicator.get('market_sentiment', 'NEUTRAL')
            num_buys = consensus_indicator.get('num_buys', 0)
            num_sells = consensus_indicator.get('num_sells', 0)

            if score >= 70:
                insights.append(
                    f"🟢 **Güçlü Kurumsal Alım**: Consensus score {score:.0f}/100. "
                    f"Whale'ler net alıcı pozisyonunda ({num_buys} alım vs {num_sells} satım)!"
                )
            elif score >= 60:
                insights.append(
                    f"📈 **Pozitif Momentum**: Score {score:.0f}/100. "
                    f"Kurumsal para giriyor ama henüz güçlü değil."
                )
            elif score >= 40:
                insights.append(
                    f"⚠️ **Nötr Piyasa**: Score {score:.0f}/100. "
                    f"Whale'ler kararsız - yön bekleniyor."
                )
            elif score >= 30:
                insights.append(
                    f"📉 **Negatif Momentum**: Score {score:.0f}/100. "
                    f"Kurumsal satış baskısı artıyor."
                )
            else:
                insights.append(
                    f"🔴 **Güçlü Kurumsal Satış**: Score {score:.0f}/100. "
                    f"Whale'ler net satıcı ({num_sells} satım vs {num_buys} alım)!"
                )

        # Consensus buys analysis
        if consensus_buys and len(consensus_buys) > 0:
            top_buy = consensus_buys[0]

            if top_buy['num_buyers'] >= 5:
                insights.append(
                    f"🎯 **Güçlü Konsensus**: {top_buy['ticker']} hissesini {top_buy['num_buyers']} whale birlikte alıyor! "
                    f"({', '.join(top_buy['buyer_whales'][:3])}...)"
                )
            elif top_buy['num_buyers'] >= 3:
                insights.append(
                    f"💡 **Orta Konsensus**: {top_buy['ticker']} için {top_buy['num_buyers']} whale alıcı. "
                    f"Araştırmaya değer."
                )

            # Multiple strong buys
            strong_buys = [b for b in consensus_buys if b['num_buyers'] >= 4]
            if len(strong_buys) >= 3:
                tickers = [b['ticker'] for b in strong_buys[:3]]
                insights.append(
                    f"🟢 **Geniş Konsensus**: {len(strong_buys)} hisse için 4+ whale alıcı. "
                    f"Top 3: {', '.join(tickers)}"
                )

        # Consensus sells analysis
        if consensus_sells and len(consensus_sells) > 0:
            top_sell = consensus_sells[0]

            if top_sell['num_sellers'] >= 5:
                insights.append(
                    f"⚠️ **Kuvvetli Satış Sinyali**: {top_sell['ticker']} hissesini {top_sell['num_sellers']} whale birlikte satıyor! "
                    f"Dikkat!"
                )
            elif top_sell['num_sellers'] >= 3:
                insights.append(
                    f"🔴 **Satış Konsensus**: {top_sell['ticker']} için {top_sell['num_sellers']} whale satıcı."
                )

        # Divergence analysis
        if divergences and len(divergences) > 0:
            top_divergence = divergences[0]

            insights.append(
                f"🔀 **Whale Çatışması**: {top_divergence['ticker']} için {top_divergence['num_buyers']} alıcı, "
                f"{top_divergence['num_sellers']} satıcı. Volatilite artabilir!"
            )

            if len(divergences) >= 5:
                insights.append(
                    f"⚠️ **Yüksek Belirsizlik**: {len(divergences)} hissede whale divergence var. "
                    f"Piyasa yön arıyor."
                )

        # Top momentum analysis
        if top_momentum is not None and len(top_momentum) > 0:
            top_stock = top_momentum.iloc[0]

            if top_stock['momentum_score'] >= 0.8:
                insights.append(
                    f"⚡ **Maksimum Momentum**: {top_stock['ticker']} momentum score {top_stock['momentum_score']:.2f}. "
                    f"{top_stock['num_whales']} whale involved!"
                )
            elif top_stock['momentum_score'] >= 0.6:
                insights.append(
                    f"📈 **Güçlü Momentum**: {top_stock['ticker']} için {top_stock['momentum_score']:.2f} momentum. "
                    f"Takip et!"
                )

        # Actionable recommendations
        if consensus_indicator:
            score = consensus_indicator.get('consensus_score', 50)

            if score >= 65 and consensus_buys:
                top_tickers = [b['ticker'] for b in consensus_buys[:3]]
                insights.append(
                    f"💡 **Yatırım Önerisi**: Güçlü kurumsal alım var. "
                    f"Watchlist: {', '.join(top_tickers)}"
                )
            elif score <= 35 and consensus_sells:
                insights.append(
                    f"💡 **Risk Yönetimi**: Güçlü kurumsal satış var. "
                    f"Portföy riskini azaltmayı düşünün."
                )
            elif 45 <= score <= 55 and divergences:
                insights.append(
                    f"💡 **Bekleme Modu**: Whale'ler kararsız. "
                    f"Net sinyal gelene kadar sabırlı olun."
                )

        # Market regime detection
        if consensus_indicator and consensus_buys and consensus_sells:
            buy_strength = len([b for b in consensus_buys if b['num_buyers'] >= 4])
            sell_strength = len([s for s in consensus_sells if s['num_sellers'] >= 4])

            if buy_strength > sell_strength * 2:
                insights.append(
                    f"🟢 **Risk-On Modu**: Alım konsensusü çok güçlü. "
                    f"Growth/momentum stratejileri favori."
                )
            elif sell_strength > buy_strength * 2:
                insights.append(
                    f"🔴 **Risk-Off Modu**: Satış konsensusü dominant. "
                    f"Defensive/cash stratejiler favori."
                )

        return insights

    def format_insight_card(self, insight: str, card_type: str = "info") -> str:
        """
        Format insight as Streamlit-compatible markdown card

        Args:
            insight: Insight text
            card_type: "success", "warning", "error", "info"
        """
        colors = {
            "success": "#d4edda",
            "warning": "#fff3cd",
            "error": "#f8d7da",
            "info": "#d1ecf1"
        }

        border_colors = {
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "info": "#17a2b8"
        }

        # Auto-detect card type from emoji
        if insight.startswith("🟢"):
            card_type = "success"
        elif insight.startswith("⚠️") or insight.startswith("🟡"):
            card_type = "warning"
        elif insight.startswith("🔴"):
            card_type = "error"

        bg_color = colors.get(card_type, colors["info"])
        border_color = border_colors.get(card_type, border_colors["info"])

        return f"""
<div style='padding: 12px; margin: 8px 0; background: {bg_color};
     border-left: 4px solid {border_color}; border-radius: 4px;'>
    {insight}
</div>
"""


def generate_all_insights(data_type: str, **kwargs) -> List[str]:
    """
    Convenience function to generate insights

    Args:
        data_type: "portfolio" or "etf" or "weight_history" or "scenario"
        **kwargs: Data for insight generation
    """
    engine = InsightEngine()

    if data_type == "portfolio":
        return engine.generate_portfolio_insights(
            kwargs.get('enriched_df'),
            kwargs.get('summary')
        )
    elif data_type == "etf":
        return engine.generate_etf_insights(
            kwargs.get('stock_symbol'),
            kwargs.get('holdings_df'),
            kwargs.get('action_signal')
        )
    elif data_type == "weight_history":
        return engine.generate_weight_change_insight(
            kwargs.get('stock_symbol'),
            kwargs.get('history_df'),
            kwargs.get('fund_code')
        )
    elif data_type == "scenario":
        return engine.generate_scenario_insights(
            kwargs.get('result_df'),
            kwargs.get('scenario'),
            kwargs.get('total_impact_pct')
        )
    elif data_type == "fund_flow":
        return engine.generate_fund_flow_insights(
            kwargs.get('sector_flows'),
            kwargs.get('signals'),
            kwargs.get('anomalies')
        )
    elif data_type == "whale_investor":
        return engine.generate_whale_investor_insights(
            kwargs.get('investor_name'),
            kwargs.get('investor_style'),
            kwargs.get('whale_moves'),
            kwargs.get('concentration'),
            kwargs.get('sector_alloc')
        )
    elif data_type == "whale_correlation":
        return engine.generate_whale_correlation_insights(
            kwargs.get('correlation_matrix'),
            kwargs.get('top_pairs'),
            kwargs.get('clusters'),
            kwargs.get('num_investors')
        )
    elif data_type == "whale_momentum":
        return engine.generate_whale_momentum_insights(
            kwargs.get('consensus_indicator'),
            kwargs.get('consensus_buys'),
            kwargs.get('consensus_sells'),
            kwargs.get('divergences'),
            kwargs.get('top_momentum')
        )
    else:
        return []
