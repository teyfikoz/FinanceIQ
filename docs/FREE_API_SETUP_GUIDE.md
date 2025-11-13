# 🔑 Ücretsiz API Kayıt Rehberi

Bu rehber, FinanceIQ uygulamasında kullanabileceğin tüm ücretsiz API'leri nasıl alacağını gösterir.

---

## 📊 ETF & Hisse Senedi (Global)

### 1️⃣ **Alpha Vantage** (Önerilen!)
**Limit:** 25 requests/day (ücretsiz) | 500 requests/day (öğrenci/kişisel)

**Kayıt:**
1. Git: https://www.alphavantage.co/support/#api-key
2. Email: `teyfikoz@yahoo.com`
3. "Get Your Free API Key Today" butonuna tıkla
4. Formu doldur:
   - First Name: Tefik
   - Email: teyfikoz@yahoo.com
   - Organization: Personal Use
   - How will you use: Personal finance tracking
5. ✅ API key hemen gelecek

**Sağladığı Veriler:**
- ✅ Hisse senedi fiyatları (realtime + historical)
- ✅ Teknik göstergeler (RSI, MACD, EMA, SMA)
- ✅ Global quotes
- ✅ Forex data
- ✅ Crypto prices
- ✅ Economic indicators (GDP, CPI, inflation)

**Rate Limit Stratejisi:**
```python
# 25 request/day = her 1 saatte ~1 request
# Cache: 1 saat
# Priority: Sadece kritik datalar için kullan
```

---

### 2️⃣ **Yahoo Finance** (Ücretsiz & Sınırsız!)
**Limit:** Yok (unofficial API, yfinance library kullanıyoruz)

**Kayıt:** ❌ Gerekmiyor! Zaten entegre.

**Sağladığı Veriler:**
- ✅ Hisse senedi fiyatları (realtime)
- ✅ ETF data
- ✅ Crypto prices
- ✅ Options data
- ✅ Financials (balance sheet, income statement)
- ✅ Historical data

**Kullanımda:**
```python
import yfinance as yf
# Zaten kullanıyoruz, rate limit yok!
```

---

## 🇹🇷 Fon (Türkiye)

### 3️⃣ **TEFAS API** (Ücretsiz & Açık!)
**Limit:** Yok

**Kayıt:** ❌ Gerekmiyor!

**Endpoint:**
```
https://ws.tefas.gov.tr/PortfolioInformationService.asmx
```

**Sağladığı Veriler:**
- ✅ Tüm TEFAS fonları
- ✅ Günlük fiyatlar
- ✅ Portföy kompozisyonu
- ✅ Historical data

**Not:** XML formatında geliyor, parser yazacağız.

---

### 4️⃣ **Investpy** (Ücretsiz Library)
**Limit:** Yok

**Kayıt:** ❌ Gerekmiyor!

```bash
pip install investpy
```

**Sağladığı Veriler:**
- ✅ Türkiye hisse senetleri
- ✅ ETF'ler
- ✅ Fonlar
- ✅ Tahviller

---

## 💰 Kripto

### 5️⃣ **Binance API** (Ücretsiz!)
**Limit:** 1200 requests/minute (API key olmadan)
**Limit (API Key ile):** 6000 requests/minute

**Kayıt:**
1. Git: https://www.binance.com/en/support/faq/how-to-create-api-360002502072
2. Binance hesabı aç (email: teyfikoz@yahoo.com)
3. Account → API Management
4. Create API Key
   - Label: "FinanceIQ App"
   - Restrictions: Enable Reading ✅, Disable Trading ❌
5. ✅ API Key + Secret Key alacaksın

**Sağladığı Veriler:**
- ✅ Crypto prices (realtime)
- ✅ Order book
- ✅ Historical klines
- ✅ 24h ticker
- ✅ Market depth

---

### 6️⃣ **CoinGecko** (Ücretsiz & Önerilen!)
**Limit:** 10-50 requests/minute (API key olmadan)

**Kayıt:**
1. Git: https://www.coingecko.com/en/api
2. Email ile kayıt ol: teyfikoz@yahoo.com
3. Free tier seç
4. ✅ API key gelecek (opsiyonel, key olmadan da çalışır!)

**Sağladığı Veriler:**
- ✅ 10,000+ crypto prices
- ✅ Market cap
- ✅ Volume
- ✅ Dominance metrics
- ✅ Historical data

**Not:** Zaten uygulamada kullanıyoruz!

---

## 📈 Makro Döngüler & Ekonomik Data

### 7️⃣ **FRED API** (Federal Reserve - Ücretsiz!)
**Limit:** Yok!

**Kayıt:**
1. Git: https://fred.stlouisfed.org/docs/api/api_key.html
2. "Request API Key" tıkla
3. Email: teyfikoz@yahoo.com
4. Account bilgileri doldur
5. ✅ API key hemen gelecek

**Sağladığı Veriler:**
- ✅ GDP, CPI, inflation
- ✅ Unemployment rate
- ✅ Fed funds rate
- ✅ M2 money supply
- ✅ Treasury yields
- ✅ 500,000+ economic indicators

