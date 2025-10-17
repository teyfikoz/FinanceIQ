"""Institutional Holdings Analysis using yfinance"""
import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict, Optional, List, Tuple
from utils.sankey_theme import SankeyTheme, create_theme_selector, create_scale_selector
import plotly.graph_objects as go


class InstitutionalHoldingsAnalyzer:
    """Analyze institutional holdings for stocks"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)

    def get_institutional_holders(self) -> Optional[pd.DataFrame]:
        """Get top institutional holders

        Returns:
            DataFrame with institutional holders or None
        """
        try:
            holders = self.ticker.institutional_holders
            if holders is not None and not holders.empty:
                return holders
            return None
        except Exception as e:
            print(f"Error fetching institutional holders: {str(e)}")
            return None

    def get_mutual_fund_holders(self) -> Optional[pd.DataFrame]:
        """Get top mutual fund holders

        Returns:
            DataFrame with mutual fund holders or None
        """
        try:
            holders = self.ticker.mutualfund_holders
            if holders is not None and not holders.empty:
                return holders
            return None
        except Exception as e:
            print(f"Error fetching mutual fund holders: {str(e)}")
            return None

    def get_major_holders(self) -> Optional[pd.DataFrame]:
        """Get major holders summary

        Returns:
            DataFrame with major holders summary or None
        """
        try:
            holders = self.ticker.major_holders
            if holders is not None and not holders.empty:
                return holders
            return None
        except Exception as e:
            print(f"Error fetching major holders: {str(e)}")
            return None

    def get_holdings_analysis(self) -> Dict:
        """Get comprehensive holdings analysis

        Returns:
            Dictionary with holdings data
        """
        try:
            institutional = self.get_institutional_holders()
            mutual_funds = self.get_mutual_fund_holders()
            major = self.get_major_holders()

            analysis = {
                'has_data': False,
                'institutional_holders': None,
                'mutual_fund_holders': None,
                'major_holders': None,
                'summary': {}
            }

            if institutional is not None and not institutional.empty:
                analysis['has_data'] = True
                analysis['institutional_holders'] = institutional

                # Calculate summary stats - handle different column names
                try:
                    total_shares = institutional['Shares'].sum() if 'Shares' in institutional.columns else 0

                    # Try different percentage column names
                    pct_col = None
                    for col in ['% Out', 'pctHeld', 'Percent Held']:
                        if col in institutional.columns:
                            pct_col = col
                            break

                    if pct_col:
                        if institutional[pct_col].dtype == 'object':
                            avg_pct = institutional[pct_col].str.rstrip('%').astype(float).mean()
                        else:
                            avg_pct = institutional[pct_col].mean() * 100
                    else:
                        avg_pct = 0

                    analysis['summary']['institutional'] = {
                        'total_holders': len(institutional),
                        'total_shares': total_shares,
                        'avg_ownership_pct': avg_pct
                    }
                except Exception as e:
                    print(f"Error calculating institutional summary: {str(e)}")
                    analysis['summary']['institutional'] = {
                        'total_holders': len(institutional),
                        'total_shares': 0,
                        'avg_ownership_pct': 0
                    }

            if mutual_funds is not None and not mutual_funds.empty:
                analysis['has_data'] = True
                analysis['mutual_fund_holders'] = mutual_funds

                # Calculate summary stats - handle different column names
                try:
                    total_shares = mutual_funds['Shares'].sum() if 'Shares' in mutual_funds.columns else 0

                    # Try different percentage column names
                    pct_col = None
                    for col in ['% Out', 'pctHeld', 'Percent Held']:
                        if col in mutual_funds.columns:
                            pct_col = col
                            break

                    if pct_col:
                        if mutual_funds[pct_col].dtype == 'object':
                            avg_pct = mutual_funds[pct_col].str.rstrip('%').astype(float).mean()
                        else:
                            avg_pct = mutual_funds[pct_col].mean() * 100
                    else:
                        avg_pct = 0

                    analysis['summary']['mutual_funds'] = {
                        'total_holders': len(mutual_funds),
                        'total_shares': total_shares,
                        'avg_ownership_pct': avg_pct
                    }
                except Exception as e:
                    print(f"Error calculating mutual funds summary: {str(e)}")
                    analysis['summary']['mutual_funds'] = {
                        'total_holders': len(mutual_funds),
                        'total_shares': 0,
                        'avg_ownership_pct': 0
                    }

            if major is not None and not major.empty:
                analysis['has_data'] = True
                analysis['major_holders'] = major

            return analysis

        except Exception as e:
            return {
                'has_data': False,
                'error': str(e)
            }

    def format_holdings_for_display(self, holders_df: pd.DataFrame, holder_type: str = "Institutional") -> pd.DataFrame:
        """Format holdings dataframe for display

        Args:
            holders_df: Raw holders dataframe
            holder_type: Type of holder (Institutional, Mutual Fund)

        Returns:
            Formatted dataframe
        """
        if holders_df is None or holders_df.empty:
            return pd.DataFrame()

        try:
            df = holders_df.copy()

            # Format columns
            if 'Shares' in df.columns:
                df['Shares'] = df['Shares'].apply(lambda x: f"{x:,.0f}")

            if 'Value' in df.columns:
                df['Value'] = df['Value'].apply(lambda x: f"${x:,.0f}")

            # Rename columns for clarity
            df = df.rename(columns={
                'Holder': f'{holder_type} Holder',
                '% Out': 'Ownership %',
                'Date Reported': 'Report Date'
            })

            return df

        except Exception as e:
            print(f"Error formatting holdings: {str(e)}")
            return holders_df

    def create_holdings_sankey(
        self,
        institutional: pd.DataFrame,
        mutual_funds: pd.DataFrame,
        theme: SankeyTheme,
        top_n: int = 10
    ) -> Optional[go.Figure]:
        """Create Sankey diagram showing stock ownership distribution

        Args:
            institutional: Institutional holders dataframe
            mutual_funds: Mutual fund holders dataframe
            theme: SankeyTheme instance
            top_n: Number of top holders to display

        Returns:
            Plotly Figure or None
        """
        try:
            nodes = [f"{self.symbol} Stock"]
            sources = []
            targets = []
            values = []
            node_colors = []

            # Root node color
            node_colors.append('#FFD166')  # Yellow for stock

            # Add institutional holders
            if institutional is not None and not institutional.empty:
                # Find percentage column
                pct_col = None
                for col in ['% Out', 'pctHeld', 'Percent Held']:
                    if col in institutional.columns:
                        pct_col = col
                        break

                if pct_col:
                    inst_node_idx = len(nodes)
                    nodes.append('Institutional Investors')
                    node_colors.append(theme.get_color_palette('assets')['primary'])

                    sources.append(0)  # From stock
                    targets.append(inst_node_idx)

                    # Sum of top institutional holdings
                    if institutional[pct_col].dtype == 'object':
                        inst_total_pct = institutional.head(top_n)[pct_col].str.rstrip('%').astype(float).sum()
                    else:
                        inst_total_pct = institutional.head(top_n)[pct_col].sum() * 100
                    values.append(inst_total_pct)

                    # Add top institutional holders
                    for idx, row in institutional.head(top_n).iterrows():
                        holder_name = row['Holder']
                        # Truncate long names
                        if len(holder_name) > 30:
                            holder_name = holder_name[:27] + '...'

                        nodes.append(holder_name)
                        node_colors.append(theme.get_color_palette('assets')['breakdown'][len(nodes) % 4])

                        sources.append(inst_node_idx)
                        targets.append(len(nodes) - 1)

                        if institutional[pct_col].dtype == 'object':
                            pct = float(row[pct_col].rstrip('%'))
                        else:
                            pct = float(row[pct_col]) * 100
                        values.append(pct)

            # Add mutual fund holders
            if mutual_funds is not None and not mutual_funds.empty:
                # Find percentage column
                pct_col = None
                for col in ['% Out', 'pctHeld', 'Percent Held']:
                    if col in mutual_funds.columns:
                        pct_col = col
                        break

                if pct_col:
                    fund_node_idx = len(nodes)
                    nodes.append('Mutual Funds')
                    node_colors.append(theme.get_color_palette('liabilities')['current'])

                    sources.append(0)  # From stock
                    targets.append(fund_node_idx)

                    # Sum of top mutual fund holdings
                    if mutual_funds[pct_col].dtype == 'object':
                        fund_total_pct = mutual_funds.head(top_n)[pct_col].str.rstrip('%').astype(float).sum()
                    else:
                        fund_total_pct = mutual_funds.head(top_n)[pct_col].sum() * 100
                    values.append(fund_total_pct)

                    # Add top mutual funds
                    for idx, row in mutual_funds.head(top_n).iterrows():
                        holder_name = row['Holder']
                        # Truncate long names
                        if len(holder_name) > 30:
                            holder_name = holder_name[:27] + '...'

                        nodes.append(holder_name)
                        node_colors.append(theme.get_color_palette('liabilities')['breakdown'][len(nodes) % 4])

                        sources.append(fund_node_idx)
                        targets.append(len(nodes) - 1)

                        if mutual_funds[pct_col].dtype == 'object':
                            pct = float(row[pct_col].rstrip('%'))
                        else:
                            pct = float(row[pct_col]) * 100
                        values.append(pct)

            if not sources:
                return None

            # Create custom hover templates
            hover_templates = []
            for i, (src, tgt, val) in enumerate(zip(sources, targets, values)):
                template = (
                    f"<b>{nodes[src]} → {nodes[tgt]}</b><br>"
                    f"Ownership: {val:.2f}%<br>"
                    "<extra></extra>"
                )
                hover_templates.append(template)

            # Create Sankey
            fig = theme.create_sankey_figure(
                nodes=nodes,
                sources=sources,
                targets=targets,
                values=values,
                node_colors=node_colors,
                title=f"{self.symbol} Ownership Distribution (Top {top_n} Holders)",
                height=800,
                scale='',  # Percentage, no scale needed
                show_percentage=False,
                link_labels=hover_templates
            )

            return fig

        except Exception as e:
            print(f"Error creating holdings Sankey: {str(e)}")
            return None


def display_institutional_holdings(symbol: str):
    """Display institutional holdings analysis in Streamlit

    Args:
        symbol: Stock symbol
    """
    try:
        analyzer = InstitutionalHoldingsAnalyzer(symbol)
        analysis = analyzer.get_holdings_analysis()

        # Check for error
        if 'error' in analysis:
            st.warning(f"⚠️ Error fetching holdings data: {analysis['error']}")
            return

        if not analysis.get('has_data', False):
            st.info("📊 Institutional holdings data not available for this stock. This may be due to:")
            st.markdown("""
            - Stock is not publicly traded or too small
            - Data temporarily unavailable from provider
            - International stocks may have limited data
            """)
            return
    except Exception as e:
        st.error(f"Error loading holdings: {str(e)}")
        return

    st.subheader("🏦 Institutional & Fund Holdings")

    # Add Sankey visualization controls
    st.markdown("---")
    st.markdown("### 📊 Ownership Distribution Visualization")

    # Theme selector
    theme = create_theme_selector()

    # Top N selector
    col1, col2 = st.columns([2, 1])
    with col2:
        top_n = st.slider(
            "Top N Holders",
            min_value=5,
            max_value=20,
            value=10,
            help="Number of top holders to display in Sankey chart"
        )

    # Create and display Sankey chart
    if analysis.get('institutional_holders') is not None or analysis.get('mutual_fund_holders') is not None:
        sankey_fig = analyzer.create_holdings_sankey(
            analysis.get('institutional_holders'),
            analysis.get('mutual_fund_holders'),
            theme,
            top_n
        )

        if sankey_fig:
            st.plotly_chart(sankey_fig, use_container_width=True)

            with st.expander("ℹ️ How to Read Ownership Distribution"):
                st.markdown("""
                **Sankey Diagram** shows who owns shares of this stock:

                - **Center (Yellow)**: The stock itself
                - **Institutional Investors (Green)**: Banks, pension funds, hedge funds
                - **Mutual Funds (Orange)**: Investment funds accessible to retail investors

                **Features:**
                - Hover over flows to see exact ownership percentages
                - Width represents relative ownership size
                - Shows top institutional and fund holders
                - Adjust "Top N Holders" slider to see more/fewer holders
                """)
        else:
            st.info("Sankey chart requires both institutional and mutual fund data.")

    st.markdown("---")

    # Major holders summary
    if analysis['major_holders'] is not None:
        st.markdown("### 📈 Ownership Summary")
        major = analysis['major_holders']

        col1, col2 = st.columns(2)
        with col1:
            for idx in range(0, len(major), 2):
                st.metric(
                    major.iloc[idx, 1],
                    major.iloc[idx, 0]
                )
        with col2:
            for idx in range(1, len(major), 2):
                st.metric(
                    major.iloc[idx, 1],
                    major.iloc[idx, 0]
                )

    # Institutional holders
    if analysis['institutional_holders'] is not None:
        st.markdown("### 🏛️ Top Institutional Holders")

        summary = analysis['summary'].get('institutional', {})
        if summary:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Institutions", f"{summary['total_holders']}")
            with col2:
                st.metric("Total Shares Held", f"{summary['total_shares']:,.0f}")
            with col3:
                st.metric("Avg Ownership", f"{summary['avg_ownership_pct']:.2f}%")

        formatted_df = analyzer.format_holdings_for_display(
            analysis['institutional_holders'],
            "Institutional"
        )

        # Add note about holdings changes
        st.info("💡 **Tracking Changes**: Compare 'Report Date' column across holders to identify recent position changes. Newer dates indicate more current holdings data.")

        st.dataframe(formatted_df, use_container_width=True, hide_index=True)

        # Show which holders reported most recently
        if 'Date Reported' in analysis['institutional_holders'].columns:
            recent_holders = analysis['institutional_holders'].nlargest(3, 'Date Reported')
            st.markdown("**📅 Most Recent Reports:**")
            for idx, row in recent_holders.iterrows():
                st.text(f"• {row['Holder']}: {row['Date Reported'].strftime('%Y-%m-%d')}")

    # Mutual fund holders
    if analysis['mutual_fund_holders'] is not None:
        st.markdown("### 🏢 Top Mutual Fund Holders")

        summary = analysis['summary'].get('mutual_funds', {})
        if summary:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Funds", f"{summary['total_holders']}")
            with col2:
                st.metric("Total Shares Held", f"{summary['total_shares']:,.0f}")
            with col3:
                st.metric("Avg Ownership", f"{summary['avg_ownership_pct']:.2f}%")

        formatted_df = analyzer.format_holdings_for_display(
            analysis['mutual_fund_holders'],
            "Mutual Fund"
        )

        st.info("💡 **ETF/Fund Tracking**: Monitor which funds are increasing/decreasing positions by comparing report dates and ownership percentages over time.")

        st.dataframe(formatted_df, use_container_width=True, hide_index=True)

        # Show which funds reported most recently
        if 'Date Reported' in analysis['mutual_fund_holders'].columns:
            recent_funds = analysis['mutual_fund_holders'].nlargest(3, 'Date Reported')
            st.markdown("**📅 Most Recent Fund Reports:**")
            for idx, row in recent_funds.iterrows():
                st.text(f"• {row['Holder']}: {row['Date Reported'].strftime('%Y-%m-%d')}")

    # Summary analysis section
    if analysis.get('institutional_holders') is not None or analysis.get('mutual_fund_holders') is not None:
        st.markdown("---")
        st.markdown("### 📈 Holdings Analysis Summary")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🏛️ Institutional Holdings Insights:**")
            if analysis.get('institutional_holders') is not None:
                inst_df = analysis['institutional_holders']

                # Find percentage column
                pct_col = None
                for col in ['% Out', 'pctHeld', 'Percent Held']:
                    if col in inst_df.columns:
                        pct_col = col
                        break

                if pct_col:
                    if inst_df[pct_col].dtype == 'object':
                        total_inst_pct = inst_df[pct_col].str.rstrip('%').astype(float).sum()
                    else:
                        total_inst_pct = inst_df[pct_col].sum() * 100
                    st.metric("Total Institutional Ownership", f"{total_inst_pct:.2f}%")

                    # Top 3 holders
                    top_3 = inst_df.head(3)
                    st.markdown("**Top 3 Institutions:**")
                    for idx, row in top_3.iterrows():
                        pct_display = row[pct_col] if inst_df[pct_col].dtype == 'object' else f"{row[pct_col]*100:.2f}%"
                        st.markdown(f"• **{row['Holder']}**: {pct_display}")

        with col2:
            st.markdown("**🏢 Mutual Fund Holdings Insights:**")
            if analysis.get('mutual_fund_holders') is not None:
                fund_df = analysis['mutual_fund_holders']

                # Find percentage column
                pct_col = None
                for col in ['% Out', 'pctHeld', 'Percent Held']:
                    if col in fund_df.columns:
                        pct_col = col
                        break

                if pct_col:
                    if fund_df[pct_col].dtype == 'object':
                        total_fund_pct = fund_df[pct_col].str.rstrip('%').astype(float).sum()
                    else:
                        total_fund_pct = fund_df[pct_col].sum() * 100
                    st.metric("Total Fund Ownership", f"{total_fund_pct:.2f}%")

                    # Top 3 funds
                    top_3_funds = fund_df.head(3)
                    st.markdown("**Top 3 Funds/ETFs:**")
                    for idx, row in top_3_funds.iterrows():
                        pct_display = row[pct_col] if fund_df[pct_col].dtype == 'object' else f"{row[pct_col]*100:.2f}%"
                        st.markdown(f"• **{row['Holder']}**: {pct_display}")
