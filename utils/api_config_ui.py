"""
🔐 API Configuration UI
User-friendly interface for managing API keys
"""

import streamlit as st
import os
import json
from pathlib import Path
from .unified_api_manager import api_manager


class APIConfigUI:
    """UI for configuring API keys"""

    def __init__(self):
        self.config_dir = Path("config")
        self.config_file = self.config_dir / "api_keys.json"
        self.config_dir.mkdir(exist_ok=True)

    def render(self):
        """Render API configuration interface"""

        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
            <h1 style='color: white; text-align: center; margin: 0;'>
                🔑 API Key Configuration
            </h1>
            <p style='color: rgba(255,255,255,0.9); text-align: center; margin-top: 0.5rem;'>
                Configure your free API keys for enhanced data access
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Show current API status
        self._render_api_status()

        st.markdown("---")

        # Configuration tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Stock & ETF APIs",
            "📈 Economic Data APIs",
            "💰 Crypto APIs",
            "📰 News & Sentiment APIs"
        ])

        with tab1:
            self._render_stock_apis()

        with tab2:
            self._render_economic_apis()

        with tab3:
            self._render_crypto_apis()

        with tab4:
            self._render_news_apis()

        st.markdown("---")

        # Quick setup guide
        with st.expander("📚 Quick Setup Guide", expanded=False):
            st.markdown("""
            ### How to Get Free API Keys:

            1. **Alpha Vantage** (Stock data)
               - Visit: https://www.alphavantage.co/support/#api-key
               - Click "Get Your Free API Key"
               - Free: 25 requests/day

            2. **FRED** (Economic data)
               - Visit: https://fred.stlouisfed.org/docs/api/api_key.html
               - Click "Request API Key"
               - Free: Unlimited requests

            3. **Finnhub** (News & Sentiment)
               - Visit: https://finnhub.io/register
               - Sign up for free
               - Free: 60 requests/minute

            4. **Binance** (Crypto data)
               - Visit: https://www.binance.com
               - Create account → API Management
               - Free: 1200 requests/minute

            📖 **Full guide:** See `docs/FREE_API_SETUP_GUIDE.md`
            """)

    def _render_api_status(self):
        """Show current status of all APIs"""
        st.markdown("### 📊 API Status Dashboard")

        status = api_manager.get_api_status()

        # Create status cards
        col1, col2, col3, col4 = st.columns(4)

        configured_count = sum(1 for v in status.values() if v['configured'])
        total_count = len(status)

        with col1:
            st.metric(
                "Configured APIs",
                f"{configured_count}/{total_count}",
                delta=f"{configured_count/total_count*100:.0f}% coverage"
            )

        with col2:
            unlimited_apis = ['yahoo', 'fred', 'tefas', 'worldbank']
            unlimited_count = sum(1 for api in unlimited_apis if status.get(api, {}).get('configured'))
            st.metric(
                "Unlimited APIs",
                unlimited_count,
                delta="No rate limits"
            )

        with col3:
            total_calls = sum(v.get('calls_made', 0) for v in status.values())
            st.metric(
                "API Calls Today",
                total_calls,
                delta="Cached responses"
            )

        with col4:
            cache_size = len(api_manager.cache.cache)
            st.metric(
                "Cache Size",
                cache_size,
                delta="Active entries"
            )

        # Detailed status table
        st.markdown("#### Detailed Status")

        status_data = []
        for api_name, info in status.items():
            status_emoji = "✅" if info['configured'] else "❌"
            status_data.append({
                "API": api_name.replace('_', ' ').title(),
                "Status": status_emoji,
                "Rate Limit": info['rate_limit'],
                "Calls Made": info['calls_made']
            })

        st.dataframe(status_data, use_container_width=True, hide_index=True)

    def _render_stock_apis(self):
        """Render stock & ETF API configuration"""
        st.markdown("### 📊 Stock & ETF Data Sources")

        # Alpha Vantage
        st.markdown("#### Alpha Vantage")
        st.info("📌 Provides: Stock prices, technical indicators, fundamentals")

        current_av_key = api_manager.api_keys.get('alpha_vantage', '')
        av_key = st.text_input(
            "Alpha Vantage API Key",
            value=current_av_key,
            type="password",
            key="av_key_input",
            help="Get free key: https://www.alphavantage.co/support/#api-key"
        )

        if st.button("💾 Save Alpha Vantage Key", key="save_av"):
            self._save_api_key('alpha_vantage', av_key)
            st.success("✅ Alpha Vantage key saved!")
            st.rerun()

        # Yahoo Finance info (no key needed)
        st.markdown("#### Yahoo Finance")
        st.success("✅ **Already configured!** (No API key needed)")
        st.caption("📊 Unlimited stock quotes via yfinance library")

    def _render_economic_apis(self):
        """Render economic data API configuration"""
        st.markdown("### 📈 Economic & Macro Data Sources")

        # FRED
        st.markdown("#### FRED (Federal Reserve)")
        st.info("📌 Provides: GDP, CPI, unemployment, interest rates, M2 money supply")

        current_fred_key = api_manager.api_keys.get('fred', '')
        fred_key = st.text_input(
            "FRED API Key",
            value=current_fred_key,
            type="password",
            key="fred_key_input",
            help="Get free key: https://fred.stlouisfed.org/docs/api/api_key.html"
        )

        if st.button("💾 Save FRED Key", key="save_fred"):
            self._save_api_key('fred', fred_key)
            st.success("✅ FRED key saved!")
            st.rerun()

        # Trading Economics
        st.markdown("#### TradingEconomics")
        st.info("📌 Provides: Global economic calendar, forecasts, country indicators")

        current_te_key = api_manager.api_keys.get('tradingeconomics', '')
        te_key = st.text_input(
            "TradingEconomics API Key",
            value=current_te_key,
            type="password",
            key="te_key_input",
            help="Get free key: https://tradingeconomics.com/api/"
        )

        if st.button("💾 Save TradingEconomics Key", key="save_te"):
            self._save_api_key('tradingeconomics', te_key)
            st.success("✅ TradingEconomics key saved!")
            st.rerun()

        # World Bank info
        st.markdown("#### World Bank API")
        st.success("✅ **Already configured!** (No API key needed)")
        st.caption("🌍 Unlimited global economic data")

    def _render_crypto_apis(self):
        """Render crypto API configuration"""
        st.markdown("### 💰 Cryptocurrency Data Sources")

        # Binance
        st.markdown("#### Binance")
        st.info("📌 Provides: Crypto prices, order book, historical data")

        col1, col2 = st.columns(2)

        with col1:
            current_binance_key = api_manager.api_keys.get('binance_key', '')
            binance_key = st.text_input(
                "Binance API Key",
                value=current_binance_key,
                type="password",
                key="binance_key_input"
            )

        with col2:
            current_binance_secret = api_manager.api_keys.get('binance_secret', '')
            binance_secret = st.text_input(
                "Binance Secret Key",
                value=current_binance_secret,
                type="password",
                key="binance_secret_input"
            )

        if st.button("💾 Save Binance Keys", key="save_binance"):
            self._save_api_key('binance_key', binance_key)
            self._save_api_key('binance_secret', binance_secret)
            st.success("✅ Binance keys saved!")
            st.rerun()

        st.caption("⚠️ Tip: Enable only 'Reading' permissions, disable 'Trading'")

        # CoinGecko info
        st.markdown("#### CoinGecko")
        st.success("✅ **Already configured!** (No API key needed)")
        st.caption("💎 50 requests/minute for free")

    def _render_news_apis(self):
        """Render news & sentiment API configuration"""
        st.markdown("### 📰 News & Sentiment Data Sources")

        # Finnhub
        st.markdown("#### Finnhub")
        st.info("📌 Provides: Stock news, social sentiment, earnings calendar")

        current_fh_key = api_manager.api_keys.get('finnhub', '')
        fh_key = st.text_input(
            "Finnhub API Key",
            value=current_fh_key,
            type="password",
            key="fh_key_input",
            help="Get free key: https://finnhub.io/register"
        )

        if st.button("💾 Save Finnhub Key", key="save_fh"):
            self._save_api_key('finnhub', fh_key)
            st.success("✅ Finnhub key saved!")
            st.rerun()

        # NewsAPI
        st.markdown("#### NewsAPI")
        st.info("📌 Provides: Financial news headlines from 80,000+ sources")

        current_news_key = api_manager.api_keys.get('newsapi', '')
        news_key = st.text_input(
            "NewsAPI Key",
            value=current_news_key,
            type="password",
            key="news_key_input",
            help="Get free key: https://newsapi.org/register"
        )

        if st.button("💾 Save NewsAPI Key", key="save_news"):
            self._save_api_key('newsapi', news_key)
            st.success("✅ NewsAPI key saved!")
            st.rerun()

        # Polygon
        st.markdown("#### Polygon.io")
        st.info("📌 Provides: Stocks, options, forex, crypto data")

        current_poly_key = api_manager.api_keys.get('polygon', '')
        poly_key = st.text_input(
            "Polygon API Key",
            value=current_poly_key,
            type="password",
            key="poly_key_input",
            help="Get free key: https://polygon.io/dashboard/signup"
        )

        if st.button("💾 Save Polygon Key", key="save_poly"):
            self._save_api_key('polygon', poly_key)
            st.success("✅ Polygon key saved!")
            st.rerun()

    def _save_api_key(self, key_name: str, key_value: str):
        """Save API key to config file"""
        # Load existing config
        config = {}
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)

        # Update key
        config[key_name] = key_value

        # Save config
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

        # Update api_manager
        api_manager.api_keys[key_name] = key_value

    def _load_config(self) -> dict:
        """Load config from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}


def create_api_config_ui():
    """Main entry point for API configuration UI"""
    ui = APIConfigUI()
    ui.render()
