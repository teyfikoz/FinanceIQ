# 📋 FinanceIQ Pro - Phase 3-4 Kalan Modüller Detaylı Plan

**Tarih:** 25 Ocak 2025
**Durum:** Design & Planning Complete - Ready for Implementation
**Versiyon:** 1.7-1.8 Roadmap

---

## Kalan 4 Modül Listesi

1. **Hedge Fund Activity Radar** (Phase 3)
2. **Institutional Event Reaction Lab** (Phase 4)
3. **Whale Sentiment Engine** (Phase 4)
4. **AI Narrative Generator** (Phase 4)

---

## 1️⃣ Hedge Fund Activity Radar

### 🎯 Amaç
13F filings, short interest, put/call ratio ve insider transactions'ı birleştirerek kurumsal aktivite haritası oluştur.

### 📊 Veri Kaynakları

| Veri Tipi | Kaynak | Frekans | Format |
|-----------|--------|---------|--------|
| 13F Filings | SEC EDGAR API | Quarterly | XML/JSON |
| Short Interest | FINRA / Yahoo Finance | Bi-weekly | CSV |
| Put/Call Ratio | CBOE | Daily | JSON |
| Insider Transactions | SEC Form 4 | Real-time | XML |
| TEFAS Flows | TEFAS API | Daily | JSON |

### 🔧 Teknik Mimari

```python
class HedgeFundActivityRadar:
    """
    Kurumsal aktivite izleme ve korelasyon motoru
    """

    def __init__(self):
        self.activity_types = ['13F', 'SHORT', 'OPTIONS', 'INSIDER']
        self.sentiment_weights = {
            '13F_BUY': +1.0,
            '13F_SELL': -1.0,
            'SHORT_INCREASE': -0.8,
            'SHORT_DECREASE': +0.6,
            'PUT_CALL_HIGH': -0.7,  # >1.0 ratio
            'PUT_CALL_LOW': +0.5,   # <0.7 ratio
            'INSIDER_BUY': +0.9,
            'INSIDER_SELL': -0.4
        }

    def calculate_activity_score(self, ticker, timeframe='30d'):
        """
        Composite activity score: -100 to +100

        Formula:
        Activity Score = Σ(Activity_Type × Weight × Magnitude)

        Returns:
            {
                'ticker': str,
                'activity_score': float,  # -100 to +100
                'signal': str,  # BULLISH/BEARISH/NEUTRAL
                'breakdown': {
                    '13f_score': float,
                    'short_score': float,
                    'options_score': float,
                    'insider_score': float
                }
            }
        """
        pass

    def detect_unusual_activity(self, lookback_days=30):
        """
        Anomaly detection for unusual institutional moves

        Criteria:
        - 13F position change >50% in one quarter
        - Short interest increase >20% in 2 weeks
        - Put/call ratio spike >2.5σ
        - Insider cluster buying (3+ insiders in 7 days)

        Returns:
            List of {
                'ticker': str,
                'activity_type': str,
                'magnitude': float,
                'z_score': float,
                'description': str
            }
        """
        pass

    def correlate_tefas_with_hedge_funds(self):
        """
        TEFAS akışları ile hedge fund aktivitesi korelasyonu

        Analiz:
        1. Teknoloji fonlarına giriş vs QQQ short interest
        2. Finansal fon çıkışı vs XLF 13F selling
        3. Lead/lag relationship (TEFAS önce mi, hedge fund önce mi?)

        Returns:
            {
                'correlation_score': float,  # -1 to +1
                'lead_lag_days': int,  # Positive = TEFAS leads
                'sector_correlations': Dict[str, float]
            }
        """
        pass

    def generate_activity_heatmap(self, tickers, date_range):
        """
        Time × Ticker heatmap for institutional activity

        Visualization:
        - X-axis: Date (daily)
        - Y-axis: Ticker
        - Color: Activity score (-100 red, 0 gray, +100 green)
        - Size: Magnitude of activity

        Returns:
            Plotly heatmap figure
        """
        pass
```

### 📈 UI Bileşenleri

```python
class HedgeFundActivityRadarUI:

    def render(self):
        # 1. Activity Score Dashboard
        st.metric("Market Activity Index", "67/100", delta="+12")

        # 2. Top Unusual Activities
        st.dataframe([
            {'Ticker': 'AAPL', 'Type': 'SHORT_SPIKE', 'Score': -85, 'Z-Score': 3.2},
            {'Ticker': 'TSLA', 'Type': 'INSIDER_BUY', 'Score': +92, 'Z-Score': 4.1}
        ])

        # 3. Activity Heatmap
        fig = px.imshow(activity_matrix, color_continuous_scale='RdYlGn')
        st.plotly_chart(fig)

        # 4. TEFAS-HedgeFund Correlation
        st.line_chart(correlation_timeseries)

        # 5. Sector Activity Breakdown
        fig = go.Figure(data=[
            go.Bar(name='13F', x=sectors, y=thirteenf_scores),
            go.Bar(name='Short', x=sectors, y=short_scores),
            go.Bar(name='Options', x=sectors, y=options_scores)
        ])
        st.plotly_chart(fig)
```

### 🤖 AI Insights (8+ Rules)

