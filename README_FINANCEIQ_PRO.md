# 📊 FundPortal Pro - Advanced Portfolio Analytics

**Bloomberg Terminal seviyesinde analitik araçlar, bireysel yatırımcılar için.**

## 🎯 Özellikler

### **1. Portfolio Health Score** 📊
Portföyünüzü 8 farklı metrikle analiz ederek 0-100 arası sağlık skoru hesaplar.

**Metrikler:**
- ✅ **Çeşitlendirme (20%)** - Sektör dağılımı ve hisse sayısı
- ⚠️ **Risk Yönetimi (20%)** - Beta ve volatilite analizi
- 📈 **Momentum (15%)** - 3 aylık getiri trendi
- 💧 **Likidite (10%)** - İşlem hacmi analizi
- 💰 **Vergi Verimliliği (10%)** - Stopaj optimizasyonu
- ⚖️ **Denge (10%)** - Pozisyon dağılımı
- ⏱️ **Süre Uyumu (5%)** - Tutma süresi analizi
- 📊 **Sektör Performansı (10%)** - Endeks karşılaştırması

**Görselleştirmeler:**
- 🎯 Gauge Chart (Ana skor)
- 🕸️ Radar Chart (Metrik dağılımı)
- 📊 Bar Charts (Detaylı skorlar)
- 🗺️ Risk Haritası (Beta vs Volatilite)
- 🥧 Sektör Dağılımı (Pie Chart)

**Öneriler:**
- Actionable tavsiyeler
- Zayıf nokta tespiti
- İyileştirme fırsatları

---

### **2. ETF Holdings Weight Tracker** 📈
Hisselerin ETF/fonlardaki ağırlıklarını takip edin. Kurumsal yatırımcıların hareketlerini görün.

**Özellikler:**

#### **A) Hisse Analizi** 🔍
- Bir hissenin hangi ETF/fonlarda bulunduğunu görün
- Ağırlık yüzdelerini karşılaştırın
- 25+ popüler ETF takibi (SPY, QQQ, ARK, vs.)

#### **B) Ağırlık Geçmişi** 📊
- Zaman içinde ağırlık değişimlerini takip edin
- Trend analizi (yükseliş/düşüş)
- Fon yöneticisi aksiyonlarını tespit edin

#### **C) Fon Yöneticisi Sinyalleri** 🎯
- En çok ağırlık artan/azalan hisseler
- Kurumsal alım-satım sinyalleri
- Bullish/Bearish sentiment analizi

**Veri Kaynakları:**
- Yahoo Finance ETF holdings API
- SQLite veritabanı (tarihsel takip)
- 25+ ETF real-time tracking

---

## 🚀 Hızlı Başlangıç

### **Kurulum**

```bash
# Repository'yi klonlayın
git clone https://github.com/yourusername/financeiq-pro.git
cd financeiq-pro

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı çalıştırın
streamlit run financeiq_pro.py
```

### **Kullanım**

#### **Portfolio Health Score:**

1. **Portföy Yükle:**
   - CSV dosyası yükleyin (Symbol, Shares, Price, Value)
   - Veya "Örnek Portföy" kullanın

2. **Analiz Et:**
   - "Sağlık Skoru Hesapla" butonuna tıklayın
   - 30-60 saniye bekleyin (yfinance API çağrıları)

3. **Sonuçları İncele:**
   - Toplam skor ve not görün
   - Metrik detaylarını inceleyin
   - Önerileri okuyun
   - Excel/CSV olarak dışa aktarın

#### **ETF Weight Tracker:**

1. **ETF Verilerini Güncelle:**
   - "Veri Yönetimi" sekmesine gidin
   - "Tümü" seçip "Verileri Güncelle"
   - 5-10 dakika bekleyin (ilk sefer)

2. **Hisse Analizi:**
   - Hisse sembolü girin (örn: AAPL)
   - "Analiz Et" butonuna tıklayın
   - Hangi ETF'lerde olduğunu görün

3. **Ağırlık Geçmişi:**
   - Hisse ve fon seçin
   - Tarihsel ağırlık grafiğini görün
   - Trend yorumunu okuyun

4. **Fon Yöneticisi Sinyalleri:**
   - "En Aktif Hisseleri Bul"
   - En çok ağırlık değişen hisseleri görün
   - Bullish/Bearish sinyalleri takip edin

---

## 📂 Proje Yapısı

