## 🚀 FinanceIQ Pro - Phase 2 Build Prompt
### Comprehensive Development Plan: Scenario Sandbox + Fund Flow Radar + Factor Exposure

---

## 🎯 MISSION STATEMENT

Transform FinanceIQ Pro from "portfolio analytics tool" → **"Bloomberg-level decision intelligence platform"**

**Core Value Proposition:**
> "Yatırımcılar sadece 'ne oldu' değil, 'ne olabilir' ve 'ne yapmalıyım' sorularına cevap alsın."

---

## 📦 Phase 2 Modules (6-8 Hafta)

| Module | Priority | Time | Impact | Revenue Potential |
|--------|----------|------|--------|------------------|
| **Scenario Sandbox** | 🔥 HIGH | 2 hafta | 🎯🎯🎯🎯 | Premium feature |
| **Fund Flow Radar** | 🔥 HIGH | 2-3 hafta | 🎯🎯🎯🎯🎯 | Premium feature |
| **Factor Exposure Analyzer** | 🟡 MEDIUM | 2 hafta | 🎯🎯🎯 | Premium feature |
| **Smart Alerts Engine** | 🟢 LOW | 1 hafta | 🎯🎯 | Notification upsell |
| **Performance Dashboard** | 🔥 HIGH | 1 hafta | 🎯🎯 | System health |

---

## 🧩 MODULE 1: Scenario Sandbox

### **Concept:**
"What-if" analizi - Kullanıcı makro senaryolar oluşturur, portföyüne etkisini görür.

### **Use Cases:**
1. **TCMB Faiz Artışı**: "Faiz 500bp artarsa BIST %12 düşer → Portföyüm ne olur?"
2. **USD/TRY Şoku**: "Dolar 35₺'ye çıkarsa → En çok etkilenen hisselerim?"
3. **Petrol Fiyat Artışı**: "Petrol $120 olursa → TUPRS, PETKM ne olur?"
4. **FED Faiz İndirimi**: "FED 50bp indirirse → Teknoloji hisselerim?"

### **Data Sources:**

#### **Historical Correlations:**
```python
# TCMB Faiz vs BIST Sektörleri (2018-2024 tarihi data)
data_sources = {
    'tcmb_rates': 'TCMB API (https://evds2.tcmb.gov.tr/)',
    'bist_sectors': 'yfinance (XUSIN, XUMAL, XBANK, etc.)',
    'usd_try': 'FRED API (DEXU STR)',
    'oil_price': 'yfinance (CL=F, BZ=F)',
    'gold_price': 'yfinance (GC=F, XAUUSD=X)'
}
```

#### **Correlation Coefficients:**
```python
# Örnek: TCMB faiz vs BIST sektörleri
correlations = {
    'BIST_Finans': -0.68,    # Negatif korelasyon
    'BIST_Sanayi': -0.52,
    'BIST_Teknoloji': -0.45,
    'BIST_Tüketim': -0.38,
    'USD/TRY': 0.82          # Pozitif korelasyon
}
```

### **Technical Implementation:**

#### **File:** `modules/scenario_sandbox.py`

```python
class ScenarioSandbox:
    """
    Macro scenario simulator for portfolio impact analysis
    """

    SCENARIO_TYPES = {
        'interest_rate': {
            'name': 'Faiz Oranı Değişimi',
            'parameters': ['tcmb_change_bp', 'fed_change_bp'],
            'affected_assets': ['BIST', 'USD/TRY', 'bonds']
        },
        'currency_shock': {
            'name': 'Döviz Kuru Şoku',
            'parameters': ['usd_try_target', 'eur_try_target'],
            'affected_assets': ['BIST_exporters', 'BIST_importers']
        },
        'commodity_price': {
            'name': 'Emtia Fiyat Değişimi',
            'parameters': ['oil_price_target', 'gold_price_target'],
            'affected_assets': ['energy', 'mining', 'gold']
        },
        'equity_market_shock': {
            'name': 'Piyasa Şoku',
            'parameters': ['sp500_change_pct', 'bist100_change_pct'],
            'affected_assets': ['all']
        }
    }

    def __init__(self):
        self.correlation_matrix = self._load_correlations()

    def create_scenario(self, scenario_type: str, **params) -> Dict:
        """
        Create scenario and calculate expected portfolio impact

        Args:
            scenario_type: One of SCENARIO_TYPES keys
            **params: Scenario-specific parameters

        Returns:
            Dict with scenario results
        """
        pass

    def simulate_portfolio_impact(
        self,
        portfolio: pd.DataFrame,
        scenario: Dict
    ) -> pd.DataFrame:
        """
        Calculate portfolio impact based on scenario

        Uses historical correlations to estimate changes
        """
        pass

    def stress_test_portfolio(
        self,
        portfolio: pd.DataFrame,
        scenarios: List[Dict]
    ) -> pd.DataFrame:
        """
        Run multiple scenarios (best/base/worst case)
        """
        pass
```