```python
def generate_hedge_fund_insights(activity_data):
    insights = []

    # Rule 1: Unusual short interest
    if activity_data['short_spike_count'] > 5:
        insights.append(
            f"⚠️ **Short Interest Spike**: {activity_data['short_spike_count']} "
            f"hissede kısa pozisyon artışı. Hedge fund'lar düşüş bekliyor!"
        )

    # Rule 2: Insider buying cluster
    if activity_data['insider_buy_clusters'] > 0:
        insights.append(
            f"🟢 **Insider Cluster**: {activity_data['insider_buy_clusters']} "
            f"hissede içeriden alım. Pozitif sinyal!"
        )

    # Rule 3: Put/Call imbalance
    if activity_data['avg_put_call_ratio'] > 1.5:
        insights.append(
            f"🔴 **Options Bearish**: Put/Call ratio {activity_data['avg_put_call_ratio']:.2f}. "
            f"Koruma alımları artıyor - düşüş beklentisi!"
        )

    # Rule 4: TEFAS-HedgeFund divergence
    if abs(activity_data['tefas_hf_correlation']) < 0.3:
        insights.append(
            f"🔀 **Retail vs Institutional Divergence**: TEFAS ve hedge fund'lar "
            f"farklı yönde. Korelasyon {activity_data['tefas_hf_correlation']:.2f}"
        )

    # Rule 5: Sector rotation signal
    if activity_data['sector_rotation_strength'] > 0.7:
        from_sector = activity_data['rotation_from']
        to_sector = activity_data['rotation_to']
        insights.append(
            f"🔄 **Sector Rotation**: {from_sector} → {to_sector}. "
            f"Hedge fund'lar pozisyon değiştiriyor!"
        )

    # Rule 6: 13F consensus with short squeeze risk
    if activity_data['13f_bullish_consensus'] and activity_data['high_short_interest']:
        insights.append(
            f"⚡ **Short Squeeze Risk**: Hedge fund'lar alırken short interest yüksek. "
            f"Squeeze potansiyeli var!"
        )

    # Rule 7: Activity spike after earnings
    if activity_data['post_earnings_activity_spike']:
        insights.append(
            f"📊 **Earnings Reaction**: Sonuçlar sonrası hedge fund aktivitesi arttı. "
            f"Consensus değişiyor olabilir."
        )

    # Rule 8: Defensive positioning
    if activity_data['defensive_rotation_score'] > 60:
        insights.append(
            f"🛡️ **Risk-Off Mode**: Hedge fund'lar defensive'e dönüyor. "
            f"Healthcare, utilities, consumer staples alımı artıyor."
        )

    return insights
```

### 📊 Örnek Çıktı

```
HEDGE FUND ACTIVITY RADAR - GÜNCEL DURUM
=========================================

Market Activity Index: 67/100 (+12 son 7 günde)
Sentiment: CAUTIOUSLY BULLISH

TOP 10 UNUSUAL ACTIVITIES:
1. AAPL - SHORT_SPIKE (-85 score, +340% in 2 weeks)
   → 5 hedge fund kısa pozisyon açtı

2. TSLA - INSIDER_BUY_CLUSTER (+92 score, 4 insider 7 günde)
   → Elon + 3 executive alım yaptı

3. NVDA - PUT_CALL_SPIKE (-78 score, ratio 2.8)
   → Koruma alımları rekor seviyede

TEFAS-HEDGEFUND CORRELATION: 0.42
→ Moderate positive correlation
→ TEFAS 3 gün önce hareket ediyor (leading indicator)

SECTOR ROTATION DETECTED:
Technology (-12%) → Healthcare (+18%)
→ Defensive rotation başladı
```

### 💰 Premium Feature (Pro Tier)

- Real-time unusual activity alerts (Telegram/Email)
- Historical activity database (5 years)
- Custom activity score weights
- API access for activity data

**Estimated Code:** ~800 lines (core + UI + tests)

---

## 2️⃣ Institutional Event Reaction Lab

### 🎯 Amaç
FOMC, TCMB, CPI, Jobs Report gibi makro olaylardan önce/sonra whale ve ETF reaksiyonlarını modellemek.

### 📅 İzlenen Olaylar

| Event Type | Frequency | Impact Level | Data Source |
|------------|-----------|--------------|-------------|
| FOMC Rate Decision | 8x/year | 🔴 Critical | Federal Reserve |
| TCMB Rate Decision | 12x/year | 🔴 Critical | TCMB |
| CPI (Inflation) | Monthly | 🟡 High | BLS |
| Jobs Report (NFP) | Monthly | 🟡 High | BLS |
| GDP Release | Quarterly | 🟢 Medium | BEA |
| Retail Sales | Monthly | 🟢 Medium | Census Bureau |
| PMI Data | Monthly | 🟢 Medium | ISM |

### 🔧 Teknik Mimari

```python
class InstitutionalEventReactionLab:
    """
    Makro olay öncesi/sonrası kurumsal davranış analizi
    """

    def __init__(self):
        self.events = self._load_economic_calendar()
        self.lookback_days = 7  # Before event
        self.lookahead_days = 7  # After event

    def analyze_event_reaction(self, event_type, event_date):
        """
        Specific event reaction analysis

        Analysis:
        1. T-7 to T-1: Pre-event positioning
        2. T: Event day reaction
        3. T+1 to T+7: Post-event adjustment

        Returns:
            {
                'event': str,
                'date': datetime,
                'pre_event_positioning': {
                    'whale_moves': List[Dict],
                    'etf_flows': Dict,
                    'sector_rotation': Dict
                },
                'event_day_reaction': {
                    'immediate_moves': List[Dict],
                    'volatility_spike': float,
                    'volume_change': float
                },
                'post_event_adjustment': {
                    'whale_rebalancing': List[Dict],
                    'new_consensus': str,  # BULLISH/BEARISH/NEUTRAL
                    'duration_days': int  # How long reaction lasted
                }
            }
        """
        pass

    def detect_positioning_patterns(self):
        """
        Historical pattern detection for event positioning

        Patterns:
        1. "Buy the Rumor, Sell the News"
        2. "Defensive Rotation Pre-FOMC"
        3. "Tech Bounce Post-CPI"
        4. "Small Cap Rally Post-Rate Cut"

        Machine Learning:
        - Random Forest classifier
        - Features: [pre_event_momentum, volatility, sentiment,
                     past_event_reactions, sector_weights]
        - Target: post_event_direction (UP/DOWN/NEUTRAL)

        Returns:
            {
                'pattern_name': str,
                'probability': float,
                'historical_accuracy': float,
                'recommended_action': str
            }
        """
        pass

    def integrate_with_scenario_sandbox(self, event, whale_portfolio):
        """
        Event + Scenario Sandbox integration

        Flow:
        1. Upcoming FOMC → Expected +0.25 bps rate hike
        2. Run Scenario Sandbox: interest_rate_change = +25
        3. Compare with historical whale reactions to +25 hikes
        4. Generate probability-weighted portfolio impact

        Returns:
            {
                'scenario': Dict,
                'expected_whale_reaction': str,
                'portfolio_impact_range': {
                    'pessimistic': float,
                    'base_case': float,
                    'optimistic': float
                },
                'recommended_hedges': List[str]
            }
        """
        pass

    def generate_event_calendar_with_signals(self, lookforward_days=90):
        """
        3-month event calendar with pre-event signals

        Visualization:
        - Calendar view (month grid)
        - Each event: icon + impact level + whale positioning signal

        Returns:
            DataFrame with columns:
            ['date', 'event_type', 'impact_level',
             'whale_positioning_signal', 'confidence']
        """
        pass
```

