#!/usr/bin/env python3
"""
🚀 FinanceIQ Game Changer Dashboard - Phase 1
Consolidated dashboard with all Phase 1 features:
- Social Layer (Snapshots, Watchlists, Notes, Leaderboard)
- Advanced Visualizations (Heatmaps, Sector Rotation, Fear & Greed, 3D Portfolio)
- AI-Lite Tools (Monte Carlo, Backtesting, Auto Annotation, News Sentiment)
- Export & Sharing (PDF, Excel, QR Codes)
"""

import streamlit as st
import warnings
import sys
import os

warnings.filterwarnings('ignore')

# Add app directory to path to avoid config import issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Game Changer modules (they are self-contained)
try:
    from app.analytics.social_features import SocialFeatures, render_social_features
    from app.analytics.visualization_tools import VisualizationTools, render_visualization_tools
    from app.analytics.ai_lite_tools import AILiteTools, render_ai_lite_tools
    from app.ui.navigation import create_game_changer_navigation, create_feature_overview, create_quick_actions_sidebar
    from app.ui.export_tools import create_export_ui
    from app.ui.theme_toggle import apply_theme, create_theme_toggle
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Configure page
st.set_page_config(
    page_title="FinanceIQ | Game Changer Features",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme
apply_theme()


def main():
    """Main dashboard application"""

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/667eea/ffffff?text=FinanceIQ", use_container_width=True)
        st.markdown("---")

        # Theme toggle
        create_theme_toggle()

        # Quick stats
        st.markdown("### 📊 Dashboard Stats")
        st.metric("Active Features", "15+")
        st.metric("Cost", "$0")
        st.metric("Offline Ready", "✅")

        # Quick actions
        create_quick_actions_sidebar()

    # Main navigation
    main_tabs = create_game_changer_navigation()

    # Tab 0: Overview
    with main_tabs[0]:
        create_feature_overview()

        # Demo video or tutorial section
        st.markdown("---")
        st.markdown("### 🎥 Featured Tutorials")

        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container():
                st.markdown("""
                <div style="padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
                    <h4>📸 Portfolio Snapshots</h4>
                    <p>Create beautiful, shareable portfolio cards</p>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            with st.container():
                st.markdown("""
                <div style="padding: 1rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white;">
                    <h4>🎲 Monte Carlo</h4>
                    <p>Simulate 10,000+ portfolio scenarios</p>
                </div>
                """, unsafe_allow_html=True)

        with col3:
            with st.container():
                st.markdown("""
                <div style="padding: 1rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white;">
                    <h4>📊 Visualizations</h4>
                    <p>Interactive charts and heatmaps</p>
                </div>
                """, unsafe_allow_html=True)

    # Tab 1: Social Features
    with main_tabs[1]:
        render_social_features()

    # Tab 2: Visualizations
    with main_tabs[2]:
        render_visualization_tools()

    # Tab 3: AI Tools
    with main_tabs[3]:
        render_ai_lite_tools()

    # Tab 4: Export & Share
    with main_tabs[4]:
        create_export_ui()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #666;">
        <p><strong>🧠 FinanceIQ</strong> | AI-Powered Financial Analysis Platform</p>
        <p>Phase 1 Game Changer Features | Cost: $0 | Offline-Friendly | No Paid APIs</p>
        <p style="font-size: 0.85rem;">© 2024 FinanceIQ. Built with Streamlit, Plotly, and ❤️</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
