"""
Comparison Module
Provides side-by-side comparison functionality for financial data.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def compare_income_statements(data_list: List[Dict[str, Any]],
                               metric: str = 'net_margin') -> go.Figure:
    """
    Create comparison chart for multiple companies' income statements.

    Args:
        data_list: List of dicts with keys: ticker, meta (from sankey)
        metric: Metric to compare ('gross_margin', 'op_margin', 'net_margin', 'revenue')

    Returns:
        Plotly figure with comparison
    """
    tickers = [d['ticker'] for d in data_list]
    values = [d['meta'].get(metric, 0) for d in data_list]

    # Determine if percentage or currency
    is_percentage = metric.endswith('_margin')

    fig = go.Figure(data=[
        go.Bar(
            x=tickers,
            y=values,
            text=[f"{v:.2f}%" if is_percentage else f"${v:,.0f}" for v in values],
            textposition='auto',
            marker=dict(
                color=values,
                colorscale='Blues',
                showscale=False
            )
        )
    ])

    title_map = {
        'gross_margin': 'Gross Margin Comparison',
        'op_margin': 'Operating Margin Comparison',
        'net_margin': 'Net Margin Comparison',
        'revenue': 'Revenue Comparison'
    }

    fig.update_layout(
        title=title_map.get(metric, f'{metric} Comparison'),
        xaxis_title='Company',
        yaxis_title='Percentage (%)' if is_percentage else 'USD',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12, family="Inter, sans-serif", color="#4B5563"),
        height=400
    )

    return fig


def compare_fund_holdings(holdings_list: List[Dict[str, Any]],
                          top_n: int = 10) -> pd.DataFrame:
    """
    Compare holdings across multiple funds.

    Args:
        holdings_list: List of dicts with keys: fund, holdings
        top_n: Number of top holdings to show

    Returns:
        DataFrame with comparison
    """
    # Collect all unique symbols
    all_symbols = set()
    for item in holdings_list:
        for holding in item['holdings']:
            all_symbols.add(holding['symbol'])

    # Build comparison table
    comparison_data = []

    for symbol in sorted(all_symbols):
        row = {'Symbol': symbol}

        for item in holdings_list:
            fund = item['fund']
            weight = 0.0

            for holding in item['holdings']:
                if holding['symbol'] == symbol:
                    weight = holding.get('weight', 0)
                    break

            row[fund] = f"{weight:.2f}%" if weight > 0 else "-"

        comparison_data.append(row)

    df = pd.DataFrame(comparison_data)

    # Sort by total weight (sum across funds)
    df['_total'] = 0.0
    for col in df.columns:
        if col not in ['Symbol', '_total']:
            df['_total'] += df[col].apply(
                lambda x: float(x.replace('%', '')) if isinstance(x, str) and x != '-' else 0
            )

    df = df.sort_values('_total', ascending=False).head(top_n)
    df = df.drop('_total', axis=1)

    return df


def create_fy_vs_ltm_comparison(fy_data: pd.DataFrame,
                                  ltm_data: pd.DataFrame,
                                  ticker: str) -> go.Figure:
    """
    Compare Fiscal Year vs Last Twelve Months data.

    Args:
        fy_data: Fiscal year income statement
        ltm_data: LTM income statement
        ticker: Stock ticker

    Returns:
        Plotly figure with comparison
    """
    if fy_data.empty or ltm_data.empty:
        return go.Figure()

    metrics = ['revenue', 'gross_profit', 'operating_income', 'net_income']
    fy_values = [abs(float(fy_data.iloc[0].get(m, 0))) for m in metrics]
    ltm_values = [abs(float(ltm_data.iloc[0].get(m, 0))) for m in metrics]

    fig = go.Figure(data=[
        go.Bar(
            name='Fiscal Year',
            x=metrics,
            y=fy_values,
            text=[f"${v/1e9:.1f}B" for v in fy_values],
            textposition='auto',
            marker=dict(color='#2563EB')
        ),
        go.Bar(
            name='Last 12 Months',
            x=metrics,
            y=ltm_values,
            text=[f"${v/1e9:.1f}B" for v in ltm_values],
            textposition='auto',
            marker=dict(color='#22C55E')
        )
    ])

    fig.update_layout(
        title=f'{ticker} - Fiscal Year vs LTM Comparison',
        xaxis_title='Metric',
        yaxis_title='USD',
        barmode='group',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12, family="Inter, sans-serif", color="#4B5563"),
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_multi_ticker_sankey_grid(sankey_data_list: List[Dict[str, Any]],
                                     rows: int = 2,
                                     cols: int = 2) -> go.Figure:
    """
    Create grid of Sankey diagrams for multiple tickers.

    Args:
        sankey_data_list: List of dicts with keys: ticker, sankey_data
        rows: Number of rows
        cols: Number of columns

    Returns:
        Plotly figure with subplots
    """
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=[d['ticker'] for d in sankey_data_list[:rows*cols]],
        specs=[[{'type': 'sankey'} for _ in range(cols)] for _ in range(rows)],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

    for idx, data in enumerate(sankey_data_list[:rows*cols]):
        row = (idx // cols) + 1
        col = (idx % cols) + 1

        sankey = data['sankey_data']

        fig.add_trace(
            go.Sankey(
                node=dict(
                    pad=10,
                    thickness=12,
                    line=dict(color="white", width=1),
                    label=sankey['labels'],
                    color=sankey['colors']
                ),
                link=dict(
                    source=sankey['sources'],
                    target=sankey['targets'],
                    value=sankey['values'],
                )
            ),
            row=row,
            col=col
        )

    fig.update_layout(
        title_text="Income Statement Comparison Grid",
        font=dict(size=10, family="Inter, sans-serif"),
        height=800,
        showlegend=False,
        paper_bgcolor='white'
    )

    return fig


def create_trend_animation(historical_df: pd.DataFrame,
                           metric: str = 'net_margin',
                           ticker: str = '') -> go.Figure:
    """
    Create animated trend chart for historical data.

    Args:
        historical_df: DataFrame with historical periods
        metric: Metric to animate
        ticker: Stock ticker

    Returns:
        Plotly figure with animation
    """
    if historical_df.empty:
        return go.Figure()

    # Prepare data
    periods = historical_df['period_end'].tolist()
    values = historical_df[metric].tolist()

    # Create frames for animation
    frames = []
    for i in range(1, len(periods) + 1):
        frame_data = go.Scatter(
            x=periods[:i],
            y=values[:i],
            mode='lines+markers',
            line=dict(color='#2563EB', width=3),
            marker=dict(size=10)
        )
        frames.append(go.Frame(data=[frame_data], name=str(i)))

    # Initial figure
    fig = go.Figure(
        data=[go.Scatter(
            x=periods[:1],
            y=values[:1],
            mode='lines+markers',
            line=dict(color='#2563EB', width=3),
            marker=dict(size=10)
        )],
        frames=frames
    )

    # Add play button
    fig.update_layout(
        title=f'{ticker} {metric.replace("_", " ").title()} Trend',
        xaxis_title='Period',
        yaxis_title=metric.replace("_", " ").title(),
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'buttons': [
                {
                    'label': 'Play',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': 500, 'redraw': True},
                        'fromcurrent': True
                    }]
                },
                {
                    'label': 'Pause',
                    'method': 'animate',
                    'args': [[None], {
                        'frame': {'duration': 0, 'redraw': False},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }]
                }
            ]
        }],
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400
    )

    return fig