### 📈 UI Bileşenleri

```python
class InstitutionalEventReactionLabUI:

    def render(self):
        # 1. Upcoming Events Calendar
        st.markdown("### 📅 Upcoming Events (Next 90 Days)")

        events_df = pd.DataFrame([
            {'Date': '2025-01-31', 'Event': 'FOMC Decision',
             'Expected': '+0.25 bps', 'Whale Signal': '🔴 Defensive'},
            {'Date': '2025-02-07', 'Event': 'Jobs Report',
             'Expected': '200K', 'Whale Signal': '🟢 Neutral'},
            {'Date': '2025-02-13', 'Event': 'CPI',
             'Expected': '+3.2% YoY', 'Whale Signal': '🟡 Cautious'}
        ])

        st.dataframe(events_df, use_container_width=True)

        # 2. Historical Event Reaction Analysis
        st.markdown("### 📊 Historical FOMC Reactions")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[-7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7],
            y=[0, -2, -3, -5, -3, -1, +2, +8, +5, +3, +1, 0, -1, 0, +1],
            mode='lines+markers',
            name='Avg Whale Portfolio Return (%)'
        ))
        fig.update_layout(
            title="Pre/Post FOMC Whale Portfolio Performance",
            xaxis_title="Days Relative to Event (0 = Event Day)",
            yaxis_title="Cumulative Return (%)"
        )
        st.plotly_chart(fig, use_container_width=True)

        # 3. Pattern Detection Results
        st.markdown("### 🔍 Detected Patterns")

        patterns = [
            {'Pattern': 'Defensive Rotation Pre-FOMC',
             'Probability': '78%', 'Action': 'Reduce tech, buy utilities'},
            {'Pattern': 'Tech Bounce Post-CPI (if <3%)',
             'Probability': '65%', 'Action': 'QQQ call options'}
        ]

        for pattern in patterns:
            st.success(f"**{pattern['Pattern']}** ({pattern['Probability']} probability)")
            st.write(f"→ Recommended: {pattern['Action']}")

        # 4. Scenario Sandbox Integration
        st.markdown("### 🧪 Event Scenario Simulation")

        col1, col2 = st.columns(2)

        with col1:
            st.selectbox("Upcoming Event", ['FOMC 2025-01-31', 'CPI 2025-02-13'])
            st.number_input("Expected Rate Change (bps)", value=25)

        with col2:
            st.metric("Your Portfolio Impact", "-2.3%", delta="-$4,500")
            st.metric("Buffett's Historical Reaction", "+0.8% (defensive rotation)")

        if st.button("Run Event Simulation"):
            st.success("Simulation complete! Your portfolio would be -2.3% in base case.")
```

### 🤖 AI Insights (10+ Rules)

```python
def generate_event_reaction_insights(event_analysis):
    insights = []

    # Rule 1: Pre-event defensive positioning
    if event_analysis['pre_event_defensive_score'] > 60:
        insights.append(
            f"🛡️ **Defensive Pre-Event**: Whale'ler {event_analysis['event_type']} "
            f"öncesi defensive pozisyon alıyor. Healthcare/utilities ağırlık artırıldı."
        )

    # Rule 2: Historical pattern match
    if event_analysis['pattern_match_probability'] > 70:
        pattern = event_analysis['matched_pattern']
        insights.append(
            f"📈 **Pattern Detected**: '{pattern['name']}' pattern %{pattern['probability']} "
            f"olasılıkla tekrarlanabilir. Historical accuracy: %{pattern['accuracy']}"
        )

    # Rule 3: Event surprise factor
    if abs(event_analysis['actual_vs_expected']) > 0.5:
        insights.append(
            f"⚠️ **Surprise Factor**: Sonuç beklentiden çok farklı! "
            f"(Beklenen: {event_analysis['expected']}, Gerçekleşen: {event_analysis['actual']}). "
            f"Volatilite artabilir."
        )

    # Rule 4: Whale consensus shift
    if event_analysis['consensus_shift_detected']:
        old_consensus = event_analysis['pre_event_consensus']
        new_consensus = event_analysis['post_event_consensus']
        insights.append(
            f"🔄 **Consensus Shift**: Whale'ler {old_consensus} → {new_consensus} değişti. "
            f"Portfolio rebalancing bekleniyor."
        )

    # Rule 5: Sector rotation post-event
    if event_analysis['sector_rotation_strength'] > 0.6:
        insights.append(
            f"🔀 **Sector Rotation**: {event_analysis['from_sector']} → "
            f"{event_analysis['to_sector']}. {event_analysis['event_type']} sonrası "
            f"tipik rotation pattern."
        )

    # Rule 6: Duration prediction
    if event_analysis['estimated_reaction_duration'] > 0:
        insights.append(
            f"⏱️ **Reaction Duration**: Bu tür olaylarda ortalama {event_analysis['estimated_reaction_duration']} "
            f"gün sürer. Sabırlı olun!"
        )

    # Rule 7: Volatility spike warning
    if event_analysis['expected_volatility_increase'] > 50:
        insights.append(
            f"⚡ **Volatility Warning**: Olay sonrası volatilite %{event_analysis['expected_volatility_increase']} "
            f"artabilir. Stop-loss'ları gözden geçirin."
        )

    # Rule 8: Option market signals
    if event_analysis['option_market_positioning'] != 'NEUTRAL':
        insights.append(
            f"📊 **Options Market**: Put/call positioning {event_analysis['option_market_positioning']}. "
            f"Institutional traders {event_analysis['option_directional_bias']} beklentisinde."
        )

    # Rule 9: Small cap vs large cap divergence
    if abs(event_analysis['small_cap_reaction'] - event_analysis['large_cap_reaction']) > 5:
        insights.append(
            f"🔀 **Size Divergence**: Small cap {event_analysis['small_cap_reaction']:+.1f}%, "
            f"large cap {event_analysis['large_cap_reaction']:+.1f}%. "
            f"Risk appetite değişiyor."
        )

    # Rule 10: Bond-equity correlation
    if event_analysis['bond_equity_correlation_change'] < -0.3:
        insights.append(
            f"📉 **Bond-Equity Decoupling**: Olay sonrası tahvil-hisse korelasyonu bozuldu. "
            f"Flight to safety olabilir."
        )

    return insights
```