**Kullanım:**
```python
# Örnek: GDP data
https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=YOUR_KEY
```

---

### 8️⃣ **TradingEconomics** (Ücretsiz Tier)
**Limit:** 500 requests/month (ücretsiz)

**Kayıt:**
1. Git: https://tradingeconomics.com/api/
2. "Start Free Trial" (kredi kartı gerektirmez!)
3. Email: teyfikoz@yahoo.com
4. ✅ API key gelecek

**Sağladığı Veriler:**
- ✅ Global economic calendar
- ✅ Country indicators (200+ countries)
- ✅ PMI, retail sales, industrial production
- ✅ Forecasts

---

### 9️⃣ **World Bank API** (Tamamen Ücretsiz!)
**Limit:** Yok

**Kayıt:** ❌ Gerekmiyor!

**Endpoint:**
```
https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.CD
```

**Sağladığı Veriler:**
- ✅ Global GDP
- ✅ Inflation rates
- ✅ Population
- ✅ Poverty metrics

---

## 📰 Alternatif Veri (Sentiment, News)

### 🔟 **Finnhub** (Ücretsiz!)
**Limit:** 60 requests/minute

**Kayıt:**
1. Git: https://finnhub.io/register
2. Email: teyfikoz@yahoo.com
3. Password: (güçlü bir şifre seç)
4. ✅ Dashboard'dan API key kopyala

**Sağladığı Veriler:**
- ✅ Stock news
- ✅ Market sentiment
- ✅ Company news
- ✅ Earnings calendar
- ✅ Insider transactions
- ✅ Social sentiment (Reddit, Twitter)

---

### 1️⃣1️⃣ **NewsAPI** (Ücretsiz Tier)
**Limit:** 100 requests/day

**Kayıt:**
1. Git: https://newsapi.org/register
2. Email: teyfikoz@yahoo.com
3. ✅ API key hemen gelecek

**Sağladığı Veriler:**
- ✅ Financial news
- ✅ Breaking news
- ✅ News sources filtering

---

### 1️⃣2️⃣ **Polygon.io** (Ücretsiz Tier)
**Limit:** 5 requests/minute (ücretsiz)

**Kayıt:**
1. Git: https://polygon.io/dashboard/signup
2. Email: teyfikoz@yahoo.com
3. Free tier seç
4. ✅ API key gelecek

**Sağladığı Veriler:**
- ✅ Stocks, options, forex, crypto
- ✅ Market status
- ✅ Aggregates
- ✅ Last trade/quote

---

## 🎯 Önerilen API Stratejisi

### Öncelik Sırası:
1. **Yahoo Finance** (primary) - Sınırsız, ücretsiz
2. **FRED** (macro data) - Sınırsız, ücretsiz
3. **TEFAS** (Turkish funds) - Sınırsız, ücretsiz
4. **CoinGecko** (crypto) - Zaten entegre
5. **Alpha Vantage** (backup) - 25/day limit
6. **Finnhub** (news/sentiment) - 60/min
7. **Binance** (crypto backup) - 1200/min
8. **World Bank** (global macro) - Sınırsız

### Cache Stratejisi:
| Veri Tipi | Cache Süresi | API |
|-----------|--------------|-----|
| Hisse fiyatları | 1 dakika | Yahoo Finance |
| Crypto fiyatları | 30 saniye | CoinGecko |
| Makro data | 24 saat | FRED |
| Fonlar (TEFAS) | 1 saat | TEFAS |
| News | 15 dakika | Finnhub |
| Economic calendar | 12 saat | TradingEconomics |

---

## 🔐 API Key Güvenliği

**API key'leri ASLA kodda hardcode etme!**

**Kullanım:**
```python
# .env dosyası oluştur:
ALPHA_VANTAGE_KEY=your_key_here
FRED_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_secret_here
TRADINGECONOMICS_KEY=your_key_here
NEWSAPI_KEY=your_key_here
POLYGON_API_KEY=your_key_here
```

**Güvenlik:**
- ✅ `.env` dosyasını `.gitignore`'a ekle
- ✅ API key'leri asla commit etme
- ✅ Read-only permissions kullan (trading disable)

---

## 📊 Maliyet Hesabı

**Ücretsiz Limitler:**
- Yahoo Finance: ♾️ Sınırsız
- FRED: ♾️ Sınırsız
- TEFAS: ♾️ Sınırsız
- CoinGecko: 10-50/min = ~72,000/day
- Alpha Vantage: 25/day
- Finnhub: 60/min = ~86,400/day
- Binance: 1200/min = ~1.7M/day
- NewsAPI: 100/day
- TradingEconomics: 500/month
- Polygon: 5/min = ~7,200/day

**Toplam Günlük Kapasite:**
- ~2 milyon+ request/day
- **$0 maliyet** ✅

---

## 🚀 Sonraki Adım

1. ✅ Yukarıdaki linklere git
2. ✅ API key'leri al (5-10 dakika)
3. ✅ API key'leri bana ver
4. ✅ Ben entegre edeyim!

**Hangi API'lerle başlamak istersin?** Hepsini mi yoksa önce critical olanları mı?
