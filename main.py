#!/usr/bin/env python3
"""
FinanceIQ Pro - Integrated Platform
Combines original features with Phase 3-4 advanced institutional analytics
"""

import streamlit as st
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

# Import Phase 3-4 modules
try:
    from modules.portfolio_health_ui import PortfolioHealthUI
    from modules.etf_weight_tracker_ui import ETFWeightTrackerUI
    from modules.data_reliability import DataReliabilityAuditor
    from modules.scenario_sandbox_ui import ScenarioSandboxUI
    from modules.fund_flow_radar_ui import FundFlowRadarUI
    from modules.whale_investor_analytics_ui import WhaleInvestorAnalyticsUI
    from modules.whale_correlation_ui import WhaleCorrelationUI
    from modules.whale_momentum_tracker_ui import WhaleMomentumTrackerUI
    from modules.etf_whale_linkage_ui import ETFWhaleLinkageUI
    from modules.hedge_fund_activity_radar_ui import HedgeFundActivityRadarUI
    from modules.institutional_event_reaction_lab_ui import InstitutionalEventReactionLabUI
    PHASE_3_4_AVAILABLE = True
except ImportError as e:
    PHASE_3_4_AVAILABLE = False
    st.warning(f"⚠️ Phase 3-4 modules not available: {e}")

# Import original features (optional - won't break if missing)
try:
    from utils.authentication import require_authentication, get_current_user, init_session_state
    AUTHENTICATION_AVAILABLE = True
except ImportError:
    AUTHENTICATION_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="FinanceIQ Pro | Advanced Portfolio Analytics",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state if authentication available
if AUTHENTICATION_AVAILABLE:
    init_session_state()
    # Check authentication - but make it optional for demo
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True  # Auto-login for demo

# Custom CSS
st.markdown("""
<style>
    .main { padding: 1rem 2rem; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.1);
        border-radius: 6px;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.3) !important;
    }
    h1 { color: #667eea; }
    .stMetric { background: #f8f9fa; padding: 1rem; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
# 🧠 FinanceIQ Pro - Unified Platform
### Bloomberg Terminal Seviyesinde Portföy Analizi

**v1.7 - Phase 3-4 Institutional Intelligence**

**Profesyonel yatırımcılar için gelişmiş analitik araçlar:**
- 📊 Portfolio Health Score (8 metrik analizi)
- 📈 ETF Holdings Weight Tracker (Kurumsal yatırımcı takibi)
- 🧪 Scenario Sandbox (Makro senaryo simülasyonları)
- 📡 Fund Flow Radar (Para akışı analizi)
- 🐋 Whale Investor Analytics (Efsanevi yatırımcı takibi)
- 🔗 Whale Correlation Engine (Yatırımcı ilişki analizi)
- 📈 **Whale Momentum Tracker** ⭐ (Kurumsal konsensus takibi)
- 🔗 **ETF-Whale Linkage** ⭐ (Passive vs Active analizi)
- 📡 **Hedge Fund Activity Radar** ⭐ (Multi-source institutional tracking)
- 📅 **Institutional Event Reaction Lab** ⭐ (FOMC/CPI reaction analysis)
""")

st.markdown("---")

# Sidebar - Data Audit
with st.sidebar:
    st.markdown("## ⚙️ System Health")
    
    if PHASE_3_4_AVAILABLE:
        if st.button("🔍 Run Data Audit", use_container_width=True, key="sidebar_audit_btn"):
            with st.spinner("Veri kalitesi kontrol ediliyor..."):
                auditor = DataReliabilityAuditor()
                audit_results = auditor.run_full_audit()
                
                health_score = audit_results['health_score']
                
                # Display health score with color coding
                if health_score >= 80:
                    st.success(f"**Health Score:** {health_score:.1f}/100")
                    st.success("✅ Excellent - Data is reliable")
                elif health_score >= 60:
                    st.warning(f"**Health Score:** {health_score:.1f}/100")
                    st.warning("⚠️ Good - Minor issues detected")
                else:
                    st.error(f"**Health Score:** {health_score:.1f}/100")
                    st.error("🔴 Poor - Immediate action required")
                
                # Show recommendations
                if audit_results['recommendations']:
                    st.markdown("**💡 Recommendations:**")
                    for rec in audit_results['recommendations']:
                        st.info(rec)
    
    st.markdown("---")
    st.markdown("### 📚 Quick Links")
    st.markdown("""
    - [GitHub Repo](https://github.com/teyfikoz/FinanceIQ)
    - [Documentation](https://github.com/teyfikoz/FinanceIQ/blob/main/README.md)
    - [Report Bug](https://github.com/teyfikoz/FinanceIQ/issues)
    """)
    
    st.markdown("---")
    st.markdown(f"""
    **Status:**
    - Phase 3-4: {'✅ Active' if PHASE_3_4_AVAILABLE else '❌ Unavailable'}
    - Authentication: {'✅ Active' if AUTHENTICATION_AVAILABLE else '⚠️ Demo Mode'}
    """)