### 📊 Örnek Çıktı

```
EVENT REACTION ANALYSIS: FOMC 2024-12-18
========================================

Event: FOMC Rate Decision
Date: 2024-12-18
Actual: +0.25 bps (as expected)
Market Reaction: +1.2% (S&P 500)

PRE-EVENT POSITIONING (T-7 to T-1):
- Defensive Score: 68/100 (HIGH)
- Whale Moves:
  * Buffett: +3.2% healthcare, -2.1% tech
  * Dalio: +5.5% bonds, -1.8% equities
  * Wood: HOLD (no major changes)

POST-EVENT REACTION (T+1 to T+7):
- Pattern Match: "Buy the News" (72% probability)
- Consensus Shift: CAUTIOUS → NEUTRAL
- Sector Rotation: Utilities → Technology
- Duration: 3-5 days (estimated)

YOUR PORTFOLIO IMPACT:
- Base Case: -0.8%
- Pessimistic: -2.3%
- Optimistic: +1.1%

RECOMMENDED ACTIONS:
1. ✅ Hold current positions
2. 🟡 Consider reducing overweight in tech if rally extends
3. 🔴 Set stop-loss at -3% for risk management
```

### 💰 Premium Feature (Pro Tier)

- Event alerts 7 days before (email/SMS)
- Custom event tracking (earnings, M&A, etc.)
- ML-powered pattern prediction
- Automated scenario simulation pre-event

**Estimated Code:** ~700 lines

---

## 3️⃣ Whale Sentiment Engine

### 🎯 Amaç
Tüm veri kaynaklarını birleştirerek composite kurumsal duyarlılık endeksi (0-100) oluştur.

### 📊 Veri Kaynakları (Ağırlıklı)

| Source | Weight | Refresh | Description |
|--------|--------|---------|-------------|
| Whale Momentum | 30% | Weekly | Consensus buy/sell signals |
| Fund Flow Radar | 25% | Daily | TEFAS net flows |
| Hedge Fund Activity | 20% | Bi-weekly | 13F + short interest |
| Whale Correlation | 15% | Quarterly | Consensus level among whales |
| Event Reactions | 10% | Event-driven | Pre/post event positioning |

### 🔧 Teknik Mimari

```python
class WhaleSentimentEngine:
    """
    Composite institutional sentiment calculator
    """

    def __init__(self):
        self.weights = {
            'whale_momentum': 0.30,
            'fund_flow': 0.25,
            'hedge_activity': 0.20,
            'whale_correlation': 0.15,
            'event_reaction': 0.10
        }

        self.sentiment_bands = {
            (80, 100): 'EXTREME_BULLISH',
            (65, 80): 'BULLISH',
            (55, 65): 'MILDLY_BULLISH',
            (45, 55): 'NEUTRAL',
            (35, 45): 'MILDLY_BEARISH',
            (20, 35): 'BEARISH',
            (0, 20): 'EXTREME_BEARISH'
        }

    def calculate_sentiment_index(self):
        """
        Calculate composite sentiment (0-100)

        Formula:
        Sentiment = Σ(Source_Score × Weight)

        Where:
        - whale_momentum_score = (consensus_score / 100) * 100
        - fund_flow_score = normalize(net_flow, -100, +100) → 0-100
        - hedge_activity_score = activity_index (already 0-100)
        - whale_correlation_score = (avg_correlation + 1) / 2 * 100
        - event_reaction_score = defensive_score (0-100)

        Returns:
            {
                'sentiment_index': float,  # 0-100
                'sentiment_band': str,
                'breakdown': {
                    'whale_momentum': float,
                    'fund_flow': float,
                    'hedge_activity': float,
                    'whale_correlation': float,
                    'event_reaction': float
                },
                'trend': str,  # IMPROVING/STABLE/DETERIORATING
                'change_1d': float,
                'change_7d': float,
                'change_30d': float
            }
        """
        pass

    def detect_market_regime(self, sentiment_history):
        """
        Identify current market regime

        Regimes:
        1. RISK_ON: Sentiment >65, improving trend
        2. RISK_OFF: Sentiment <35, deteriorating trend
        3. ROTATION: Sentiment 45-55, high volatility
        4. UNCERTAINTY: Sentiment volatile (σ >15 over 30d)
        5. COMPLACENCY: Sentiment >70, stable (σ <5)

        Returns:
            {
                'regime': str,
                'confidence': float,
                'duration_days': int,
                'characteristics': List[str]
            }
        """
        pass

    def calculate_leading_indicator(self):
        """
        Sentiment as leading indicator for S&P 500

        Analysis:
        - Correlation: sentiment_index(t) vs SPY_return(t+7)
        - Lead time: How many days sentiment leads price?
        - Accuracy: % of correct directional predictions

        Backtesting:
        - Use 2018-2024 historical data
        - Calculate rolling correlation
        - Validate predictive power

        Returns:
            {
                'lead_time_days': int,
                'correlation': float,
                'accuracy': float,
                'current_prediction': str,  # UP/DOWN/NEUTRAL
                'confidence': float
            }
        """
        pass

    def generate_sentiment_timeseries(self, period='1y'):
        """
        Historical sentiment index time series

        Visualization:
        - Line chart: sentiment index over time
        - Colored bands: regime periods
        - Annotations: major events (FOMC, CPI, etc.)
        - Overlay: S&P 500 price (secondary y-axis)

        Returns:
            pd.DataFrame with columns:
            ['date', 'sentiment_index', 'regime',
             'sp500_price', 'major_event']
        """
        pass
```

