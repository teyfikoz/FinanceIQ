# 🎯 API Usage Strategy - Zero Cost Operations

## Genel Bakış

FinanceIQ uygulaması **tamamen ücretsiz API'ler** kullanarak günde **2+ milyon request** kapasitesine sahip.

---

## 📊 API Önceliklendirme Sistemi

### Tier 1: Primary (Unlimited & Free)
Bu API'ler hiç rate limit olmadan kullanılıyor:

| API | Kullanım | Maliyet | Priority |
|-----|----------|---------|----------|
| **Yahoo Finance** | Hisse, ETF, crypto fiyatları | $0 | 🟢 HIGH |
| **FRED** | Makro ekonomik data | $0 | 🟢 HIGH |
| **TEFAS** | Türk fonları | $0 | 🟢 HIGH |
| **World Bank** | Global ekonomik göstergeler | $0 | 🟢 MEDIUM |

**Strateji:** Her zaman önce bu API'leri kullan!

---

### Tier 2: High Limit (Free with limits)
Günlük/dakikalık yüksek limitli API'ler:

| API | Limit | Kullanım | Maliyet |
|-----|-------|----------|---------|
| **CoinGecko** | 50/min | Crypto fiyatları | $0 |
| **Binance** | 1200/min | Crypto trading data | $0 |
| **Finnhub** | 60/min | News, sentiment | $0 |
| **Polygon** | 5/min | Backup stock data | $0 |

**Strateji:** Cache agresif kullan (30 saniye - 15 dakika)

---

### Tier 3: Limited (Free but restricted)
Günlük limiti olan API'ler:

| API | Limit | Kullanım | Öneri |
|-----|-------|----------|-------|
| **Alpha Vantage** | 25/day | Backup stock data | Sadece Yahoo fail olursa |
| **NewsAPI** | 100/day | Haber başlıkları | Cache 15 dakika |
| **TradingEconomics** | 500/month | Economic calendar | Cache 12 saat |

**Strateji:** Sadece fallback olarak kullan!

---

## 🔄 Caching Strategy

### Cache Duration (TTL) per Data Type

```python
CACHE_DURATIONS = {
    # Real-time data (aggressive cache)
    'stock_price': 60,          # 1 dakika
    'crypto_price': 30,          # 30 saniye
    'forex': 60,                 # 1 dakika

    # Semi-static data (moderate cache)
    'news': 900,                 # 15 dakika
    'funds': 3600,               # 1 saat
    'etf_composition': 3600,     # 1 saat

    # Static data (long cache)
    'macro_data': 86400,         # 24 saat
    'economic_calendar': 43200,  # 12 saat
    'company_info': 86400,       # 24 saat
    'historical': 3600,          # 1 saat
}
```

### Cache Hit Rate Hedefi
- **Target:** 80%+ cache hit rate
- **Benefit:** 80% of requests served from cache = 5x capacity multiplier

---

## 🎯 Request Optimization Techniques

### 1. Batch Requests
```python
# ❌ Bad: 100 ayrı request
for symbol in symbols:
    price = get_price(symbol)

# ✅ Good: 1 batch request
prices = yf.download(symbols, group_by='ticker')
```

### 2. Prefetching
```python
# Popüler sembolleri background'da önceden cache'le
POPULAR_SYMBOLS = ['SPY', 'QQQ', 'AAPL', 'TSLA', ...]
prefetch_data(POPULAR_SYMBOLS)
```

### 3. Lazy Loading
```python
# Sadece kullanıcı tıkladığında detay çek
if st.button("Show Details"):
    detailed_data = fetch_detailed_data()
```

### 4. Fallback Chain
```python
# Otomatik fallback
def get_stock_price(symbol):
    # 1. Try Yahoo (unlimited)
    result = yahoo.get_price(symbol)
    if result: return result

    # 2. Try cache
    cached = cache.get(symbol)
    if cached: return cached

    # 3. Try Alpha Vantage (limited)
    result = alpha_vantage.get_price(symbol)
    if result: return result

    # 4. Try Finnhub (limited)
    result = finnhub.get_price(symbol)
    return result
```

---

## 📈 Daily Request Budget

### Kullanıcı Başına Tahmin (aktif kullanım)

| Feature | Requests/User/Day | API Used |
|---------|-------------------|----------|
| Dashboard view | 50 | Yahoo (cached) |
| Stock research | 20 | Yahoo + Alpha Vantage |
| Screener | 100 | Yahoo (batch) |
| News feed | 10 | Finnhub (cached) |
| Cycle analysis | 5 | FRED (unlimited) |
| Crypto tracking | 30 | CoinGecko (cached) |
| **TOTAL** | **215 req/user/day** | Mostly cached |

