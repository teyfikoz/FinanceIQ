# ✅ API Setup Checklist

Uygulamayı sıfır maliyetle canlıya almak için bu adımları takip et:

---

## 🎯 Öncelikli API'ler (İlk 15 Dakika)

Bu 4 API ile uygulamanın %90'ı çalışır:

### 1. ✅ Yahoo Finance
- **Status:** ✅ Zaten entegre!
- **Action:** Hiçbir şey yapma
- **Limit:** Sınırsız
- **Priority:** 🔥 CRITICAL

### 2. ⏳ FRED (Federal Reserve)
- **URL:** https://fred.stlouisfed.org/docs/api/api_key.html
- **Steps:**
  1. "Request API Key" tıkla
  2. Email: `teyfikoz@yahoo.com`
  3. Form doldur (2 dakika)
  4. Email'den API key kopyala
  5. Uygulamada: Settings → API Configuration → FRED
- **Limit:** Sınırsız
- **Priority:** 🔥 CRITICAL
- **Time:** 3 dakika

### 3. ⏳ Finnhub (News & Sentiment)
- **URL:** https://finnhub.io/register
- **Steps:**
  1. Email ile kayıt ol: `teyfikoz@yahoo.com`
  2. Dashboard'a git
  3. API key kopyala
  4. Uygulamada: Settings → API Configuration → Finnhub
- **Limit:** 60/minute (86,400/day)
- **Priority:** 🔥 HIGH
- **Time:** 2 dakika

### 4. ✅ CoinGecko
- **Status:** ✅ Zaten entegre!
- **Action:** Hiçbir şey yapma (key olmadan da çalışıyor)
- **Limit:** 50/minute
- **Priority:** 🔥 HIGH

---

## 🚀 Önerilen API'ler (Sonraki 10 Dakika)

Bu API'ler ek özellikler sağlar:

### 5. ⏳ Binance (Crypto)
- **URL:** https://www.binance.com/en/support/faq/how-to-create-api-360002502072
- **Steps:**
  1. Binance hesabı aç (email: teyfikoz@yahoo.com)
  2. Account → API Management
  3. Create API Key
  4. **IMPORTANT:** Enable "Reading" ✅, Disable "Trading" ❌
  5. API Key + Secret Key kopyala
  6. Uygulamada: Settings → API Configuration → Binance
- **Limit:** 1200/minute
- **Priority:** 🟡 MEDIUM
- **Time:** 5 dakika

### 6. ⏳ NewsAPI
- **URL:** https://newsapi.org/register
- **Steps:**
  1. Email ile kayıt: `teyfikoz@yahoo.com`
  2. API key hemen gelecek
  3. Uygulamada: Settings → API Configuration → NewsAPI
- **Limit:** 100/day
- **Priority:** 🟡 MEDIUM
- **Time:** 2 dakika

---

## 💼 Opsiyonel API'ler (İhtiyaç Halinde)

### 7. ⚪ Alpha Vantage (Backup)
- **URL:** https://www.alphavantage.co/support/#api-key
- **Steps:** Basit form
- **Limit:** 25/day
- **Priority:** ⚪ LOW (sadece Yahoo fail olursa)
- **Time:** 2 dakika

### 8. ⚪ TradingEconomics
- **URL:** https://tradingeconomics.com/api/
- **Limit:** 500/month
- **Priority:** ⚪ LOW
- **Time:** 3 dakika

### 9. ⚪ Polygon.io
- **URL:** https://polygon.io/dashboard/signup
- **Limit:** 5/minute
- **Priority:** ⚪ LOW
- **Time:** 2 dakika

---

## 📝 Setup Process

### Adım 1: API Key'leri Al (15 dakika)

```bash
☐ FRED API key aldım
☐ Finnhub API key aldım
☐ Binance API key aldım (opsiyonel)
☐ NewsAPI key aldım (opsiyonel)
```

### Adım 2: Uygulamada Yapılandır (5 dakika)

1. Uygulamayı başlat:
   ```bash
   streamlit run main.py
   ```

2. Login (demo/demo123)

3. Git: **Settings tab** → **API Configuration**

4. Her API için key'leri gir ve **Save** tıkla

5. **Status Dashboard**'u kontrol et:
   ```
   ✅ yahoo: Configured
   ✅ fred: Configured
   ✅ finnhub: Configured
   ✅ coingecko: Configured
   ```

### Adım 3: Test Et (2 dakika)

1. **Cycle Intelligence** tabına git
2. Analiz yüklendiğinde başarılı! ✅

3. **Stock Research** → Bir hisse ara
4. Data geliyorsa başarılı! ✅

5. **Crypto** → BTC fiyatı görüyorsan başarılı! ✅

---

## 🔐 Güvenlik

### ✅ Yapılması Gerekenler

```bash
# .env dosyası oluştur (opsiyonel)
cp .env.example .env

# API key'leri .env'e ekle
echo "FRED_API_KEY=your_key_here" >> .env
echo "FINNHUB_API_KEY=your_key_here" >> .env

# VEYA: UI'dan yapılandır (önerilen)
# Settings → API Configuration
```

### ❌ Yapılmaması Gerekenler

- ❌ API key'leri asla git'e commit etme
- ❌ API key'leri screenshot'ta paylaşma
- ❌ Binance API'de "Trading" iznini açma
- ❌ API key'leri public yerlerde paylaşma

---

## 📊 Sonuç

### Minimum Setup (5 dakika)
```
✅ Yahoo Finance (zaten entegre)
✅ FRED API
✅ CoinGecko (zaten entegre)
```
**Result:** Core features çalışır! 🎉

### Recommended Setup (15 dakika)
```
✅ Yahoo Finance
✅ FRED API
✅ Finnhub API
✅ CoinGecko
✅ Binance API
✅ NewsAPI
```
**Result:** Full features! 🚀

### Maximum Setup (25 dakika)
```
✅ Hepsi yukarıdaki + Alpha Vantage + TradingEconomics + Polygon
```
**Result:** Ultimate coverage! 🌟

---

## 🎯 İlk 3 API ile Başla

**Öncelik sırasına göre:**

1. **FRED** - 3 dakika → Cycle Intelligence için kritik
2. **Finnhub** - 2 dakika → News & sentiment için
3. **Binance** - 5 dakika (opsiyonel) → Crypto detay için

**Toplam:** 10 dakika

**Maliyet:** $0

**Kapasite:** 100+ user/day

---

## 📞 Destek

**Sorular:**
- API key alamıyorsan: `docs/FREE_API_SETUP_GUIDE.md`
- Rate limit hataları: `docs/API_USAGE_STRATEGY.md`
- Configuration sorunları: Settings → API Configuration → Status Dashboard

**Ready to go!** 🚀