### 📈 UI Bileşenleri

```python
class WhaleSentimentEngineUI:

    def render(self):
        # 1. Current Sentiment Index (Gauge)
        st.markdown("### 🎯 Whale Sentiment Index")

        current_sentiment = 67.3

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=current_sentiment,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Sentiment Index"},
            delta={'reference': 65.0, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 35], 'color': "lightcoral"},
                    {'range': [35, 65], 'color': "lightyellow"},
                    {'range': [65, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))

        st.plotly_chart(fig, use_container_width=True)

        # 2. Sentiment Breakdown
        st.markdown("### 📊 Sentiment Breakdown")

        breakdown = pd.DataFrame({
            'Source': ['Whale Momentum', 'Fund Flow', 'Hedge Activity',
                      'Whale Correlation', 'Event Reaction'],
            'Score': [72, 65, 58, 68, 70],
            'Weight': [30, 25, 20, 15, 10],
            'Contribution': [21.6, 16.3, 11.6, 10.2, 7.0]
        })

        st.dataframe(breakdown, use_container_width=True, hide_index=True)

        fig = go.Figure(go.Waterfall(
            x=breakdown['Source'],
            y=breakdown['Contribution'],
            text=[f"+{x:.1f}" for x in breakdown['Contribution']],
            textposition="outside"
        ))
        fig.update_layout(title="Contribution to Sentiment (Waterfall)", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # 3. Market Regime
        st.markdown("### 🌍 Market Regime")

        st.success("**RISK-ON** (67.3/100)")
        st.write("Characteristics:")
        st.write("- ✅ Improving trend (+5.2 in 7 days)")
        st.write("- ✅ High whale consensus")
        st.write("- ✅ Positive fund flows")
        st.write("- ⚠️ Moderate hedge fund activity")

        # 4. Sentiment Time Series
        st.markdown("### 📈 Sentiment History (1 Year)")

        dates = pd.date_range(end='2025-01-25', periods=365, freq='D')
        sentiment_ts = pd.DataFrame({
            'Date': dates,
            'Sentiment': np.random.normal(55, 10, 365).cumsum() / 10 + 50,
            'SP500': np.random.normal(4500, 50, 365).cumsum() / 100 + 4000
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sentiment_ts['Date'], y=sentiment_ts['Sentiment'],
                                name='Sentiment Index', yaxis='y1'))
        fig.add_trace(go.Scatter(x=sentiment_ts['Date'], y=sentiment_ts['SP500'],
                                name='S&P 500', yaxis='y2', opacity=0.5))

        fig.update_layout(
            title="Sentiment Index vs S&P 500",
            yaxis=dict(title="Sentiment Index"),
            yaxis2=dict(title="S&P 500", overlaying='y', side='right'),
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # 5. Leading Indicator Analysis
        st.markdown("### 🔮 Predictive Power")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Lead Time", "7 days", help="Sentiment leads price by 7 days")

        with col2:
            st.metric("Correlation", "0.68", help="Correlation with future returns")

        with col3:
            st.metric("Accuracy", "72%", help="Directional prediction accuracy")

        st.info("📊 **Current Prediction**: Sentiment 67.3 suggests **+2-3% upside** in next 7 days (72% confidence)")
```

### 🤖 AI Insights (6+ Rules)

```python
def generate_sentiment_insights(sentiment_data):
    insights = []

    # Rule 1: Extreme sentiment levels
    if sentiment_data['index'] > 80:
        insights.append(
            f"🔴 **Extreme Bullish**: Sentiment {sentiment_data['index']:.1f}/100. "
            f"Historically, bu seviye sonrası kısa vadeli düzeltme olasılığı %65."
        )
    elif sentiment_data['index'] < 20:
        insights.append(
            f"🟢 **Extreme Bearish**: Sentiment {sentiment_data['index']:.1f}/100. "
            f"Contrarian indicator - alım fırsatı olabilir!"
        )

    # Rule 2: Trend momentum
    if sentiment_data['change_7d'] > 10:
        insights.append(
            f"📈 **Hızlı Yükseliş**: Sentiment 7 günde +{sentiment_data['change_7d']:.1f} puan arttı. "
            f"FOMO riski var, temkinli olun."
        )
    elif sentiment_data['change_7d'] < -10:
        insights.append(
            f"📉 **Hızlı Düşüş**: Sentiment 7 günde {sentiment_data['change_7d']:.1f} puan düştü. "
            f"Panic selling sinyali, fırsat arayın."
        )

    # Rule 3: Regime shift
    if sentiment_data['regime'] != sentiment_data['previous_regime']:
        insights.append(
            f"🔄 **Regime Change**: {sentiment_data['previous_regime']} → {sentiment_data['regime']}. "
            f"Portfolio rebalancing yapın!"
        )

    # Rule 4: Divergence from price
    if sentiment_data['sentiment_vs_price_divergence'] > 0.5:
        insights.append(
            f"⚠️ **Sentiment-Price Divergence**: Sentiment yüksek ama fiyat düşük. "
            f"Ya sentiment yanlış, ya da fiyat yakında toparlanacak."
        )

    # Rule 5: Leading indicator signal
    if sentiment_data['leading_prediction'] == 'UP' and sentiment_data['prediction_confidence'] > 70:
        insights.append(
            f"🔮 **Leading Indicator Bullish**: Sentiment 7 gün sonra yukarı yönlü hareket gösteriyor "
            f"(%{sentiment_data['prediction_confidence']:.0f} confidence)."
        )

    # Rule 6: Complacency warning
    if sentiment_data['index'] > 70 and sentiment_data['volatility_30d'] < 5:
        insights.append(
            f"💤 **Complacency Risk**: Sentiment yüksek ve stabil (düşük volatilite). "
            f"Piyasa şok'a hazırlıksız olabilir - risk yönetimi önemli!"
        )

    return insights
```

