# 🚀 API Entegrasyon Rehberi

## Eklenen Ücretsiz API Entegrasyonları

### 1. 📰 Alpha Vantage API
**Özellikler:**
- Gerçek zamanlı haber sentiment analizi
- Hisse arama (autocomplete)
- Sentiment skorları ve etiketleri

**Kurulum:**
```bash
# API Key alın: https://www.alphavantage.co/support/#api-key
# .env dosyasına ekleyin:
ALPHA_VANTAGE_API_KEY=your_key_here
```

**Limitler:**
- Free tier: 25 request/gün
- 5 request/dakika

**Kullanım:**
```python
from utils.alpha_vantage_api import AlphaVantageAPI

av_api = AlphaVantageAPI()
sentiment = av_api.get_news_sentiment("AAPL", limit=10)
results = av_api.search_symbol("Tesla")
```

---

### 2. 📊 FRED API (Federal Reserve Economic Data)
**Özellikler:**
- Global likidite endeksi (M2 + Fed Balance Sheet)
- Faiz oranları (Fed Funds, Treasury 10Y/2Y)
- Ekonomik göstergeler (GDP, CPI, İşsizlik)

**Kurulum:**
```bash
# API Key alın: https://fred.stlouisfed.org/docs/api/api_key.html
pip install fredapi
# .env dosyasına ekleyin:
FRED_API_KEY=your_key_here
```

**Limitler:**
- Ücretsiz, sınırsız kullanım

**Kullanım:**
```python
from utils.fred_api import FREDAPI

fred_api = FREDAPI()
liquidity = fred_api.get_global_liquidity_index()
rates = fred_api.get_interest_rates()
indicators = fred_api.get_economic_indicators()
```

---

### 3. 💼 Financial Modeling Prep (FMP) API
**Özellikler:**
- Şirket profilleri ve temel veriler
- Finansal oranlar (PE, PB, ROE, vb.)
- Kazanç takvimi
- Şirket haberleri

**Kurulum:**
```bash
# API Key alın: https://site.financialmodelingprep.com/developer/docs/
# .env dosyasına ekleyin:
FMP_API_KEY=your_key_here
```

**Limitler:**
- Free tier: 250 request/gün

**Kullanım:**
```python
from utils.fmp_api import FMPAPI

fmp_api = FMPAPI()
profile = fmp_api.get_company_profile("AAPL")
ratios = fmp_api.get_financial_ratios("AAPL")
earnings = fmp_api.get_earnings_calendar(limit=20)
news = fmp_api.get_stock_news("AAPL", limit=10)
```

---

### 4. 🪙 CoinGecko API
**Özellikler:**
- Kripto fiyatları (bitcoin, ethereum, vb.)
- Global kripto piyasa verileri
- Top 20 kripto para listesi
- Trend olan coin'ler
- Historik veri

**Kurulum:**
```bash
# API Key gerekmez (Free tier)
```

**Limitler:**
- Free tier: 50 request/dakika
- API key gerekmez

**Kullanım:**
```python
from utils.coingecko_api import CoinGeckoAPI

cg_api = CoinGeckoAPI()
prices = cg_api.get_crypto_prices(['bitcoin', 'ethereum'])
global_data = cg_api.get_global_crypto_data()
top_coins = cg_api.get_top_cryptocurrencies(limit=20)
trending = cg_api.get_trending_coins()
history = cg_api.get_coin_history('bitcoin', days=30)
```

---

## 🔍 Hisse Arama (Stock Search)

**Özellikler:**
- Popüler hisseler için hızlı seçim butonları
- Manuel giriş desteği
- Alpha Vantage entegrasyonu (opsiyonel)

**Kullanım:**
```python
from utils.stock_search import simple_stock_search_ui, create_enhanced_stock_search

# Basit arama (API gerekmez)
symbol = simple_stock_search_ui()

# Gelişmiş arama (Alpha Vantage gerekir)
symbol = create_enhanced_stock_search()
```

---

## 🔔 Fiyat Alarm Sistemi

