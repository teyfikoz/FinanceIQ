# 🔑 ÜCRETSİZ API ANAHTARLARI ALMA REHBERİ

Bu rehber, Global Liquidity Dashboard için gereken tüm **ÜCRETSİZ** API anahtarlarını nasıl alacağınızı adım adım açıklar.

## 🎯 Özet: Hangi API'ler Gerekli?

| API | Durum | Limit | Ne İçin Kullanılır |
|-----|-------|-------|-------------------|
| **FRED API** | ✅ **GEREKLİ** | 120K/gün | Ekonomik göstergeler, Fed verisi |
| **Alpha Vantage** | 🟡 Opsiyonel | 500/gün | Detaylı hisse analizi |
| **CoinGecko Pro** | 🟡 Opsiyonel | 100K/ay | Kripto veriler (ücretsiz plan var) |
| **Yahoo Finance** | ✅ Otomatik | Sınırsız | Hisse, endeks, döviz (API key yok) |

---

## 1. 🏦 FRED API (Federal Reserve Economic Data) - **GEREKLİ**

### 📋 Ne İçin Kullanılır:
- Fed bilançosu verisi
- M2 para arzı
- Enflasyon oranları
- İşsizlik verileri
- Faiz oranları
- ECB ve BoJ bilançoları

### 🔗 Kayıt Adımları:
1. **Web sitesine gidin**: https://fred.stlouisfed.org/
2. **Hesap oluşturun**: Sağ üstte "Sign In" → "Create Account"
3. **Email doğrulama**: Email'inizde gelen linke tıklayın
4. **API key alın**: https://fred.stlouisfed.org/docs/api/api_key.html
5. **"Request API Key" butonuna tıklayın**
6. **Hemen API key alırsınız** (dakikalar içinde)

### 📊 Limitler:
- **120,000 istek/gün** (çok bol)
- **2 istek/saniye**
- **Tamamen ücretsiz**

### 💡 Örnek API Key:
```
abcd1234567890abcd1234567890abcd
```

---

## 2. 📈 Alpha Vantage API - **Opsiyonel**

### 📋 Ne İçin Kullanılır:
- Detaylı hisse senedi analizi
- Teknik göstergeler (RSI, MACD, Bollinger)
- Gerçek zamanlı fiyatlar
- Tarihsel veriler

### 🔗 Kayıt Adımları:
1. **Web sitesine gidin**: https://www.alphavantage.co/support/#api-key
2. **"Get your free API key today!" linkine tıklayın**
3. **Formu doldurun**:
   - First Name: Adınız
   - Last Name: Soyadınız
   - Email: Email adresiniz
   - How will you use Alpha Vantage?: "Personal research and analysis"
4. **Submit butonuna tıklayın**
5. **Hemen API key alırsınız**

### 📊 Limitler:
- **500 istek/gün** (ücretsiz plan)
- **5 istek/dakika**
- **Tamamen ücretsiz**

### 💡 Örnek API Key:
```
ABC123DEF456
```

---

## 3. 🪙 CoinGecko Pro API - **Opsiyonel**

### 📋 Ne İçin Kullanılır:
- Kripto para fiyatları
- Market cap verileri
- Trading volume
- Fear & Greed Index

### 🔗 Kayıt Adımları:
1. **Web sitesine gidin**: https://www.coingecko.com/en/api/pricing
2. **"Start Free" butonuna tıklayın**
3. **Hesap oluşturun** (Google ile hızlı kayıt)
4. **Email doğrulama**
5. **Dashboard'dan API key alın**

### 📊 Limitler:
- **100,000 istek/ay** (ücretsiz plan)
- **50 istek/dakika**
- **API key olmadan da 10-50 istek/dakika**

### 💡 Not:
CoinGecko API key'i olmadan da çalışır, ancak daha düşük limitlerle.

---

## 4. 📊 Yahoo Finance - **Otomatik**

### 📋 Ne İçin Kullanılır:
- Hisse senedi fiyatları (ABD ve Türkiye)
- Endeks verileri (S&P 500, BIST 100)
- Döviz kurları (USD/TRY, EUR/USD)
- Emtia fiyatları (altın, petrol)

### ✅ Avantajlar:
- **API key gerektirmez**
- **Tamamen ücretsiz**
- **Sınırsız kullanım**
- **Türk hisse senetleri dahil**

### 🔧 Kullanım:
`yfinance` Python kütüphanesi ile otomatik çalışır.

---

## 🔧 API Anahtarlarını Nasıl Kullanırsınız?

### 1. `.env` Dosyasını Oluşturun:
```bash
cd global_liquidity_dashboard
cp .env.example .env
nano .env
```

### 2. API Anahtarlarını Ekleyin:
```env
# FRED API (GEREKLİ)
FRED_API_KEY=your_fred_api_key_here

# Alpha Vantage (Opsiyonel)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# CoinGecko Pro (Opsiyonel)
COINGECKO_API_KEY=your_coingecko_key_here
```

### 3. Dashboard'u Yeniden Başlatın:
```bash
# Mevcut Streamlit'i durdurun (Ctrl+C)
# Sonra yeniden başlatın:
streamlit run dashboard/multilingual_app.py --server.port 8502
```

---

## 🚀 API Key'ler Olmadan Kullanım

Dashboard, API key'ler olmadan da çalışır:
- **Yahoo Finance**: Otomatik çalışır (API key gerektirmez)
- **Örnek Veriler**: Gerçekçi örnek verilerle demo
- **Türk Hisse Senetleri**: Yahoo Finance üzerinden otomatik

### 🎯 Öncelik Sırası:
1. **İlk olarak**: FRED API key alın (en önemli)
2. **İkinci olarak**: Alpha Vantage (hisse analizi için)
3. **Üçüncü olarak**: CoinGecko Pro (kripto için)

---

## 🔍 API Key'lerin Test Edilmesi

### FRED API Testi:
```bash
curl "https://api.stlouisfed.org/fred/series?series_id=GDP&api_key=YOUR_KEY&file_type=json"
```

### Alpha Vantage Testi:
```bash
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"
```

### CoinGecko Testi:
```bash
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&x_cg_pro_api_key=YOUR_KEY"
```

---

## 🛠️ Sorun Giderme

### ❌ API Key Çalışmıyorsa:
1. **Key'i doğru kopyaladığınızdan emin olun**
2. **Boşluk karakteri olmadığından emin olun**
3. **Email doğrulamasını yaptığınızdan emin olun**
4. **Günlük limitinizi aşmadığınızdan emin olun**

### 🔄 API Key Yenileme:
- **FRED**: Süresiz geçerli
- **Alpha Vantage**: Süresiz geçerli
- **CoinGecko**: Süresiz geçerli

### 📧 Destek:
- **FRED**: support@stlouisfed.org
- **Alpha Vantage**: support@alphavantage.co
- **CoinGecko**: hello@coingecko.com

---

## 🎉 Tamamlandı!

API anahtarlarınızı aldıktan sonra:

1. **✅ `.env` dosyasına ekleyin**
2. **✅ Dashboard'u yeniden başlatın**
3. **✅ Gerçek verilerle analiz yapmaya başlayın**

**Dashboard URL'leri:**
- **Temel Dashboard**: http://localhost:8501
- **Gelişmiş Dashboard (Türkçe/İngilizce)**: http://localhost:8502

---

## 💰 Toplam Maliyet: **0 TL**

Tüm API'ler ücretsiz planlarla kullanılabilir! 🎉