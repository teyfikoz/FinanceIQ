"""Balance Sheet Sankey Chart Visualization with Enhanced Styling"""
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from typing import Dict, Optional, List, Tuple
from utils.sankey_theme import SankeyTheme, create_theme_selector, create_scale_selector


class BalanceSheetSankey:
    """Create Sankey diagrams for balance sheet visualization"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)

    def get_balance_sheet_data(self) -> Optional[pd.DataFrame]:
        """Get balance sheet data from yfinance

        Returns:
            Balance sheet dataframe or None
        """
        try:
            bs = self.ticker.balance_sheet
            if bs is not None and not bs.empty:
                return bs
            return None
        except Exception as e:
            print(f"Error fetching balance sheet: {str(e)}")
            return None

    def prepare_sankey_data(
        self,
        balance_sheet: pd.DataFrame,
        theme: SankeyTheme
    ) -> Optional[Dict]:
        """Prepare data for Sankey diagram with theme colors

        Args:
            balance_sheet: Balance sheet dataframe
            theme: SankeyTheme instance

        Returns:
            Dictionary with nodes, links, colors, and values
        """
        try:
            # Get latest column (most recent data)
            latest_col = balance_sheet.columns[0]
            bs = balance_sheet[latest_col]

            # Initialize data structures
            nodes = []
            sources = []
            targets = []
            values = []
            node_colors = []

            # Define main nodes
            main_nodes = ['Total Assets', 'Total Liabilities & Equity']
            asset_nodes = ['Current Assets', 'Non-Current Assets']
            liability_nodes = ['Current Liabilities', 'Non-Current Liabilities', 'Stockholders\' Equity']

            nodes.extend(main_nodes + asset_nodes + liability_nodes)

            # Assign colors
            asset_colors = theme.get_color_palette('assets')
            liability_colors = theme.get_color_palette('liabilities')
            equity_colors = theme.get_color_palette('equity')

            node_colors = [
                asset_colors['primary'],          # Total Assets
                liability_colors['primary'],       # Total Liab & Equity
                asset_colors['current'],           # Current Assets
                asset_colors['non_current'],       # Non-Current Assets
                liability_colors['current'],       # Current Liabilities
                liability_colors['non_current'],   # Non-Current Liabilities
                equity_colors['primary']           # Stockholders' Equity
            ]

            node_indices = {node: idx for idx, node in enumerate(nodes)}

            # Calculate totals
            total_assets = bs.get('Total Assets', 0)
            current_assets = bs.get('Current Assets', 0)
            total_non_current_assets = bs.get('Total Non Current Assets', total_assets - current_assets)

            current_liabilities = bs.get('Current Liabilities', 0)
            total_non_current_liabilities = bs.get('Total Non Current Liabilities Net Minority Interest', 0)
            stockholders_equity = bs.get('Stockholders Equity', 0)

            # Assets side flows
            if current_assets > 0:
                sources.append(node_indices['Total Assets'])
                targets.append(node_indices['Current Assets'])
                values.append(abs(current_assets))

            if total_non_current_assets > 0:
                sources.append(node_indices['Total Assets'])
                targets.append(node_indices['Non-Current Assets'])
                values.append(abs(total_non_current_assets))

            # Liabilities & Equity side flows
            if current_liabilities > 0:
                sources.append(node_indices['Total Liabilities & Equity'])
                targets.append(node_indices['Current Liabilities'])
                values.append(abs(current_liabilities))

            if total_non_current_liabilities > 0:
                sources.append(node_indices['Total Liabilities & Equity'])
                targets.append(node_indices['Non-Current Liabilities'])
                values.append(abs(total_non_current_liabilities))

            if stockholders_equity > 0:
                sources.append(node_indices['Total Liabilities & Equity'])
                targets.append(node_indices['Stockholders\' Equity'])
                values.append(abs(stockholders_equity))

            # Add detailed asset breakdowns
            asset_details = [
                ('Cash And Cash Equivalents', 'Cash & Equivalents'),
                ('Accounts Receivable', 'Accounts Receivable'),
                ('Inventory', 'Inventory'),
                ('Net PPE', 'Property & Equipment'),
                ('Goodwill', 'Goodwill'),
                ('Intangible Assets', 'Intangible Assets')
            ]

            for bs_key, display_name in asset_details:
                if bs_key in bs.index and bs[bs_key] > 0:
                    if display_name not in nodes:
                        nodes.append(display_name)
                        node_indices[display_name] = len(nodes) - 1
                        # Assign color from breakdown palette
                        node_colors.append(asset_colors['breakdown'][len(node_colors) % len(asset_colors['breakdown'])])

                    # Determine parent (Current or Non-Current)
                    parent = 'Current Assets' if bs_key in ['Cash And Cash Equivalents', 'Accounts Receivable', 'Inventory'] else 'Non-Current Assets'

                    sources.append(node_indices[parent])
                    targets.append(node_indices[display_name])
                    values.append(abs(bs[bs_key]))

            return {
                'nodes': nodes,
                'sources': sources,
                'targets': targets,
                'values': values,
                'node_colors': node_colors,
                'total_assets': total_assets,
                'total_liabilities': current_liabilities + total_non_current_liabilities,
                'stockholders_equity': stockholders_equity,
                'date': latest_col.strftime('%Y-%m-%d')
            }

        except Exception as e:
            print(f"Error preparing Sankey data: {str(e)}")
            return None


def display_balance_sheet_sankey(symbol: str):
    """Display balance sheet Sankey diagram in Streamlit with enhanced styling

    Args:
        symbol: Stock symbol
    """
    st.subheader("💰 Balance Sheet Flow Diagram")

    # Add controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("**Interactive Balance Sheet Visualization**")

    # Theme and scale selectors
    theme = create_theme_selector()
    scale, show_pct = create_scale_selector()

    # Get data
    analyzer = BalanceSheetSankey(symbol)
    bs = analyzer.get_balance_sheet_data()

    if bs is None or bs.empty:
        st.info("📊 Balance sheet data not available for this stock.")
        return

    sankey_data = analyzer.prepare_sankey_data(bs, theme)

    if sankey_data is None:
        st.error("Unable to prepare balance sheet data.")
        return

    # Check data freshness
    from datetime import datetime, timedelta
    data_date = datetime.strptime(sankey_data['date'], '%Y-%m-%d')
    days_old = (datetime.now() - data_date).days

    if days_old > 90:
        st.warning(f"⚠️ Data is {days_old} days old (from {sankey_data['date']}). Balance sheet data is typically updated quarterly.")
    elif days_old > 30:
        st.info(f"ℹ️ Data from {sankey_data['date']} ({days_old} days ago). Balance sheet data updates quarterly.")

    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Assets",
            theme.format_value(sankey_data['total_assets'], scale)
        )
    with col2:
        st.metric(
            "Total Liabilities",
            theme.format_value(sankey_data['total_liabilities'], scale)
        )
    with col3:
        st.metric(
            "Stockholders' Equity",
            theme.format_value(sankey_data['stockholders_equity'], scale)
        )

    # Create and display Sankey chart
    fig = theme.create_sankey_figure(
        nodes=sankey_data['nodes'],
        sources=sankey_data['sources'],
        targets=sankey_data['targets'],
        values=sankey_data['values'],
        node_colors=sankey_data['node_colors'],
        title=f"{symbol} Balance Sheet Flow – {sankey_data['date']}",
        height=700,
        scale=scale,
        show_percentage=show_pct
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display explanation
    with st.expander("ℹ️ How to Read This Diagram"):
        st.markdown("""
        **Sankey Diagram** shows the flow of financial resources in the company's balance sheet:

        **Color Legend:**
        - 🟢 **Green/Teal**: Assets (company resources)
          - Light green: Current Assets (cash, receivables, inventory)
          - Blue: Non-Current Assets (property, equipment, intangibles)
        - 🔴 **Red/Orange**: Liabilities (company obligations)
          - Orange: Current Liabilities (short-term debts)
          - Dark red: Non-Current Liabilities (long-term debts)
        - 🟡 **Yellow**: Equity (shareholders' investment)

        **How to Use:**
        - Hover over flows to see detailed values and percentages
        - Use theme selector to switch between light/dark modes
        - Adjust value scale (Billions/Millions/Actual) for clarity
        - Toggle percentages on/off

        **The Balance Sheet Equation:**
        `Total Assets = Total Liabilities + Stockholders' Equity`

        The width of each flow represents the relative size of that component.
        """)
