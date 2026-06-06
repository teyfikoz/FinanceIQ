# 🚀 FundPortal Pro - Quick Start Guide

## ⚡ 5 Dakikada Başlangıç

### **Adım 1: Test Çalıştırın** ✅

```bash
cd "global_liquidity_dashboard"
python test_financeiq_pro.py
```

**Beklenen Çıktı:**
- ✅ Portfolio Health Score test başarılı
- ✅ ETF Weight Tracker test başarılı
- ⏱️ Süre: ~60 saniye

---

### **Adım 2: Uygulamayı Başlatın** 🚀

```bash
streamlit run financeiq_pro.py
```

**Tarayıcınızda otomatik açılacak:**
- 🌐 http://localhost:8501

---

### **Adım 3: Portfolio Health Score Deneyin** 📊

1. **"Portfolio Health Score" sekmesine gidin**

2. **"Örnek Portföy Kullan" butonuna tıklayın**

3. **"Sağlık Skoru Hesapla" butonuna basın**
   - ⏱️ 30-60 saniye bekleyin
   - API çağrıları yapılıyor...

4. **Sonuçları görün:**
   - 🎯 Toplam Skor (0-100)
   - 📊 Metrik Dağılımı (Radar Chart)
   - 💡 Öneriler
   - 📈 Detaylı Analiz

5. **Excel raporu indirin:**
   - "📊 Excel Raporu İndir" butonuna tıklayın

---

### **Adım 4: ETF Weight Tracker Deneyin** 📈

1. **"ETF Weight Tracker" sekmesine gidin**

2. **Veri Yönetimi → Verileri Güncelle**
   - "TÜMÜ" seçin
   - "Verileri Güncelle" butonuna basın
   - ⏱️ 5-10 dakika bekleyin (ilk sefer)

3. **Hisse Analizi yapın:**
   - Hisse Sembolü: `AAPL`
   - "Analiz Et" butonuna basın
   - AAPL'ın hangi ETF'lerde olduğunu görün

4. **Fon Yöneticisi Sinyalleri:**
   - "Fon Yöneticisi Sinyalleri" sekmesine gidin
   - "En Aktif Hisseleri Bul" butonuna basın
   - En çok ağırlık değişen hisseleri görün

---

## 🎯 Kullanım Örnekleri

### **Örnek 1: Kendi Portföyünüzü Analiz Edin**

**1. CSV Hazırlayın:**

Dosya: `my_portfolio.csv`

```csv
Symbol,Shares,Price,Value
AAPL,50,178.50,8925.00
MSFT,30,378.91,11367.30
GOOGL,20,140.22,2804.40
```

**2. Yükleyin:**
- "Portföy CSV dosyanızı yükleyin" → Dosya seçin
- "Sağlık Skoru Hesapla"

**3. Sonuçları İnceleyin:**
- Skorunuz 70'in altındaysa → Önerileri okuyun
- Skorunuz 80'in üstündeyse → Tebrikler! 🎉

---

### **Örnek 2: Kurumsal Yatırımcı Takibi**

**Soru:** "NVDA'yı kurumsal yatırımcılar alıyor mu?"

**Cevap Bulun:**

1. ETF Weight Tracker → Hisse Analizi
2. Hisse: `NVDA`
3. "Analiz Et"
4. Fon Yöneticisi Sinyali'ne bakın:
   - 🟢 BULLISH → Alınıyor
   - 🔴 BEARISH → Satılıyor
   - ⚪ NEUTRAL → Net trend yok

5. Ağırlık Geçmişi'ne gidin:
   - QQQ'da NVDA'nın ağırlık grafiğini görün
   - Trend yukarı ise → Pozitif sinyal

---

### **Örnek 3: Portföy Diversifikasyonu Kontrolü**

**Soru:** "Portföyüm çok teknoloji ağırlıklı mı?"

**Cevap:**

1. Health Score hesaplayın
2. "Diversification" skoruna bakın:
   - 90+ → Mükemmel dağılım
   - 60-80 → Orta, iyileştirilebilir
   - <60 → Zayıf, acil düzeltme gerek

3. "Sektör Dağılımı" grafiğine bakın:
   - Hiçbir sektör %40'ı geçmemeli
   - İdeal: 5+ farklı sektör

4. Önerileri okuyun:
   - Sistem size hangi sektörlere ağırlık vermenizi söyleyecek

---

## 🔧 Sorun Giderme

### **Problem 1: "ModuleNotFoundError"**

**Çözüm:**
```bash
pip install -r requirements.txt
```

### **Problem 2: "No data available"**

**Çözüm:**
- İnternet bağlantınızı kontrol edin
- yfinance API'nin çalıştığını doğrulayın:
  ```python
  import yfinance as yf
  ticker = yf.Ticker("AAPL")
  print(ticker.info['sector'])
  ```

### **Problem 3: "Health Score calculation too slow"**

**Neden:** Her hisse için API çağrısı yapılıyor

**Çözümler:**
- Portföy boyutunu azaltın (<15 hisse)
- Sabırlı olun (30-60 saniye normal)
- Alternatif: Sektör, Beta bilgilerini manuel ekleyin CSV'ye

### **Problem 4: "ETF holdings not found"**

