# 🚀 Quick Start Guide - FundPortal with Full API Integration

## ✅ API Keys Configured!

Tüm API key'lerin başarıyla yapılandırıldı:

```
✅ FRED API: 629b7...dbbd
✅ Finnhub API: d4av0c...hlc20
✅ Alpha Vantage: BYBVGO...Y25VJ
✅ TradingEconomics: 3634da...dtvr
✅ Polygon.io: FzBpuj...pt0Ds
✅ FMP (Financial Modeling Prep): FQKKwm...ihGHK
```

---

## 🎯 3 Adımda Başla

### 1️⃣ Uygulamayı Başlat (30 saniye)

```bash
cd /Users/teyfikoz/Downloads/Borsa\ Analiz/global_liquidity_dashboard
streamlit run main.py
```

### 2️⃣ API'leri Test Et (2 dakika)

```bash
python3 test_all_apis.py
```

Bu script tüm API'leri test edip rapor verecek.

### 3️⃣ Uygulamada Kullan!

API'ler otomatik yüklenecek. Artık:

- 📊 **Cycle Intelligence** → FRED data ile döngü analizi
- 📰 **News** → Finnhub'dan gerçek haberler
- 🇹🇷 **TEFAS Fonları** → Türk fonları canlı
- 💰 **Crypto** → Binance fiyatları
- 📈 **Stocks** → Yahoo + FMP + Alpha Vantage fallback

---

## 💻 Kod Kullanımı

### Basit Kullanım (Tek Satır)

```python
from utils.market_data_engine import market

# Hisse fiyatı
apple = market.get_stock('AAPL')
print(f"Apple: ${apple['price']}")

# Kripto fiyatı
btc = market.get_crypto('BTC')
print(f"Bitcoin: ${btc['price']}")

# TEFAS fonu
tcd = market.get_fund('TCD')
print(f"TCD Fon: {tcd['current_price']}")

# Makro data
gdp = market.get_macro('gdp')
print(f"GDP: {gdp['value']}")
```

### Gelişmiş Kullanım

```python
from utils.market_data_engine import market

# Çoklu hisse
stocks = market.get_multiple_stocks(['AAPL', 'GOOGL', 'MSFT'])
for symbol, data in stocks.items():
    print(f"{symbol}: ${data['price']}")

# TEFAS fon geçmişi (pandas DataFrame)
df = market.get_fund_dataframe('TCD', start_date='2023-01-01')
print(df.head())

# ETF kompozisyonu
holdings = market.get_etf_holdings('SPY')
for holding in holdings[:5]:
    print(holding)

# Haber + sentiment
news = market.get_news(symbol='AAPL')
sentiment = market.get_sentiment('AAPL')
```

### Direct API Kullanımı

```python
from utils.unified_api_manager import api_manager

# FRED
gdp_data = api_manager.get_fred_series('GDP')

# FMP
quote = api_manager.get_fmp_quote('AAPL')
profile = api_manager.get_fmp_profile('AAPL')

# TEFAS
fund_history = api_manager.get_tefas_fund_history('TCD', '2023-01-01')

# Binance
btc_ticker = api_manager.get_binance_ticker('BTCUSDT')

# Finnhub
news = api_manager.get_finnhub_news('AAPL')
sentiment = api_manager.get_finnhub_sentiment('AAPL')
```

---

## 📊 API Status Kontrol

### Python'da:

```python
from utils.market_data_engine import market

status = market.get_api_status()
for api, info in status.items():
    print(f"{api}: {'✅' if info['configured'] else '❌'}")
```

### Uygulamada:

1. **Settings** tab → **API Configuration**
2. Status Dashboard'u kontrol et
3. Tüm API'lerin ✅ olduğunu gör

---

## 🔧 Troubleshooting

### API çalışmıyor?

```python
# Cache temizle
from utils.market_data_engine import market
market.clear_cache()

# API status kontrol
status = market.get_api_status()
print(status)
```

### Rate limit hatası?

API'ler otomatik rate limit yönetiyor. Eğer limit aşılırsa:

- ✅ Otomatik cache'den servis eder
- ✅ Fallback API'ye geçer
- ⏳ Gerekirse bekler

