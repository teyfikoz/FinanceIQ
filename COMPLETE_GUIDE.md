# 🚀 GLOBAL LİKİDİTE DASHBOARD - KOMPLE KULLANIM REHBERİ

Bu rehber, dashboard'unuzun tüm özelliklerini kullanmanız için adım adım talimatlar içerir.

---

## 🎯 **1. DASHBOARD'LARA ERİŞİM**

### 🌟 **ULTIMATE DASHBOARD (ÖNERİLEN)**
- **URL**: http://localhost:8503
- **Özellikler**:
  - 🔴 **Canlı gerçek veriler** (Yahoo Finance)
  - 🇹🇷 **Türkçe/İngilizce** tam destek
  - 🔮 **AI tahmin modelleri** (1 ay - 1 yıl)
  - 📊 **Gerçek korelasyon analizi**
  - 🚨 **Akıllı uyarı sistemi**
  - 🇹🇷 **Türk hisse senetleri** özel bölümü
  - ⚡ **Otomatik yenileme** (30 saniye)

### 📊 **DİĞER DASHBOARD'LAR**
- **Gelişmiş**: http://localhost:8502 (Çok dilli)
- **Basit**: http://localhost:8501 (Temel)

---

## 🔑 **2. API ANAHTARLARI ALMA (5 DAKİKA)**

### 🤖 **Otomatik Kurulum Sihirbazı**
```bash
cd "/Users/teyfikoz/Downloads/Borsa Analiz/global_liquidity_dashboard"
python scripts/api_setup_wizard.py
```

Bu sihirbaz size yardım edecek:
- ✅ **FRED API** alma (2 dakika)
- ✅ **Alpha Vantage API** alma (1 dakika)
- ✅ **CoinGecko API** alma (2 dakika)
- ✅ **.env dosyasını** otomatik oluşturma

### 📋 **Manuel Kurulum**

#### 🏦 **FRED API (En Önemli)**
1. https://fred.stlouisfed.org/ → "Sign In" → "Create Account"
2. Email doğrulama yapın
3. https://fred.stlouisfed.org/docs/api/api_key.html → "Request API Key"
4. API anahtarınızı kopyalayın

#### 📈 **Alpha Vantage API (Hisse Analizi)**
1. https://www.alphavantage.co/support/#api-key
2. "Get your free API key today!" linkine tıklayın
3. Formu doldurun ve API anahtarını alın

#### 🪙 **CoinGecko API (Opsiyonel)**
1. https://www.coingecko.com/en/api/pricing
2. "Start Free" ile hesap oluşturun
3. Dashboard'dan API anahtarını kopyalayın

---

## 📊 **3. GERÇEK VERİLERLE ANALİZ**

### 🔴 **Canlı Veri Özellikleri**

#### **Takip Edilen Varlıklar**
- **Kripto**: Bitcoin, Ethereum, Cardano, Polkadot
- **Türk Hisseleri**: THYAO, AKBNK, GARAN, SISE, TCELL
- **Global Endeksler**: S&P 500, NASDAQ, BIST 100
- **Döviz**: USD/TRY, EUR/TRY, GBP/TRY
- **Emtialar**: Altın, Gümüş, Petrol

#### **Gerçek Zamanlı Metrikler**
- **Fiyat hareketleri** (canlı)
- **Günlük değişimler** (%)
- **İşlem hacimleri**
- **Risk skorları** (0-100)
- **Volatilite seviyeleri**

### 📈 **Korelasyon Analizi**
- **30 günlük gerçek korelasyonlar**
- **Isı haritası görselleştirme**
- **Korelasyon kırılma uyarıları**
- **Cross-asset analizi**

### 🎯 **Risk Yönetimi**
- **Otomatik risk seviyesi** hesaplama
- **Volatilite skorları**
- **Trend analizi** (yükseliş/düşüş)
- **Risk-return profili**

---

## 🇹🇷 **4. TÜRKÇE ARAYÜZÜ KULLANIM**

### 🌐 **Dil Değiştirme**
1. Sağ üst köşedeki **🇹🇷/🇺🇸** butonuna tıklayın
2. Türkçe için **🇹🇷**, İngilizce için **🇺🇸** seçin
3. Sayfa otomatik olarak yenilenecek

### 📊 **Türkçe Özellikler**
- **Tüm menüler** Türkçe
- **Grafik başlıkları** Türkçe
- **Uyarı mesajları** Türkçe
- **Veri etiketleri** Türkçe
- **Risk seviyeleri** Türkçe

### 🇹🇷 **Türk Piyasası Bölümü**
- **Türk hisse performansı** grafiği
- **TL bazında fiyatlar**
- **BIST 100 korelasyonları**
- **Türk Lirası analizi**
- **Sektörel dağılım**

---

## 🔮 **5. AI TAHMİNLERİ İNCELEME**

### 🤖 **AI Model Özellikleri**
- **Gelişmiş LSTM** modelleri
- **Random Forest** fallback
- **Seasonal adjustment** (mevsimsel düzeltme)
- **Volatilite adaptasyonu**
- **Trend decay** hesaplama

### 📈 **Tahmin Periyotları**
- **1 Ay**: Kısa vadeli taktik kararlar
- **3 Ay**: Orta vadeli yatırım planı
- **1 Yıl**: Uzun vadeli strateji

### 🎯 **Tahmin Güvenilirliği**
- **Güven aralıkları** (%95)
- **Dinamik güven skoru** (zaman azalışı)
- **Model performans** metrikleri
- **Hata analizi** ve düzeltme

