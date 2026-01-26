# FinanceIQ Deployment & Product Guide (Production)

## Executive Summary
FinanceIQ, çoklu piyasa veri akışı, kurumsal yatırımcı analizi, teknik analiz, strateji backtest ve AI destekli içgörüleri tek bir Streamlit uygulamasında birleştiren kurumsal seviye bir finans platformudur. Uygulama tek giriş noktasından (`main.py`) çalışır ve üretim için ölçeklenebilir şekilde modülerleştirilmiştir.

**Canlı uygulama:**
```
https://financeiq.streamlit.app/
```

## 1) Uygulama Nedir?
FinanceIQ, global piyasalar, ETF/fonlar, kripto, Türkiye piyasaları ve kurumsal yatırımcı analizlerini tek bir dashboard içinde sunan profesyonel bir finans analiz platformudur.

## 2) Uygulama Ne İşe Yarar?
- Çoklu piyasa (ABD, Avrupa, Türkiye) veri takibi
- Kurumsal yatırımcı (whale) aktiviteleri ve fon akış analizi
- Teknik analiz, IMSE göstergesi ve strateji backtest
- AI destekli özet, duygu, risk çıkarımı
- TEFAS/KAP gibi Türkiye’ye özel veri kanalları
- Portföy, watchlist ve alert altyapısı

## 3) Temel Özellikler (Özet)
**Ana sekmeler (main.py):**
- 🎯 Dashboard
- 🔍 Stock Research
- 📡 Screener
- 🧪 Strategy Lab
- 📊 ETFs & Funds
- 🏛️ Institutional
- 🇹🇷 Turkish Markets
- 🤖 AI Tools
- 🐋 Whale Intelligence
- 🎲 Entropy Analysis
- 📊 Crypto Dominance
- 🌀 Cycle Intelligence
- 💼 Portfolio
- 👁️ Watchlist
- 🔔 Alerts
- 🔒 Privacy

**Son geliştirmeler:**
- **Indicator Lab:** Günlük/Kısa/Orta/Uzun vade profilleri, IMSE + klasik göstergeler
- **IMSE Export-Ready Pine Script:** Strategy wrapper’lar için seri export
- **Data Quality Katmanı:** Real/Cache/Fallback etiketi ve zaman bilgisi
- **TradingView Bridge (opsiyonel):** Node + @mathieuc/tradingview ile OHLCV alma
- **HF Insights:** Özet + sentiment + risk çıkarımı (HF Inference)

## 4) Mimari ve Giriş Noktaları
- **Giriş noktası:** `main.py`
- **UI/Analytics:** `app/analytics/*`, `app/ui/*`
- **Veri katmanı:** `utils/*`, `app/data_collectors/*`, `api/*`
- **Market data fallback:** `utils/market_data_fetcher.py`
- **DB/kimlik doğrulama:** `utils/database.py`, `utils/authentication.py`

**Auth kontrolü:**
- Varsayılan: direct access (login kapalı)
- Prod için ENV ile açılabilir: `FINANCEIQ_REQUIRE_AUTH=true`

## 5) Sistem Mimarisi (Mermaid)
```mermaid
flowchart TD
    A[main.py] --> B[UI Tabs]
    B --> C[Analytics Modules]
    B --> D[Strategy Lab]
    B --> E[Whale Intelligence]

    C --> F[Market Data Fetcher]
    F --> G[yfinance]
    F --> H[Fallback/Synthetic]
    F --> I[TradingView Bridge (optional)]

    D --> J[Indicator Lab]
    J --> K[IMSE Engine]
    J --> L[Core Indicators]

    E --> M[Fund Flow Radar / TEFAS]
    E --> N[Institutional Events]

    B --> O[HF Insights]
    O --> P[HuggingFace Inference]
```

## 6) Repo ve Harici Kaynaklar
**Ana GitHub Repo:**
```
https://github.com/teyfikoz/FinanceIQ
```

**Beslendiği diğer repo (opsiyonel entegrasyon):**
```
https://github.com/Mathieu2301/TradingView-API
```

**Temel open-source bağımlılık repo referansları:**
```
https://github.com/streamlit/streamlit
https://github.com/ranaroussi/yfinance
https://github.com/plotly/plotly.py
https://github.com/pandas-dev/pandas
https://github.com/numpy/numpy
https://github.com/scikit-learn/scikit-learn
https://github.com/statsmodels/statsmodels
```

## 7) Veri Kaynakları ve API’ler
**Birincil/ücretsiz kaynaklar:**
- Yahoo Finance (yfinance)
- TEFAS (Türk fonları)
- KAP VYK API (Türkiye şirket/kurumsal verileri)

**Opsiyonel/API Key gerektiren kaynaklar:**
- FRED (makro veriler)
- Alpha Vantage
- Financial Modeling Prep (FMP)
- Finnhub
- Polygon
- CoinGecko (Pro API opsiyonel)
- Binance
- NewsAPI
- World Bank
- TradingEconomics

**AI/LLM katmanı:**
- Hugging Face Inference API (Serverless)

