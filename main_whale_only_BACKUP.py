"""
FinanceIQ Pro - Advanced Portfolio Analytics
Portfolio Health Score + ETF Holdings Weight Tracker
"""

import streamlit as st
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

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

# Page config
st.set_page_config(
    page_title="FinanceIQ Pro | Portfolio Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# 🐋 FinanceIQ Pro - Whale Intelligence
### Bloomberg Terminal Seviyesinde Kurumsal Yatırımcı Takibi

**10 Advanced Institutional Analytics Modules:**

Track legendary investors (Buffett, Gates, Dalio, Cathie Wood) and institutional money flows in real-time.
""")

st.markdown("---")

# Sidebar - Data Audit
with st.sidebar:
    st.markdown("## ⚙️ System Health")

    if st.button("🔍 Run Data Audit", use_container_width=True):
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

            # Summary stats
            with st.expander("📊 Audit Details"):
                st.markdown(f"""
                **Checks:**
                - ✅ Passed: {audit_results['checks_passed']}
                - ❌ Failed: {audit_results['checks_failed']}
                - ⚠️ Warnings: {len(audit_results['warnings'])}

                **Status:** {audit_results['timestamp']}
                """)

    st.markdown("---")
    st.markdown("### 📚 Quick Links")
    st.markdown("""
    - [Documentation](https://github.com/yourrepo)
    - [Report Bug](https://github.com/yourrepo/issues)
    - [Feature Request](https://github.com/yourrepo/issues)
    """)

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 Portfolio Health Score",
    "📈 ETF Weight Tracker",
    "🧪 Scenario Sandbox",
    "📡 Fund Flow Radar",
    "🐋 Whale Investors",
    "🔗 Whale Correlation",
    "📈 Whale Momentum",
    "🔗 ETF-Whale Linkage",
    "📡 Hedge Fund Radar",
    "📅 Event Reaction Lab"
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
    momentum_ui = WhaleMomentumTrackerUI()
    momentum_ui.render()

with tab8:
    etf_whale_ui = ETFWhaleLinkageUI()
    etf_whale_ui.render()

with tab9:
    hedge_fund_ui = HedgeFundActivityRadarUI()
    hedge_fund_ui.render()

with tab10:
    event_lab_ui = InstitutionalEventReactionLabUI()
    event_lab_ui.render()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 2rem;'>
    <p>FinanceIQ Pro v1.7 | Bloomberg-level Analytics for Retail Investors</p>
    <p>📧 support@financeiq.com | 🌐 www.financeiq.com</p>
</div>
""", unsafe_allow_html=True)
