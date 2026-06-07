#!/usr/bin/env python3
"""
🧪 Complete API Integration Test
Tests all configured APIs with real requests
"""

import sys
sys.path.insert(0, '.')

from utils.market_data_engine import market
from datetime import datetime, timedelta
import time

print("=" * 80)
print("🧪 COMPLETE API INTEGRATION TEST")
print("=" * 80)
print(f"⏰ Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Test counters
tests_passed = 0
tests_failed = 0
test_results = []

def test_api(name, func, *args, **kwargs):
    """Helper function to test an API call"""
    global tests_passed, tests_failed
    print(f"\n{'='*80}")
    print(f"🔍 Testing: {name}")
    print(f"{'='*80}")

    try:
        result = func(*args, **kwargs)

        if result:
            print(f"✅ SUCCESS")
            print(f"📊 Result preview:")

            # Pretty print result (limited)
            if isinstance(result, dict):
                for key, value in list(result.items())[:5]:  # Show first 5 keys
                    if isinstance(value, (str, int, float, bool)):
                        print(f"   {key}: {value}")
                    elif isinstance(value, list) and len(value) > 0:
                        print(f"   {key}: [{len(value)} items]")
                    else:
                        print(f"   {key}: {type(value).__name__}")
            elif isinstance(result, list):
                print(f"   Returned {len(result)} items")
                if len(result) > 0:
                    print(f"   First item: {result[0] if isinstance(result[0], (str, int, float)) else type(result[0]).__name__}")
            else:
                print(f"   {result}")

            tests_passed += 1
            test_results.append(('✅', name))
            return True
        else:
            print(f"⚠️  EMPTY RESULT (API may not be configured or data unavailable)")
            tests_failed += 1
            test_results.append(('⚠️', name))
            return False

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        tests_failed += 1
        test_results.append(('❌', name))
        return False


# ========== API STATUS ==========
print("\n" + "🔑 " + "="*76)
print("🔑 API CONFIGURATION STATUS")
print("🔑 " + "="*76)

status = market.get_api_status()
for api_name, info in status.items():
    status_icon = "✅" if info['configured'] else "❌"
    print(f"{status_icon} {api_name:20s} - {info['rate_limit']:30s} - Calls: {info['calls_made']}")

time.sleep(2)

# ========== STOCK DATA TESTS ==========
print("\n\n" + "📈 " + "="*76)
print("📈 STOCK & ETF DATA TESTS")
print("📈 " + "="*76)

test_api("Yahoo Finance - Stock Quote (AAPL)", market.get_stock, 'AAPL')
time.sleep(1)

test_api("FMP - Stock Profile (TSLA)", market.get_stock_profile, 'TSLA')
time.sleep(1)

test_api("FMP - ETF Quote (SPY)", market.get_etf, 'SPY')
time.sleep(1)

test_api("FMP - ETF Holdings (QQQ)", market.get_etf_holdings, 'QQQ')
time.sleep(1)

# ========== CRYPTO TESTS ==========
print("\n\n" + "💰 " + "="*76)
print("💰 CRYPTOCURRENCY DATA TESTS")
print("💰 " + "="*76)

test_api("Binance - BTC Price", market.get_crypto, 'BTC')
time.sleep(1)

test_api("Binance - ETH Price", market.get_crypto, 'ETH')
time.sleep(1)

test_api("Binance - BTC Historical Klines", market.get_crypto_historical, 'BTCUSDT', '1h', 10)
time.sleep(1)

# ========== TEFAS FUND TESTS ==========
print("\n\n" + "🇹🇷 " + "="*76)
print("🇹🇷 TEFAS (TURKISH FUNDS) DATA TESTS")
print("🇹🇷 " + "="*76)

test_api("TEFAS - Fund Info (TCD)", market.get_fund, 'TCD')
time.sleep(1)

test_api("TEFAS - Fund Info (AKG)", market.get_fund, 'AKG')
time.sleep(1)

# Get historical data
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
test_api("TEFAS - Fund History (TCD)", market.get_fund_history, 'TCD', start_date)
time.sleep(1)

# ========== MACRO DATA TESTS ==========
print("\n\n" + "📊 " + "="*76)
print("📊 MACRO & ECONOMIC DATA TESTS")
print("📊 " + "="*76)

test_api("FRED - GDP Data", market.get_fred_series, 'GDP')
time.sleep(1)

test_api("FRED - CPI Data", market.get_fred_series, 'CPIAUCSL')
time.sleep(1)

test_api("FRED - Unemployment Rate", market.get_fred_series, 'UNRATE')
time.sleep(1)

test_api("FRED - M2 Money Supply", market.get_fred_series, 'M2SL')
time.sleep(1)

test_api("FMP - Market Hours", market.get_market_hours)
time.sleep(1)

# ========== NEWS & SENTIMENT TESTS ==========
print("\n\n" + "📰 " + "="*76)
print("📰 NEWS & SENTIMENT DATA TESTS")
print("📰 " + "="*76)

test_api("Finnhub - Company News (AAPL)", market.get_news, symbol='AAPL')
time.sleep(1)

test_api("Finnhub - Social Sentiment (TSLA)", market.get_sentiment, 'TSLA')
time.sleep(1)

# ========== BATCH OPERATIONS ==========
print("\n\n" + "🚀 " + "="*76)
print("🚀 BATCH OPERATIONS TESTS")
print("🚀 " + "="*76)

test_api("Batch - Multiple Stocks", market.get_multiple_stocks, ['AAPL', 'GOOGL', 'MSFT'])
time.sleep(2)

test_api("Batch - Multiple Cryptos", market.get_multiple_cryptos, ['BTC', 'ETH'])
time.sleep(1)

test_api("Batch - Multiple Funds", market.get_multiple_funds, ['TCD', 'AKG'])
time.sleep(1)

# ========== FINAL RESULTS ==========
print("\n\n" + "=" * 80)
print("📊 FINAL TEST RESULTS")
print("=" * 80)

print(f"\n✅ Tests Passed: {tests_passed}")
print(f"❌ Tests Failed: {tests_failed}")
print(f"📊 Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%\n")

print("Detailed Results:")
print("-" * 80)
for icon, test_name in test_results:
    print(f"{icon} {test_name}")

# Final API status
print("\n" + "=" * 80)
print("🔑 FINAL API CALL STATISTICS")
print("=" * 80)

final_status = market.get_api_status()
for api_name, info in final_status.items():
    if info['calls_made'] > 0:
        print(f"📊 {api_name:20s} - {info['calls_made']} calls made")

print("\n" + "=" * 80)
print(f"⏰ Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Exit code
sys.exit(0 if tests_failed == 0 else 1)