### 📊 Örnek Çıktı

```
WHALE SENTIMENT ENGINE - CURRENT STATUS
=======================================

Sentiment Index: 67.3/100
Band: BULLISH
Trend: IMPROVING (+5.2 in 7 days)

BREAKDOWN:
- Whale Momentum: 72/100 (contributes +21.6)
- Fund Flow: 65/100 (contributes +16.3)
- Hedge Activity: 58/100 (contributes +11.6)
- Whale Correlation: 68/100 (contributes +10.2)
- Event Reaction: 70/100 (contributes +7.0)

MARKET REGIME: RISK-ON
Duration: 12 days
Characteristics:
- High institutional buying
- Positive fund flows
- Improving whale consensus
- Low defensive positioning

LEADING INDICATOR:
- Lead Time: 7 days
- Correlation: 0.68
- Accuracy: 72%
- Prediction: +2-3% upside in next 7 days (72% confidence)

AI INSIGHTS:
📈 Hızlı Yükseliş: Sentiment 7 günde +5.2 puan arttı. FOMO riski var.
🔮 Leading Indicator Bullish: 7 gün sonrası yukarı hareket (72% confidence).
⚠️ Sentiment yüksek - kısa vadeli düzeltme olasılığı artıyor.
```

### 💰 Premium Feature (Pro Tier)

- Daily sentiment email digest
- Custom sentiment weights
- Historical backtesting tool
- Sentiment-based trading signals

**Estimated Code:** ~500 lines

---

## 4️⃣ AI Narrative Generator

### 🎯 Amaç
Tüm modüllerden toplanan verileri kullanarak haftalık otomatik institutional intelligence raporu oluştur.

### 📄 Rapor Formatı

```
FINANCEIQ PRO - INSTITUTIONAL INTELLIGENCE REPORT
Week of January 15-21, 2025
================================================

EXECUTIVE SUMMARY
-----------------
Kurumsal sentiment bu hafta 67.3/100 ile BULLISH bantta.
Whale momentum güçlü (+5.2 puan), fund flow pozitif (₺340M giriş),
hedge fund aktivitesi orta seviyede.

Öne çıkan: 13 whale KO hissesini birlikte alıyor (consensus buy signal).
Risk: AAPL'de 16 whale satış yapıyor (consensus sell).

WHALE MOMENTUM TRACKER
----------------------
- Consensus Score: 51.3/100 (NEUTRAL)
- Top Consensus Buy: KO (13 whales, $21.4B)
- Top Consensus Sell: AAPL (16 whales, $7.4B)
- Divergences: 41 detected (high uncertainty)

ETF-WHALE LINKAGE
-----------------
- QQQ Alignment: Buffett 45%, Gates 38%, Wood 72%
- SPY Alignment: Buffett 62%, Dalio 58%
- Passive/Active Ratio (Market Avg): 55% passive, 45% active

HEDGE FUND ACTIVITY
-------------------
- Activity Index: 67/100
- Unusual Activity: TSLA insider buy cluster (4 insiders in 7 days)
- Short Interest Spike: AAPL (+340% in 2 weeks)
- TEFAS-HF Correlation: 0.42 (TEFAS leads by 3 days)

EVENT REACTIONS
---------------
Upcoming: FOMC 2025-01-31 (+0.25 bps expected)
Pre-event positioning: Defensive score 68/100 (HIGH)
Historical pattern: "Buy the News" (72% probability)

WHALE SENTIMENT ENGINE
----------------------
- Sentiment Index: 67.3/100 (BULLISH)
- Market Regime: RISK-ON (12 days duration)
- Leading Indicator: +2-3% upside predicted (72% confidence)
- Change: +5.2 in 7 days (improving trend)

ACTIONABLE INSIGHTS
-------------------
1. 🟢 BULLISH: Consensus güçlü, fund flow pozitif
2. 🎯 WATCH: KO consensus buy signal (13 whales)
3. 🔴 CAUTION: AAPL consensus sell (16 whales)
4. ⚠️ RISK: Sentiment yüksek - kısa vadeli düzeltme olasılığı
5. 🔮 PREDICTION: +2-3% upside next 7 days (72% confidence)

PORTFOLIO RECOMMENDATIONS
-------------------------
Based on current institutional intelligence:

INCREASE EXPOSURE:
- Consumer Staples (KO consensus buy)
- Healthcare (defensive pre-FOMC)

REDUCE EXPOSURE:
- Technology (AAPL consensus sell)
- High-beta growth (risk management)

HEDGING:
- Consider protective puts on QQQ (sentiment peak risk)
- Set stop-losses at -3% (volatility may increase)

---
Report generated by FinanceIQ Pro v1.8
Data sources: 13F filings, TEFAS, CBOE, SEC Form 4
Report ID: IIR-2025-W03
© 2025 FinanceIQ Pro. All rights reserved.
```

### 🔧 Teknik Mimari

