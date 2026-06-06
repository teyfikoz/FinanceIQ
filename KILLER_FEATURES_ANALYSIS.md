# 🎯 FundPortal - Killer Features Analysis
## 12 Özelliklerin Stratejik Analizi ve Önceliklendirme

---

## 📊 DEĞERLENDİRME MATRİSİ

Her özellik için puanlama (1-5 skala):

| Feature | Impact | Defensibility | Build Effort | Data Availability | TOTAL | Priority |
|---------|--------|---------------|--------------|-------------------|-------|----------|
| **1. ETF/Fund Holdings Weight Tracker** | 5 | 5 | 4 | 4 | **18** | 🥇 #1 |
| **2. Scenario Sandbox** | 5 | 4 | 3 | 5 | **17** | 🥈 #2 |
| **3. Portfolio Health Score** | 5 | 3 | 3 | 5 | **16** | 🥉 #3 |
| **4. Fund Flow Radar** | 5 | 5 | 4 | 3 | **17** | 🥈 #2 |
| **5. Smart Alerts Engine** | 4 | 3 | 4 | 4 | **15** | #5 |
| **6. Shareable Portfolio Cards** | 3 | 2 | 2 | 5 | **12** | #9 |
| **7. Leaderboards (Demo Mode)** | 3 | 2 | 2 | 5 | **12** | #9 |
| **8. Notes & Tags** | 3 | 2 | 1 | 5 | **11** | #11 |
| **9. Community Screener** | 4 | 3 | 3 | 3 | **13** | #7 |
| **10. Investment Style Profiler** | 4 | 4 | 3 | 4 | **15** | #5 |
| **11. Portfolio Time Machine** | 4 | 3 | 3 | 5 | **15** | #5 |
| **12. Factor Exposure Analyzer** | 5 | 5 | 5 | 3 | **18** | 🥇 #1 |
| **13. Thematic Trend Tracker** | 4 | 4 | 3 | 4 | **15** | #5 |
| **14. Correlated Pair Finder** | 4 | 4 | 2 | 5 | **15** | #5 |

---

## 🏆 TOP 5 ÖNCELIK SIRASI

### **🥇 TIER 1: Immediate Game Changers (Build First)**

---

#### **#1A: ETF/Fund Holdings Weight Tracker** ⭐⭐⭐⭐⭐
**Score: 18/20 | Build Time: 2-3 weeks**