**Neden:** yfinance bazı ETF'ler için holdings sağlamıyor

**Çözüm:**
- Farklı ETF deneyin (SPY, QQQ çalışır)
- API rate limit'e takılmış olabilirsiniz (10 dakika bekleyin)

---

## 📊 Veri Kaynakları

### **Portfolio Health Score:**
- **API:** yfinance (Yahoo Finance)
- **Veri:** Fiyat, beta, volatilite, sektör, market cap
- **Güncelleme:** Real-time (API çağrısında)

### **ETF Weight Tracker:**
- **API:** yfinance ETF holdings endpoint
- **Veri:** ETF içerikleri, ağırlık yüzdeleri
- **Güncelleme:** Günlük (ETF'ler) / Aylık (Ağırlık değişimi)
- **Depolama:** SQLite (local database)

---

## 🎓 İleri Düzey Kullanım

### **Custom Portfolio CSV (Gelişmiş)**

Daha hızlı sonuç için sektör ve beta bilgilerini CSV'ye ekleyin:

```csv
Symbol,Shares,Price,Value,Sector,Beta,Return_3M
AAPL,50,178.50,8925.00,Technology,1.2,15.3
MSFT,30,378.91,11367.30,Technology,0.9,12.1
JPM,40,150.25,6010.00,Financial,1.1,8.5
```

Bu şekilde API çağrısı yapılmaz, hesaplama 5 saniyeye düşer.

---

### **Programmatic Usage**

Python'dan modülleri kullanın:

```python
from modules.portfolio_health import PortfolioHealthScore
import pandas as pd

# Load portfolio
df = pd.read_csv('my_portfolio.csv')

# Calculate
calculator = PortfolioHealthScore()
calculator.load_portfolio(df)
calculator.enrich_portfolio_data()
scores = calculator.calculate_all_metrics()

# Get results
summary = calculator.get_summary()
print(f"Score: {summary['total_score']:.1f}/100")
```

---

### **Database Queries (ETF Tracker)**

SQLite database'e direkt sorgu:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/etf_holdings.db')

# Find all funds holding AAPL
query = """
    SELECT fund_code, weight_pct, report_date
    FROM holdings
    WHERE stock_symbol = 'AAPL'
    ORDER BY weight_pct DESC
"""

df = pd.read_sql_query(query, conn)
print(df)
```

---

## 🚀 Deployment (Streamlit Cloud)

### **Adım 1: GitHub'a Push**

```bash
git add .
git commit -m "Add FundPortal Pro modules"
git push origin main
```

### **Adım 2: Streamlit Cloud Deploy**

1. https://share.streamlit.io/ adresine gidin
2. "New app" → GitHub repo'nuzu seçin
3. Main file: `financeiq_pro.py`
4. Deploy!

### **Adım 3: Secrets (Opsiyonel)**

Eğer API key'ler kullanıyorsanız:

Streamlit Cloud → Settings → Secrets → Add:

```toml
[api_keys]
alpha_vantage = "YOUR_KEY"
fred = "YOUR_KEY"
```

---

## 📈 Performance Optimization

### **Tips:**

1. **Cache API Results:**
   - yfinance sonuçları 5 dakika cache'lenir
   - Tekrar hesaplama hızlıdır

2. **Limit Portfolio Size:**
   - 10-20 hisse optimal
   - 50+ hisse yavaşlatabilir

3. **Pre-populate Database:**
   - ETF verilerini önceden çekin
   - "Verileri Güncelle" → "TÜMÜ" → 1 kere

4. **Use CSV with Sector/Beta:**
   - API çağrılarını azaltır
   - Hesaplama 10x hızlanır

---

## 🎯 Next Steps

Uygulamayı kurdunuz, şimdi ne yapmalısınız?

### **Kısa Vadeli (1 Hafta):**
1. ✅ Kendi portföyünüzü analiz edin
2. ✅ ETF verilerini güncelleyin
3. ✅ Favori hisselerinizin kurumsal ilgisini takip edin

### **Orta Vadeli (1 Ay):**
1. 📊 Haftalık health score kontrolü yapın
2. 📈 Portföy önerilerini uygulayın
3. 🎯 Kurumsal alım sinyallerini takip edin

### **Uzun Vadeli (3 Ay):**
1. 🚀 Phase 2 özelliklerini ekleyin (Scenario Sandbox)
2. 🇹🇷 Turkish Market entegrasyonu (BIST, TEFAS)
3. 🤖 AI-powered öneriler (GPT-4 entegrasyonu)

---

## 📞 Yardım

**Sorunuz mu var?**

1. 📖 README_FINANCEIQ_PRO.md dosyasını okuyun
2. 🐛 GitHub Issues'a bug bildirin
3. 💬 Discord community'e katılın
4. 📧 support@financeiq.com

---

## 🎉 Başarılı Kurulum!

Artık **Bloomberg Terminal seviyesinde** analiz yapabilirsiniz - tamamen ücretsiz!

**İlk adımlar:**
1. ✅ Test script'i çalıştırın
2. ✅ Örnek portföy ile deneyin
3. ✅ Kendi portföyünüzü yükleyin
4. ✅ ETF verilerini güncelleyin

**Keyifli analizler! 🚀📊💰**

---

*Last updated: 2025-01-25*
