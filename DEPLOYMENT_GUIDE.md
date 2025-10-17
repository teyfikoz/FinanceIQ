# 🚀 Deployment Guide - Global Liquidity Dashboard

## GitHub'a Yükleme ve Canlıya Alma Rehberi

Bu rehber, uygulamanızı GitHub'a yükleyip ücretsiz/ücretli platformlarda canlıya almanız için adım adım talimatlar içerir.

---

## 📋 İçindekiler

1. [GitHub'a Yükleme](#1-githuba-yükleme)
2. [Ücretsiz Deployment Seçenekleri](#2-ücretsiz-deployment-seçenekleri)
3. [CI/CD ile Otomatik Güncelleme](#3-cicd-ile-otomatik-güncelleme)
4. [Production Ortamı Yapılandırması](#4-production-ortamı-yapılandırması)
5. [Sorun Giderme](#5-sorun-giderme)

---

## 1. GitHub'a Yükleme

### Adım 1.1: Local Git Repository Oluşturma

```bash
cd "/Users/teyfikoz/Downloads/Borsa Analiz/global_liquidity_dashboard"

# Git repository başlat
git init

# .gitignore kontrolü (zaten mevcut)
cat .gitignore

# İlk commit
git add .
git commit -m "Initial commit: Global Liquidity Dashboard v2.0"
```

### Adım 1.2: GitHub Repository Oluşturma

**Web Üzerinden:**

1. [github.com](https://github.com) → Sign in
2. Sağ üst köşe → "+" → "New repository"
3. Repository ayarları:
   - **Repository name**: `global-liquidity-dashboard`
   - **Description**: `Professional financial analytics platform with real-time market data`
   - **Visibility**: Public (veya Private)
   - ⚠️ **ÖNEMLI**: "Add a README file", ".gitignore", "license" seçeneklerini **SEÇMEYİN**

4. "Create repository" tıklayın

### Adım 1.3: Local'i GitHub'a Bağlama

GitHub'da oluşturduğunuz repository sayfasından komutları kopyalayın:

```bash
# Remote repository ekle (YOUR_USERNAME'i kendi kullanıcı adınızla değiştirin)
git remote add origin https://github.com/YOUR_USERNAME/global-liquidity-dashboard.git

# Branch'i main olarak ayarla
git branch -M main

# İlk push
git push -u origin main
```

**Alternatif: SSH ile bağlama (önerilir)**

```bash
# SSH key oluşturma (eğer yoksa)
ssh-keygen -t ed25519 -C "your-email@example.com"

# SSH key'i GitHub'a ekleme
cat ~/.ssh/id_ed25519.pub
# Bu çıktıyı kopyalayın ve GitHub Settings → SSH Keys'e ekleyin

# Remote URL'i SSH olarak değiştirin
git remote set-url origin git@github.com:YOUR_USERNAME/global-liquidity-dashboard.git
```

---

## 2. Ücretsiz Deployment Seçenekleri

### Seçenek A: Streamlit Cloud (En Kolay - %100 Ücretsiz)

**Avantajları:**
- ✅ Tamamen ücretsiz
- ✅ Otomatik deployment (git push → deploy)
- ✅ HTTPS sertifikası otomatik
- ✅ Kolay setup

**Sınırlamalar:**
- ⚠️ Sadece Streamlit dashboard (FastAPI backend için ayrı deployment gerekir)
- ⚠️ CPU/Memory limitleri (public apps için yeterli)

**Adımlar:**

1. **Streamlit Cloud'a Kaydolma**
   - [share.streamlit.io](https://share.streamlit.io) → Sign in with GitHub

2. **App Deploy Etme**
   - "New app" → "From existing repo"
   - Repository seçin: `YOUR_USERNAME/global-liquidity-dashboard`
   - Main file path: `main.py`
   - "Advanced settings" → Python version: `3.10`

3. **Secrets Ekleme**
   ```toml
   # App settings → Secrets
   [env]
   FRED_API_KEY = "your_fred_api_key_here"
   COINGECKO_API_KEY = "optional_key"
   ALPHA_VANTAGE_API_KEY = "optional_key"
   ```

4. **Deploy**
   - "Deploy!" tıklayın
   - URL: `https://YOUR_USERNAME-global-liquidity-dashboard.streamlit.app`

**Güncelleme:**
```bash
# Local'de değişiklik yapın
git add .
git commit -m "Update: feature xyz"
git push

# Streamlit Cloud OTOMATIK olarak yeniden deploy eder! 🎉
```

---

### Seçenek B: Render.com (Backend + Frontend)

**Avantajları:**
- ✅ Free tier mevcut
- ✅ FastAPI + Streamlit birlikte deploy
- ✅ PostgreSQL database free tier
- ✅ Otomatik SSL

**Sınırlamalar:**
- ⚠️ Free tier: 750 saat/ay (1 instance için yeterli)
- ⚠️ Sleep after 15 min inactivity (ilk istek 30 saniye sürer)

**Adımlar:**

1. **Render.com'a Kaydolma**
   - [render.com](https://render.com) → Sign up with GitHub

2. **render.yaml Oluşturma**

```yaml
# /Users/teyfikoz/Downloads/Borsa Analiz/global_liquidity_dashboard/render.yaml
services:
  # FastAPI Backend
  - type: web
    name: liquidity-api
    env: python
    region: oregon
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python -m app.main"
    envVars:
      - key: FRED_API_KEY
        sync: false
      - key: POSTGRES_SERVER
        fromDatabase:
          name: liquidity-db
          property: host
      - key: POSTGRES_USER
        fromDatabase:
          name: liquidity-db
          property: user
      - key: POSTGRES_PASSWORD
        fromDatabase:
          name: liquidity-db
          property: password
      - key: POSTGRES_DB
        fromDatabase:
          name: liquidity-db
          property: database
      - key: ENVIRONMENT
        value: production
      - key: DEBUG
        value: False

  # Streamlit Dashboard
  - type: web
    name: liquidity-dashboard
    env: python
    region: oregon
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "streamlit run main.py --server.port=$PORT --server.address=0.0.0.0"
    envVars:
      - key: API_URL
        fromService:
          name: liquidity-api
          type: web
          property: host

# PostgreSQL Database
databases:
  - name: liquidity-db
    databaseName: liquidity_dashboard
    user: postgres
    plan: free
```

3. **Deployment**

```bash
# render.yaml'ı commit edin
git add render.yaml
git commit -m "Add Render deployment config"
git push

# Render Dashboard'da:
# "New" → "Blueprint" → Repository seçin → Deploy
```

4. **Environment Variables Ekleme**
   - Render Dashboard → Service seçin → Environment
   - FRED_API_KEY ve diğer API key'leri ekleyin

**URL'ler:**
- API: `https://liquidity-api.onrender.com`
- Dashboard: `https://liquidity-dashboard.onrender.com`

**Güncelleme:**
```bash
git push  # Otomatik deploy! 🚀
```

---

### Seçenek C: Railway.app (Hızlı ve Kolay)

**Avantajları:**
- ✅ $5 free credit/ay
- ✅ Kolay setup
- ✅ Auto-deploy on push
- ✅ PostgreSQL ve Redis dahil

**Adımlar:**

1. **Railway'e Kaydolma**
   - [railway.app](https://railway.app) → Login with GitHub

2. **Deploy**
   - "New Project" → "Deploy from GitHub repo"
   - Repository seçin
   - Railway otomatik olarak algılar ve deploy eder

3. **Environment Variables**
   - Project → Variables
   - `.env` içeriğini kopyalayın

4. **Domain Ayarlama**
   - Settings → Generate Domain

**URL:**
- `https://YOUR_PROJECT.railway.app`

**Güncelleme:**
```bash
git push  # Otomatik deploy!
```

---

### Seçenek D: Heroku (Klasik Seçenek)

**Not:** Heroku free tier kaldırıldı, ancak $7/ay'dan başlayan planlar mevcut.

```bash
# Heroku CLI kurulumu
brew install heroku/brew/heroku  # macOS
# veya: https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# App oluşturma
heroku create global-liquidity-dashboard

# Environment variables
heroku config:set FRED_API_KEY=your_key
heroku config:set ENVIRONMENT=production

# Procfile oluşturma
echo "web: python -m app.main" > Procfile
echo "dashboard: streamlit run main.py --server.port=\$PORT" >> Procfile

# Deploy
git push heroku main
```

---

## 3. CI/CD ile Otomatik Güncelleme

### GitHub Actions ile Otomatik Deploy

**Dosya Oluştur:** `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/ --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to Render
      run: |
        curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}

    - name: Deploy to Streamlit Cloud
      run: |
        # Streamlit Cloud auto-deploys on push to main
        echo "Deployment triggered automatically"
```

**GitHub Secrets Ekleme:**

1. GitHub repository → Settings → Secrets and variables → Actions
2. "New repository secret"
3. Eklenecek secrets:
   - `RENDER_DEPLOY_HOOK`: Render'dan alınan deploy hook URL'i
   - `FRED_API_KEY`: Test için

---

## 4. Production Ortamı Yapılandırması

### 4.1 Environment Variables Güvenliği

**ÖNEMLİ:** API key'leri asla Git'e commit etmeyin!

```bash
# .gitignore kontrolü
cat .gitignore | grep .env
# Çıktı: .env olmalı

# .env dosyasını commit etmediyseniz:
git rm --cached .env
git commit -m "Remove .env from repository"
```

### 4.2 Production Settings

**Streamlit Cloud için secrets.toml:**

```toml
# Bu dosyayı LOCAL'de oluşturun, Git'e eklemeyin!
# .streamlit/secrets.toml

[env]
FRED_API_KEY = "your_key"
ENVIRONMENT = "production"
DEBUG = false
LOG_LEVEL = "INFO"

[database]
POSTGRES_SERVER = "your_db_host"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "your_password"
POSTGRES_DB = "liquidity_dashboard"
```

### 4.3 Health Check Endpoint

API'nizin sağlığını kontrol etmek için:

```bash
# Health check
curl https://your-api-url.com/health

# Beklenen çıktı:
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "production",
  "timestamp": 1234567890
}
```

---

## 5. Güncelleme Workflow'u

### Standart Güncelleme Süreci

```bash
# 1. Feature branch oluştur
git checkout -b feature/new-feature

# 2. Değişiklikleri yap
# ... kod değişiklikleri ...

# 3. Commit et
git add .
git commit -m "feat: Add new market analysis feature"

# 4. Push et
git push origin feature/new-feature

# 5. GitHub'da Pull Request oluştur
# GitHub → Pull requests → New pull request

# 6. Review sonrası main'e merge
# Merge edilince OTOMATIK DEPLOY başlar! 🎉

# 7. Local'de main'i güncelle
git checkout main
git pull origin main
```

### Hotfix (Acil Düzeltme)

```bash
# Acil düzeltme için
git checkout -b hotfix/critical-bug

# Düzeltmeyi yap
git add .
git commit -m "hotfix: Fix critical API error"

# Doğrudan main'e push (acil durumlar için)
git push origin hotfix/critical-bug

# Hemen merge et
git checkout main
git merge hotfix/critical-bug
git push origin main

# ANINDA deploy olur!
```

---

## 6. Monitoring ve Logging

### Application Monitoring

**Render.com:**
```bash
# Logs görüntüleme
render logs -s liquidity-api --tail

# Shell açma
render shell -s liquidity-api
```

**Streamlit Cloud:**
- Dashboard → App seçin → "Manage app" → "Logs"

**Railway:**
- Dashboard → Service → "View Logs"

### Error Tracking (Önerilen)

**Sentry Entegrasyonu:**

```bash
pip install sentry-sdk
```

```python
# app/main.py
import sentry_sdk

if settings.ENVIRONMENT == "production":
    sentry_sdk.init(
        dsn="your-sentry-dsn",
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0,
    )
```

---

## 7. Sorun Giderme

### Problem: App çalışmıyor

**Çözüm:**
```bash
# Logs kontrol et
# Render: Dashboard → Service → Logs
# Streamlit Cloud: Dashboard → App → Logs

# Port ayarlarını kontrol et
# Streamlit: --server.port=$PORT
# FastAPI: uvicorn run --port=$PORT
```

### Problem: Database bağlanmıyor

**Çözüm:**
```python
# Environment variables kontrolü
print(os.environ.get("POSTGRES_SERVER"))

# Connection string kontrolü
print(settings.DATABASE_URL)

# Firewall kurallarını kontrol et
# Render: Database → Connections → Add IP
```

### Problem: API key çalışmıyor

**Çözüm:**
```bash
# Platform dashboard'da secrets kontrol et
# Streamlit Cloud: App Settings → Secrets
# Render: Service → Environment
# Railway: Project → Variables

# Test et:
curl -X GET "http://localhost:8000/api/v1/market-data" \
  -H "Authorization: Bearer YOUR_KEY"
```

### Problem: Deployment başarısız

**Çözüm:**
```bash
# requirements.txt kontrol et
pip freeze > requirements.txt

# Python version uyumluluğu
# runtime.txt oluştur
echo "python-3.10.11" > runtime.txt

# Build logs kontrol et
# Her platformda "Build Logs" bölümünü inceleyin
```

---

## 8. Maliyet Optimizasyonu

### Ücretsiz Tier Kombinasyonu (Önerilen)

```
┌─────────────────────────────────────────┐
│  Streamlit Cloud (Free)                 │
│  • Dashboard hosting                    │
│  • 1 GB RAM, shared CPU                 │
│  • Sınırsız viewer                      │
│  Maliyet: $0/ay                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Render.com (Free Tier)                 │
│  • FastAPI backend                      │
│  • PostgreSQL database                  │
│  • 750 saat/ay                          │
│  Maliyet: $0/ay                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Upstash Redis (Free Tier)              │
│  • 10,000 commands/day                  │
│  • 256 MB storage                       │
│  Maliyet: $0/ay                         │
└─────────────────────────────────────────┘

TOPLAM MALİYET: $0/ay ✅
```

### Ücretli Tier (Production-Ready)

```
┌─────────────────────────────────────────┐
│  Render.com (Starter)                   │
│  • 2 Web Services                       │
│  • PostgreSQL (1 GB)                    │
│  • Always-on                            │
│  Maliyet: ~$14/ay                       │
└─────────────────────────────────────────┘

veya

┌─────────────────────────────────────────┐
│  Railway.app (Developer)                │
│  • $5 free credit + kullanıma göre      │
│  • Tüm servisler dahil                  │
│  Maliyet: ~$10-15/ay                    │
└─────────────────────────────────────────┘

TOPLAM MALİYET: $10-15/ay
```

---

## 9. Hızlı Başlangıç Checklist

### Pre-Deployment Checklist

- [ ] `.gitignore` dosyası mevcut ve `.env` içeriyor
- [ ] `.env.example` oluşturuldu (key'ler olmadan)
- [ ] `requirements.txt` güncel
- [ ] `README.md` tamamlandı
- [ ] API key'ler local'de test edildi
- [ ] Health check endpoint çalışıyor

### Deployment Checklist

- [ ] GitHub repository oluşturuldu
- [ ] Code GitHub'a push edildi
- [ ] Platform seçildi (Streamlit Cloud / Render / Railway)
- [ ] Environment variables platform'a eklendi
- [ ] İlk deployment başarılı
- [ ] Health check testi geçti
- [ ] Domain ayarlandı (opsiyonel)

### Post-Deployment Checklist

- [ ] Application erişilebilir durumda
- [ ] API endpoints test edildi
- [ ] Error tracking kuruldu (Sentry)
- [ ] Monitoring dashboard kuruldu
- [ ] CI/CD pipeline aktif
- [ ] Documentation güncel

---

## 10. Örnek Deployment Komutları

### Streamlit Cloud (En Hızlı)

```bash
# 1. GitHub'a push
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. share.streamlit.io → New app
# 3. Repository seçin
# 4. Secrets ekleyin
# 5. Deploy! ✅

# URL: https://YOUR_USERNAME-global-liquidity-dashboard.streamlit.app
```

### Render.com (Full Stack)

```bash
# 1. render.yaml oluştur (yukarıda)
git add render.yaml
git commit -m "Add Render config"
git push

# 2. render.com → New Blueprint
# 3. Repository seçin
# 4. Environment variables ekleyin
# 5. Deploy! ✅

# URL: https://liquidity-dashboard.onrender.com
```

### Railway (En Kolay)

```bash
# 1. GitHub'a push
git push origin main

# 2. railway.app → New Project
# 3. Deploy from GitHub
# 4. HERŞEY OTOMATİK! ✅

# URL: https://YOUR_PROJECT.up.railway.app
```

---

## 📞 Yardım ve Destek

**Sorun mu yaşıyorsunuz?**

1. **Logs kontrol edin**: Her platformun log viewer'ı var
2. **GitHub Issues**: Repository → Issues → New issue
3. **Platform docs**:
   - [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-cloud)
   - [Render Docs](https://render.com/docs)
   - [Railway Docs](https://docs.railway.app)

**Başarılı deployment için:**
- ✅ API key'leriniz hazır olsun
- ✅ `.gitignore` doğru yapılandırılmış olsun
- ✅ `requirements.txt` tam olsun
- ✅ Environment variables platform'a eklenmiş olsun

---

**Deployment başarıyla tamamlandığında:**

```
🎉 TEBRİKLER!

Uygulamanız canlıda ve otomatik güncellenebilir durumda!

✅ Git push = Otomatik deployment
✅ Sınırsız güncelleme
✅ Professional URL
✅ HTTPS otomatik

Mutlu kodlamalar! 🚀
```

---

*Son Güncelleme: 17 Ekim 2025*
*Versiyon: 1.0*