# Main application
if PHASE_3_4_AVAILABLE:
    # Phase 3-4 tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "📊 Portfolio Health",
        "📈 ETF Weight Tracker",
        "🧪 Scenario Sandbox",
        "📡 Fund Flow Radar",
        "🐋 Whale Investors",
        "🔗 Whale Correlation",
        "📈 Whale Momentum ⭐",
        "🔗 ETF-Whale Linkage ⭐",
        "📡 Hedge Fund Radar ⭐",
        "📅 Event Reaction Lab ⭐"
    ])
    
    with tab1:
        health_ui = PortfolioHealthUI()
        health_ui.render()
    
    with tab2:
        tracker_ui = ETFWeightTrackerUI()
        tracker_ui.render()
    
    with tab3:
        scenario_ui = ScenarioSandboxUI()
        scenario_ui.render()
    
    with tab4:
        flow_ui = FundFlowRadarUI()
        flow_ui.render()
    
    with tab5:
        whale_ui = WhaleInvestorAnalyticsUI()
        whale_ui.render()
    
    with tab6:
        correlation_ui = WhaleCorrelationUI()
        correlation_ui.render()
    
    with tab7:
        st.markdown("### 📈 Whale Momentum Tracker")
        st.markdown("**NEW in v1.7!** Track institutional consensus in real-time.")
        momentum_ui = WhaleMomentumTrackerUI()
        momentum_ui.render()
    
    with tab8:
        st.markdown("### 🔗 ETF-Whale Linkage Analyzer")
        st.markdown("**NEW in v1.7!** Understand your passive vs active exposure.")
        etf_whale_ui = ETFWhaleLinkageUI()
        etf_whale_ui.render()
    
    with tab9:
        st.markdown("### 📡 Hedge Fund Activity Radar")
        st.markdown("**NEW in v1.7!** Multi-source institutional activity tracking.")
        hedge_fund_ui = HedgeFundActivityRadarUI()
        hedge_fund_ui.render()
    
    with tab10:
        st.markdown("### 📅 Institutional Event Reaction Lab")
        st.markdown("**NEW in v1.7!** Track how whales react to FOMC, CPI, Jobs Reports.")
        event_lab_ui = InstitutionalEventReactionLabUI()
        event_lab_ui.render()

else:
    st.error("""
    ❌ **Phase 3-4 modules could not be loaded.**
    
    Please ensure all module files are present:
    - modules/portfolio_health_ui.py
    - modules/etf_weight_tracker_ui.py
    - modules/scenario_sandbox_ui.py
    - modules/fund_flow_radar_ui.py
    - modules/whale_investor_analytics_ui.py
    - modules/whale_correlation_ui.py
    - modules/whale_momentum_tracker_ui.py (NEW)
    - modules/etf_whale_linkage_ui.py (NEW)
    - modules/hedge_fund_activity_radar_ui.py (NEW)
    - modules/institutional_event_reaction_lab_ui.py (NEW)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 2rem;'>
    <p><strong>FinanceIQ Pro v1.7</strong> | Bloomberg-level Analytics for Retail Investors</p>
    <p>📧 support@financeiq.com | 🌐 www.financeiq.com</p>
    <p>🐙 <a href="https://github.com/teyfikoz/FinanceIQ" target="_blank">GitHub</a></p>
</div>
""", unsafe_allow_html=True)