**Neden #1 Öncelik:**
- ✅ Bloomberg Terminal'de bile var, **profesyonel araç**
- ✅ Rakiplerde YOK (TradingView/Investing'de yok)
- ✅ Türk yatırımcılar için kritik (TEFAS fonları çok popüler)
- ✅ Savunulabilir moat: Veri toplama + parsing complex

**Özellikler:**
1. **Holdings Composition Viewer**
   - ETF/Fon içindeki tüm hisseleri göster
   - Ağırlık yüzdeleri (örn: AAPL %8.5)
   - Sektör dağılımı

2. **Weight Change Tracker**
   - Aylık ağırlık değişimi grafiği
   - "MSFT'nin ağırlığı %7.2'den %8.1'e çıkmış" → Bullish signal
   - Alert: "QQQ'da NVDA ağırlığı 2 puan arttı"

3. **Reverse Lookup**
   - Hisse gir → "Bu hisse hangi ETF/fonlarda var?"
   - "ASELS şu 15 fonda bulunuyor, en yüksek ağırlık %4.2 (X Fonu)"

4. **Fund Manager Action Tracker**
   - "Son ayda SPY'dan AAPL ağırlığı azaltıldı" → Manager pessimistic

**Veri Kaynakları:**
- **ABD:** SEC 13F filings (ücretsiz)
- **ETF:** etfdb.com API, yfinance holdings
- **TEFAS:** TEFAS.gov.tr web scraping
- **Frequency:** Günlük update (ETF) / Aylık (13F)

**Technical Stack:**
```python
# File: app/analytics/fund_holdings_tracker.py

class FundHoldingsTracker:
    def get_etf_holdings(self, ticker: str):
        """Fetch ETF holdings from yfinance"""
        # yfinance has .holdings data

    def track_weight_changes(self, ticker: str, months: int):
        """Historical weight tracking"""
        # Store in SQLite: ticker, date, weight%

    def reverse_lookup(self, stock_ticker: str):
        """Find which ETFs/funds hold this stock"""
        # Query database of all ETF holdings

    def detect_manager_actions(self, ticker: str):
        """Detect significant weight changes"""
        # Alert: >2% weight change in 1 month
```

**UI Design:**
```
┌──────────────────────────────────────────┐
│ 🔍 Hisse Analizi: AAPL                   │
├──────────────────────────────────────────┤
│ Bu Hisseyi İçeren Fonlar:                │
│                                          │
│ 📊 SPY (S&P 500 ETF)                     │
│    ├─ Mevcut Ağırlık: 7.2%              │
│    ├─ Değişim (1ay): +0.3% ⬆️           │
│    └─ Değişim (3ay): -0.5% ⬇️           │
│                                          │
│ 📊 QQQ (Nasdaq 100 ETF)                  │
│    ├─ Mevcut Ağırlık: 12.1%             │
│    ├─ Değişim (1ay): -0.8% ⬇️           │
│    └─ ⚠️ UYARI: Ağırlık azaltılıyor!   │
│                                          │
│ [Ağırlık Geçmişi Grafiği]               │
│      12% ┤     •                         │
│      10% ┤   •                           │
│       8% ┤ •                             │
│          └────────────────               │
│          Jan  Feb  Mar  Apr              │
└──────────────────────────────────────────┘
```

---

#### **#1B: Factor Exposure Analyzer** ⭐⭐⭐⭐⭐
**Score: 18/20 | Build Time: 2 weeks**

**Neden Kritik:**
- ✅ Profesyonel fon yöneticileri kullanıyor
- ✅ Bireysel yatırımcıya ilk kez sunulacak
- ✅ Portföy risk yönetimi için essential
- ✅ Rakiplerde hiç yok

**Faktörler:**
1. **Value Factor** - P/B, P/E düşük hisseler
2. **Growth Factor** - Revenue/earnings büyüme
3. **Momentum Factor** - Son 6-12 ay performans
4. **Volatility Factor** - Risk/Beta
5. **Size Factor** - Market cap (small vs large cap)
6. **Quality Factor** - ROE, debt/equity

**Analiz:**
```python
# File: app/analytics/factor_exposure.py

class FactorExposureAnalyzer:
    def calculate_portfolio_factors(self, portfolio: pd.DataFrame):
        """Calculate factor exposures for entire portfolio"""
        # For each holding:
        # - Fetch P/E, P/B, growth rate, beta, etc.
        # - Calculate factor scores
        # - Weight-average by portfolio weights

    def factor_attribution(self, portfolio: pd.DataFrame, period: str):
        """Attribute portfolio returns to factors"""
        # "Bu ay portföyünüz %8 arttı:"
        # - %4.5 → Momentum faktörü
        # - %2.0 → Growth faktörü
        # - %1.5 → Diğer

    def factor_risk_analysis(self, portfolio: pd.DataFrame):
        """Identify concentrated factor risks"""
        # "Portföyünüz %70 momentum faktörüne bağımlı"
        # "Risk: Momentum tersine dönerse büyük kayıp"
```

**UI Example:**
```
┌──────────────────────────────────────────┐
│ 📊 Portföy Faktör Analizi                │
├──────────────────────────────────────────┤
│ Faktör Dağılımı:                         │
│                                          │
│ Momentum  ████████████████░░  70%        │
│ Growth    ████████░░░░░░░░░░  40%        │
│ Value     ████░░░░░░░░░░░░░░  20%        │
│ Quality   ██████░░░░░░░░░░░░  30%        │
│ Size      ████████░░░░░░░░░░  40% (Large)│
│ Volatility ████████████░░░░░░  60% (High)│
│                                          │
│ ⚠️ RİSK UYARISI:                         │
│ Portföyünüz yüksek momentum riski        │
│ taşıyor. Piyasa tersine dönerse          │
│ %15+ düşüş olasılığı yüksek.             │
│                                          │
│ 💡 ÖNERİ:                                │
│ Value faktörü ekleyerek dengeleyin.      │
│ Öneri hisseler: [KO, PG, JNJ]           │
└──────────────────────────────────────────┘
```

---

### **🥈 TIER 2: High Impact, Build Second**

---

#### **#2A: Scenario Sandbox** ⭐⭐⭐⭐⭐
**Score: 17/20 | Build Time: 1-2 weeks**

**Neden Güçlü:**
- ✅ Kullanıcı engagement çok yüksek (interaktif)
- ✅ TCMB kararları öncesi kullanım spike'ı
- ✅ Kolay build (Monte Carlo benzeri)

**Senaryolar:**
1. **Makro Senaryolar:**
   - TCMB faiz +500bp artarsa → BIST %?
   - USD/TRY 35'e çıkarsa → portföyüm %?
   - Fed faiz indirirse → teknoloji hisseleri %?

2. **Sektör Senaryolar:**
   - Petrol $100'e çıkarsa → enerji hisseleri
   - Altın rekor kırarsa → madencilik

3. **Şirket-Spesifik:**
   - TSLA %20 düşerse → QQQ'ya etkisi?
   - NVDA kâr açıklarsa → portföyüm %?

**Implementation:**
```python
# File: app/analytics/scenario_sandbox.py

class ScenarioSandbox:
    def create_macro_scenario(self, scenario_type: str, magnitude: float):
        """
        Scenarios:
        - interest_rate_change: TCMB faiz değişimi
        - currency_shock: USD/TRY değişimi
        - oil_price_change: Petrol fiyat değişimi
        - equity_market_shock: BIST endeks şoku
        """

    def simulate_portfolio_impact(self, portfolio: pd.DataFrame, scenario: dict):
        """Calculate portfolio impact using historical correlations"""
        # Historical regression: BIST vs TCMB faiz
        # Apply correlation to each stock
        # Return: Expected portfolio value change

    def stress_test_portfolio(self, portfolio: pd.DataFrame):
        """Run multiple worst-case scenarios"""
        # 1. 2018 Kur Krizi tekrarı
        # 2. 2008 Finansal Kriz tekrarı
        # 3. 2020 COVID şoku tekrarı
        # Return: VaR (Value at Risk)
```

**UI Design:**
```
┌──────────────────────────────────────────┐
│ 🧪 Senaryo Sandbox'ı                     │
├──────────────────────────────────────────┤
│ Senaryo Seç:                             │
│ [○] TCMB Faiz Artışı                     │
│ [○] USD/TRY Şoku                         │
│ [●] Petrol Fiyat Değişimi                │
│ [○] BIST Endeks Düşüşü                   │
│                                          │
│ Parametre:                               │
│ Petrol Fiyatı: $80 ▶️ [$120] (slider)   │
│                                          │
│ 🎯 TAHMİNİ ETKİ:                         │
│                                          │
│ Portföy Değeri:                          │
│   Mevcut: ₺100,000                       │
│   Senaryo: ₺103,500 (+3.5%) ⬆️          │
│                                          │
│ En Çok Kazananlar:                       │
│   ✅ PETKM: +8.2%                        │
│   ✅ TUPRS: +7.5%                        │
│                                          │
│ En Çok Kaybedenler:                      │
│   ❌ THYAO: -4.1%                        │
│                                          │
│ [Senaryoyu Kaydet] [PDF İndir]          │
└──────────────────────────────────────────┘
```

---

#### **#2B: Fund Flow Radar** ⭐⭐⭐⭐⭐
**Score: 17/20 | Build Time: 2-3 weeks**

**Neden Unique:**
- ✅ TradingView/Investing'de yok
- ✅ "Smart money" akışını gösterir
- ✅ TEFAS verisi ücretsiz erişilebilir

**Özellikler:**
1. **Daily Fund Flows**
   - Her fon için günlük para giriş/çıkış
   - "X Teknoloji Fonu: +₺25M giriş (bugün)"

2. **Sector Flow Map**
   - Hangi sektöre para akıyor?
   - "Son 7 gün: Teknoloji +₺150M, Finans -₺80M"

3. **Flow-Based Signals**
   - "Son 3 günde teknoloji fonlarına güçlü giriş → Bullish"
   - "Banka fonlarından çıkış hızlanıyor → Bearish"

4. **Flow Visualization**
   - Sankey diagram: "Yatırımcılar → Fonlar → Sektörler"

**Veri Kaynağı:**
- **TEFAS:** tefas.gov.tr (günlük fon büyüklükleri)
- **Calculation:** Daily AUM change = Net flow

```python
# File: app/analytics/fund_flow_radar.py

class FundFlowRadar:
    def fetch_tefas_data(self, fund_code: str):
        """Scrape TEFAS daily fund size"""
        # TEFAS sitesinden günlük fon büyüklüğü

    def calculate_daily_flows(self, fund_code: str):
        """Calculate net flows"""
        # Flow = AUM_today - AUM_yesterday - (Return% * AUM_yesterday)

    def aggregate_sector_flows(self, period: str):
        """Aggregate flows by sector"""
        # Group funds by sector
        # Sum net flows

    def create_flow_sankey(self):
        """Sankey diagram: Money → Funds → Sectors"""
        # Plotly Sankey chart
```

**UI Design:**
```
┌──────────────────────────────────────────┐
│ 📡 Fund Flow Radar                       │
├──────────────────────────────────────────┤
│ Son 7 Gün - Sektör Bazlı Akış:          │
│                                          │
│ ⬆️ EN FAZLA GİRİŞ                       │
│ 1. Teknoloji     +₺245M  🟢🟢🟢🟢      │
│ 2. Sağlık        +₺122M  🟢🟢          │
│ 3. Enerji        +₺87M   🟢            │
│                                          │
│ ⬇️ EN FAZLA ÇIKIŞ                       │
│ 1. Finans        -₺156M  🔴🔴🔴        │
│ 2. Gayrimenkul   -₺93M   🔴🔴          │
│                                          │
│ [Akış Grafiği - Sankey Diagram]         │
│                                          │
│ 💡 SİNYAL:                               │
│ Teknoloji fonlarına güçlü giriş var.    │
│ Bu genelde yükseliş öncesi görülür.      │
│ Öneri hisseler: [ASELS, LOGO, KAREL]    │
└──────────────────────────────────────────┘
```

---

#### **#3: Portfolio Health Score** ⭐⭐⭐⭐
**Score: 16/20 | Build Time: 1 week**

**Neden Seviliyor:**
- ✅ Kullanıcılar skor sistemlerini seviyor (gamification)
- ✅ Actionable insights sağlıyor
- ✅ Kolay build

**Skor Bileşenleri (10 metrik):**
1. **Diversification (20 puan)**
   - 10+ hisse → +20
   - 5-9 hisse → +15
   - <5 hisse → +5

2. **Sector Balance (15 puan)**
   - Max %30 tek sektör → +15
   - Max %50 tek sektör → +10
   - >%50 tek sektör → +5

3. **Risk Level (15 puan)**
   - Portfolio Beta 0.8-1.2 → +15
   - Beta >1.5 → +5

4. **Tax Efficiency (10 puan)**
   - Stopaj optimize → +10
   - Sub-optimal → +5

5. **Cost Efficiency (10 puan)**
   - İşlem maliyetleri <1% → +10

6. **Momentum (10 puan)**
   - 70%+ hisseler pozitif trend → +10

7. **Quality (10 puan)**
   - Avg ROE >15% → +10

8. **Liquidity (5 puan)**
   - Tüm hisseler günlük >₺1M işlem → +5

9. **Size Balance (5 puan)**
   - Large+Mid+Small cap mix → +5

**Implementation:**
```python
# File: app/analytics/portfolio_health_score.py

class PortfolioHealthScore:
    def calculate_total_score(self, portfolio: pd.DataFrame):
        """Calculate 0-100 health score"""
        score = 0
        score += self._diversification_score(portfolio)
        score += self._sector_balance_score(portfolio)
        score += self._risk_score(portfolio)
        # ... 7 more metrics
        return score

    def generate_recommendations(self, portfolio: pd.DataFrame):
        """Actionable advice to improve score"""
        # "Skor: 68/100 - İyi"
        # "İyileştirme önerileri:"
        # "1. Teknoloji ağırlığını %45'ten %30'a düşür"
        # "2. Defansif sektör ekle (sağlık, tüketim)"
```

---

## 🎯 UYGULAMA SIRASI (90 Gün)

### **Sprint 1 (Gün 1-21): Tier 1 Features**
**Week 1-2:** ETF/Fund Holdings Weight Tracker
- [ ] yfinance holdings API entegrasyonu
- [ ] TEFAS web scraper
- [ ] Weight change tracking database
- [ ] UI: Holdings viewer + weight history chart

**Week 3:** Factor Exposure Analyzer
- [ ] Factor calculation engine
- [ ] Factor attribution logic
- [ ] UI: Factor exposure dashboard

### **Sprint 2 (Gün 22-42): Tier 2 Features**
**Week 4:** Scenario Sandbox
- [ ] Scenario engine (interest rate, currency, etc.)
- [ ] Historical correlation database
- [ ] UI: Interactive scenario builder

**Week 5:** Fund Flow Radar
- [ ] TEFAS data scraper + scheduler
- [ ] Flow calculation logic
- [ ] Sector aggregation
- [ ] UI: Flow visualization (Sankey)

**Week 6:** Portfolio Health Score
- [ ] 10-metric calculation engine
- [ ] Recommendation generator
- [ ] UI: Score dashboard + improvement tips

### **Sprint 3 (Gün 43-60): Polish & Launch**
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Turkish UX improvements
- [ ] Beta user testing
- [ ] Documentation

---

## 💎 DIĞER ÖZELLİKLER (Phase 2)

### **Quick Wins (Kolay Build, Hızlı Impact):**

**#5: Smart Alerts Engine** (1 hafta)
- "Portföyündeki 3 hisse underperform ediyor"
- "USD/TRY %7 arttı, hedge düşün"
- WhatsApp/Telegram entegrasyonu

**#6: Investment Style Profiler** (1 hafta)
- Kullanıcının geçmiş işlemlerinden stil çıkar
- 🐢 Defansif / 🚀 Agresif / ⚖️ Dengeli
- Stile göre öneriler

**#7: Correlated Pair Finder** (3 gün)
- En korele hisse çiftleri
- Negatif korele çiftler (hedge için)
- Korelasyon matrisi heatmap

### **Nice-to-Have (Phase 3):**

**#8: Portfolio Time Machine**
- "2020'de bu portföyü alsaydım ne kazanırdım?"
- Alternate history simülasyonu

**#9: Thematic Trend Tracker**
- AI, Green Energy, Defense temalarındaki fonlar
- Tematik performans karşılaştırma

**#10: Shareable Portfolio Cards**
- LinkedIn/Twitter paylaşımı
- Haftalık kazanan hisse kartı

**#11: Community Screener**
- En çok takip edilen hisseler
- Topluluk sentiment'i

---

## 🏆 REKABET AVANTAJI ANALİZİ

| Özellik | TradingView | Investing.com | Bloomberg | FundPortal |
|---------|-------------|---------------|-----------|-----------|
| ETF Holdings Weight Change | ❌ | ❌ | ✅ ($$$) | ✅ FREE |
| Factor Exposure | ❌ | ❌ | ✅ | ✅ |
| Fund Flow Radar (TEFAS) | ❌ | ❌ | ❌ | ✅ |
| Scenario Sandbox (Turkish) | ❌ | ❌ | ✅ | ✅ |
| Portfolio Health Score | ❌ | ❌ | ❌ | ✅ |

**Sonuç:** Bu 5 özellik → **Bloomberg Terminal'in retail versiyonu**

---

## 💰 MONETİZASYON ETKİSİ

**Free Tier:**
- Portfolio Health Score (temel)
- Scenario Sandbox (3 senaryo/ay)
- Fund Flow (1 hafta gecikmeli)

**Premium Tier - ₺149/ay:**
- ✅ ETF Holdings Weight Tracker (unlimited)
- ✅ Factor Exposure Analyzer
- ✅ Real-time Fund Flow Radar
- ✅ Scenario Sandbox (unlimited)
- ✅ Advanced Health Score + Recommendations

**Premium justification:** Bu özellikler Bloomberg'de $24,000/yıl

---

## 🚀 İLK ADIM

**Bu hafta:** Hangisini kodlayayım?

**Önerim:**
1. **ETF/Fund Holdings Weight Tracker** (en yüksek impact)
2. **Portfolio Health Score** (en kolay build, hızlı win)

Siz hangisini tercih edersiniz? Yoksa ikisine birden paralel mi başlayalım?