```python
class AINavigatorGenerator:
    """
    Automated institutional narrative report generator
    """

    def __init__(self):
        self.report_sections = [
            'executive_summary',
            'whale_momentum',
            'etf_whale_linkage',
            'hedge_fund_activity',
            'event_reactions',
            'sentiment_engine',
            'actionable_insights',
            'portfolio_recommendations'
        ]

        self.output_formats = ['markdown', 'pdf', 'linkedin_post', 'email_html']

    def aggregate_data_from_all_modules(self):
        """
        Collect data from all 13 modules

        Data Structure:
        {
            'timestamp': datetime,
            'period': str,  # 'Week of Jan 15-21'
            'whale_momentum': Dict,
            'etf_whale_linkage': Dict,
            'hedge_fund_activity': Dict,
            'event_reactions': Dict,
            'sentiment': Dict,
            'portfolio_health': Dict,  # User's portfolio
            'fund_flows': Dict,
            'scenario_results': Dict
        }
        """
        pass

    def generate_executive_summary(self, data):
        """
        Natural language executive summary (3-5 sentences)

        Template:
        "Kurumsal sentiment bu hafta {sentiment_index}/100 ile {sentiment_band}
        bantta. Whale momentum {trend} ({change_7d} puan), fund flow {flow_direction}
        ({net_flow} giriş/çıkış), hedge fund aktivitesi {activity_level} seviyede.

        Öne çıkan: {top_consensus_buy}. Risk: {top_consensus_sell}."

        Uses:
        - Template-based generation (simple)
        - LLM-based generation (advanced, Hugging Face API)
        """
        pass

    def generate_actionable_insights(self, data):
        """
        Top 5-10 actionable insights

        Prioritization:
        1. High-confidence signals (>70%)
        2. Consensus signals (3+ whales)
        3. Unusual activity (>2σ)
        4. Leading indicator predictions
        5. Risk warnings

        Format:
        - 🟢 BULLISH: ...
        - 🔴 BEARISH: ...
        - 🎯 WATCH: ...
        - ⚠️ RISK: ...
        - 🔮 PREDICTION: ...
        """
        pass

    def generate_portfolio_recommendations(self, data, user_portfolio):
        """
        Personalized portfolio recommendations

        Analysis:
        1. User's current holdings vs whale positions
        2. User's sector allocation vs recommended
        3. User's risk level vs market regime
        4. Specific buy/sell/hold recommendations

        Output:
        {
            'increase_exposure': List[str],  # Sectors/tickers
            'reduce_exposure': List[str],
            'hedging_suggestions': List[str],
            'rebalancing_needed': bool,
            'risk_score_change': int  # -10 to +10
        }
        """
        pass

    def export_to_pdf(self, report_data):
        """
        Professional PDF export with charts

        Libraries:
        - ReportLab (Python PDF generation)
        - Matplotlib (embed charts)
        - PIL (image handling)

        Format:
        - Cover page with logo
        - Table of contents
        - Executive summary (page 1)
        - Detailed sections with charts (pages 2-8)
        - Appendix with methodology (page 9)
        - Footer with disclaimer

        Returns:
            PDF file path
        """
        pass

    def export_to_linkedin_post(self, report_data):
        """
        Optimized LinkedIn post format

        Constraints:
        - Max 3000 characters
        - Emoji-rich (visual engagement)
        - Hashtags (#FinanceIQ #InstitutionalIntelligence)
        - Call-to-action (link to full report)

        Template:
        "📊 WEEKLY INSTITUTIONAL INTELLIGENCE

        Whale Sentiment: {index}/100 ({band})
        🟢 Consensus Buy: {ticker}
        🔴 Consensus Sell: {ticker}

        Leading Indicator: {prediction}

        Full report: link.financeiq.com/IIR-2025-W03

        #FinanceIQ #InstitutionalIntelligence #SmartMoney"

        Returns:
            String (ready to post)
        """
        pass

    def schedule_weekly_generation(self):
        """
        Automated weekly report generation

        Schedule:
        - Every Sunday 18:00 UTC
        - Generate report for past week (Mon-Fri)
        - Email to Pro/Enterprise subscribers
        - Publish to web dashboard

        Tech Stack:
        - APScheduler (Python scheduling)
        - SendGrid (email delivery)
        - AWS S3 (PDF storage)
        """
        pass
```

### 📈 UI Bileşenleri

```python
class AINavigatorGeneratorUI:

    def render(self):
        st.markdown("### 🤖 AI Narrative Generator")

        st.info("""
        Tüm modüllerden toplanan verileri kullanarak otomatik rapor oluştur.
        Haftalık institutional intelligence özeti!
        """)

        # 1. Report Configuration
        col1, col2 = st.columns(2)

        with col1:
            period = st.selectbox("Rapor Dönemi", [
                "Son 7 gün",
                "Son 30 gün",
                "Bu ay",
                "Geçen ay"
            ])

        with col2:
            format_type = st.selectbox("Çıktı Formatı", [
                "📄 Markdown",
                "📕 PDF",
                "📱 LinkedIn Post",
                "📧 Email HTML"
            ])

        include_user_portfolio = st.checkbox(
            "Kendi portföyüm için özelleştirilmiş öneriler dahil et",
            value=True
        )

        # 2. Generate Button
        if st.button("🤖 Rapor Oluştur", type="primary", use_container_width=True):
            with st.spinner("AI rapor oluşturuyor..."):
                report = self._generate_report(period, format_type, include_user_portfolio)
                self._display_report(report, format_type)

        # 3. Scheduled Reports (Enterprise Feature)
        st.markdown("---")
        st.markdown("### 📅 Otomatik Raporlama (Enterprise)")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.selectbox("Frekans", ["Haftalık", "Aylık"])

        with col2:
            st.selectbox("Gün", ["Pazartesi", "Pazar"])

        with col3:
            st.time_input("Saat", value=datetime.time(18, 0))

        st.multiselect("Email Alıcıları", ["user@example.com"])

        if st.button("Otomatik Rapor Ayarla"):
            st.success("✅ Otomatik haftalık rapor ayarlandı!")

    def _display_report(self, report, format_type):
        """Display generated report"""

        if "Markdown" in format_type:
            st.markdown("---")
            st.markdown("### 📄 Generated Report")
            st.markdown(report['markdown'])

            # Download button
            st.download_button(
                label="📥 Download Markdown",
                data=report['markdown'],
                file_name=f"institutional_intelligence_{report['timestamp']}.md",
                mime="text/markdown"
            )

        elif "PDF" in format_type:
            st.success("✅ PDF oluşturuldu!")

            # Download button
            with open(report['pdf_path'], 'rb') as f:
                st.download_button(
                    label="📥 Download PDF",
                    data=f,
                    file_name=f"institutional_intelligence_{report['timestamp']}.pdf",
                    mime="application/pdf"
                )

        elif "LinkedIn" in format_type:
            st.markdown("---")
            st.markdown("### 📱 LinkedIn Post (Copy & Paste)")

            st.text_area(
                "LinkedIn Post",
                value=report['linkedin_post'],
                height=300,
                help="Copy this text and paste to LinkedIn"
            )

            st.info(f"Character count: {len(report['linkedin_post'])}/3000")

        elif "Email" in format_type:
            st.markdown("---")
            st.markdown("### 📧 Email HTML Preview")

            st.components.v1.html(report['email_html'], height=600, scrolling=True)
```