### **UI Design:**

```python
# File: modules/scenario_sandbox_ui.py

def render_scenario_sandbox():
    st.title("🧪 Scenario Sandbox")

    # Scenario selector
    scenario_type = st.selectbox(
        "Senaryo Türü",
        options=list(ScenarioSandbox.SCENARIO_TYPES.keys()),
        format_func=lambda x: ScenarioSandbox.SCENARIO_TYPES[x]['name']
    )

    # Dynamic parameter inputs based on scenario type
    if scenario_type == 'interest_rate':
        tcmb_change = st.slider(
            "TCMB Faiz Değişimi (bp)",
            min_value=-500,
            max_value=1000,
            value=0,
            step=50
        )

    # Run simulation button
    if st.button("🎯 Simülasyonu Çalıştır"):
        sandbox = ScenarioSandbox()
        results = sandbox.simulate_portfolio_impact(portfolio, scenario)

        # Display results
        # - Portfolio value change
        # - Top winners/losers
        # - Risk metrics (VaR, Expected Shortfall)
```

### **Visualizations:**

1. **Waterfall Chart**: Portfolio value change by position
2. **Heatmap**: Sector impact matrix
3. **Gauge**: Portfolio VaR (Value at Risk)
4. **Scatter**: Risk vs Return in scenario

---

## 🧩 MODULE 2: Fund Flow Radar

### **Concept:**
"Paranın nereye aktığını gör" - TEFAS + ETF bazlı para akışı analizi.

### **Data Sources:**

#### **TEFAS (Turkish Funds):**
```python
# TEFAS API/Scraping
url = "https://www.tefas.gov.tr/api/DB/BindHistoryAllocation"
params = {
    'fontip': 'YAT',  # YAT = Hisse Fonları
    'sfontur': '',
    'bastarih': '2024-01-01',
    'bittarih': '2024-12-31'
}

# Parse response → daily fund sizes
# Calculate: Net Flow = Size_today - Size_yesterday - (Return% * Size_yesterday)
```

#### **US ETFs:**
```python
# Use existing ETF Weight Tracker data
# Aggregate by sector
```

### **Technical Implementation:**

#### **File:** `modules/fund_flow_radar.py`

```python
class FundFlowRadar:
    """
    Track money flows into/out of funds and sectors
    """

    def fetch_tefas_flows(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch daily TEFAS fund sizes"""
        pass

    def calculate_net_flows(self, fund_sizes: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate net flows (excluding performance)

        Flow = AUM_t - AUM_{t-1} - (Return_{t-1} * AUM_{t-1})
        """
        pass

    def aggregate_sector_flows(
        self,
        flows: pd.DataFrame,
        period: str = '7d'
    ) -> pd.DataFrame:
        """
        Aggregate flows by sector

        Returns:
            sector, net_flow, num_funds, avg_flow
        """
        pass

    def create_flow_sankey(self, flows: pd.DataFrame) -> go.Figure:
        """
        Sankey diagram: Source → Sectors → Funds

        Layers:
        1. Yatırımcılar (Source)
        2. Sektörler (Middle)
        3. Fonlar (Target)
        """
        pass

    def detect_flow_anomalies(
        self,
        flows: pd.DataFrame,
        threshold: float = 2.0
    ) -> List[Dict]:
        """
        Detect unusual flow patterns (>2 std dev)
        """
        pass
```

### **UI Design:**

```python
def render_fund_flow_radar():
    st.title("📡 Fund Flow Radar")

    # Period selector
    period = st.selectbox(
        "Analiz Dönemi",
        options=['7d', '30d', '90d', 'ytd'],
        format_func=lambda x: {
            '7d': 'Son 7 Gün',
            '30d': 'Son 30 Gün',
            '90d': 'Son 3 Ay',
            'ytd': 'Yıl Başından Beri'
        }[x]
    )

    # Calculate flows
    radar = FundFlowRadar()
    flows = radar.aggregate_sector_flows(period=period)

    # Display top gainers/losers
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⬆️ En Çok Para Giren Sektörler")
        top_inflows = flows.nlargest(5, 'net_flow')
        # Display bar chart + table

    with col2:
        st.markdown("### ⬇️ En Çok Para Çıkan Sektörler")
        top_outflows = flows.nsmallest(5, 'net_flow')
        # Display bar chart + table

    # Sankey diagram
    st.markdown("### 🔀 Para Akışı Haritası")
    fig_sankey = radar.create_flow_sankey(flows)
    st.plotly_chart(fig_sankey)

    # Insights
    st.markdown("### 💡 Sinyal ve Yorumlar")
    # Auto-generate insights using InsightEngine
```

