#!/usr/bin/env python3

import yfinance as yf
from datetime import datetime
import pandas as pd

print('=== GÜNCEL MARKET VERİLERİ TEST EDİLİYOR ===\n')

# Test sembolleri
symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'XU100.IS', 'SPY']

for symbol in symbols:
    try:
        ticker = yf.Ticker(symbol)
        # Son 5 günlük veri çek
        hist = ticker.history(period='5d')
        info = ticker.info

        if not hist.empty:
            latest_price = hist['Close'].iloc[-1]
            latest_date = hist.index[-1].strftime('%Y-%m-%d %H:%M:%S')
            volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0

            print(f'{symbol}:')
            print(f'  Son Fiyat: ${latest_price:.2f}')
            print(f'  Son Güncelleme: {latest_date}')
            print(f'  Hacim: {volume:,.0f}')
            print(f'  Market Cap: ${info.get("marketCap", 0)/1e9:.1f}B')
            print()
        else:
            print(f'{symbol}: Veri alınamadı')

    except Exception as e:
        print(f'{symbol}: HATA - {str(e)}')
        print()

print('=== TEST TAMAMLANDI ===')