### 📊 **Tahmin Kullanım Adımları**
1. **"🔮 AI Tahmin Analizi"** bölümüne gidin
2. **Varlık seçin** (dropdown menüden)
3. **Tahmin periyodu** seçin (1 Ay/3 Ay/1 Yıl)
4. **Grafiği inceleyin**:
   - 🔴 **Kırmızı nokta**: Mevcut fiyat
   - 🔵 **Mavi çizgi**: AI tahmini
   - 🟢 **Yeşil alan**: Güven aralığı
5. **Tahmin özetini** kontrol edin:
   - Mevcut fiyat
   - Tahmini fiyat
   - Beklenen getiri (%)
   - Tahmin güveni (%)

---

## 🚨 **6. UYARI SİSTEMİ KULLANIMI**

### ⚙️ **Uyarı Ayarları**
1. Sol menüden **"🚨 Uyarı Ayarları"** bölümüne gidin
2. **Volatilite uyarısı** seviyesini ayarlayın (%)
3. Değişiklikler otomatik kaydedilir

### 🔔 **Uyarı Türleri**
- **Volatilite Uyarısı**: %X üzeri değişimler
- **Fiyat Hareketi**: Büyük fiyat dalgalanmaları
- **Korelasyon Kırılması**: Beklenmedik korelasyon değişimleri
- **Risk Seviyesi**: Yüksek risk durumları

### 📱 **Uyarı Görüntüleme**
- **Renkli kutular**: Uyarı türüne göre renklendirme
- **Zaman damgası**: Uyarının oluşma zamanı
- **Detaylı mesaj**: Tam açıklama
- **Önem seviyesi**: Düşük/Orta/Yüksek

---

## 🛠️ **7. GELİŞMİŞ ÖZELLİKLER**

### 🔄 **Otomatik Yenileme**
- Sol menüden **"🔄 Otomatik Yenileme"** kutusunu işaretleyin
- **30 saniye** aralıklarla veriler güncellenir
- **Gerçek zamanlı** piyasa takibi

### 📊 **Detaylı Analiz Sekmeler**
1. **📈 Piyasa Verileri**: Tüm varlıkların canlı verileri
2. **🔗 Korelasyonlar**: 30 günlük korelasyon matrisi
3. **⚠️ Risk Analizi**: Detaylı risk metrikleri

### 🎨 **Görselleştirme Özellikleri**
- **İnteraktif grafikler** (zoom, pan)
- **Hover bilgileri** (fare ile üzerine gelince)
- **Renk kodlaması** (yeşil: artış, kırmızı: düşüş)
- **Animasyonlu güncellemeler**

---

## 🚀 **8. PERFORMANS OPTİMİZASYONU**

### ⚡ **Hızlandırma İpuçları**
1. **Gereksiz sekmeler** kapatın
2. **Otomatik yenilemeyi** gerektiğinde kullanın
3. **Tahmin periyodunu** ihtiyaç kadar seçin
4. **Browser cache'ini** temizleyin

### 📈 **Veri Yönetimi**
- **Cache süresi**: 5-30 dakika
- **Otomatik veri temizliği**
- **Hata yönetimi** (fallback)
- **Bağlantı kontrolü**

---

## 🔧 **9. SORUN GİDERME**

### ❌ **Sık Karşılaşılan Sorunlar**

#### **Dashboard açılmıyor**
```bash
# Port kontrolü
lsof -i :8503

# Yeniden başlatma
Ctrl+C ile durdurun
streamlit run dashboard/enhanced_realtime_app.py --server.port 8503
```

#### **Veriler güncellenmiyor**
1. **"🔄 Verileri Yenile"** butonuna tıklayın
2. **İnternet bağlantısını** kontrol edin
3. **API limitlerini** kontrol edin
4. **Browser'ı yenileyin** (F5)

#### **API hataları**
1. **.env dosyasını** kontrol edin
2. **API anahtarlarını** yeniden girin
3. **API limitlerini** kontrol edin
4. **Sihirbazı** tekrar çalıştırın

### 📞 **Destek**
- **Logları** kontrol edin (terminal)
- **Network** sekmesini inceleyin (F12)
- **API test** scriptlerini çalıştırın

---

## 🎉 **10. İLERİ SEVİYE KULLANIM**

### 📊 **Özel Analiz**
1. **Korelasyon matrisi** excel'e aktarın
2. **Risk metriklerini** karşılaştırın
3. **Tahmin doğruluğunu** takip edin
4. **Portföy optimizasyonu** yapın

### 🤖 **AI Model Geliştirme**
- **Model parametrelerini** ayarlayın
- **Training dataları** genişletin
- **Feature engineering** yapın
- **Ensemble modeller** deneyin

### 📈 **Yatırım Stratejisi**
1. **Korelasyon breakout** stratejisi
2. **Volatilite trading** yaklaşımı
3. **Mean reversion** taktikleri
4. **Risk parity** portföy

---

## 🏆 **SONUÇ**

Dashboard'unuz artık **tam fonksiyonel** ve **profesyonel** bir finansal analiz aracı!

### ✅ **Sahip Olduğunuz Özellikler**
- 🔴 **Canlı veriler** (gerçek zamanlı)
- 🇹🇷 **Türkçe destek** (tam)
- 🔮 **AI tahminler** (gelişmiş)
- 🚨 **Akıllı uyarılar**
- 📊 **Profesyonel grafikler**
- 🎯 **Risk yönetimi**
- 🇹🇷 **Türk piyasası** analizi

### 📈 **Kullanım Önerileri**
1. **Günlük**: Uyarıları kontrol edin
2. **Haftalık**: Korelasyonları inceleyin
3. **Aylık**: AI tahminlerini değerlendirin
4. **Yatırım öncesi**: Risk analizini yapın

**Başarılar! 🚀📊💰**