### **Visualizations:**

1. **Sankey Diagram**: Money flow (Investors → Sectors → Funds)
2. **Bar Chart**: Top inflow/outflow sectors
3. **Heatmap**: Flow intensity by sector + time
4. **Time Series**: Cumulative flows over time

---

## 🧩 MODULE 3: Factor Exposure Analyzer

### **Concept:**
"Portföyün faktör risklerini ölç" - Profesyonel fon yöneticilerinin kullandığı analiz.

### **Factors:**

1. **Value** - P/B, P/E düşük hisseler
2. **Growth** - Revenue/Earnings growth yüksek
3. **Momentum** - Son 6-12 ay performans
4. **Volatility** - Risk/Beta
5. **Size** - Market cap (small vs large)
6. **Quality** - ROE, Debt/Equity

### **Technical Implementation:**

#### **File:** `modules/factor_exposure.py`

```python
class FactorExposureAnalyzer:
    """
    Calculate portfolio factor exposures

    Based on Fama-French factor models
    """

    FACTORS = {
        'value': {
            'metrics': ['pb_ratio', 'pe_ratio', 'ps_ratio'],
            'ideal_range': (0, 15),  # Low P/E = high value
            'weight': 'inverse'  # Lower is better
        },
        'growth': {
            'metrics': ['revenue_growth', 'earnings_growth'],
            'ideal_range': (15, 50),  # High growth
            'weight': 'direct'
        },
        'momentum': {
            'metrics': ['return_6m', 'return_12m'],
            'ideal_range': (10, 50),
            'weight': 'direct'
        },
        'volatility': {
            'metrics': ['beta', 'std_dev'],
            'ideal_range': (0.8, 1.2),
            'weight': 'inverse'
        },
        'size': {
            'metrics': ['market_cap'],
            'ideal_range': (10e9, 100e9),  # Mid-cap
            'weight': 'neutral'
        },
        'quality': {
            'metrics': ['roe', 'debt_to_equity'],
            'ideal_range': (15, 25),  # High ROE
            'weight': 'direct'
        }
    }

    def calculate_factor_scores(
        self,
        portfolio: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate factor scores for each stock

        Returns:
            DataFrame with factor scores (0-100)
        """
        pass

    def calculate_portfolio_exposure(
        self,
        portfolio: pd.DataFrame
    ) -> Dict:
        """
        Calculate weighted portfolio factor exposure

        Returns:
            {factor: score, concentration: pct}
        """
        pass

    def factor_attribution(
        self,
        portfolio: pd.DataFrame,
        returns: pd.Series
    ) -> Dict:
        """
        Attribute portfolio returns to factors

        Example:
        - Momentum factor contributed +4.5%
        - Value factor contributed +2.0%
        - Other: +1.5%
        """
        pass

    def recommend_factor_balance(
        self,
        current_exposure: Dict
    ) -> List[str]:
        """
        Generate recommendations to balance factors
        """
        pass
```

### **UI Design:**

```python
def render_factor_exposure():
    st.title("📊 Factor Exposure Analyzer")

    # Calculate exposures
    analyzer = FactorExposureAnalyzer()
    exposure = analyzer.calculate_portfolio_exposure(portfolio)

    # Radar chart
    st.markdown("### 🕸️ Faktör Dağılımı")
    fig_radar = create_factor_radar_chart(exposure)
    st.plotly_chart(fig_radar)

    # Factor breakdown
    for factor, score in exposure.items():
        col1, col2 = st.columns([1, 3])

        with col1:
            st.metric(factor.capitalize(), f"{score:.1f}/100")

        with col2:
            progress_bar(score / 100)
            if score > 70:
                st.success(f"Yüksek {factor} exposure")
            elif score < 30:
                st.warning(f"Düşük {factor} exposure")

    # Recommendations
    recs = analyzer.recommend_factor_balance(exposure)
    st.markdown("### 💡 Öneriler")
    for rec in recs:
        st.info(rec)
```

---

## 🧩 MODULE 4: Smart Alerts Engine

### **Concept:**
Proaktif bildirimler - Sadece fiyat değil, davranış sinyali.

### **Alert Types:**

1. **Portfolio Alerts:**
   - "3 hisseniz endekse göre underperform ediyor"
   - "Portföy sağlık skoru 70'in altına düştü"
   - "Top pozisyonunuz %30'u geçti"