```
financeiq-pro/
├── financeiq_pro.py                # Ana uygulama
├── modules/
│   ├── __init__.py
│   ├── portfolio_health.py         # Health Score hesaplama motoru
│   ├── portfolio_health_ui.py      # Health Score UI
│   ├── etf_weight_tracker.py       # ETF tracker backend
│   └── etf_weight_tracker_ui.py    # ETF tracker UI
├── sample_data/
│   └── sample_portfolio.csv        # Örnek portföy
├── data/
│   └── etf_holdings.db             # SQLite veritabanı (auto-created)
├── requirements.txt                # Python bağımlılıkları
└── README_FINANCEIQ_PRO.md         # Bu dosya
```

---

## 🎨 Örnek CSV Formatı

### Portfolio CSV:
```csv
Symbol,Shares,Price,Value
AAPL,50,178.50,8925.00
MSFT,30,378.91,11367.30
GOOGL,20,140.22,2804.40
TSLA,15,242.84,3642.60
```

**Gerekli Sütunlar:**
- `Symbol`: Hisse sembolü (örn: AAPL, MSFT)
- `Shares`: Adet
- `Price`: Fiyat
- `Value`: Toplam değer (Shares x Price)

**Opsiyonel Sütunlar:**
- `Sector`: Sektör (yoksa otomatik tespit edilir)
- `Beta`: Beta değeri (yoksa API'den çekilir)
- `Return_3M`: 3 aylık getiri (yoksa hesaplanır)

---

## 📊 Takip Edilen ETF'ler

### **US Market ETFs:**
- SPY - SPDR S&P 500 ETF
- QQQ - Invesco QQQ (Nasdaq 100)
- IWM - iShares Russell 2000
- DIA - SPDR Dow Jones Industrial
- VTI - Vanguard Total Stock Market
- VOO - Vanguard S&P 500

### **Sector ETFs:**
- XLK - Technology Select Sector
- XLF - Financial Select Sector
- XLE - Energy Select Sector
- XLV - Health Care Select Sector
- XLI - Industrial Select Sector
- XLP - Consumer Staples Select
- XLY - Consumer Discretionary Select
- XLU - Utilities Select Sector
- XLRE - Real Estate Select Sector
- XLC - Communication Services Select

### **Tech/Growth ETFs:**
- ARKK - ARK Innovation ETF
- ARKW - ARK Next Generation Internet
- WCLD - WisdomTree Cloud Computing
- SKYY - First Trust Cloud Computing
- VUG - Vanguard Growth ETF
- MTUM - iShares Edge MSCI Momentum

**Toplam: 25+ ETF**

---

## 🔧 Teknik Detaylar

### **Technology Stack:**
- **Frontend:** Streamlit
- **Visualization:** Plotly, Matplotlib, Seaborn
- **Data Processing:** Pandas, NumPy
- **Data Source:** yfinance (Yahoo Finance API)
- **Database:** SQLite (holdings history)
- **Export:** Excel (openpyxl), CSV

### **Performance:**
- **Health Score Calculation:** 30-60 seconds (depends on portfolio size)
- **ETF Data Fetch:** 10-20 seconds per ETF
- **Bulk ETF Update:** 5-10 minutes (all 25 ETFs)
- **Database Queries:** <1 second

### **Data Storage:**
- Holdings data stored in `data/etf_holdings.db`
- Auto-created on first run
- Indexed for fast queries
- Historical data preserved

---

## 📈 Kullanım Senaryoları

### **Senaryo 1: Portföy Sağlık Kontrolü**
**Problem:** "Portföyüm dengeli mi? Riskli mi?"

**Çözüm:**
1. Portföyünüzü CSV olarak yükleyin
2. Health Score hesaplayın
3. Skorun 70'in üzerinde olup olmadığına bakın
4. Önerileri okuyun ve uygulayın

**Sonuç:** Portföyünüzün zayıf noktalarını görüp düzeltirsiniz.

---

### **Senaryo 2: Kurumsal Yatırımcı Takibi**
**Problem:** "NVDA'yı kurumsal yatırımcılar alıyor mu satıyor mu?"

**Çözüm:**
1. ETF Weight Tracker → Hisse Analizi
2. "NVDA" yazıp "Analiz Et"
3. Hangi ETF'lerde olduğunu görün
4. Ağırlık Geçmişi'ne gidin
5. QQQ'da NVDA ağırlığını inceleyin

**Sonuç:** Trend yukarı ise → Bullish sinyal

---

### **Senaryo 3: Alım-Satım Sinyali Bulma**
**Problem:** "Hangi hisse şu an kurumsal ilgi görüyor?"

**Çözüm:**
1. ETF Weight Tracker → Fon Yöneticisi Sinyalleri
2. "En Aktif Hisseleri Bul"
3. En çok ağırlık artan hisseleri görün
4. Bu hisseler üzerinde araştırma yapın

**Sonuç:** Kurumsal yatırımcıların biriktirdiği hisseleri keşfedersiniz.

---

## 🎯 Gelecek Özellikler (Roadmap)

### **Phase 2: Enhanced Analytics** (2-3 hafta)
- [ ] Scenario Sandbox (makro senaryo simülasyonu)
- [ ] Fund Flow Radar (TEFAS para akışı)
- [ ] Factor Exposure Analyzer (risk faktörleri)

### **Phase 3: Turkish Market** (3-4 hafta)
- [ ] BIST sentiment tracker (Ekşi Sözlük, Twitter)
- [ ] Turkish tax calculator (stopaj, sermaye kazancı)
- [ ] TCMB impact simulator
- [ ] TEFAS fon analizi

### **Phase 4: Automation** (4-6 hafta)
- [ ] Scheduled ETF updates (daily)
- [ ] Email/WhatsApp alerts
- [ ] Portfolio rebalancing suggestions
- [ ] API for developers

---

## 🐛 Troubleshooting

### **Problem: "No data available for ticker"**
**Çözüm:**
- Hisse sembolünü kontrol edin (AAPL, MSFT, vs.)
- Türk hisseleri için `.IS` eklemeyi deneyin (ASELS.IS)
- yfinance API'nin erişilebilir olduğundan emin olun

### **Problem: "ETF holdings not found"**
**Çözüm:**
- Veri Yönetimi sekmesine gidin
- "Verileri Güncelle" butonuna tıklayın
- 5-10 dakika bekleyin
- Bazı ETF'ler holdings data sağlamayabilir (API kısıtı)

### **Problem: "Health score calculation takes too long"**
**Çözüm:**
- Normal: 10+ hisse için 30-60 saniye beklenir
- Her hisse için yfinance API çağrısı yapılır
- Portföy boyutunu azaltmayı deneyin (<20 hisse)

### **Problem: "Database error"**
**Çözüm:**
```bash
# Veritabanını sıfırla
rm data/etf_holdings.db

# Uygulamayı yeniden başlat
streamlit run financeiq_pro.py
```

---

## 📚 API Referansı

### **PortfolioHealthScore**

```python
from modules.portfolio_health import PortfolioHealthScore

# Initialize
calculator = PortfolioHealthScore()

# Load portfolio
portfolio_df = pd.read_csv('my_portfolio.csv')
calculator.load_portfolio(portfolio_df)

# Enrich with market data
enriched = calculator.enrich_portfolio_data()

# Calculate scores
scores = calculator.calculate_all_metrics()

# Get summary
summary = calculator.get_summary()
print(f"Health Score: {summary['total_score']:.1f}/100")
print(f"Grade: {summary['grade']}")
```

### **ETFWeightTracker**

```python
from modules.etf_weight_tracker import ETFWeightTracker

# Initialize
tracker = ETFWeightTracker()

# Fetch ETF holdings
holdings = tracker.fetch_etf_holdings('SPY')

# Find funds holding a stock
funds = tracker.get_funds_for_stock('AAPL', min_weight=1.0)

# Get weight history
history = tracker.get_weight_history('AAPL', 'QQQ')

# Detect fund manager actions
signal = tracker.detect_fund_manager_actions('NVDA')
print(f"Signal: {signal['signal']} (Confidence: {signal['confidence']}%)")
```

---

## 🤝 Katkıda Bulunma

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

**Code Style:**
- Follow PEP 8
- Add docstrings (Google style)
- Include type hints
- Write unit tests (TODO: Add pytest)

---

## 📜 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **yfinance**: Free Yahoo Finance data
- **Plotly**: Interactive visualizations
- **Streamlit**: Rapid dashboard development
- **NumPy/Pandas**: Data processing backbone
- **Bloomberg Terminal**: Inspiration for professional analytics

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/financeiq-pro/issues)
- **Email**: support@financeiq.com
- **Discord**: [Join our community](https://discord.gg/financeiq)

---

## 🎉 Quick Links

- 🌐 **Live Demo**: https://financeiq-pro.streamlit.app/
- 📚 **Documentation**: [Full Docs](https://docs.financeiq.com)
- 🚀 **Tutorial Videos**: [YouTube Playlist](https://youtube.com/financeiq)
- 💬 **Community**: [Discord](https://discord.gg/financeiq)

---

**Built with ❤️ for retail investors who deserve Bloomberg-level tools.**

**🚀 FundPortal Pro | $0 Cost | Open Source**
