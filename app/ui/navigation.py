"""
Navigation Component for Game Changer Features
Provides tab-based navigation for all Phase 1 features
"""

import streamlit as st


def create_game_changer_navigation():
    """
    Create navigation tabs for Game Changer features
    Returns the selected tab name
    """

    st.markdown("""
    <style>
        .game-changer-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
        }
        .feature-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.85rem;
            margin: 0.2rem;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="game-changer-header">
        <h1>🚀 FinanceIQ Game Changer Features</h1>
        <p style="font-size: 1.1rem; margin-top: 0.5rem;">
            Phase 1: Social, Visualization & AI-Lite Tools
        </p>
        <div style="margin-top: 1rem;">
            <span class="feature-badge">💰 $0 Cost</span>
            <span class="feature-badge">🌐 Offline-Friendly</span>
            <span class="feature-badge">🚀 No Paid APIs</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Create main navigation tabs
    main_tabs = st.tabs([
        "🏠 Overview",
        "🎯 Social Features",
        "🎨 Visualizations",
        "🤖 AI Tools",
        "📤 Export & Share"
    ])

    return main_tabs


def create_feature_overview():
    """Display overview of all Game Changer features"""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🎯 Social Layer
        - **📸 Portfolio Snapshots**: Create shareable PNG cards
        - **📋 Public Watchlists**: Curated stock lists (ETFs, Blue Chips, etc.)
        - **📝 Ticker Notes**: Personal notes per stock (session-based)
        - **🏆 Leaderboard**: Demo performance rankings

        ### 🎨 Advanced Visualizations
        - **📅 Heatmap Calendar**: GitHub-style returns calendar
        - **🔄 Sector Rotation Wheel**: Interactive sector performance
        - **😱 Fear & Greed Gauge**: Market sentiment indicator
        - **📊 3D Portfolio**: Interactive treemap & sunburst charts
        """)

    with col2:
        st.markdown("""
        ### 🤖 AI-Powered Tools
        - **🎲 Monte Carlo Simulation**: 10,000+ portfolio paths
        - **⚡ Backtesting Engine**: Test SMA/RSI/MACD strategies
        - **🎯 Auto Chart Annotation**: Support/resistance detection
        - **📰 News Sentiment**: Keyword-based sentiment scoring

        ### 📤 Export & Sharing
        - **📄 PDF Export**: Professional reports
        - **📊 Excel Export**: Data downloads
        - **📱 QR Codes**: Share dashboard URLs
        - **🌓 Dark/Light Theme**: Custom UI themes
        """)

    st.markdown("---")

    # Quick stats
    st.markdown("### 📊 Quick Stats")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Features", "15+", delta="Phase 1")
    with col2:
        st.metric("Cost", "$0", delta="Free Forever")
    with col3:
        st.metric("APIs Required", "0", delta="Offline Ready")
    with col4:
        st.metric("Data Sources", "yfinance", delta="Free & Open")

    # Getting Started
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")

    st.info("""
    **Navigate using the tabs above:**
    1. **Social Features**: Build your portfolio snapshot, explore watchlists
    2. **Visualizations**: Analyze with advanced charts and heatmaps
    3. **AI Tools**: Run simulations, backtest strategies, analyze sentiment
    4. **Export & Share**: Download reports and share insights
    """)


def create_quick_actions_sidebar():
    """Create quick actions in sidebar"""

    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚡ Quick Actions")

        if st.button("📸 Create Snapshot", use_container_width=True):
            st.session_state['quick_action'] = 'snapshot'

        if st.button("🎲 Run Monte Carlo", use_container_width=True):
            st.session_state['quick_action'] = 'monte_carlo'

        if st.button("📊 Sector Rotation", use_container_width=True):
            st.session_state['quick_action'] = 'sector_rotation'

        if st.button("😱 Fear & Greed", use_container_width=True):
            st.session_state['quick_action'] = 'fear_greed'

        st.markdown("---")
        st.markdown("### 📚 Resources")
        st.markdown("""
        - [User Guide](#)
        - [API Docs](#)
        - [Report Issues](#)
        - [Feature Requests](#)
        """)


if __name__ == "__main__":
    tabs = create_game_changer_navigation()

    with tabs[0]:
        create_feature_overview()

    with tabs[1]:
        st.info("Social Features will be displayed here")

    with tabs[2]:
        st.info("Visualizations will be displayed here")

    with tabs[3]:
        st.info("AI Tools will be displayed here")

    with tabs[4]:
        st.info("Export tools will be displayed here")

    create_quick_actions_sidebar()