**Özellikler:**
- Hedef fiyat belirleme (üstünde/altında)
- Kullanıcı bazlı alarm yönetimi
- Tetiklenen alarmları takip
- SQLite veritabanı entegrasyonu

**Kullanım:**
```python
from utils.price_alerts import PriceAlertManager, create_price_alerts_ui

# Alarm yöneticisi
alert_mgr = PriceAlertManager()

# Alarm oluştur
alert_mgr.create_alert(
    user_id=1,
    symbol="AAPL",
    target_price=200.00,
    condition="above",
    current_price=180.00
)

# Kullanıcının alarmlarını al
alerts = alert_mgr.get_user_alerts(user_id=1)

# UI ile kullanım
create_price_alerts_ui(user_id=1)
```

---

## 🛠️ Kurulum Adımları

### 1. Gerekli Paketleri Yükleyin
```bash
pip install requests fredapi streamlit
```

### 2. API Anahtarlarını Ayarlayın
```bash
# .env.example dosyasını kopyalayın
cp .env.example .env

# .env dosyasını düzenleyin ve API anahtarlarınızı ekleyin
nano .env
```

### 3. Uygulamayı Başlatın
```bash
streamlit run main.py
```

---

## 📋 Yeni Özellikler

### Ana Sayfa
- ✅ **Auto-refresh**: 30 saniyelik otomatik yenileme toggle (sidebar)
- ✅ **Stock Comparison**: İki hisseyi karşılaştırma aracı
- ✅ **Enhanced Stock Search**: Popüler hisseler + manuel arama

### Yeni Sekmeler
- ✅ **Price Alerts (🔔)**: Fiyat alarm sistemi

### Performans İyileştirmeleri
- ✅ **Batch Download**: Çoklu sembol için tek seferde veri çekimi
- ✅ **TTL Cache**: 1 dakika (real-time), 5 dakika (teknik göstergeler)
- ✅ **Optimized API Calls**: Rate limiting ve fallback mekanizmaları

---

## 📊 API Kullanım Önerileri

### Rate Limiting Stratejileri
1. **Alpha Vantage** (25/gün): En önemli hisseler için kullanın
2. **FMP** (250/gün): Temel veriler ve kazanç takvimi için
3. **FRED** (sınırsız): Makro göstergeler için
4. **CoinGecko** (50/dakika): Kripto veriler için

### Cache Stratejisi
- **Real-time data**: 1-5 dakika TTL
- **News/Sentiment**: 1 saat TTL
- **Economic data**: 24 saat TTL
- **Company fundamentals**: 1 saat TTL

### Fallback Mekanizması
Tüm API'ler başarısız olursa:
1. Cached veri kullanılır
2. Mock veri gösterilir
3. Kullanıcı uyarılır

---

## 🔐 Güvenlik Notları

1. **.env dosyasını asla commit etmeyin**
2. API anahtarlarını paylaşmayın
3. Rate limitlere dikkat edin
4. Hassas verileri şifreleyin

---

## 📈 Gelecek Geliştirmeler (Opsiyonel)

1. **Finnhub WebSocket**: Gerçek zamanlı fiyat akışı
2. **SEC EDGAR**: Insider trading verileri
3. **World Bank API**: Global ekonomik göstergeler
4. **Trading Economics**: Ekonomik takvim
5. **Dark/Light Theme**: Tema seçimi

---

## 🆘 Sorun Giderme

### API Key Hataları
```python
# API key kontrolü
import os
print(os.getenv('ALPHA_VANTAGE_API_KEY'))
```

### Rate Limit Aşımı
- Cache TTL'yi artırın
- Daha az sık veri çekin
- Fallback mekanizmasını kullanın

### Import Hataları
```bash
# Gerekli paketleri yükleyin
pip install -r requirements.txt
```

---

## 📞 Destek

API dokümantasyonları:
- [Alpha Vantage](https://www.alphavantage.co/documentation/)
- [FRED](https://fred.stlouisfed.org/docs/api/fred/)
- [FMP](https://site.financialmodelingprep.com/developer/docs/)
- [CoinGecko](https://www.coingecko.com/en/api/documentation)