### 🤖 AI Generation Examples

**Using LLM (Hugging Face Inference API):**

```python
import requests

def generate_narrative_with_llm(data_summary):
    """
    Use Hugging Face Inference API for narrative generation

    Model: meta-llama/Llama-2-7b-chat-hf or similar
    """

    API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    prompt = f"""
    You are a financial analyst writing an institutional intelligence report.

    Data summary:
    - Sentiment Index: {data_summary['sentiment_index']}/100
    - Whale Consensus Score: {data_summary['consensus_score']}/100
    - Top Consensus Buy: {data_summary['top_buy']} ({data_summary['num_buyers']} whales)
    - Top Consensus Sell: {data_summary['top_sell']} ({data_summary['num_sellers']} whales)
    - Fund Flow: {data_summary['net_flow']} (₺)

    Write a 3-sentence executive summary in Turkish, highlighting key trends and risks.
    """

    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 150, "temperature": 0.7}
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    return response.json()[0]['generated_text']
```

### 📊 Örnek Çıktı (LinkedIn Post Format)

```
📊 HAFTALIK INSTITUTIONAL INTELLIGENCE RAPOR
Week of Jan 15-21, 2025

🎯 Whale Sentiment: 67.3/100 (BULLISH)
📈 Trend: IMPROVING (+5.2 in 7 days)

TOP SIGNALS:
🟢 Consensus Buy: KO (13 whales, $21.4B)
   → Buffett, Gates, Dalio, Ackman, Burry alıyor

🔴 Consensus Sell: AAPL (16 whales, $7.4B)
   → Geniş satış - dikkat!

🔮 LEADING INDICATOR:
+2-3% upside predicted (next 7 days, 72% confidence)

⚠️ RISK WARNING:
Sentiment yüksek - kısa vadeli düzeltme olasılığı artıyor

📄 Full Report: link.financeiq.com/IIR-2025-W03

#FinanceIQ #InstitutionalIntelligence #SmartMoney #WhaleTracking #13F #HedgeFunds

---
Powered by FinanceIQ Pro v1.8 | 14 AI-powered modules
```

### 💰 Premium Feature (Enterprise Tier)

- Automated weekly PDF reports (email delivery)
- Custom branding (logo, colors)
- White-label reports for RIA firms
- API access to narrative generation
- Unlimited report history (5 years)

**Estimated Code:** ~600 lines

---

## 📊 Implementation Priority & Timeline

### Phase 3-4 Implementation Order:

| Module | Priority | Est. Time | Dependencies |
|--------|----------|-----------|--------------|
| 3. Hedge Fund Activity Radar | HIGH | 3-4 days | Whale Momentum, ETF Tracker |
| 5. Whale Sentiment Engine | MEDIUM | 2-3 days | All Phase 3 modules |
| 4. Event Reaction Lab | MEDIUM | 3-4 days | Scenario Sandbox, Whale Analytics |
| 6. AI Narrative Generator | LOW | 4-5 days | All modules (Phase 1-4) |

**Total Estimated Time:** 12-16 days (full-time development)

---

## 🎯 Success Metrics

### KPIs for Phase 3-4 Modules:

1. **Hedge Fund Activity Radar**
   - Activity Index accuracy vs actual market moves: >65%
   - Unusual activity detection rate: >80% true positives
   - TEFAS-HF correlation: >0.4 (moderate positive)

2. **Event Reaction Lab**
   - Pattern prediction accuracy: >70%
   - Pre-event positioning detection: >75%
   - Portfolio impact estimation error: <3%

3. **Whale Sentiment Engine**
   - Leading indicator correlation: >0.65
   - Directional prediction accuracy: >70%
   - Regime detection accuracy: >80%

4. **AI Narrative Generator**
   - Report generation time: <30 seconds
   - User engagement (opens): >60%
   - Actionable insight quality rating: >4.2/5

---

## 💡 Innovation Highlights

### What Makes These Modules Unique:

1. **First-in-Market:**
   - TEFAS + Hedge Fund correlation analysis (unique to Turkey)
   - Composite sentiment index from 5 data sources
   - Automated institutional intelligence reports

2. **Technical Innovation:**
   - Real-time anomaly detection (>2σ)
   - Machine learning pattern recognition
   - LLM-powered narrative generation

3. **User Value:**
   - Actionable insights (not just data)
   - Personalized recommendations
   - Professional-grade reports

---

## 📞 Next Steps for Implementation

1. ✅ Review and approve this plan
2. ✅ Prioritize modules (recommend: 3 → 5 → 4 → 6)
3. ✅ Set up development environment (HF API, PDF libs)
4. ✅ Begin implementation (Module 3 first)
5. ✅ Iterative testing with real data
6. ✅ Documentation and integration
7. ✅ Launch Phase 3-4 (v1.7-1.8)

---

**Total Phase 3-4 Estimated Code:** ~2,600 lines
**FinanceIQ Pro Total (When Complete):** ~11,660 lines

**Target Launch Date:** Q1 2025 (February-March)

---

*Plan prepared: 25 Ocak 2025*
*Status: READY FOR IMPLEMENTATION*
*Author: FinanceIQ Pro Development Team*
