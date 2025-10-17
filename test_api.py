#!/usr/bin/env python3
"""
Test script for verifying real-time data fetching
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

def test_turkish_stocks():
    """Test Turkish stock data fetching"""
    print("🇹🇷 Testing Turkish Stocks...")
    print("=" * 50)

    turkish_stocks = [
        "THYAO.IS",  # Turkish Airlines
        "AKBNK.IS",  # Akbank
        "BIMAS.IS",  # BIM
        "KCHOL.IS",  # Koc Holding
        "TUPRS.IS",  # Tupras
        "TCELL.IS"   # Turkcell
    ]

    for symbol in turkish_stocks:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")

            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                print(f"✅ {symbol:12} - Current: ₺{current_price:8.2f} - Status: OK")
            else:
                print(f"❌ {symbol:12} - No data available")
        except Exception as e:
            print(f"❌ {symbol:12} - Error: {str(e)[:50]}")

    print()

def test_norway_fund_holdings():
    """Test Norway Fund Turkish holdings"""
    print("🇳🇴 Testing Norway Fund Turkish Holdings...")
    print("=" * 50)

    norway_turkish_holdings = {
        "KCHOL.IS": "Koc Holding",
        "AKBNK.IS": "Akbank",
        "BIMAS.IS": "BIM Stores",
        "THYAO.IS": "Turkish Airlines",
        "TCELL.IS": "Turkcell",
        "TUPRS.IS": "Tupras"
    }

    total_value = 0
    for symbol, name in norway_turkish_holdings.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")

            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                print(f"✅ {symbol:12} ({name:20}) - ₺{current_price:8.2f}")
                total_value += current_price
            else:
                print(f"❌ {symbol:12} ({name:20}) - No data")
        except Exception as e:
            print(f"❌ {symbol:12} ({name:20}) - Error")

    print(f"\n💰 Total Portfolio Value Index: ₺{total_value:.2f}")
    print()

def test_global_indices():
    """Test major global indices"""
    print("🌍 Testing Global Indices...")
    print("=" * 50)

    indices = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ",
        "^DJI": "Dow Jones",
        "^FTSE": "FTSE 100",
        "^GDAXI": "DAX",
        "XU100.IS": "BIST 100"
    }

    for symbol, name in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")

            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                print(f"✅ {name:15} ({symbol:10}) - {current_price:10.2f}")
            else:
                print(f"❌ {name:15} ({symbol:10}) - No data")
        except Exception as e:
            print(f"❌ {name:15} ({symbol:10}) - Error")

    print()

def test_stock_analysis(symbol="THYAO.IS"):
    """Test individual stock analysis"""
    print(f"📊 Testing Stock Analysis for {symbol}...")
    print("=" * 50)

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")

        if not hist.empty:
            print(f"✅ Data fetched successfully")
            print(f"   Period: {hist.index[0].date()} to {hist.index[-1].date()}")
            print(f"   Data points: {len(hist)}")
            print(f"   Current Price: ₺{hist['Close'].iloc[-1]:.2f}")
            print(f"   Volume: {hist['Volume'].iloc[-1]:,.0f}")

            # Test technical indicators
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['RSI'] = calculate_rsi(hist['Close'])

            print(f"   SMA(20): ₺{hist['SMA_20'].iloc[-1]:.2f}")
            print(f"   RSI: {hist['RSI'].iloc[-1]:.2f}")
        else:
            print(f"❌ No data available")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    print()

def calculate_rsi(series, period=14):
    """Calculate RSI"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔍 API TEST SUITE - Real-time Data Verification")
    print("=" * 50)
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50 + "\n")

    # Run all tests
    test_turkish_stocks()
    test_norway_fund_holdings()
    test_global_indices()
    test_stock_analysis("THYAO.IS")
    test_stock_analysis("AKBNK.IS")

    print("=" * 50)
    print("✅ Test suite completed!")
    print("=" * 50)
