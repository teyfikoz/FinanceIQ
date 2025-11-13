"""
🌀 Cycle Analysis UI Module
Full-featured visualization components for cycle intelligence
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from .cycle_analysis import CycleAnalysisEngine


class CycleAnalysisUI:
    """
    Comprehensive Cycle Intelligence UI
    Features: Cycle Wheel, Timeline, Gauge, AI Commentary, ETF Recommendations
    """

    def __init__(self, fred_api=None, alpha_vantage_api=None):
        self.engine = CycleAnalysisEngine(fred_api, alpha_vantage_api)

    def render(self):
        """Render the complete Cycle Intelligence dashboard"""
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
            <h1 style='color: white; text-align: center; margin: 0;'>
                🌀 Cycle Intelligence Engine
            </h1>
            <p style='color: rgba(255,255,255,0.9); text-align: center; margin-top: 0.5rem;'>
                Comprehensive Market, Economic, Liquidity & Sentiment Analysis
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Get comprehensive analysis
        with st.spinner('🔄 Analyzing market cycles...'):
            analysis = self.engine.get_comprehensive_analysis()

        # Top-level metrics
        self._render_top_metrics(analysis)

        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎯 Overview",
            "📊 Cycle Wheel",
            "📈 Timeline",
            "💼 ETF Allocation",
            "⚙️ Advanced"
        ])

        with tab1:
            self._render_overview(analysis)

        with tab2:
            self._render_cycle_wheel(analysis)

        with tab3:
            self._render_timeline(analysis)

        with tab4:
            self._render_etf_recommendations(analysis)

        with tab5:
            self._render_advanced_analytics(analysis)

    def _render_top_metrics(self, analysis):
        """Render top-level summary metrics"""
        overall = analysis['overall_condition']
        risk = analysis['risk_level']

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {overall["color"]}AA, {overall["color"]});
                        padding: 1.5rem; border-radius: 10px; text-align: center;'>
                <div style='font-size: 3rem;'>{overall['emoji']}</div>
                <div style='color: white; font-size: 1.2rem; font-weight: bold;'>
                    {overall['condition']}
                </div>
                <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-top: 0.5rem;'>
                    Overall Market Condition
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {analysis['cycles']['market']['color']}AA, {analysis['cycles']['market']['color']});
                        padding: 1.5rem; border-radius: 10px; text-align: center;'>
                <div style='color: white; font-size: 1.5rem; font-weight: bold;'>
                    {analysis['cycles']['market']['phase']}
                </div>
                <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-top: 0.5rem;'>
                    Market Cycle
                </div>
                <div style='color: white; font-size: 0.8rem; margin-top: 0.3rem;'>
                    {analysis['cycles']['market']['confidence']*100:.0f}% confidence
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {analysis['cycles']['economic']['color']}AA, {analysis['cycles']['economic']['color']});
                        padding: 1.5rem; border-radius: 10px; text-align: center;'>
                <div style='color: white; font-size: 1.5rem; font-weight: bold;'>
                    {analysis['cycles']['economic']['phase']}
                </div>
                <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-top: 0.5rem;'>
                    Economic Cycle
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {risk['color']}AA, {risk['color']});
                        padding: 1.5rem; border-radius: 10px; text-align: center;'>
                <div style='color: white; font-size: 1.5rem; font-weight: bold;'>
                    {risk['score']}/100
                </div>
                <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-top: 0.5rem;'>
                    Risk Level
                </div>
                <div style='color: white; font-size: 0.8rem; margin-top: 0.3rem;'>
                    {risk['category']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_overview(self, analysis):
        """Render overview with AI commentary and key signals"""
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 🤖 AI Cycle Commentary")
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #2c3e50, #34495e);
                        padding: 1.5rem; border-radius: 10px; color: white;
                        border-left: 4px solid #3498db;'>
                {analysis['ai_commentary'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 📊 Cycle Phase Details")

            # Create detailed phase cards
            phases_col1, phases_col2 = st.columns(2)

            with phases_col1:
                # Market cycle
                market = analysis['cycles']['market']
                st.markdown(f"""
                <div style='background: {market['color']}22; padding: 1rem; border-radius: 8px;
                            border-left: 3px solid {market['color']};'>
                    <h4 style='color: {market['color']}; margin-top: 0;'>📈 Market Cycle</h4>
                    <p><strong>Phase:</strong> {market['phase']}</p>
                    <p><strong>Score:</strong> {market['score']*100:.1f}/100</p>
                    <p><strong>Confidence:</strong> {market['confidence']*100:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)

                # Liquidity cycle
                liquidity = analysis['cycles']['liquidity']
                st.markdown(f"""
                <div style='background: {liquidity['color']}22; padding: 1rem; border-radius: 8px;
                            border-left: 3px solid {liquidity['color']}; margin-top: 1rem;'>
                    <h4 style='color: {liquidity['color']}; margin-top: 0;'>💰 Liquidity Cycle</h4>
                    <p><strong>Phase:</strong> {liquidity['phase']}</p>
                    <p><strong>Score:</strong> {liquidity['score']*100:.1f}/100</p>
                </div>
                """, unsafe_allow_html=True)

            with phases_col2:
                # Economic cycle
                economic = analysis['cycles']['economic']
                st.markdown(f"""
                <div style='background: {economic['color']}22; padding: 1rem; border-radius: 8px;
                            border-left: 3px solid {economic['color']};'>
                    <h4 style='color: {economic['color']}; margin-top: 0;'>🏭 Economic Cycle</h4>
                    <p><strong>Phase:</strong> {economic['phase']}</p>
                    <p><strong>Score:</strong> {economic['score']*100:.1f}/100</p>
                </div>
                """, unsafe_allow_html=True)

                # Sentiment cycle
                sentiment = analysis['cycles']['sentiment']
                st.markdown(f"""
                <div style='background: {sentiment['color']}22; padding: 1rem; border-radius: 8px;
                            border-left: 3px solid {sentiment['color']}; margin-top: 1rem;'>
                    <h4 style='color: {sentiment['color']}; margin-top: 0;'>😊 Sentiment Cycle</h4>
                    <p><strong>Phase:</strong> {sentiment['phase']}</p>
                    <p><strong>Score:</strong> {sentiment['score']*100:.1f}/100</p>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            st.markdown("### 🎯 Key Signals")

            if analysis['key_signals']:
                for signal in analysis['key_signals']:
                    signal_color = '#E74C3C' if signal['type'] == 'warning' else '#2ECC71'
                    st.markdown(f"""
                    <div style='background: {signal_color}22; padding: 1rem; border-radius: 8px;
                                border-left: 3px solid {signal_color}; margin-bottom: 1rem;'>
                        <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>{signal['icon']}</div>
                        <div style='font-weight: bold; color: {signal_color};'>{signal['title']}</div>
                        <div style='font-size: 0.9rem; margin-top: 0.5rem;'>{signal['message']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No critical signals at this time")

            st.markdown("### 🎲 Phase Probabilities")
            probabilities = self.engine.get_phase_probabilities()

            for phase, prob in probabilities.items():
                st.markdown(f"""
                <div style='margin-bottom: 0.5rem;'>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 0.2rem;'>
                        <span style='font-size: 0.85rem;'>{phase}</span>
                        <span style='font-weight: bold;'>{prob}%</span>
                    </div>
                    <div style='background: #ecf0f1; border-radius: 10px; overflow: hidden;'>
                        <div style='background: linear-gradient(90deg, #3498db, #2ecc71);
                                    width: {prob}%; height: 8px;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    def _render_cycle_wheel(self, analysis):
        """Render interactive cycle wheel visualization"""
        st.markdown("### 🎯 Cycle Wheel - Visual Phase Indicator")

        cycles = analysis['cycles']

        # Create cycle wheel using plotly
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
                   [{'type': 'indicator'}, {'type': 'indicator'}]],
            subplot_titles=('Market Cycle', 'Economic Cycle', 'Liquidity Cycle', 'Sentiment Cycle')
        )

        # Market cycle gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=cycles['market']['score'] * 100,
            title={'text': cycles['market']['phase']},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': cycles['market']['color']},
                'steps': [
                    {'range': [0, 25], 'color': "#E74C3C"},
                    {'range': [25, 50], 'color': "#F39C12"},
                    {'range': [50, 75], 'color': "#2ECC71"},
                    {'range': [75, 100], 'color': "#3498DB"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': cycles['market']['score'] * 100
                }
            }
        ), row=1, col=1)

        # Economic cycle gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=cycles['economic']['score'] * 100,
            title={'text': cycles['economic']['phase']},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': cycles['economic']['color']},
                'steps': [
                    {'range': [0, 25], 'color': "#E74C3C"},
                    {'range': [25, 50], 'color': "#F39C12"},
                    {'range': [50, 75], 'color': "#2ECC71"},
                    {'range': [75, 100], 'color': "#3498DB"}
                ],
            }
        ), row=1, col=2)

        # Liquidity cycle gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=cycles['liquidity']['score'] * 100,
            title={'text': cycles['liquidity']['phase']},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': cycles['liquidity']['color']},
                'steps': [
                    {'range': [0, 30], 'color': "#E74C3C"},
                    {'range': [30, 50], 'color': "#F39C12"},
                    {'range': [50, 70], 'color': "#2ECC71"},
                    {'range': [70, 100], 'color': "#27AE60"}
                ],
            }
        ), row=2, col=1)

        # Sentiment cycle gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=cycles['sentiment']['score'] * 100,
            title={'text': cycles['sentiment']['phase']},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': cycles['sentiment']['color']},
                'steps': [
                    {'range': [0, 20], 'color': "#C0392B"},
                    {'range': [20, 40], 'color': "#E74C3C"},
                    {'range': [40, 60], 'color': "#F39C12"},
                    {'range': [60, 80], 'color': "#2ECC71"},
                    {'range': [80, 100], 'color': "#27AE60"}
                ],
            }
        ), row=2, col=2)

        fig.update_layout(
            height=700,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white', 'size': 12}
        )

        st.plotly_chart(fig, use_container_width=True)

        # Composite score
        st.markdown("### 🎯 Composite Market Score")
        composite_score = analysis['composite_score']

        fig_composite = go.Figure(go.Indicator(
            mode="gauge+number",
            value=composite_score * 100,
            title={'text': "Overall Market Condition", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': analysis['overall_condition']['color'], 'thickness': 0.75},
                'steps': [
                    {'range': [0, 25], 'color': "#E74C3C"},
                    {'range': [25, 45], 'color': "#E67E22"},
                    {'range': [45, 65], 'color': "#2ECC71"},
                    {'range': [65, 100], 'color': "#3498DB"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': composite_score * 100
                }
            }
        ))

        fig_composite.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white', 'size': 20}
        )

        st.plotly_chart(fig_composite, use_container_width=True)

    def _render_timeline(self, analysis):
        """Render historical timeline of cycle phases"""
        st.markdown("### 📈 Historical Cycle Timeline")
        st.info("📌 Historical phase tracking - showing simplified mock data")

        # Get historical phases (mock data for now)
        historical_data = self.engine.get_historical_phases(lookback_months=24)

        if historical_data:
            df = pd.DataFrame(historical_data)

            # Create timeline chart
            fig = go.Figure()

            # Composite score line
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['composite_score'],
                mode='lines+markers',
                name='Composite Score',
                line=dict(color='#3498db', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(52, 152, 219, 0.2)'
            ))

            # Add phase zones
            phases = df['market_phase'].unique()
            for phase in phases:
                phase_data = df[df['market_phase'] == phase]
                if not phase_data.empty:
                    fig.add_vrect(
                        x0=phase_data['date'].iloc[0],
                        x1=phase_data['date'].iloc[-1],
                        fillcolor='rgba(52, 152, 219, 0.1)',
                        layer="below",
                        line_width=0,
                        annotation_text=phase,
                        annotation_position="top left"
                    )

            fig.update_layout(
                title="Market Cycle Composite Score Over Time",
                xaxis_title="Date",
                yaxis_title="Score (0-1)",
                hovermode='x unified',
                height=500,
                template='plotly_dark',
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)

        # Phase distribution
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Phase Distribution (24M)")

            phase_counts = pd.DataFrame(historical_data)['market_phase'].value_counts()

            fig_pie = go.Figure(data=[go.Pie(
                labels=phase_counts.index,
                values=phase_counts.values,
                hole=.4,
                marker=dict(colors=['#2ECC71', '#F39C12', '#E74C3C', '#3498DB'])
            )])

            fig_pie.update_layout(
                height=400,
                template='plotly_dark',
                showlegend=True
            )

            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.markdown("### 📈 Score Trend")

            df_hist = pd.DataFrame(historical_data)
            df_hist['MA_3M'] = df_hist['composite_score'].rolling(3).mean()

            fig_trend = go.Figure()

            fig_trend.add_trace(go.Scatter(
                x=df_hist['date'],
                y=df_hist['composite_score'],
                mode='lines',
                name='Score',
                line=dict(color='#3498db', width=2)
            ))

            fig_trend.add_trace(go.Scatter(
                x=df_hist['date'],
                y=df_hist['MA_3M'],
                mode='lines',
                name='3M Average',
                line=dict(color='#e74c3c', width=2, dash='dash')
            ))

            fig_trend.update_layout(
                height=400,
                template='plotly_dark',
                showlegend=True,
                xaxis_title="Date",
                yaxis_title="Score"
            )

            st.plotly_chart(fig_trend, use_container_width=True)

    def _render_etf_recommendations(self, analysis):
        """Render ETF allocation recommendations"""
        st.markdown("### 💼 Cycle-Based ETF Allocation Recommendations")

        recommendations = analysis['etf_recommendations']
        allocations = recommendations['allocations']

        if allocations:
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("#### 📊 Recommended Allocation")

                # Create allocation pie chart
                fig_alloc = go.Figure(data=[go.Pie(
                    labels=list(allocations.keys()),
                    values=list(allocations.values()),
                    hole=.4,
                    marker=dict(colors=['#2ECC71', '#3498DB', '#F39C12', '#E67E22', '#95A5A6', '#9B59B6']),
                    textinfo='label+percent',
                    textfont=dict(size=14)
                )])

                fig_alloc.update_layout(
                    height=500,
                    template='plotly_dark',
                    showlegend=True,
                    legend=dict(orientation="v", x=1.1, y=0.5)
                )

                st.plotly_chart(fig_alloc, use_container_width=True)

            with col2:
                st.markdown("#### 🎯 Top ETF Picks")

                for rec in recommendations['recommendations']:
                    category = rec['category']
                    weight = rec['weight']
                    etfs = rec['etfs']

                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #2c3e50, #34495e);
                                padding: 1rem; border-radius: 10px; margin-bottom: 1rem;
                                border-left: 4px solid #3498db;'>
                        <h4 style='color: #3498db; margin-top: 0;'>{category}</h4>
                        <p style='color: white;'><strong>Allocation:</strong> {weight}%</p>
                        <p style='color: rgba(255,255,255,0.8);'>
                            <strong>Recommended ETFs:</strong><br>
                            {' | '.join(etfs)}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

        # Allocation table
        st.markdown("#### 📋 Full Allocation Breakdown")

        df_alloc = pd.DataFrame([
            {'Asset Class': k, 'Allocation %': v}
            for k, v in sorted(allocations.items(), key=lambda x: x[1], reverse=True)
        ])

        st.dataframe(
            df_alloc,
            use_container_width=True,
            hide_index=True
        )

    def _render_advanced_analytics(self, analysis):
        """Render advanced analytics and diagnostics"""
        st.markdown("### ⚙️ Advanced Analytics")

        tab1, tab2, tab3 = st.tabs(["📊 Indicators", "🔬 Diagnostics", "📥 Export"])

        with tab1:
            st.markdown("#### Raw Indicator Values")

            cycles = analysis['cycles']

            # Market indicators
            st.markdown("**Market Cycle Indicators:**")
            if cycles['market']['indicators']:
                df_market = pd.DataFrame([cycles['market']['indicators']])
                st.dataframe(df_market, use_container_width=True)

            # Economic indicators
            st.markdown("**Economic Cycle Indicators:**")
            if cycles['economic']['indicators']:
                df_econ = pd.DataFrame([cycles['economic']['indicators']])
                st.dataframe(df_econ, use_container_width=True)

            # Liquidity indicators
            st.markdown("**Liquidity Cycle Indicators:**")
            if cycles['liquidity']['indicators']:
                df_liq = pd.DataFrame([cycles['liquidity']['indicators']])
                st.dataframe(df_liq, use_container_width=True)

            # Sentiment indicators
            st.markdown("**Sentiment Cycle Indicators:**")
            if cycles['sentiment']['indicators']:
                df_sent = pd.DataFrame([cycles['sentiment']['indicators']])
                st.dataframe(df_sent, use_container_width=True)

        with tab2:
            st.markdown("#### 🔬 System Diagnostics")

            st.json({
                'timestamp': analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'composite_score': round(analysis['composite_score'], 3),
                'overall_condition': analysis['overall_condition']['condition'],
                'risk_score': analysis['risk_level']['score'],
                'confidence_levels': {
                    'market': round(cycles['market']['confidence'], 2),
                    'economic': round(cycles['economic']['confidence'], 2),
                    'liquidity': round(cycles['liquidity']['confidence'], 2),
                    'sentiment': round(cycles['sentiment']['confidence'], 2)
                }
            })

        with tab3:
            st.markdown("#### 📥 Export Analysis")

            st.info("Export functionality - coming soon")

            if st.button("📄 Generate PDF Report"):
                st.success("PDF report generation would be implemented here")

            if st.button("💾 Download Raw Data (JSON)"):
                st.download_button(
                    label="Download JSON",
                    data=str(analysis),
                    file_name=f"cycle_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )


def create_cycle_intelligence_ui(fred_api=None, alpha_vantage_api=None):
    """
    Main entry point for Cycle Intelligence UI
    Call this from main.py
    """
    ui = CycleAnalysisUI(fred_api, alpha_vantage_api)
    ui.render()
