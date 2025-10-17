"""Stock search with autocomplete functionality"""
import streamlit as st
from typing import List, Callable
from utils.alpha_vantage_api import AlphaVantageAPI


def stock_search_autocomplete(search_func: Callable, placeholder: str = "Search stocks...") -> str:
    """Create a stock search input with autocomplete

    Args:
        search_func: Function to search for stocks
        placeholder: Placeholder text

    Returns:
        Selected stock symbol
    """
    # Initialize session state
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = ''
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ''

    # Search input
    search_query = st.text_input(
        "🔍 Search Stock Symbol or Company Name",
        value=st.session_state.search_query,
        placeholder=placeholder,
        key='stock_search_input'
    )

    # Update search query
    if search_query != st.session_state.search_query:
        st.session_state.search_query = search_query

        # Perform search if query is long enough
        if len(search_query) >= 2:
            results = search_func(search_query)
            st.session_state.search_results = results
        else:
            st.session_state.search_results = []

    # Display search results
    if st.session_state.search_results and len(st.session_state.search_query) >= 2:
        st.markdown("**Search Results:**")

        # Create columns for better layout
        for result in st.session_state.search_results[:10]:
            col1, col2, col3 = st.columns([2, 3, 1])

            with col1:
                st.markdown(f"**{result['symbol']}**")
            with col2:
                st.markdown(f"{result['name'][:40]}..." if len(result['name']) > 40 else result['name'])
            with col3:
                if st.button("Select", key=f"select_{result['symbol']}"):
                    st.session_state.selected_symbol = result['symbol']
                    st.session_state.search_query = result['symbol']
                    st.session_state.search_results = []
                    st.rerun()

        st.markdown("---")

    return st.session_state.selected_symbol or st.session_state.search_query.upper()


def create_enhanced_stock_search():
    """Create enhanced stock search interface with Alpha Vantage"""
    st.markdown("### 🔍 Stock Symbol Search")

    # Initialize Alpha Vantage API
    av_api = AlphaVantageAPI()

    # Search function
    def search_stocks(query: str) -> List[dict]:
        """Search stocks using Alpha Vantage"""
        results = av_api.search_symbol(query)
        return results if results else []

    # Use autocomplete search
    selected_symbol = stock_search_autocomplete(
        search_func=search_stocks,
        placeholder="e.g., AAPL, Microsoft, Tesla..."
    )

    # Display selected symbol info
    if selected_symbol:
        st.info(f"✅ Selected: **{selected_symbol}**")

        # Return the symbol for use in analysis
        return selected_symbol

    return None


def simple_stock_search_ui():
    """Simple stock search UI without external API"""
    st.markdown("### 🔍 Stock Symbol Search")

    # Popular stocks for quick selection
    popular_stocks = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corp.",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.",
        "TSLA": "Tesla Inc.",
        "META": "Meta Platforms",
        "NVDA": "NVIDIA Corp.",
        "JPM": "JPMorgan Chase",
        "V": "Visa Inc.",
        "WMT": "Walmart Inc."
    }

    # Quick select popular stocks
    st.markdown("**Popular Stocks:**")
    cols = st.columns(5)
    selected = None

    for idx, (symbol, name) in enumerate(popular_stocks.items()):
        with cols[idx % 5]:
            if st.button(f"{symbol}", key=f"quick_{symbol}", help=name):
                selected = symbol

    # Manual input
    st.markdown("**Or enter manually:**")
    manual_input = st.text_input(
        "Stock Symbol",
        value=selected if selected else "",
        placeholder="e.g., AAPL, MSFT, TSLA...",
        key="manual_stock_input"
    ).upper()

    return manual_input if manual_input else selected
