"""
🎯 Social Layer - Phase 1 Game Changer Features
Shareable Portfolio Snapshots, Public Watchlists, Notes & Demo Leaderboard
All features are offline-friendly and require no paid APIs
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import yfinance as yf


class SocialFeatures:
    """Social layer functionality for FinanceIQ"""

    def __init__(self):
        self._init_session_state()

    def _init_session_state(self):
        """Initialize session state for social features"""
        if 'user_notes' not in st.session_state:
            st.session_state.user_notes = {}
        if 'public_watchlists' not in st.session_state:
            st.session_state.public_watchlists = self._get_default_watchlists()
        if 'leaderboard_data' not in st.session_state:
            st.session_state.leaderboard_data = self._generate_demo_leaderboard()

    def _get_default_watchlists(self):
        """Predefined public watchlists"""
        return {
            "Top ETFs": ["SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "GLD", "SLV"],
            "Blue Chips": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK-B"],
            "Sustainability Leaders": ["TSLA", "NEE", "ENPH", "SEDG", "PLUG", "FSLR", "BE", "ICLN"],
            "High Dividend": ["T", "VZ", "XOM", "CVX", "JNJ", "PFE", "KO", "PEP"],
            "Growth Tech": ["NVDA", "AMD", "AVGO", "CRM", "NOW", "SNOW", "DDOG", "NET"],
            "Financial Sector": ["JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW"]
        }

    def _generate_demo_leaderboard(self):
        """Generate demo leaderboard with simulated performance data"""
        np.random.seed(42)
        users = [
            "TraderPro2024", "InvestorElite", "MarketMaven", "BullishBob",
            "DividendKing", "TechInvestor", "ValueHunter", "MomentumTrader",
            "OptionsMaster", "LongTermGrowth"
        ]

        data = []
        for i, user in enumerate(users):
            # Simulate realistic portfolio performance
            ytd_return = np.random.normal(12, 15)  # Mean 12%, std 15%
            total_return = ytd_return * np.random.uniform(1.2, 2.5)
            sharpe = np.random.uniform(0.5, 2.5)

            data.append({
                "Rank": i + 1,
                "User": user,
                "YTD Return (%)": round(ytd_return, 2),
                "Total Return (%)": round(total_return, 2),
                "Sharpe Ratio": round(sharpe, 2),
                "Win Rate (%)": round(np.random.uniform(45, 75), 1),
                "Trades": np.random.randint(50, 500),
                "Badge": self._get_badge(i + 1)
            })

        return pd.DataFrame(data)

    def _get_badge(self, rank):
        """Get badge emoji based on rank"""
        if rank == 1:
            return "🏆"
        elif rank == 2:
            return "🥈"
        elif rank == 3:
            return "🥉"
        elif rank <= 5:
            return "⭐"
        else:
            return "📊"

    # ========== 1. Shareable Portfolio Snapshots ==========

    def create_portfolio_snapshot(self, portfolio_data, portfolio_name="My Portfolio"):
        """Generate downloadable PNG card for portfolio snapshot"""

        fig = go.Figure()

        # Create visual portfolio card
        total_value = portfolio_data['Value'].sum()
        total_gain = portfolio_data['Gain/Loss'].sum()
        total_gain_pct = (total_gain / (total_value - total_gain)) * 100

        # Pie chart for allocation
        fig.add_trace(go.Pie(
            labels=portfolio_data['Symbol'],
            values=portfolio_data['Value'],
            hole=0.4,
            marker=dict(colors=px.colors.qualitative.Bold),
            textposition='inside',
            textinfo='label+percent'
        ))

        # Add portfolio stats as annotation
        stats_text = f"""
        <b>{portfolio_name}</b><br>
        Total Value: ${total_value:,.2f}<br>
        Total Gain: ${total_gain:,.2f} ({total_gain_pct:+.2f}%)<br>
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """

        fig.update_layout(
            title=dict(
                text=f"📊 {portfolio_name} Snapshot",
                font=dict(size=24, color='#1f77b4', family='Arial Black')
            ),
            annotations=[dict(
                text=stats_text,
                x=0.5, y=-0.15,
                showarrow=False,
                xref="paper", yref="paper",
                font=dict(size=14),
                align='center'
            )],
            height=600,
            showlegend=True,
            paper_bgcolor='rgba(240,240,245,1)',
            plot_bgcolor='rgba(255,255,255,0.8)'
        )

        # Convert to PNG
        img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)

        return img_bytes

    def portfolio_snapshot_ui(self):
        """UI for creating and downloading portfolio snapshots"""
        st.subheader("📸 Shareable Portfolio Snapshot")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("Create beautiful, shareable snapshots of your portfolio performance")

            # Example portfolio input
            portfolio_name = st.text_input("Portfolio Name", "My Portfolio")

            # Sample portfolio data
            sample_data = pd.DataFrame({
                'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],
                'Shares': [10, 15, 5, 8, 20],
                'Price': [178.50, 378.91, 140.22, 145.32, 495.22],
            })
            sample_data['Value'] = sample_data['Shares'] * sample_data['Price']
            sample_data['Gain/Loss'] = sample_data['Value'] * np.random.uniform(-0.1, 0.3, len(sample_data))

            edited_df = st.data_editor(
                sample_data,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Symbol": st.column_config.TextColumn("Symbol", max_chars=10),
                    "Shares": st.column_config.NumberColumn("Shares", min_value=0),
                    "Price": st.column_config.NumberColumn("Price ($)", format="$%.2f"),
                    "Value": st.column_config.NumberColumn("Value ($)", format="$%.2f"),
                    "Gain/Loss": st.column_config.NumberColumn("Gain/Loss ($)", format="$%.2f"),
                }
            )

        with col2:
            st.markdown("### Quick Stats")
            total_value = edited_df['Value'].sum()
            total_gain = edited_df['Gain/Loss'].sum()

            st.metric("Total Value", f"${total_value:,.2f}")
            st.metric("Total Gain/Loss", f"${total_gain:,.2f}",
                     delta=f"{(total_gain/total_value)*100:.2f}%")

        if st.button("🎨 Generate Snapshot", type="primary", use_container_width=True):
            with st.spinner("Creating your portfolio snapshot..."):
                img_bytes = self.create_portfolio_snapshot(edited_df, portfolio_name)

                st.success("✅ Snapshot created!")
                st.download_button(
                    label="⬇️ Download PNG",
                    data=img_bytes,
                    file_name=f"portfolio_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png",
                    use_container_width=True
                )

    # ========== 2. Public Watchlists ==========

    def public_watchlists_ui(self):
        """Display and interact with public watchlists"""
        st.subheader("📋 Public Watchlists")

        # Watchlist selector
        watchlist_names = list(st.session_state.public_watchlists.keys())
        selected_watchlist = st.selectbox(
            "Select a Watchlist",
            watchlist_names,
            key="watchlist_selector"
        )

        if selected_watchlist:
            symbols = st.session_state.public_watchlists[selected_watchlist]

            # Fetch real-time data for watchlist
            with st.spinner(f"Loading {selected_watchlist}..."):
                watchlist_data = self._fetch_watchlist_data(symbols)
                watchlist_data = self._normalize_watchlist_df(watchlist_data, symbols)

            if watchlist_data.empty:
                st.info("No data available for this watchlist right now. Showing symbols only.")
                st.dataframe(pd.DataFrame({"Symbol": symbols}), use_container_width=True, hide_index=True)
                return

            # Display watchlist with metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Stocks", len(symbols))
            with col2:
                if 'Change (%)' in watchlist_data.columns:
                    avg_change = watchlist_data['Change (%)'].mean()
                    st.metric("Avg Change", f"{avg_change:.2f}%", delta=f"{avg_change:.2f}%")
                else:
                    st.metric("Avg Change", "N/A")
            with col3:
                if 'Change (%)' in watchlist_data.columns:
                    gainers = (watchlist_data['Change (%)'] > 0).sum()
                    st.metric("Gainers", f"{gainers}/{len(symbols)}")
                else:
                    st.metric("Gainers", "N/A")

            # Watchlist table
            st.dataframe(
                watchlist_data,
                use_container_width=True,
                column_config={
                    "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Change (%)": st.column_config.NumberColumn("Change (%)", format="%.2f%%"),
                    "Volume": st.column_config.NumberColumn("Volume", format="%d"),
                    "Market Cap": st.column_config.TextColumn("Market Cap"),
                }
            )

            # Watchlist performance chart
            self._plot_watchlist_performance(watchlist_data)

    def _fetch_watchlist_data(self, symbols):
        """Fetch real-time data for watchlist symbols"""
        data = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")

                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = info.get('previousClose', current_price)
                    change_pct = ((current_price - prev_close) / prev_close) * 100

                    data.append({
                        'Symbol': symbol,
                        'Price': current_price,
                        'Change (%)': change_pct,
                        'Volume': hist['Volume'].iloc[-1],
                        'Market Cap': self._format_market_cap(info.get('marketCap', 0))
                    })
            except:
                continue

        return pd.DataFrame(data)

    def _normalize_watchlist_df(self, df: pd.DataFrame, symbols):
        """Ensure watchlist dataframe has required columns and safe defaults."""
        if df is None or df.empty:
            return pd.DataFrame()

        required_cols = ["Symbol", "Price", "Change (%)", "Volume", "Market Cap"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = np.nan

        # Ensure Symbol column is present
        if df["Symbol"].isna().all():
            df["Symbol"] = symbols[:len(df)]

        return df[required_cols]

    def _format_market_cap(self, market_cap):
        """Format market cap in human-readable form"""
        if market_cap >= 1e12:
            return f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            return f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            return f"${market_cap/1e6:.2f}M"
        else:
            return f"${market_cap:,.0f}"

    def _plot_watchlist_performance(self, watchlist_data):
        """Plot watchlist performance bar chart"""
        if watchlist_data is None or watchlist_data.empty or 'Change (%)' not in watchlist_data.columns:
            st.info("Performance chart is not available for this watchlist yet.")
            return

        fig = px.bar(
            watchlist_data.sort_values('Change (%)', ascending=True),
            x='Change (%)',
            y='Symbol',
            orientation='h',
            color='Change (%)',
            color_continuous_scale=['#d62728', '#2ca02c'],
            title="Watchlist Performance"
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_title="Change (%)",
            yaxis_title="Symbol"
        )

        st.plotly_chart(fig, use_container_width=True)

    # ========== 3. Comments & Notes ==========

    def ticker_notes_ui(self, ticker_symbol=None):
        """LocalStorage-based per-ticker notes"""
        st.subheader("📝 Ticker Notes & Comments")

        if ticker_symbol is None:
            ticker_symbol = st.text_input("Enter Ticker Symbol", "AAPL").upper()

        if ticker_symbol:
            # Display existing notes
            notes = st.session_state.user_notes.get(ticker_symbol, [])

            st.markdown(f"### Notes for **{ticker_symbol}**")

            # Add new note
            with st.form(key=f"note_form_{ticker_symbol}"):
                new_note = st.text_area("Add a new note", height=100)
                submit = st.form_submit_button("💾 Save Note")

                if submit and new_note:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    note_entry = {
                        'timestamp': timestamp,
                        'note': new_note
                    }

                    if ticker_symbol not in st.session_state.user_notes:
                        st.session_state.user_notes[ticker_symbol] = []

                    st.session_state.user_notes[ticker_symbol].insert(0, note_entry)
                    st.success(f"✅ Note saved for {ticker_symbol}")
                    st.rerun()

            # Display existing notes
            if notes:
                st.markdown("---")
                st.markdown("### Previous Notes")

                for idx, note in enumerate(notes):
                    with st.expander(f"📌 {note['timestamp']}", expanded=(idx == 0)):
                        st.markdown(note['note'])
                        if st.button(f"🗑️ Delete", key=f"delete_{ticker_symbol}_{idx}"):
                            st.session_state.user_notes[ticker_symbol].pop(idx)
                            st.rerun()
            else:
                st.info(f"No notes yet for {ticker_symbol}. Add your first note above!")

    # ========== 4. Demo Leaderboard ==========

    def leaderboard_ui(self):
        """Display demo leaderboard with simulated performance"""
        st.subheader("🏆 FinanceIQ Leaderboard")

        st.markdown("""
        **Top performing portfolios** based on YTD returns, Sharpe ratio, and consistency.
        *Demo data - actual performance tracking coming soon!*
        """)

        # Leaderboard filters
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                ["YTD Return (%)", "Total Return (%)", "Sharpe Ratio", "Win Rate (%)"],
                key="leaderboard_sort"
            )
        with col2:
            ascending = st.checkbox("Ascending", False)

        # Sort leaderboard
        sorted_leaderboard = st.session_state.leaderboard_data.sort_values(
            by=sort_by,
            ascending=ascending
        ).reset_index(drop=True)
        sorted_leaderboard['Rank'] = range(1, len(sorted_leaderboard) + 1)
        sorted_leaderboard['Badge'] = sorted_leaderboard['Rank'].apply(self._get_badge)

        # Display leaderboard
        st.dataframe(
            sorted_leaderboard,
            use_container_width=True,
            column_config={
                "Badge": st.column_config.TextColumn("", width="small"),
                "Rank": st.column_config.NumberColumn("Rank", width="small"),
                "User": st.column_config.TextColumn("User", width="medium"),
                "YTD Return (%)": st.column_config.NumberColumn(
                    "YTD Return (%)",
                    format="%.2f%%"
                ),
                "Total Return (%)": st.column_config.NumberColumn(
                    "Total Return (%)",
                    format="%.2f%%"
                ),
                "Sharpe Ratio": st.column_config.NumberColumn("Sharpe Ratio", format="%.2f"),
                "Win Rate (%)": st.column_config.NumberColumn("Win Rate (%)", format="%.1f%%"),
                "Trades": st.column_config.NumberColumn("Trades"),
            },
            hide_index=True
        )

        # Top 3 visualization
        st.markdown("### 🎯 Top 3 Performers")
        top3 = sorted_leaderboard.head(3)

        cols = st.columns(3)
        for idx, (_, row) in enumerate(top3.iterrows()):
            with cols[idx]:
                st.metric(
                    f"{row['Badge']} {row['User']}",
                    f"{row['YTD Return (%)']}%",
                    delta=f"Sharpe: {row['Sharpe Ratio']:.2f}"
                )


def render_social_features():
    """Main function to render social features UI"""
    social = SocialFeatures()

    st.title("🎯 Social Features")

    tabs = st.tabs([
        "📸 Portfolio Snapshots",
        "📋 Public Watchlists",
        "📝 Ticker Notes",
        "🏆 Leaderboard"
    ])

    with tabs[0]:
        social.portfolio_snapshot_ui()

    with tabs[1]:
        social.public_watchlists_ui()

    with tabs[2]:
        social.ticker_notes_ui()

    with tabs[3]:
        social.leaderboard_ui()


if __name__ == "__main__":
    render_social_features()
