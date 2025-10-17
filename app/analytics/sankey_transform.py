"""
Sankey Transform Module
Converts financial data into Sankey diagram format (nodes, links) for Plotly visualization.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def income_to_sankey(df: pd.DataFrame, fiscal_index: int = 0) -> Dict[str, Any]:
    """
    Transform income statement data into Sankey diagram format.

    Args:
        df: DataFrame with income statement data (columns: revenue, cost_of_revenue, etc.)
        fiscal_index: Row index to use (0 = most recent)

    Returns:
        Dict with keys: labels, sources, targets, values, colors, meta
    """
    if df.empty or fiscal_index >= len(df):
        return _empty_sankey("No income statement data available")

    row = df.iloc[fiscal_index]

    # Extract values
    revenue = abs(float(row.get('revenue', 0)))
    cost_of_revenue = abs(float(row.get('cost_of_revenue', 0)))
    gross_profit = abs(float(row.get('gross_profit', 0)))
    operating_income = abs(float(row.get('operating_income', 0)))
    rd_expense = abs(float(row.get('rd_expense', 0)))
    sga_expense = abs(float(row.get('sga_expense', 0)))
    other_operating_expense = abs(float(row.get('other_operating_expense', 0)))
    tax_expense = abs(float(row.get('tax_expense', 0)))
    interest_expense = abs(float(row.get('interest_expense', 0)))
    net_income = abs(float(row.get('net_income', 0)))

    # Validate basic balance
    if gross_profit == 0:
        gross_profit = revenue - cost_of_revenue if revenue > cost_of_revenue else revenue * 0.3

    # Calculate operating expenses if not available
    total_opex = rd_expense + sga_expense + other_operating_expense
    if total_opex == 0 and gross_profit > operating_income:
        total_opex = gross_profit - operating_income
        # Distribute evenly if not detailed
        sga_expense = total_opex * 0.6
        rd_expense = total_opex * 0.25
        other_operating_expense = total_opex * 0.15

    # Calculate net income if missing
    if net_income == 0:
        net_income = max(0, operating_income - tax_expense - interest_expense)

    # Build Sankey structure
    labels = []
    sources = []
    targets = []
    values = []
    colors_nodes = []

    # Define color scheme
    COLOR_REVENUE = "#B0B7C3"  # Gray
    COLOR_PROFIT = "#22C55E"   # Green
    COLOR_OPERATING = "#2DD4BF"  # Teal
    COLOR_COST = "#EF4444"     # Red
    COLOR_TAX = "#DC2626"      # Dark red
    COLOR_NET = "#16A34A"      # Dark green

    # Node 0: Revenue
    labels.append("Revenue")
    colors_nodes.append(COLOR_REVENUE)

    # Node 1: Cost of Revenue
    labels.append("Cost of Revenue")
    colors_nodes.append(COLOR_COST)

    # Node 2: Gross Profit
    labels.append("Gross Profit")
    colors_nodes.append(COLOR_PROFIT)

    # Revenue → Cost of Revenue
    sources.append(0)
    targets.append(1)
    values.append(cost_of_revenue)

    # Revenue → Gross Profit
    sources.append(0)
    targets.append(2)
    values.append(gross_profit)

    # Node 3: Operating Expenses
    if total_opex > 0:
        labels.append("Operating Expenses")
        colors_nodes.append(COLOR_COST)

        # Gross Profit → Operating Expenses
        sources.append(2)
        targets.append(3)
        values.append(total_opex)

        # Node 4: Operating Income
        labels.append("Operating Income")
        colors_nodes.append(COLOR_OPERATING)

        # Gross Profit → Operating Income
        sources.append(2)
        targets.append(4)
        values.append(operating_income)

        # Break down Operating Expenses
        if rd_expense > 0:
            labels.append("R&D")
            colors_nodes.append(COLOR_COST)
            sources.append(3)
            targets.append(len(labels) - 1)
            values.append(rd_expense)

        if sga_expense > 0:
            labels.append("SG&A")
            colors_nodes.append(COLOR_COST)
            sources.append(3)
            targets.append(len(labels) - 1)
            values.append(sga_expense)

        if other_operating_expense > 0:
            labels.append("Other OpEx")
            colors_nodes.append(COLOR_COST)
            sources.append(3)
            targets.append(len(labels) - 1)
            values.append(other_operating_expense)

        operating_income_idx = 4
    else:
        # No detailed opex breakdown
        operating_income_idx = 3
        labels.append("Operating Income")
        colors_nodes.append(COLOR_OPERATING)
        sources.append(2)
        targets.append(3)
        values.append(operating_income)

    # Net Income node
    net_income_idx = len(labels)
    labels.append("Net Income")
    colors_nodes.append(COLOR_NET)

    # Operating Income → Tax
    if tax_expense > 0:
        tax_idx = len(labels)
        labels.append("Tax")
        colors_nodes.append(COLOR_TAX)
        sources.append(operating_income_idx)
        targets.append(tax_idx)
        values.append(tax_expense)

    # Operating Income → Interest
    if interest_expense > 0:
        interest_idx = len(labels)
        labels.append("Interest")
        colors_nodes.append(COLOR_TAX)
        sources.append(operating_income_idx)
        targets.append(interest_idx)
        values.append(interest_expense)

    # Operating Income → Net Income
    sources.append(operating_income_idx)
    targets.append(net_income_idx)
    values.append(net_income)

    # Calculate margins
    gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
    op_margin = (operating_income / revenue * 100) if revenue > 0 else 0
    net_margin = (net_income / revenue * 100) if revenue > 0 else 0

    # YoY calculations
    yoy_revenue = _calculate_yoy(df, 'revenue', fiscal_index)
    yoy_net_income = _calculate_yoy(df, 'net_income', fiscal_index)

    meta = {
        'revenue': revenue,
        'gross_margin': gross_margin,
        'op_margin': op_margin,
        'net_margin': net_margin,
        'yoy_revenue': yoy_revenue,
        'yoy_net_income': yoy_net_income,
        'period_end': row.get('period_end', 'N/A')
    }

    return {
        'labels': labels,
        'sources': sources,
        'targets': targets,
        'values': values,
        'colors': colors_nodes,
        'meta': meta
    }


def fund_to_sankey(fund_name: str, holdings: List[Dict]) -> Dict[str, Any]:
    """
    Transform fund holdings into Sankey diagram (Fund → Stocks).

    Args:
        fund_name: Name of the fund
        holdings: List of dicts with keys: symbol, weight (%)

    Returns:
        Dict with Sankey structure
    """
    if not holdings:
        return _empty_sankey(f"No holdings data for {fund_name}")

    labels = [fund_name]
    sources = []
    targets = []
    values = []
    colors_nodes = ["#2563EB"]  # Blue for fund

    # Sort by weight descending
    holdings_sorted = sorted(holdings, key=lambda x: x.get('weight', 0), reverse=True)

    for holding in holdings_sorted:
        symbol = holding.get('symbol', 'Unknown')
        weight = float(holding.get('weight', 0))

        if weight <= 0:
            continue

        labels.append(symbol)
        colors_nodes.append("#22C55E")  # Green for stocks

        sources.append(0)  # From fund
        targets.append(len(labels) - 1)
        values.append(weight)

    total_weight = sum(values)
    top3_concentration = sum(sorted(values, reverse=True)[:3]) if len(values) >= 3 else total_weight

    meta = {
        'fund_name': fund_name,
        'holdings_count': len(holdings_sorted),
        'total_weight': total_weight,
        'top3_concentration': top3_concentration
    }

    return {
        'labels': labels,
        'sources': sources,
        'targets': targets,
        'values': values,
        'colors': colors_nodes,
        'meta': meta
    }


def stock_to_funds_sankey(stock_symbol: str, funds_data: List[Dict]) -> Dict[str, Any]:
    """
    Transform stock ownership into Sankey diagram (Stock → Funds).

    Args:
        stock_symbol: Stock ticker
        funds_data: List of dicts with keys: fund_symbol, weight (%)

    Returns:
        Dict with Sankey structure
    """
    if not funds_data:
        return _empty_sankey(f"No fund ownership data for {stock_symbol}")

    labels = [stock_symbol]
    sources = []
    targets = []
    values = []
    colors_nodes = ["#2563EB"]  # Blue for stock

    # Sort by weight descending
    funds_sorted = sorted(funds_data, key=lambda x: x.get('weight', 0), reverse=True)

    for fund_data in funds_sorted:
        fund_symbol = fund_data.get('fund_symbol', 'Unknown')
        weight = float(fund_data.get('weight', 0))

        if weight <= 0:
            continue

        labels.append(fund_symbol)
        colors_nodes.append("#22C55E")  # Green for funds

        sources.append(0)  # From stock
        targets.append(len(labels) - 1)
        values.append(weight)

    avg_weight = np.mean(values) if values else 0
    max_weight = max(values) if values else 0

    meta = {
        'stock_symbol': stock_symbol,
        'number_of_funds': len(funds_sorted),
        'avg_weight': avg_weight,
        'max_weight': max_weight
    }

    return {
        'labels': labels,
        'sources': sources,
        'targets': targets,
        'values': values,
        'colors': colors_nodes,
        'meta': meta
    }


def macro_to_sankey(liquidity_sources: Dict[str, float],
                    asset_allocations: Dict[str, float]) -> Dict[str, Any]:
    """
    Transform macro liquidity flows into Sankey diagram.

    Args:
        liquidity_sources: Dict of source → value (e.g., {'M2': 1000, 'CB_Balance': 500})
        asset_allocations: Dict of asset → value (e.g., {'Equities': 800, 'BTC': 400})

    Returns:
        Dict with Sankey structure
    """
    if not liquidity_sources or not asset_allocations:
        return _empty_sankey("No macro liquidity data available")

    labels = []
    sources = []
    targets = []
    values = []
    colors_nodes = []

    # Normalize to 100 for visualization
    total_sources = sum(liquidity_sources.values())
    total_assets = sum(asset_allocations.values())

    if total_sources == 0 or total_assets == 0:
        return _empty_sankey("Invalid macro liquidity values")

    # Add source nodes
    source_indices = {}
    for i, (source_name, value) in enumerate(liquidity_sources.items()):
        labels.append(source_name)
        source_indices[source_name] = i
        colors_nodes.append("#9333EA")  # Purple for sources

    # Add asset nodes
    asset_offset = len(labels)
    asset_indices = {}
    for i, (asset_name, value) in enumerate(asset_allocations.items()):
        labels.append(asset_name)
        asset_indices[asset_name] = asset_offset + i
        colors_nodes.append("#22C55E")  # Green for assets

    # Create proportional flows
    # Each source contributes to each asset proportionally
    for source_name, source_val in liquidity_sources.items():
        source_idx = source_indices[source_name]
        source_proportion = source_val / total_sources

        for asset_name, asset_val in asset_allocations.items():
            asset_idx = asset_indices[asset_name]
            asset_proportion = asset_val / total_assets

            flow_value = source_proportion * asset_proportion * 100  # Normalized to 100

            sources.append(source_idx)
            targets.append(asset_idx)
            values.append(flow_value)

    meta = {
        'total_liquidity': total_sources,
        'total_allocation': total_assets,
        'sources_count': len(liquidity_sources),
        'assets_count': len(asset_allocations)
    }

    return {
        'labels': labels,
        'sources': sources,
        'targets': targets,
        'values': values,
        'colors': colors_nodes,
        'meta': meta
    }


def _calculate_yoy(df: pd.DataFrame, column: str, current_index: int) -> Optional[float]:
    """Calculate Year-over-Year change percentage."""
    if len(df) <= current_index + 1:
        return None

    current = df.iloc[current_index].get(column, 0)
    previous = df.iloc[current_index + 1].get(column, 0)

    if previous == 0:
        return None

    return ((current - previous) / abs(previous)) * 100


def _empty_sankey(message: str) -> Dict[str, Any]:
    """Return empty Sankey structure with error message."""
    return {
        'labels': ['No Data'],
        'sources': [],
        'targets': [],
        'values': [],
        'colors': ['#9CA3AF'],
        'meta': {'error': message}
    }