### TEFAS veri gelmiyor?

```python
# TEFAS test
from utils.market_data_engine import market

fund = market.get_fund('TCD')
print(fund)

# Boş geliyorsa, direkt API test:
from utils.unified_api_manager import api_manager
history = api_manager.get_tefas_fund_history('TCD', '2024-01-01')
print(history)
```

---

## 📈 Özellikler

### ✅ Çalışan API'ler:

| API | Status | Limit | Kullanım |
|-----|--------|-------|----------|
| Yahoo Finance | ✅ | Unlimited | Primary stock data |
| FRED | ✅ | Unlimited | Macro data |
| FMP | ✅ | 250/day | Stock/ETF/Crypto backup |
| TEFAS | ✅ | Unlimited | Turkish funds |
| Finnhub | ✅ | 60/min | News & sentiment |
| Alpha Vantage | ✅ | 25/day | Stock backup |
| Polygon | ✅ | 5/min | Stock backup |
| TradingEconomics | ✅ | 500/month | Economic calendar |
| Binance | ⚠️  | 1200/min | Crypto (key optional) |

### 🎯 Coverage:

- 📊 **Stocks**: Yahoo (primary) + FMP + Alpha Vantage + Finnhub + Polygon
- 💰 **Crypto**: Binance + FMP + CoinGecko
- 🇹🇷 **Funds**: TEFAS (full coverage)
- 📈 **Macro**: FRED + World Bank + TradingEconomics
- 📰 **News**: Finnhub + NewsAPI
- 🎯 **ETFs**: FMP holdings + Yahoo prices

---

## 🚀 Production Deployment

### Environment Variables (Opsiyonel)

```bash
# .env dosyası oluştur
export FRED_API_KEY="629b7edf6527882dd34e63e9d997dbbd"
export FINNHUB_API_KEY="d4av0chr01qp275hlc1gd4av0chr01qp275hlc20"
export ALPHA_VANTAGE_KEY="BYBVGOL3FJUY25VJ"
export FMP_API_KEY="FQKKwmFS2XU4qv2RGnpubSVMFydihGHK"
export POLYGON_API_KEY="FzBpujruNLMWzu9gkd059VxCpIipt0Ds"
export TRADINGECONOMICS_KEY="3634da0992cf49f:uvn9offvqlvdtvr"
```

**NOT:** API key'ler zaten `config/api_keys.json`'da! Environment variables opsiyonel.

### Heroku Deployment

```bash
# Heroku'da environment variables set et
heroku config:set FRED_API_KEY="629b7edf6527882dd34e63e9d997dbbd"
heroku config:set FINNHUB_API_KEY="d4av0chr01qp275hlc1gd4av0chr01qp275hlc20"
# ... diğerleri

# Deploy
git push heroku main
```

### Docker

```dockerfile
# API keys'i Docker secrets olarak ekle
docker secret create fred_key /path/to/fred_key.txt
docker secret create finnhub_key /path/to/finnhub_key.txt
```

---

## 💰 Maliyet

### Şu Anki Durum: **$0/month**

```
Günlük Kapasite:
├── Yahoo Finance: Unlimited
├── FRED: Unlimited
├── TEFAS: Unlimited
├── FMP: 250 calls/day
├── Finnhub: 86,400 calls/day
├── Binance: 1,728,000 calls/day
└── TOTAL: 2M+ calls/day

Cache Hit Rate: 80% hedef
Effective Capacity: 10M+ calls/day
```

### 100+ User: **Hala $0**
### 1000+ User: **~$150/month** (opsiyonel upgrades)

---

## 📚 Daha Fazla Bilgi

- **API Setup Guide:** `docs/FREE_API_SETUP_GUIDE.md`
- **API Usage Strategy:** `docs/API_USAGE_STRATEGY.md`
- **Setup Checklist:** `docs/API_SETUP_CHECKLIST.md`

---

## ✅ Hazır!

```bash
# Test yap
python3 test_all_apis.py

# Uygulamayı başlat
streamlit run main.py

# Enjoy! 🎉
```

**Artık sıfır maliyet ile 2M+ daily request kapasitesine sahipsin!** 🚀
