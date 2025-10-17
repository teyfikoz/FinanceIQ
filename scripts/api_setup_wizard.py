#!/usr/bin/env python3
"""
API Setup Wizard - 5 dakikada API anahtarlarını alın!
"""

import os
import requests
import time
from datetime import datetime

def print_header():
    print("🌍" + "=" * 60)
    print("   API ANAHTARLARI KURULUM SIHIRBAZI")
    print("   5 dakikada tüm anahtarları alın!")
    print("=" * 62)

def step_1_fred_api():
    print("\n🏦 ADIM 1: FRED API Anahtarı (En Önemli)")
    print("─" * 50)
    print("✅ ÜCRETSİZ - Günde 120,000 istek")
    print("⏱️  Süre: 2 dakika")
    print("🎯 İçin: Fed bilançosu, ekonomik göstergeler")
    print()
    print("📋 YAPIN:")
    print("1. Bu linki açın: https://fred.stlouisfed.org/")
    print("2. Sağ üstte 'Sign In' → 'Create Account'")
    print("3. Email ve şifre ile hesap oluşturun")
    print("4. Email'inizde doğrulama linkine tıklayın")
    print("5. Bu linke gidin: https://fred.stlouisfed.org/docs/api/api_key.html")
    print("6. 'Request API Key' butonuna tıklayın")
    print("7. API anahtarınız hemen görünecek!")
    print()

    api_key = input("🔑 FRED API anahtarınızı buraya yapıştırın (örn: abcd1234...): ").strip()

    if api_key and len(api_key) > 10:
        # Test the API key
        try:
            test_url = f"https://api.stlouisfed.org/fred/series?series_id=GDP&api_key={api_key}&file_type=json"
            response = requests.get(test_url, timeout=10)
            if response.status_code == 200:
                print("✅ FRED API anahtarı çalışıyor!")
                return api_key
            else:
                print("❌ API anahtarı çalışmıyor. Lütfen kontrol edin.")
                return None
        except:
            print("⚠️ İnternet bağlantısı kontrolü yapılamadı, anahtar kaydedildi.")
            return api_key
    else:
        print("❌ Geçersiz API anahtarı")
        return None

def step_2_alpha_vantage():
    print("\n📈 ADIM 2: Alpha Vantage API (Hisse Analizi)")
    print("─" * 50)
    print("✅ ÜCRETSİZ - Günde 500 istek")
    print("⏱️  Süre: 1 dakika")
    print("🎯 İçin: Detaylı hisse senedi analizi")
    print()
    print("📋 YAPIN:")
    print("1. Bu linki açın: https://www.alphavantage.co/support/#api-key")
    print("2. 'Get your free API key today!' linkine tıklayın")
    print("3. Formu doldurun:")
    print("   - First Name: Adınız")
    print("   - Last Name: Soyadınız")
    print("   - Email: Email adresiniz")
    print("   - Organization: 'Personal'")
    print("   - How will you use?: 'Personal research and analysis'")
    print("4. 'GET FREE API KEY' butonuna tıklayın")
    print("5. API anahtarınız hemen görünecek!")
    print()

    choice = input("🤔 Alpha Vantage API almak istiyor musunuz? (e/h): ").lower()
    if choice == 'e':
        api_key = input("🔑 Alpha Vantage API anahtarınızı buraya yapıştırın: ").strip()

        if api_key and len(api_key) > 5:
            # Test the API key
            try:
                test_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={api_key}"
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200 and "Global Quote" in response.text:
                    print("✅ Alpha Vantage API anahtarı çalışıyor!")
                    return api_key
                else:
                    print("❌ API anahtarı çalışmıyor. Lütfen kontrol edin.")
                    return None
            except:
                print("⚠️ Test yapılamadı, anahtar kaydedildi.")
                return api_key
        else:
            print("❌ Geçersiz API anahtarı")
            return None
    else:
        print("⏭️ Alpha Vantage API atlandı")
        return None

def step_3_coingecko():
    print("\n🪙 ADIM 3: CoinGecko Pro API (Opsiyonel)")
    print("─" * 50)
    print("✅ ÜCRETSİZ - Ayda 100,000 istek")
    print("⏱️  Süre: 2 dakika")
    print("🎯 İçin: Kripto para detaylı verileri")
    print()
    print("📋 YAPIN:")
    print("1. Bu linki açın: https://www.coingecko.com/en/api/pricing")
    print("2. 'Start Free' butonuna tıklayın")
    print("3. Google ile hızlı kayıt yapın")
    print("4. Email doğrulaması yapın")
    print("5. Dashboard'a gidin ve API anahtarını kopyalayın")
    print()
    print("💡 NOT: CoinGecko olmadan da çalışır, ama daha az limit")

    choice = input("🤔 CoinGecko Pro API almak istiyor musunuz? (e/h): ").lower()
    if choice == 'e':
        api_key = input("🔑 CoinGecko API anahtarınızı buraya yapıştırın: ").strip()

        if api_key and len(api_key) > 10:
            print("✅ CoinGecko API anahtarı kaydedildi!")
            return api_key
        else:
            print("❌ Geçersiz API anahtarı")
            return None
    else:
        print("⏭️ CoinGecko API atlandı")
        return None

