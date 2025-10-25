"""
Institutional Event Reaction Lab UI - Interactive interface for event reaction analysis
Visualizes how whales react to FOMC, CPI, Jobs Reports, etc.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List

from modules.institutional_event_reaction_lab import (
    InstitutionalEventReactionLab,
    EconomicEvent,
    quick_event_reaction_analysis
)
from modules.whale_investor_analytics import WhaleInvestorAnalytics


class InstitutionalEventReactionLabUI:
    """Streamlit UI for Institutional Event Reaction Lab"""

    def __init__(self):
        self.lab = InstitutionalEventReactionLab()
        self.whale_analytics = WhaleInvestorAnalytics()

    def render(self):
        """Main render method"""

        st.markdown("""
        ## 📅 Institutional Event Reaction Lab

        **Track how whale investors react to major economic events:**
        - 📊 FOMC meetings (Fed rate decisions)
        - 📈 CPI releases (inflation data)
        - 💼 Jobs Reports (Nonfarm Payrolls)
        - 🎤 Fed speeches (Powell, etc.)
        - 📉 Earnings seasons

        **Analysis:**
        - Before/After portfolio comparison
        - Sector rotation detection (Defensive ↔ Growth)
        - Reaction latency (how quickly whales react)
        - Anticipatory positioning (did they know beforehand?)
        - Whale consensus vs divergence

        **Use Case:** "Did Buffett rotate to defensive BEFORE the FOMC hawkish surprise?"
        """)

        st.markdown("---")

        # Settings
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Event date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)  # 6 months

            date_range = st.date_input(
                "Event Date Range",
                value=(start_date, end_date),
                key="event_date_range"
            )

        with col2:
            # Event types
            event_types = st.multiselect(
                "Event Types",
                options=['FOMC', 'CPI', 'JOBS', 'GDP', 'FED_SPEECH'],
                default=['FOMC', 'CPI', 'JOBS'],
                key="event_types"
            )

        with col3:
            # Analysis window
            window_days = st.number_input(
                "Analysis Window (days)",
                min_value=3,
                max_value=30,
                value=7,
                key="event_window"
            )

        # Whale selection
        st.markdown("### 🐋 Select Whale Investors")
        all_investors = list(self.whale_analytics.WHALE_INVESTORS.keys())
        selected_investors = st.multiselect(
            "Whale investors to analyze",
            options=all_investors,
            default=['buffett', 'gates', 'wood', 'dalio'],
            format_func=lambda x: f"{self.whale_analytics.WHALE_INVESTORS[x]['icon']} {self.whale_analytics.WHALE_INVESTORS[x]['name']}",
            key="event_whales"
        )

        # Analyze button
        if st.button("📅 Analyze Event Reactions", type="primary", use_container_width=True):
            if len(selected_investors) < 2:
                st.error("❌ En az 2 whale seçin")
                return

            if len(event_types) == 0:
                st.error("❌ En az 1 event type seçin")
                return

            with st.spinner("Event reactions analiz ediliyor..."):
                self._analyze_and_display(selected_investors, date_range, event_types, window_days)

    def _analyze_and_display(self, selected_investors, date_range, event_types, window_days):
        """Analyze and display results"""

        # Generate events
        start_date = datetime.combine(date_range[0], datetime.min.time())
        end_date = datetime.combine(date_range[1], datetime.min.time())

        events = self.lab.generate_synthetic_events(start_date, end_date)

        # Filter by event types
        events = [e for e in events if e.event_type in event_types]

        if len(events) == 0:
            st.warning("⚠️ No events found in selected date range")
            return

        st.success(f"✅ {len(events)} events found in date range")

        # Load whale portfolios
        whale_portfolios = {}
        for inv_key in selected_investors:
            df = self.whale_analytics.load_whale_data(inv_key, '2024Q4')
            if df is not None and len(df) > 0:
                name = self.whale_analytics.WHALE_INVESTORS[inv_key]['name']
                whale_portfolios[name] = df

        if len(whale_portfolios) < 2:
            st.error("❌ Yeterli whale data yüklenemedi")
            return

        # Run analysis
        results = quick_event_reaction_analysis(whale_portfolios, events)

        # Display results
        self._display_event_timeline(results['event_timeline'])
        self._display_event_analyses(results['event_analyses'])
        self._display_reaction_latencies(results['reaction_latencies'])
        self._display_sector_rotations(results['event_analyses'])
        self._display_anticipatory_moves(results['anticipatory_moves'])

    def _display_event_timeline(self, timeline: pd.DataFrame):
        """Display event timeline"""
        st.markdown("---")
        st.markdown("### 📅 Event Timeline")

        if len(timeline) == 0:
            st.info("No timeline data available")
            return

        # Timeline chart
        fig = go.Figure()

        # Event markers
        colors = {
            'FOMC': 'red',
            'CPI': 'orange',
            'JOBS': 'blue',
            'GDP': 'green',
            'FED_SPEECH': 'purple'
        }

        for event_type in timeline['event_type'].unique():
            events = timeline[timeline['event_type'] == event_type]

            fig.add_trace(go.Scatter(
                x=events['date'],
                y=events['magnitude'],
                mode='markers+text',
                name=event_type,
                marker=dict(
                    size=events['magnitude'] * 3,
                    color=colors.get(event_type, 'gray'),
                    line=dict(width=1, color='white')
                ),
                text=events['description'].str[:20],
                textposition='top center',
                hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Magnitude: %{y:.1f}<br>Whale Activity: %{customdata}<extra></extra>',
                customdata=events['total_whale_activity']
            ))

        fig.update_layout(
            title="Economic Events Timeline (Size = Magnitude)",
            xaxis_title="Date",
            yaxis_title="Event Magnitude (0-10)",
            height=400,
            hovermode='closest'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Event table
        with st.expander("📋 Event Details"):
            display_df = timeline[['date', 'event_type', 'description', 'impact', 'magnitude', 'total_whale_activity']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df.columns = ['Date', 'Type', 'Description', 'Impact', 'Magnitude', 'Whale Activity']
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    def _display_event_analyses(self, event_analyses: List[Dict]):
        """Display individual event analyses"""
        st.markdown("---")
        st.markdown("### 🔍 Event-by-Event Analysis")

        if len(event_analyses) == 0:
            st.info("No event analyses available")
            return

        # Select event to view
        event_options = [f"{a['event'].event_type} - {a['event'].date.strftime('%Y-%m-%d')} ({a['event'].impact})"
                        for a in event_analyses]

        if len(event_options) == 0:
            return

        selected_event_idx = st.selectbox(
            "Select event to view details",
            options=range(len(event_options)),
            format_func=lambda i: event_options[i],
            key="selected_event"
        )

        analysis = event_analyses[selected_event_idx]

        # Event header
        st.markdown(f"#### {analysis['event'].description}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Event Type", analysis['event'].event_type)

        with col2:
            st.metric("Impact", analysis['event'].impact)

        with col3:
            st.metric("Consensus", analysis['consensus'])

        with col4:
            st.metric("Whales Analyzed", analysis['num_whales'])

        # Reaction scores
        st.markdown("#### 📊 Whale Reaction Scores")

        reaction_data = []
        for reaction in analysis['reactions']:
            reaction_data.append({
                'Whale': reaction['whale_name'],
                'Reaction Score': reaction['reaction_score'],
                'Rotation': reaction['rotation'],
                'Changes': reaction['num_changes']
            })

        reaction_df = pd.DataFrame(reaction_data).sort_values('Reaction Score', ascending=False)

        # Bar chart
        fig = go.Figure()

        colors = reaction_df['Reaction Score'].apply(
            lambda x: 'green' if x > 20 else 'red' if x < -20 else 'gray'
        )

        fig.add_trace(go.Bar(
            x=reaction_df['Whale'],
            y=reaction_df['Reaction Score'],
            marker_color=colors,
            text=reaction_df['Rotation'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Score: %{y:.1f}<br>Rotation: %{text}<extra></extra>'
        ))

        fig.update_layout(
            title="Reaction Scores (Positive = Risk-On, Negative = Risk-Off)",
            xaxis_title="Whale",
            yaxis_title="Reaction Score",
            height=400
        )
        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        if analysis['consensus'] == 'STRONG_CONSENSUS':
            st.success(f"✅ **Strong Consensus**: All whales reacted similarly (std: {analysis['std_reaction_score']:.1f})")
        elif analysis['consensus'] == 'MODERATE_CONSENSUS':
            st.info(f"🟡 **Moderate Consensus**: Some agreement among whales (std: {analysis['std_reaction_score']:.1f})")
        else:
            st.warning(f"⚠️ **Divergence**: Whales reacted very differently (std: {analysis['std_reaction_score']:.1f})")

        st.markdown(f"🟢 **Most Bullish:** {analysis['most_bullish_whale']} ({analysis['most_bullish_score']:.1f})")
        st.markdown(f"🔴 **Most Bearish:** {analysis['most_bearish_whale']} ({analysis['most_bearish_score']:.1f})")

    def _display_reaction_latencies(self, latencies: pd.DataFrame):
        """Display reaction latency analysis"""
        st.markdown("---")
        st.markdown("### ⏱️ Reaction Latency (Speed)")

        if len(latencies) == 0:
            st.info("💡 **Latency Analysis:** Requires whale moves data (not available in synthetic mode)")
            return

        # Bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=latencies['whale'],
            y=latencies['avg_latency'],
            error_y=dict(
                type='data',
                array=(latencies['max_latency'] - latencies['min_latency']) / 2,
                visible=True
            ),
            marker_color='lightblue',
            hovertemplate='<b>%{x}</b><br>Avg Latency: %{y:.1f} days<br>Range: %{customdata[0]:.0f}-%{customdata[1]:.0f} days<extra></extra>',
            customdata=latencies[['min_latency', 'max_latency']].values
        ))

        fig.update_layout(
            title="Average Reaction Latency (Days After Event)",
            xaxis_title="Whale",
            yaxis_title="Days",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 **Yorumlama:** Düşük latency = hızlı hareket eden whale (proactive)")

    def _display_sector_rotations(self, event_analyses: List[Dict]):
        """Display sector rotation patterns"""
        st.markdown("---")
        st.markdown("### 🔄 Sector Rotation Patterns")

        # Aggregate sector rotations across all events
        rotation_counts = {'DEFENSIVE': 0, 'GROWTH': 0, 'NEUTRAL': 0}

        for analysis in event_analyses:
            for reaction in analysis['reactions']:
                rotation_counts[reaction['rotation']] += 1

        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=list(rotation_counts.keys()),
            values=list(rotation_counts.values()),
            marker=dict(colors=['orange', 'green', 'gray'])
        )])

        fig.update_layout(
            title="Sector Rotation Distribution Across All Events",
            height=350
        )

        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Defensive Rotations", rotation_counts['DEFENSIVE'])
            st.caption("Risk-off moves")

        with col2:
            st.metric("Growth Rotations", rotation_counts['GROWTH'])
            st.caption("Risk-on moves")

        with col3:
            st.metric("Neutral", rotation_counts['NEUTRAL'])
            st.caption("No clear rotation")

    def _display_anticipatory_moves(self, anticipatory_moves: List[Dict]):
        """Display anticipatory positioning analysis"""
        st.markdown("---")
        st.markdown("### 🔮 Anticipatory Positioning")

        if len(anticipatory_moves) == 0:
            st.info("💡 **Anticipatory Moves:** Requires whale moves data (not available in synthetic mode)")
            st.markdown("""
            **What is anticipatory positioning?**
            - Whale makes a move BEFORE an event
            - Move aligns with eventual event impact
            - Suggests insider knowledge or superior forecasting

            **Example:**
            - Buffett sells tech 5 days before hawkish FOMC → Anticipatory ✅
            - Buffett sells tech 3 days after hawkish FOMC → Reactive ❌
            """)
            return

        st.success(f"🔮 **{len(anticipatory_moves)} anticipatory moves detected!**")

        # Group by whale
        whale_counts = {}
        for move in anticipatory_moves:
            whale = move['whale']
            whale_counts[whale] = whale_counts.get(whale, 0) + 1

        # Bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=list(whale_counts.keys()),
            y=list(whale_counts.values()),
            marker_color='purple',
            text=list(whale_counts.values()),
            textposition='outside'
        ))

        fig.update_layout(
            title="Anticipatory Moves by Whale",
            xaxis_title="Whale",
            yaxis_title="# of Anticipatory Moves",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Details
        with st.expander("📋 Anticipatory Move Details"):
            moves_df = pd.DataFrame(anticipatory_moves)
            display_cols = ['whale', 'ticker', 'action', 'days_before_event', 'alignment']
            if all(col in moves_df.columns for col in display_cols):
                display_df = moves_df[display_cols].copy()
                display_df.columns = ['Whale', 'Ticker', 'Action', 'Days Before', 'Alignment']
                st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_institutional_event_reaction_lab():
    """Main render function"""
    ui = InstitutionalEventReactionLabUI()
    ui.render()


if __name__ == "__main__":
    render_institutional_event_reaction_lab()
