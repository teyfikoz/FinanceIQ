# FinanceIQ Kullanici Rehberi

Bu rehber, FinanceIQ uygulamasinin ana bolumlerini, tipik is akislari ve pratik kullanim ipuclarini aciklar.

---

## 1) Genel Bakis
FinanceIQ; global piyasalar, ETF ve fon analizleri, teknik analiz, kurumsal yatirimci takibi ve makro indikatorleri tek bir Streamlit arayuzunde birlestirir. Uygulama tek giris noktasi olan `main.py` uzerinden calisir.

**Canli uygulama**
```
https://financeiq.streamlit.app/
```

---

## 2) Ekran Yapisi ve Navigasyon
Ust kısımda ana sekmeler bulunur. Her sekmede ilgili moduller ve alt sekmeler yer alir.

### Sidebar (Sol Panel)
- **Open Access Mode**: Auth kapaliysa herkes erisebilir.
- **Auto-refresh (30s)**: Sayfayi periyodik yeniler (API limitlerini arttirabilir).
- **System Status**:
  - Ortam (production/dev)
  - Auth durumu
  - TradingView Bridge durumu
  - API key'lerin set/missing bilgisi (degerler goruntulenmez)

### Veri Kalite Etiketi
Arayuzde bazen `Real/Cache/Fallback` rozetleri gorunur:
- **Real**: Canli veri
- **Cache**: Yakın zamanli cache verisi
- **Fallback**: Rate limit veya kaynak hatasi; gecikmeli/sentetik veri

---

## 3) Ana Sekmeler ve Icerik

### 3.1 Dashboard
Global piyasa gorunumu ve hizli ozet:
- Ana endeksler ve gunluk degisimler
- Sektor performansi karsilastirmasi
- Global pazar grafigi

### 3.2 Stock Research
Iki ana alt sekme:
- **Individual Stock**: Tek hisse analizi
  - Fiyat, hacim, temel metrikler
  - Candlestick + SMA/EMA + MACD + RSI
  - Fon holding dagilimi (ETF ve Mutual Fund)
  - AI sentiment ozeti (varsa)
- **Compare Stocks**: Coklu hisse karsilastirma

**Not:** Turk hisseleri icin `.IS` uzantisi kullanin (ornegin `THYAO.IS`).

### 3.3 Screener
Filtre tabanli hisse taramasi. Belirledigin kriterlere gore liste uretir.

### 3.4 Strategy Lab
Strateji testleri ve indikator analizleri:
- **Backtesting**: Strateji parametrelerini girip geriye donuk test
- **Indicator Lab**: IMSE + klasik indikator setleri
- **TradingView Tools**: Pine export ve bridge bilgisi

### 3.5 ETFs & Funds
Global ETF ve fon performanslari:
- Getiri, trend ve temel karsilastirmalar
- Fon/ETF dagilim analizleri

### 3.6 Institutional
Kurumsal yatirimci ve buyuk fon verileri:
- Sovereign Wealth Funds (ornek: Norway GPF, GIC, PIF)
- Portfoy ve performans ozetleri

### 3.7 Turkish Markets
Turkiye odakli piyasa gorunumu:
- BIST endeksleri
- BIST 30 listesi
- TEFAS fon portfoy analizi (modul varsa)

### 3.8 AI Tools (Game Changer)
Uretken ve analitik ozellikler:
- **Social Features**: Portfolio snapshots, public watchlists, ticker notes, leaderboard
- **Advanced Visualizations**: calendar heatmap, sector rotation, fear&greed, 3D portfolio
- **AI Lite Tools**:
  - Monte Carlo simulation
  - Strategy backtesting
  - Auto-annotated chart
  - News sentiment analysis
- **Export & Share**: ciktilari disari aktarma

### 3.9 Whale Intelligence
Kurumsal hareket ve akil urunleri:
- Whale investor takibi
- Whale correlation network
- Whale momentum tracker
- ETF-Whale linkage
- Hedge Fund radar
- Event reaction lab

### 3.10 Entropy Analysis
Piyasa belirsizligi ve rejim analizi.

### 3.11 Crypto Dominance
Kripto dominans oranlari ve trend analizi.

### 3.12 Cycle Intelligence
Makro dongu sinyalleri ve risk/return rejimleri.

### 3.13 Portfolio
Portfoy olusturma ve raporlama:
- Portfoy ve pozisyon ekleme
- Performans ozeti
- Excel / CSV / HTML rapor indirme

### 3.14 Watchlist
Takip listeleri (auth aciksa):
- Yeni watchlist olusturma
- Canli fiyat tablosu

### 3.15 Alerts
Fiyat alarm kurallari (auth aciksa):
- Ust/alt esik bildirimleri

### 3.16 Privacy
Gizlilik ayarlari (auth aciksa).

---

## 4) Ornek Kullanim Akislari

### Hisse Analizi
1. Stock Research -> Individual Stock
2. Sembol gir, period sec
3. Analyze Stock
4. Teknik grafik ve metrikleri incele

### Strateji Testi
1. Strategy Lab -> Backtesting
2. Ticker ve strateji parametrelerini sec
3. Run Backtest
4. Sonuc metriklerini degerlendir

### IMSE / Indicator Lab
1. Strategy Lab -> Indicator Lab
2. Sembol ve veri kaynagini sec
3. Profil sekmelerinden (Gunluk/Kisa/Orta/Uzun) analiz et
4. IMSE skor, trend ve guven metriklerine bak

### Portfoy Raporu
1. Portfolio sekmesi
2. Portfoy ve islem ekle
3. Export bolumunden Excel/CSV/HTML indir

---

## 5) Opsiyonel Ayarlar ve Entegrasyonlar
- **TradingView Bridge**: Node.js + `@mathieuc/tradingview` gerekir.
- **AI**: HF API token eklenirse LLM tabanli ozetler aktif olur.
- **FRED / Alpha Vantage / FMP**: Makro ve alternatif veri icin opsiyonel.

---

## 6) Sık Sorulan Sorular

**Veri gelmiyor / N/A gorunuyor**
- Sembol formatini kontrol et (TR hisseleri `.IS`)
- Rate limit olabilir; birkac dakika bekle
- Auto-refresh kapali deneyin

**Real/Cache/Fallback ne demek?**
- Real: canli veri
- Cache: yakinda alinmis veri
- Fallback: API limiti/erisim sorunu

**Watchlist/Alerts calismiyor**
- Auth kapaliysa bu ozellikler sadece bilgilendirme mesaji gosterir.

**Browser Console uyarilari**
- `content.js` uyarisi eklenti kaynaklidir.
- Tema uyarilari `docs/DEPLOYMENT_TROUBLESHOOTING.md` icinde aciklanmistir.

---

## 7) Ipuclari
- Auto-refresh ozelligini sadece gerekli oldugunda acik tutun.
- Cok fazla sembol ile ayni anda sorgu yapmak rate limit ihtimalini arttirir.

---

## 8) Not
FinanceIQ bir finansal analiz platformudur. Yatirim tavsiyesi degildir.