def create_env_file(fred_key, alpha_key=None, coingecko_key=None):
    """Create .env file with API keys"""
    env_path = "/Users/teyfikoz/Downloads/Borsa Analiz/global_liquidity_dashboard/.env"

    env_content = f"""# ===========================================
# Global Liquidity Dashboard - API Anahtarları
# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} tarihinde oluşturuldu
# ===========================================

# Database Configuration (Varsayılan)
DATABASE_URL=postgresql://username:password@localhost:5432/liquidity_dashboard
REDIS_URL=redis://localhost:6379/0

# ===========================================
# API ANAHTARLARI (ÜCRETSİZ)
# ===========================================

# FRED API (Federal Reserve Economic Data) - GEREKLİ
FRED_API_KEY={fred_key}

"""

    if alpha_key:
        env_content += f"""# Alpha Vantage API (Hisse Senedi Analizi)
ALPHA_VANTAGE_API_KEY={alpha_key}

"""
    else:
        env_content += """# Alpha Vantage API (Hisse Senedi Analizi) - BOŞ
# ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

"""

    if coingecko_key:
        env_content += f"""# CoinGecko Pro API (Kripto Para)
COINGECKO_API_KEY={coingecko_key}

"""
    else:
        env_content += """# CoinGecko Pro API (Kripto Para) - BOŞ
# COINGECKO_API_KEY=your_coingecko_key_here

"""

    env_content += """# ===========================================
# UYGULAMA AYARLARI
# ===========================================

# Dil Ayarları
DEFAULT_LANGUAGE=tr
SUPPORTED_LANGUAGES=tr,en

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# Dashboard Configuration
STREAMLIT_PORT=8501
API_PORT=8000
UPDATE_FREQUENCY_HOURS=1

# ===========================================
# VERİ AYARLARI
# ===========================================

# Türk Hisse Senetleri
TURKISH_STOCKS=THYAO.IS,AKBNK.IS,GARAN.IS,SISE.IS,TCELL.IS,BIMAS.IS,KOZAL.IS,SAHOL.IS,ISCTR.IS

# Global Endeksler
GLOBAL_INDICES=^GSPC,^IXIC,^DJI,^FTSE,^GDAXI

# Emtialar
COMMODITIES=GC=F,SI=F,CL=F

# Döviz Kurları
CURRENCIES=USDTRY=X,EURTRY=X,EURUSD=X

# ===========================================
# UYARI AYARLARI
# ===========================================

ENABLE_ALERTS=True
CORRELATION_ALERT_THRESHOLD=0.2
VOLATILITY_ALERT_THRESHOLD=25.0
PRICE_CHANGE_ALERT_THRESHOLD=5.0

# ===========================================
# TAHMİN MODELİ AYARLARI
# ===========================================

LSTM_SEQUENCE_LENGTH=60
LSTM_EPOCHS=50
PREDICTION_DAYS=365
RETRAIN_FREQUENCY_DAYS=7
"""

    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ .env dosyası başarıyla oluşturuldu: {env_path}")
        return True
    except Exception as e:
        print(f"❌ .env dosyası oluşturulamadı: {e}")
        return False

def final_steps():
    print("\n🎉 KURULUM TAMAMLANDI!")
    print("=" * 62)
    print("✅ API anahtarları .env dosyasına kaydedildi")
    print("✅ Dashboard gerçek verilerle çalışmaya hazır")
    print()
    print("🚀 SONRAKİ ADIMLAR:")
    print("1. Dashboard'u yeniden başlatın:")
    print("   Ctrl+C ile durdurun, sonra tekrar çalıştırın")
    print()
    print("2. Dashboard'lara erişin:")
    print("   📊 Gelişmiş: http://localhost:8502")
    print("   📊 Basit: http://localhost:8501")
    print()
    print("3. Gerçek verilerle analiz yapmaya başlayın!")
    print()
    print("💡 TİP: İlk veri yüklenmesi 1-2 dakika sürebilir")

def main():
    print_header()

    print("🎯 BU SIHIRBAZ SİZE YARDIM EDECEK:")
    print("• FRED API (zorunlu) - 2 dakika")
    print("• Alpha Vantage API (opsiyonel) - 1 dakika")
    print("• CoinGecko API (opsiyonel) - 2 dakika")
    print("• .env dosyası otomatik oluşturma")
    print()

    input("📍 Başlamak için Enter'a basın...")

    # Step 1: FRED API (required)
    fred_key = step_1_fred_api()
    if not fred_key:
        print("❌ FRED API anahtarı olmadan devam edilemez!")
        print("Lütfen önce FRED API anahtarını alın.")
        return

    # Step 2: Alpha Vantage API (optional)
    alpha_key = step_2_alpha_vantage()

    # Step 3: CoinGecko API (optional)
    coingecko_key = step_3_coingecko()

    # Create .env file
    print("\n💾 .env dosyası oluşturuluyor...")
    if create_env_file(fred_key, alpha_key, coingecko_key):
        final_steps()
    else:
        print("❌ Kurulum tamamlanamadı!")

if __name__ == "__main__":
    main()