"""Balance Sheet Sankey Chart Visualization"""
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from typing import Dict, Optional, List, Tuple


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

    def prepare_sankey_data(self, balance_sheet: pd.DataFrame) -> Dict:
        """Prepare data for Sankey diagram

        Args:
            balance_sheet: Balance sheet dataframe

        Returns:
            Dictionary with nodes, links, and values
        """
        try:
            # Get latest column (most recent data)
            latest_col = balance_sheet.columns[0]
            bs = balance_sheet[latest_col]

            # Define key balance sheet items
            assets_items = {
                'Current Assets': ['Cash And Cash Equivalents', 'Accounts Receivable', 'Inventory',
                                  'Cash Cash Equivalents And Short Term Investments'],
                'Non-Current Assets': ['Net PPE', 'Goodwill', 'Intangible Assets',
                                      'Long Term Equity Investment', 'Properties']
            }

            liabilities_items = {
                'Current Liabilities': ['Accounts Payable', 'Current Debt', 'Current Deferred Liabilities'],
                'Non-Current Liabilities': ['Long Term Debt', 'Non Current Deferred Liabilities']
            }

            equity_items = ['Stockholders Equity', 'Common Stock', 'Retained Earnings']

            # Initialize nodes and links
            nodes = ['Total Assets', 'Total Liabilities & Equity',
                    'Current Assets', 'Non-Current Assets',
                    'Current Liabilities', 'Non-Current Liabilities', 'Equity']

            links = {
                'source': [],
                'target': [],
                'value': [],
                'label': []
            }

            node_indices = {node: idx for idx, node in enumerate(nodes)}

            # Calculate totals
            total_assets = bs.get('Total Assets', 0)
            current_assets = bs.get('Current Assets', 0)
            total_non_current_assets = bs.get('Total Non Current Assets', total_assets - current_assets)

            current_liabilities = bs.get('Current Liabilities', 0)
            total_non_current_liabilities = bs.get('Total Non Current Liabilities Net Minority Interest', 0)
            stockholders_equity = bs.get('Stockholders Equity', 0)

            # Assets breakdown
            if current_assets > 0:
                links['source'].append(node_indices['Total Assets'])
                links['target'].append(node_indices['Current Assets'])
                links['value'].append(abs(current_assets))
                links['label'].append(f'${current_assets/1e9:.2f}B')

            if total_non_current_assets > 0:
                links['source'].append(node_indices['Total Assets'])
                links['target'].append(node_indices['Non-Current Assets'])
                links['value'].append(abs(total_non_current_assets))
                links['label'].append(f'${total_non_current_assets/1e9:.2f}B')

            # Liabilities & Equity breakdown
            if current_liabilities > 0:
                links['source'].append(node_indices['Total Liabilities & Equity'])
                links['target'].append(node_indices['Current Liabilities'])
                links['value'].append(abs(current_liabilities))
                links['label'].append(f'${current_liabilities/1e9:.2f}B')

            if total_non_current_liabilities > 0:
                links['source'].append(node_indices['Total Liabilities & Equity'])
                links['target'].append(node_indices['Non-Current Liabilities'])
                links['value'].append(abs(total_non_current_liabilities))
                links['label'].append(f'${total_non_current_liabilities/1e9:.2f}B')

            if stockholders_equity > 0:
                links['source'].append(node_indices['Total Liabilities & Equity'])
                links['target'].append(node_indices['Equity'])
                links['value'].append(abs(stockholders_equity))
                links['label'].append(f'${stockholders_equity/1e9:.2f}B')

            # Add detailed breakdowns for current assets
            for item_name in ['Cash And Cash Equivalents', 'Accounts Receivable', 'Inventory']:
                if item_name in bs.index and bs[item_name] > 0:
                    node_name = item_name.replace('And', '&')
                    if node_name not in nodes:
                        nodes.append(node_name)
                        node_indices[node_name] = len(nodes) - 1

                    links['source'].append(node_indices['Current Assets'])
                    links['target'].append(node_indices[node_name])
                    links['value'].append(abs(bs[item_name]))
                    links['label'].append(f'${bs[item_name]/1e9:.2f}B')

            return {
                'nodes': nodes,
                'links': links,
                'total_assets': total_assets,
                'total_liabilities': current_liabilities + total_non_current_liabilities,
                'stockholders_equity': stockholders_equity,
                'date': latest_col.strftime('%Y-%m-%d')
            }

        except Exception as e:
            print(f"Error preparing Sankey data: {str(e)}")
            return None

    def create_sankey_chart(self, sankey_data: Dict) -> go.Figure:
        """Create Sankey diagram

        Args:
            sankey_data: Prepared Sankey data

        Returns:
            Plotly figure
        """
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=sankey_data['nodes'],
                color=['#2E86AB', '#A23B72',
                       '#06D6A0', '#118AB2',
                       '#EF476F', '#F78C6B', '#06D6A0'] +
                      ['#FFD166'] * (len(sankey_data['nodes']) - 7)
            ),
            link=dict(
                source=sankey_data['links']['source'],
                target=sankey_data['links']['target'],
                value=sankey_data['links']['value'],
                label=sankey_data['links']['label']
            )
        )])

        fig.update_layout(
            title=f"{self.symbol} Balance Sheet Flow - {sankey_data['date']}",
            font=dict(size=12),
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        return fig


def display_balance_sheet_sankey(symbol: str):
    """Display balance sheet Sankey diagram in Streamlit

    Args:
        symbol: Stock symbol
    """
    st.subheader("💰 Balance Sheet Flow Diagram")

    analyzer = BalanceSheetSankey(symbol)
    bs = analyzer.get_balance_sheet_data()

    if bs is None or bs.empty:
        st.info("📊 Balance sheet data not available for this stock.")
        return

    sankey_data = analyzer.prepare_sankey_data(bs)

    if sankey_data is None:
        st.error("Unable to prepare balance sheet data.")
        return

    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Assets", f"${sankey_data['total_assets']/1e9:.2f}B")
    with col2:
        st.metric("Total Liabilities", f"${sankey_data['total_liabilities']/1e9:.2f}B")
    with col3:
        st.metric("Stockholders' Equity", f"${sankey_data['stockholders_equity']/1e9:.2f}B")

    # Create and display Sankey chart
    fig = analyzer.create_sankey_chart(sankey_data)
    st.plotly_chart(fig, use_container_width=True)

    # Display explanation
    with st.expander("ℹ️ How to Read This Diagram"):
        st.markdown("""
        **Sankey Diagram** shows the flow of financial resources in the company's balance sheet:

        - **Left side (Assets):** Shows how the company's resources are allocated
          - Current Assets: Cash, receivables, inventory, etc.
          - Non-Current Assets: Property, equipment, intangibles, etc.

        - **Right side (Liabilities & Equity):** Shows how those assets are financed
          - Current Liabilities: Short-term debts and obligations
          - Non-Current Liabilities: Long-term debts
          - Equity: Shareholders' investment

        The width of each flow represents the relative size of that component.
        """)