### Capacity per API

**Yahoo Finance:**
- Limit: ∞
- Capacity: 10,000+ users/day

**FRED:**
- Limit: ∞
- Capacity: 10,000+ users/day

**CoinGecko:**
- Limit: 50/min = 72,000/day
- With 80% cache hit: 360,000 effective requests/day
- Capacity: 1,000+ users/day

**Finnhub:**
- Limit: 60/min = 86,400/day
- With 80% cache hit: 432,000 effective requests/day
- Capacity: 2,000+ users/day

**Alpha Vantage:**
- Limit: 25/day (backup only)
- Usage: <5% of requests
- Sufficient for 100+ users

---

## 🚀 Scaling Strategy

### Phase 1: 0-100 users/day
- **Cost:** $0/month
- **APIs:** Free tier her şeyi karşılar
- **Cache:** In-memory cache yeterli

### Phase 2: 100-1000 users/day
- **Cost:** $0/month (hala ücretsiz!)
- **Optimization:** Redis cache ekle
- **Upgrade:** Alpha Vantage Pro ($50/month) opsiyonel

### Phase 3: 1000-10000 users/day
- **Cost:** ~$100-200/month
- **Upgrades:**
  - Alpha Vantage Pro: $50/month
  - Finnhub Starter: $0 (hala ücretsiz yeterli!)
  - CoinGecko Analyst: $129/month (opsiyonel)
  - CDN + Redis: $50/month

### Phase 4: 10000+ users/day
- **Cost:** ~$500-1000/month
- **Architecture:**
  - Dedicated Redis cluster
  - CDN (Cloudflare)
  - API Gateway
  - Load balancer

---

## 💡 Cost Optimization Tips

### 1. User Behavior Analysis
```python
# Track most requested data
track_popular_queries()
# Agresif cache popular queries
```

### 2. Smart Prefetching
```python
# S&P 500 stocks'u her sabah prefetch et
if hour == 9:
    prefetch_sp500_data()
```

### 3. Regional API Selection
```python
# Türk kullanıcı için TEFAS prioritize et
if user.location == 'TR':
    use_tefas_primary()
```

### 4. Time-based Caching
```python
# Market saatleri dışında daha uzun cache
if is_market_closed():
    cache_duration *= 10
```

---

## 📊 Monitoring & Alerts

### Key Metrics to Track

```python
# API Usage Dashboard
{
    "daily_requests": {
        "yahoo": 5000,
        "fred": 200,
        "finnhub": 1500,
        "alpha_vantage": 10,  # Should stay low!
    },
    "cache_hit_rate": 0.82,  # Target: >80%
    "avg_response_time": 150,  # ms
    "error_rate": 0.01,  # Target: <1%
}
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Alpha Vantage daily usage | >15/25 | >23/25 |
| Cache hit rate | <70% | <60% |
| Error rate | >2% | >5% |
| Response time | >500ms | >1000ms |

---

## 🔐 Security Best Practices

### API Key Management

1. ✅ **NEVER hardcode keys**
   ```python
   # ❌ Bad
   API_KEY = "abc123..."

   # ✅ Good
   API_KEY = os.getenv('API_KEY')
   ```

2. ✅ **Use read-only permissions**
   - Binance: Enable "Reading" only
   - Disable "Trading", "Withdrawal"

3. ✅ **Rotate keys regularly**
   - Every 3-6 months
   - Immediately if suspicious activity

4. ✅ **Monitor usage**
   - Set up email alerts for unusual activity
   - Track API key usage in dashboard

---

## 📝 Summary

### ✅ Advantages
- 💰 **$0 maliyet** (100+ user'a kadar)
- ⚡ **2M+ requests/day** capacity
- 🛡️ Multiple fallback layers
- 📊 80%+ cache hit rate
- 🌍 Global + Türkiye data coverage

### 🎯 Success Formula

```
Zero Cost Operations =
    Unlimited APIs (Primary) +
    Aggressive Caching (80% hit rate) +
    Smart Fallbacks (Tier system) +
    Batch Processing +
    Rate Limiting
```

### 🚀 Ready to Scale

- Phase 1 (0-100 users): **$0**
- Phase 2 (100-1K users): **$0**
- Phase 3 (1K-10K users): **~$150/month**
- Phase 4 (10K+ users): **~$500/month**

**Current Status:** Phase 1'e hazır! 🎉
