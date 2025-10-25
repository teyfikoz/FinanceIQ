"""
🎨 Advanced Visualization Tools - Phase 1 Game Changer Features
Heatmap Calendar, Sector Rotation Wheel, Fear & Greed Gauge, 3D Portfolio Allocation
All visualizations are offline-friendly using Plotly, Seaborn, and Matplotlib
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import yfinance as yf
import calendar


class VisualizationTools:
    """Advanced visualization toolkit for FinanceIQ"""

    def __init__(self):
        self.sector_colors = {
            'Technology': '#1f77b4',
            'Healthcare': '#ff7f0e',
            'Financial': '#2ca02c',
            'Consumer': '#d62728',
            'Industrial': '#9467bd',
            'Energy': '#8c564b',
            'Materials': '#e377c2',
            'Utilities': '#7f7f7f',
            'Real Estate': '#bcbd22',
            'Communication': '#17becf',
            'Consumer Defensive': '#aec7e8',
            'Other': '#c5b0d5'
        }

    # ========== 1. Heatmap Calendar (GitHub-style) ==========

    def create_returns_heatmap_calendar(self, ticker, period="1y"):
        """
        Create GitHub-style calendar heatmap of daily returns
        """
        st.subheader(f"📅 Returns Calendar Heatmap - {ticker}")

        # Fetch historical data
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)

            if df.empty:
                st.error(f"No data available for {ticker}")
                return

            # Calculate daily returns
            df['Returns'] = df['Close'].pct_change() * 100
            df = df.dropna()

            # Prepare calendar data
            df['Date'] = df.index.date
            df['Year'] = df.index.year
            df['Month'] = df.index.month
            df['Day'] = df.index.day
            df['Weekday'] = df.index.dayofweek
            df['Week'] = df.index.isocalendar().week

            # Create heatmap using Plotly
            years = sorted(df['Year'].unique())

            for year in years:
                year_data = df[df['Year'] == year].copy()

                # Create calendar grid
                fig = self._create_calendar_heatmap(year_data, year, ticker)
                st.plotly_chart(fig, use_container_width=True)

            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Daily Return", f"{df['Returns'].mean():.3f}%")
            with col2:
                st.metric("Best Day", f"{df['Returns'].max():.2f}%")
            with col3:
                st.metric("Worst Day", f"{df['Returns'].min():.2f}%")
            with col4:
                positive_days = (df['Returns'] > 0).sum() / len(df) * 100
                st.metric("Positive Days", f"{positive_days:.1f}%")

        except Exception as e:
            st.error(f"Error creating calendar heatmap: {e}")

    def _create_calendar_heatmap(self, year_data, year, ticker):
        """Create calendar heatmap for a single year"""

        # Create month labels
        month_labels = [calendar.month_abbr[i] for i in range(1, 13)]

        # Prepare data matrix
        weeks_in_year = 53
        calendar_matrix = np.full((7, weeks_in_year), np.nan)
        text_matrix = np.full((7, weeks_in_year), '', dtype=object)

        for _, row in year_data.iterrows():
            week_idx = int(row['Week']) - 1
            day_idx = int(row['Weekday'])

            if 0 <= week_idx < weeks_in_year and 0 <= day_idx < 7:
                calendar_matrix[day_idx, week_idx] = row['Returns']
                text_matrix[day_idx, week_idx] = f"{row['Date']}<br>{row['Returns']:.2f}%"

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=calendar_matrix,
            text=text_matrix,
            hovertemplate='%{text}<extra></extra>',
            colorscale=[
                [0, '#d73027'],      # Deep red for negative
                [0.45, '#fee090'],   # Light yellow
                [0.5, '#ffffff'],    # White for zero
                [0.55, '#e0f3f8'],   # Light blue
                [1, '#4575b4']       # Deep blue for positive
            ],
            zmid=0,
            colorbar=dict(title="Return (%)"),
            xgap=2,
            ygap=2
        ))

        fig.update_layout(
            title=f"{ticker} Daily Returns Calendar - {year}",
            xaxis=dict(
                title="Week of Year",
                tickmode='linear',
                tick0=0,
                dtick=4
            ),
            yaxis=dict(
                title="",
                tickmode='array',
                tickvals=[0, 1, 2, 3, 4, 5, 6],
                ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            ),
            height=300,
            margin=dict(l=50, r=50, t=50, b=50)
        )

        return fig

    # ========== 2. Sector Rotation Wheel ==========

    def create_sector_rotation_wheel(self, custom_sectors=None):
        """
        Interactive sector rotation wheel (Plotly sunburst)
        Shows sector performance and momentum
        """
        st.subheader("🔄 Sector Rotation Wheel")

        # Default sector ETFs
        if custom_sectors is None:
            sector_etfs = {
                'Technology': 'XLK',
                'Healthcare': 'XLV',
                'Financial': 'XLF',
                'Consumer Discretionary': 'XLY',
                'Industrial': 'XLI',
                'Energy': 'XLE',
                'Materials': 'XLB',
                'Utilities': 'XLU',
                'Real Estate': 'XLRE',
                'Communication': 'XLC',
                'Consumer Defensive': 'XLP'
            }
        else:
            sector_etfs = custom_sectors

        # Fetch sector performance
        sector_data = []

        with st.spinner("Loading sector data..."):
            for sector, etf in sector_etfs.items():
                try:
                    ticker = yf.Ticker(etf)
                    hist = ticker.history(period="3mo")

                    if not hist.empty:
                        # Calculate metrics
                        current_price = hist['Close'].iloc[-1]
                        price_1m_ago = hist['Close'].iloc[-22] if len(hist) >= 22 else hist['Close'].iloc[0]
                        price_3m_ago = hist['Close'].iloc[0]

                        return_1m = ((current_price - price_1m_ago) / price_1m_ago) * 100
                        return_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100

                        # Momentum score
                        momentum = return_1m * 0.6 + return_3m * 0.4

                        sector_data.append({
                            'Sector': sector,
                            'ETF': etf,
                            '1M Return (%)': return_1m,
                            '3M Return (%)': return_3m,
                            'Momentum': momentum,
                            'Size': abs(momentum) + 10  # For visualization
                        })
                except:
                    continue

        if not sector_data:
            st.error("Unable to fetch sector data")
            return

        sector_df = pd.DataFrame(sector_data)

        # Create sunburst chart
        fig = go.Figure(go.Sunburst(
            labels=sector_df['Sector'],
            parents=[''] * len(sector_df),
            values=sector_df['Size'],
            text=sector_df['1M Return (%)'].apply(lambda x: f"{x:+.1f}%"),
            marker=dict(
                colors=sector_df['Momentum'],
                colorscale='RdYlGn',
                cmid=0,
                colorbar=dict(title="Momentum Score")
            ),
            hovertemplate='<b>%{label}</b><br>' +
                         '1M Return: %{text}<br>' +
                         '<extra></extra>'
        ))

        fig.update_layout(
            title="Sector Rotation Wheel - Performance & Momentum",
            height=600,
            margin=dict(t=50, l=0, r=0, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display sector table
        st.markdown("### Sector Performance Table")
        st.dataframe(
            sector_df.sort_values('Momentum', ascending=False),
            use_container_width=True,
            column_config={
                "Sector": st.column_config.TextColumn("Sector"),
                "ETF": st.column_config.TextColumn("ETF"),
                "1M Return (%)": st.column_config.NumberColumn("1M Return (%)", format="%.2f%%"),
                "3M Return (%)": st.column_config.NumberColumn("3M Return (%)", format="%.2f%%"),
                "Momentum": st.column_config.NumberColumn("Momentum Score", format="%.2f"),
            },
            hide_index=True
        )

    # ========== 3. Fear & Greed Gauge ==========

    def create_fear_greed_gauge(self):
        """
        Fear & Greed Index gauge using composite indicators
        Based on VIX, Put/Call Ratio, Market Breadth, RSI
        """
        st.subheader("😱😎 Fear & Greed Gauge")

        try:
            # Fetch VIX (volatility index)
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="5d")
            current_vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 20

            # Fetch SPY for market breadth
            spy = yf.Ticker("SPY")
            spy_data = spy.history(period="1mo")

            # Calculate Fear & Greed components
            components = self._calculate_fear_greed_components(current_vix, spy_data)

            # Composite Fear & Greed Index (0-100)
            fg_index = components['composite_score']

            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=fg_index,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Fear & Greed Index", 'font': {'size': 24}},
                delta={'reference': 50, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': self._get_fg_color(fg_index)},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 25], 'color': '#d62728'},
                        {'range': [25, 45], 'color': '#ff7f0e'},
                        {'range': [45, 55], 'color': '#bcbd22'},
                        {'range': [55, 75], 'color': '#2ca02c'},
                        {'range': [75, 100], 'color': '#1f77b4'}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': fg_index
                    }
                }
            ))

            fig.update_layout(
                height=400,
                font={'color': "darkblue", 'family': "Arial"}
            )

            col1, col2 = st.columns([2, 1])

            with col1:
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("### Interpretation")
                sentiment = self._get_sentiment_label(fg_index)
                st.markdown(f"**Current Sentiment:** {sentiment}")

                st.markdown("---")
                st.markdown("### Components")
                st.metric("VIX Score", f"{components['vix_score']:.1f}/25")
                st.metric("RSI Score", f"{components['rsi_score']:.1f}/25")
                st.metric("Momentum Score", f"{components['momentum_score']:.1f}/25")
                st.metric("Breadth Score", f"{components['breadth_score']:.1f}/25")

        except Exception as e:
            st.error(f"Error creating Fear & Greed Gauge: {e}")

    def _calculate_fear_greed_components(self, vix, spy_data):
        """Calculate individual components of Fear & Greed Index"""

        # 1. VIX Score (inverse - high VIX = fear)
        # VIX typically ranges 10-40, normalize to 0-25
        vix_normalized = np.clip((40 - vix) / 30 * 25, 0, 25)

        # 2. RSI Score (14-day RSI)
        if len(spy_data) >= 14:
            closes = spy_data['Close']
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            # Normalize RSI (50 is neutral)
            rsi_score = np.clip((current_rsi - 30) / 40 * 25, 0, 25)
        else:
            rsi_score = 12.5

        # 3. Momentum Score (5-day vs 20-day MA)
        if len(spy_data) >= 20:
            ma5 = spy_data['Close'].rolling(5).mean().iloc[-1]
            ma20 = spy_data['Close'].rolling(20).mean().iloc[-1]
            momentum_pct = ((ma5 - ma20) / ma20) * 100
            momentum_score = np.clip((momentum_pct + 2) / 4 * 25, 0, 25)
        else:
            momentum_score = 12.5

        # 4. Market Breadth Score (% of days closing up)
        up_days = (spy_data['Close'] > spy_data['Open']).sum()
        total_days = len(spy_data)
        breadth_pct = up_days / total_days * 100
        breadth_score = np.clip((breadth_pct - 30) / 40 * 25, 0, 25)

        # Composite score
        composite = vix_normalized + rsi_score + momentum_score + breadth_score

        return {
            'vix_score': vix_normalized,
            'rsi_score': rsi_score,
            'momentum_score': momentum_score,
            'breadth_score': breadth_score,
            'composite_score': composite
        }

    def _get_fg_color(self, score):
        """Get color based on Fear & Greed score"""
        if score < 25:
            return '#d62728'  # Extreme Fear - Red
        elif score < 45:
            return '#ff7f0e'  # Fear - Orange
        elif score < 55:
            return '#bcbd22'  # Neutral - Yellow
        elif score < 75:
            return '#2ca02c'  # Greed - Green
        else:
            return '#1f77b4'  # Extreme Greed - Blue

    def _get_sentiment_label(self, score):
        """Get sentiment label from score"""
        if score < 25:
            return "🔴 Extreme Fear"
        elif score < 45:
            return "🟠 Fear"
        elif score < 55:
            return "🟡 Neutral"
        elif score < 75:
            return "🟢 Greed"
        else:
            return "🔵 Extreme Greed"

    # ========== 4. 3D Portfolio Allocation ==========

    def create_3d_portfolio_allocation(self, portfolio_data=None):
        """
        3D sunburst/treemap for portfolio allocation
        Multi-level: Asset Class → Sector → Individual Holdings
        """
        st.subheader("📊 3D Portfolio Allocation")

        # Sample portfolio data if none provided
        if portfolio_data is None:
            portfolio_data = self._generate_sample_portfolio()

        # Create treemap
        fig = go.Figure(go.Treemap(
            labels=portfolio_data['Label'],
            parents=portfolio_data['Parent'],
            values=portfolio_data['Value'],
            text=portfolio_data['Text'],
            textposition='middle center',
            marker=dict(
                colors=portfolio_data['Color'],
                colorscale='RdYlGn',
                cmid=0,
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>%{label}</b><br>' +
                         'Value: $%{value:,.2f}<br>' +
                         '%{text}<br>' +
                         '<extra></extra>'
        ))

        fig.update_layout(
            title="3D Portfolio Allocation Treemap",
            height=700,
            margin=dict(t=50, l=0, r=0, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Alternative: Sunburst chart
        st.markdown("### 🌟 Sunburst View")

        fig_sunburst = go.Figure(go.Sunburst(
            labels=portfolio_data['Label'],
            parents=portfolio_data['Parent'],
            values=portfolio_data['Value'],
            branchvalues="total",
            marker=dict(
                colors=portfolio_data['Color'],
                colorscale='Viridis',
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>%{label}</b><br>' +
                         'Value: $%{value:,.2f}<br>' +
                         '<extra></extra>'
        ))

        fig_sunburst.update_layout(
            title="Portfolio Sunburst - Hierarchical View",
            height=700,
            margin=dict(t=50, l=0, r=0, b=0)
        )

        st.plotly_chart(fig_sunburst, use_container_width=True)

    def _generate_sample_portfolio(self):
        """Generate sample hierarchical portfolio data"""
        data = {
            'Label': [],
            'Parent': [],
            'Value': [],
            'Text': [],
            'Color': []
        }

        # Root
        data['Label'].append('Portfolio')
        data['Parent'].append('')
        data['Value'].append(0)
        data['Text'].append('Total Portfolio')
        data['Color'].append(0)

        # Asset classes
        asset_classes = {
            'Stocks': 60000,
            'Bonds': 25000,
            'Crypto': 10000,
            'Cash': 5000
        }

        for asset_class, value in asset_classes.items():
            data['Label'].append(asset_class)
            data['Parent'].append('Portfolio')
            data['Value'].append(value)
            data['Text'].append(f"{value/sum(asset_classes.values())*100:.1f}%")
            data['Color'].append(np.random.uniform(-2, 2))

        # Stocks breakdown by sector
        stock_sectors = {
            'Technology': ('Stocks', 25000),
            'Healthcare': ('Stocks', 15000),
            'Finance': ('Stocks', 12000),
            'Consumer': ('Stocks', 8000)
        }

        for sector, (parent, value) in stock_sectors.items():
            data['Label'].append(sector)
            data['Parent'].append(parent)
            data['Value'].append(value)
            data['Text'].append(f"${value:,.0f}")
            data['Color'].append(np.random.uniform(-2, 2))

        # Individual holdings
        holdings = {
            'AAPL': ('Technology', 8000),
            'MSFT': ('Technology', 7500),
            'GOOGL': ('Technology', 6000),
            'NVDA': ('Technology', 3500),
            'JNJ': ('Healthcare', 7000),
            'PFE': ('Healthcare', 5000),
            'UNH': ('Healthcare', 3000),
            'JPM': ('Finance', 6000),
            'BAC': ('Finance', 4000),
            'GS': ('Finance', 2000),
            'AMZN': ('Consumer', 5000),
            'TSLA': ('Consumer', 3000)
        }

        for holding, (parent, value) in holdings.items():
            data['Label'].append(holding)
            data['Parent'].append(parent)
            data['Value'].append(value)
            data['Text'].append(f"${value:,.0f}")
            data['Color'].append(np.random.uniform(-5, 5))

        return pd.DataFrame(data)


def render_visualization_tools():
    """Main function to render visualization tools UI"""
    viz = VisualizationTools()

    st.title("🎨 Advanced Visualization Tools")

    tabs = st.tabs([
        "📅 Calendar Heatmap",
        "🔄 Sector Rotation",
        "😱 Fear & Greed",
        "📊 3D Portfolio"
    ])

    with tabs[0]:
        ticker = st.text_input("Enter Ticker Symbol", "SPY", key="heatmap_ticker")
        period = st.selectbox("Select Period", ["1y", "2y", "3y", "5y"], key="heatmap_period")
        if st.button("Generate Heatmap", type="primary"):
            viz.create_returns_heatmap_calendar(ticker.upper(), period)

    with tabs[1]:
        viz.create_sector_rotation_wheel()

    with tabs[2]:
        viz.create_fear_greed_gauge()

    with tabs[3]:
        viz.create_3d_portfolio_allocation()


if __name__ == "__main__":
    render_visualization_tools()