2. **ETF Weight Alerts:**
   - "QQQ'da NVDA ağırlığı %2 arttı"
   - "SPY'dan AAPL ağırlığı azaltıldı"

3. **Fund Flow Alerts:**
   - "Teknoloji fonlarına 3 günde ₺500M giriş"
   - "Finans fonlarından hızlı çıkış var"

4. **Technical Alerts:**
   - "ASELS 50-day MA'yı yukarı kesti"
   - "THYAO RSI 30'un altında (oversold)"

### **Delivery Channels:**

- **In-App:** Streamlit notification (st.toast)
- **Email:** SMTP (Gmail, SendGrid)
- **WhatsApp:** Twilio API
- **Telegram:** Telegram Bot API

---

## 🧩 MODULE 5: Performance Dashboard

### **Concept:**
System health + usage analytics.

### **Metrics Tracked:**

1. **Data Health:**
   - Last update time
   - Data coverage (%)
   - API status (yfinance, TEFAS)

2. **Usage Analytics:**
   - Most viewed stocks/ETFs
   - Average portfolio health score
   - Popular scenarios

3. **System Performance:**
   - Cache hit rate
   - Avg response time
   - Error rate

### **UI Design:**

```python
def render_performance_dashboard():
    st.title("⚙️ System Performance")

    # Data health
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Veri Güncellik", "2 saat önce", delta="✅")

    with col2:
        st.metric("ETF Kapsama", "92%", delta="+5%")

    with col3:
        st.metric("API Durumu", "Çalışıyor", delta="✅")

    # Most viewed assets
    st.markdown("### 📊 En Popüler Hisseler")
    # Display bar chart

    # Average health scores
    st.markdown("### 📈 Ortalama Health Score Dağılımı")
    # Display histogram
```

---

## 📅 6-WEEK IMPLEMENTATION TIMELINE

### **Week 1-2: Scenario Sandbox** 🧪
- [ ] Day 1-2: Data collection (TCMB, BIST correlations)
- [ ] Day 3-5: Scenario engine implementation
- [ ] Day 6-8: UI development
- [ ] Day 9-10: Testing + insights integration
- [ ] Day 11-14: Polish + documentation

### **Week 3-5: Fund Flow Radar** 📡
- [ ] Day 1-3: TEFAS API/scraper
- [ ] Day 4-6: Flow calculation engine
- [ ] Day 7-10: Sankey visualization
- [ ] Day 11-14: Sector aggregation
- [ ] Day 15-18: Alert system integration
- [ ] Day 19-21: Testing + polish

### **Week 6: Factor Exposure + Polish** 📊
- [ ] Day 1-4: Factor calculation engine
- [ ] Day 5-7: UI + visualizations
- [ ] Day 8-10: Integration testing
- [ ] Day 11-14: Bug fixes + deployment prep

---

## 🎯 SUCCESS METRICS

### **Technical:**
- ✅ 3 new major modules
- ✅ 1,500+ lines of production code
- ✅ Test coverage >80%
- ✅ Performance: <3 sec response time

### **User Experience:**
- ✅ 5+ new visualizations
- ✅ 20+ new insights
- ✅ Actionable alerts
- ✅ Mobile-friendly UI

### **Business:**
- ✅ Premium feature differentiation
- ✅ User engagement +50%
- ✅ Avg session time +3 min
- ✅ Conversion funnel ready

---

## 💰 MONETIZATION STRATEGY

### **Free Tier:**
- Portfolio Health Score (basic)
- ETF Tracker (limited stocks)
- 3 scenarios/month
- No alerts

### **Premium Tier - ₺149/ay ($5/mo):**
- ✅ Unlimited scenarios
- ✅ Fund Flow Radar (real-time)
- ✅ Factor Exposure Analyzer
- ✅ Smart Alerts (WhatsApp/Email)
- ✅ Historical data (12 months)
- ✅ Export unlimited

### **Pro Tier - ₺299/ay ($10/mo):**
- ✅ All Premium features
- ✅ API access
- ✅ Custom alerts
- ✅ Priority support
- ✅ Advanced scenarios (custom correlations)

---

## 🚀 NEXT STEPS

**Immediate (This Week):**
1. Set up TEFAS data pipeline
2. Build correlation matrix (TCMB/BIST)
3. Create scenario engine skeleton

**Month 1:**
1. Complete Scenario Sandbox
2. Start Fund Flow Radar
3. Launch beta testing (50 users)

**Month 2:**
1. Complete Fund Flow Radar
2. Add Factor Exposure
3. Launch premium tier
4. Target: 100 paying users

---

**Ready to start coding? Say the word and I'll generate the first module!** 🚀