**TradingView Bridge:**
- Node + @mathieuc/tradingview
- TradingView session cookie ile daha kararlı veri

## 8) Kurulum ve Çalıştırma (Local)
```bash
cd /Users/teyfikoz/github-projects/FinanceIQ

# bağımlılıklar
pip install -r requirements.txt

# uygulama
streamlit run main.py --server.port 8501
```

Uygulama: http://localhost:8501

## 9) Opsiyonel ENV / Secrets
Uygulama anahtar olmadan çalışır; aşağıdakiler opsiyoneldir:

```bash
# Makro / piyasalar
FRED_API_KEY=...
ALPHA_VANTAGE_API_KEY=...
FMP_API_KEY=...
FINNHUB_API_KEY=...
POLYGON_API_KEY=...
NEWSAPI_KEY=...
COINGECKO_API_KEY=...
BINANCE_API_KEY=...
BINANCE_SECRET_KEY=...

# HF Inference
HF_API_TOKEN=...
HF_SUMMARY_MODEL=facebook/bart-large-cnn
HF_SENTIMENT_MODEL=ProsusAI/finbert
HF_RISK_MODEL=google/flan-t5-base

# TradingView bridge
TRADINGVIEW_SESSION=...
TRADINGVIEW_SIGNATURE=...

# Auth / env
FINANCEIQ_ENV=production
FINANCEIQ_REQUIRE_AUTH=true
FINANCEIQ_DIRECT_ACCESS=false
```

## 10) Streamlit Cloud Deploy (Canlı Örnek)
- Uygulama URL’si: https://financeiq.streamlit.app/
- Ana dosya: `main.py`
- Python: 3.10 / 3.11 önerilir

**Streamlit Secrets örneği:**
```toml
[api_keys]
FRED_API_KEY = "..."
ALPHA_VANTAGE_API_KEY = "..."
FMP_API_KEY = "..."

[ai]
HF_API_TOKEN = "..."
 
[app]
FINANCEIQ_ENV = "production"
FINANCEIQ_REQUIRE_AUTH = false
FINANCEIQ_DIRECT_ACCESS = true
FINANCEIQ_CREATE_DEMO_USER = false
```

## 11) Custom Domain + DNS + SSL (Streamlit Cloud)
1. Streamlit Cloud Dashboard → App → **Settings** → **Custom Domain**
2. Domain girin (ör. `app.financeiq.com`)
3. DNS kayıtları:
   - CNAME: `app.financeiq.com` → Streamlit’in verdiği target
4. SSL: Streamlit otomatik sertifika sağlar (DNS doğrulama tamamlanınca aktif olur)

## 12) Docker (Opsiyonel)
Repo’da `Dockerfile` ve `docker-compose.yml` mevcut. İstersen Docker ile servis edilebilir.

## 13) Kullanım Rehberi (Hızlı)
**1) Dashboard**
- Piyasa özetleri, ana endeksler, likidite göstergeleri

**2) Stock Research**
- Şirket özetleri, teknik analiz, temel metrikler, görseller

**3) Screener**
- Çoklu filtre ile hisse taraması

**4) Strategy Lab**
- Backtesting
- Indicator Lab (IMSE + klasik göstergeler)
- TradingView Tools (Pine export)

**5) Turkish Markets**
- BIST, TEFAS portföy analizi

**6) Whale Intelligence**
- Kurumsal yatırımcı aktiviteleri, correlation, fund flow

**7) AI Tools**
- Monte Carlo, Backtest
- HF Insights (özet/sentiment/risk)

## 14) Ops Checklist (Production)
- [ ] `requirements.txt` güncel
- [ ] `.streamlit/config.toml` mevcut
- [ ] Secrets tanımlandı (HF/FRED vb.)
- [ ] Auth/Direct Access ENV ayarlı
- [ ] TradingView Bridge opsiyonel kurulumu yapıldı
- [ ] Smoke test: `streamlit run main.py`
- [ ] Logging aktif (`FINANCEIQ_LOG_LEVEL=INFO`)
- [ ] Deployment pipeline (Streamlit Cloud) çalışıyor

## 15) Teknik Notlar ve Limitasyonlar
- TradingView veri kullanımı lisans koşullarına tabidir.
- Bazı modüller opsiyonel API key gerektirir; key yoksa fallback çalışır.
- TEFAS verileri iş günü güncellenir; hafta sonu/tatil gecikmeli olabilir.
- HF Inference ilk çağrıda model yükleme gecikmesi olabilir.

## 16) Dosya / Modül İndeksi (Seçme)
- `main.py` → ana giriş
- `utils/market_data_fetcher.py` → veri çekimi + fallback
- `app/analytics/custom_indicator_suite.py` → IMSE + indikator motoru
- `app/ui/indicator_lab.py` → Indicator Lab UI
- `app/ui/hf_insights.py` → HF Insights UI
- `app/ui/tradingview_tools.py` → Pine export / TV tools
- `docs/imse_indicator.pine` → Pine script

---

**Not:** Bu dosya ürün + deployment + operasyon bilgilerini tek yerde toplar. Güncellemeler için aynı dosyayı sürümleyin.
