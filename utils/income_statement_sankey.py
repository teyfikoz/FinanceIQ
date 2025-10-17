"""Income Statement Sankey Chart Visualization"""
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from typing import Dict, Optional, List
from datetime import datetime
from utils.sankey_theme import SankeyTheme, create_theme_selector, create_scale_selector


class IncomeStatementSankey:
    """Create Sankey diagrams for income statement visualization"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)

    def get_income_statement_data(self) -> Optional[pd.DataFrame]:
        """Get income statement data from yfinance

        Returns:
            Income statement dataframe or None
        """
        try:
            income_stmt = self.ticker.income_stmt
            if income_stmt is not None and not income_stmt.empty:
                return income_stmt
            return None
        except Exception as e:
            print(f"Error fetching income statement: {str(e)}")
            return None

    def prepare_sankey_data(
        self,
        income_stmt: pd.DataFrame,
        theme: SankeyTheme
    ) -> Optional[Dict]:
        """Prepare data for Sankey diagram showing revenue breakdown

        Args:
            income_stmt: Income statement dataframe
            theme: SankeyTheme instance

        Returns:
            Dictionary with nodes, links, colors, and values
        """
        try:
            # Get latest column (most recent data)
            latest_col = income_stmt.columns[0]
            inc = income_stmt[latest_col]

            # Initialize data structures
            nodes = []
            sources = []
            targets = []
            values = []
            node_colors = []

            # Get color palettes
            income_colors = theme.get_color_palette('income')
            expense_colors = theme.get_color_palette('liabilities')
            profit_colors = theme.get_color_palette('equity')

            # Main nodes
            nodes.append('Total Revenue')
            node_colors.append(income_colors['revenue'])

            # Get key income statement items
            total_revenue = inc.get('Total Revenue', 0)
            cost_of_revenue = inc.get('Cost Of Revenue', 0)
            gross_profit = inc.get('Gross Profit', total_revenue - cost_of_revenue)
            operating_expenses = inc.get('Operating Expense', 0)
            operating_income = inc.get('Operating Income', gross_profit - operating_expenses)

            # Try different names for net income
            net_income = inc.get('Net Income',
                                inc.get('Net Income Common Stockholders',
                                       inc.get('Net Income Continuing Operations', 0)))

            if total_revenue <= 0:
                return None

            # Build the flow: Revenue -> Gross Profit -> Operating Income -> Net Income

            # Revenue to Cost of Revenue and Gross Profit
            if cost_of_revenue > 0:
                nodes.append('Cost of Revenue')
                node_colors.append(expense_colors['current'])
                sources.append(0)  # From Total Revenue
                targets.append(len(nodes) - 1)
                values.append(abs(cost_of_revenue))

            if gross_profit > 0:
                nodes.append('Gross Profit')
                node_colors.append(income_colors['profit'])
                sources.append(0)  # From Total Revenue
                targets.append(len(nodes) - 1)
                values.append(abs(gross_profit))

                gross_profit_idx = len(nodes) - 1

                # Gross Profit to Operating Expenses and Operating Income
                if operating_expenses > 0:
                    nodes.append('Operating Expenses')
                    node_colors.append(expense_colors['non_current'])
                    sources.append(gross_profit_idx)
                    targets.append(len(nodes) - 1)
                    values.append(abs(operating_expenses))

                if operating_income > 0:
                    nodes.append('Operating Income')
                    node_colors.append(profit_colors['primary'])
                    sources.append(gross_profit_idx)
                    targets.append(len(nodes) - 1)
                    values.append(abs(operating_income))

                    operating_income_idx = len(nodes) - 1

                    # Operating Income to Net Income and Other Expenses
                    other_expense = abs(operating_income - net_income)

                    if net_income > 0:
                        nodes.append('Net Income')
                        node_colors.append(profit_colors['secondary'])
                        sources.append(operating_income_idx)
                        targets.append(len(nodes) - 1)
                        values.append(abs(net_income))

                    if other_expense > 0 and other_expense > abs(net_income) * 0.01:  # Only show if > 1% of net income
                        nodes.append('Other Expenses/Income')
                        node_colors.append(expense_colors['breakdown'][0])
                        sources.append(operating_income_idx)
                        targets.append(len(nodes) - 1)
                        values.append(other_expense)

            # Add detailed expense breakdown if available
            research_dev = inc.get('Research And Development', 0)
            selling_gen_admin = inc.get('Selling General And Administration', 0)

            if 'Operating Expenses' in nodes:
                op_exp_idx = nodes.index('Operating Expenses')

                if research_dev > 0:
                    nodes.append('R&D Expenses')
                    node_colors.append(expense_colors['breakdown'][1])
                    sources.append(op_exp_idx)
                    targets.append(len(nodes) - 1)
                    values.append(abs(research_dev))

                if selling_gen_admin > 0:
                    nodes.append('SG&A Expenses')
                    node_colors.append(expense_colors['breakdown'][2])
                    sources.append(op_exp_idx)
                    targets.append(len(nodes) - 1)
                    values.append(abs(selling_gen_admin))

            return {
                'nodes': nodes,
                'sources': sources,
                'targets': targets,
                'values': values,
                'node_colors': node_colors,
                'total_revenue': total_revenue,
                'gross_profit': gross_profit,
                'operating_income': operating_income,
                'net_income': net_income,
                'date': latest_col.strftime('%Y-%m-%d')
            }

        except Exception as e:
            print(f"Error preparing income statement Sankey data: {str(e)}")
            return None


def display_income_statement_sankey(symbol: str):
    """Display income statement Sankey diagram in Streamlit

    Args:
        symbol: Stock symbol
    """
    st.subheader("💵 Income Statement Flow Diagram")

    # Add controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("**Interactive Income Statement Visualization**")

    # Theme and scale selectors
    theme = create_theme_selector()
    scale, show_pct = create_scale_selector()

    # Get data
    analyzer = IncomeStatementSankey(symbol)
    income_stmt = analyzer.get_income_statement_data()

    if income_stmt is None or income_stmt.empty:
        st.info("📊 Income statement data not available for this stock.")
        return

    sankey_data = analyzer.prepare_sankey_data(income_stmt, theme)

    if sankey_data is None:
        st.error("Unable to prepare income statement data.")
        return

    # Check data freshness
    data_date = datetime.strptime(sankey_data['date'], '%Y-%m-%d')
    days_old = (datetime.now() - data_date).days

    if days_old > 90:
        st.warning(f"⚠️ Data is {days_old} days old (from {sankey_data['date']}). Income statement data is typically updated quarterly.")
    elif days_old > 30:
        st.info(f"ℹ️ Data from {sankey_data['date']} ({days_old} days ago). Income statement data updates quarterly.")

    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total Revenue",
            theme.format_value(sankey_data['total_revenue'], scale)
        )
    with col2:
        st.metric(
            "Gross Profit",
            theme.format_value(sankey_data['gross_profit'], scale)
        )
    with col3:
        st.metric(
            "Operating Income",
            theme.format_value(sankey_data['operating_income'], scale)
        )
    with col4:
        st.metric(
            "Net Income",
            theme.format_value(sankey_data['net_income'], scale)
        )

    # Create and display Sankey chart
    fig = theme.create_sankey_figure(
        nodes=sankey_data['nodes'],
        sources=sankey_data['sources'],
        targets=sankey_data['targets'],
        values=sankey_data['values'],
        node_colors=sankey_data['node_colors'],
        title=f"{symbol} Income Statement Flow – {sankey_data['date']}",
        height=700,
        scale=scale,
        show_percentage=show_pct
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display explanation
    with st.expander("ℹ️ How to Read This Diagram"):
        st.markdown("""
        **Sankey Diagram** shows the flow of revenue through the company's income statement:

        **Color Legend:**
        - 🟢 **Green**: Revenue and Profit (company earnings)
          - Teal: Total Revenue
          - Light green: Gross Profit
          - Yellow: Operating Income, Net Income
        - 🔴 **Red/Orange**: Expenses (company costs)
          - Orange: Cost of Revenue (COGS)
          - Dark red: Operating Expenses
          - Pink: Other Expenses/Income

        **Flow Structure:**
        1. **Total Revenue** → splits into:
           - Cost of Revenue (what it costs to make/deliver products)
           - Gross Profit (revenue minus COGS)

        2. **Gross Profit** → splits into:
           - Operating Expenses (R&D, SG&A, etc.)
           - Operating Income (profit from core operations)

        3. **Operating Income** → splits into:
           - Other Expenses/Income (interest, taxes, one-time items)
           - Net Income (final profit to shareholders)

        **How to Use:**
        - Hover over flows to see detailed values and percentages
        - Use theme selector to switch between light/dark modes
        - Adjust value scale (Billions/Millions/Actual) for clarity
        - Toggle percentages on/off

        **Key Metrics:**
        - **Gross Margin** = Gross Profit / Revenue
        - **Operating Margin** = Operating Income / Revenue
        - **Net Margin** = Net Income / Revenue

        The width of each flow represents the relative size of that component.
        """)
