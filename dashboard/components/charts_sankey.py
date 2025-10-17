"""
Sankey Charts Component
Reusable Plotly Sankey chart builders with consistent styling.
"""

from typing import Dict, Any, Optional
import plotly.graph_objects as go


def _theme_colors(theme: str = "Light") -> dict:
    """
    Get theme-specific colors for Sankey charts.

    Args:
        theme: "Light" or "Dark"

    Returns:
        Dict with text, node_border, paper_bg, plot_bg colors
    """
    if theme == "Dark":
        return {
            "text": "#F9FAFB",
            "node_border": "#111827",
            "paper_bg": "#0B1220",
            "plot_bg": "#0B1220",
        }
    else:  # Light
        return {
            "text": "#1F2937",
            "node_border": "#FFFFFF",
            "paper_bg": "#F9FAFB",
            "plot_bg": "#F9FAFB",
        }


def plot_income_sankey(payload: Dict[str, Any], title: str = "Income Statement Flow",
                       theme: str = "Light", scale_display: str = "$") -> go.Figure:
    """
    Create Plotly Sankey diagram for income statement.

    Args:
        payload: Dict with keys: labels, sources, targets, values, colors, meta
        title: Chart title
        theme: "Light" or "Dark" theme
        scale_display: "$", "$M", or "$B" for value scaling

    Returns:
        Plotly Figure
    """
    labels = payload.get('labels', [])
    sources = payload.get('sources', [])
    targets = payload.get('targets', [])
    values = payload.get('values', [])
    colors = payload.get('colors', [])
    meta = payload.get('meta', {})

    if not labels or not values:
        return _empty_chart("No income statement data available", theme)

    # Get theme colors
    theme_cols = _theme_colors(theme)

    # Scale values based on display preference
    scale_factor = {"$": 1, "$M": 1e-6, "$B": 1e-9}.get(scale_display, 1)
    scaled_values = [v * scale_factor for v in values]

    # Build link colors (semi-transparent versions of node colors)
    link_colors = []
    for src in sources:
        if src < len(colors):
            base_color = colors[src]
            # Convert hex to RGBA with transparency
            link_colors.append(_hex_to_rgba(base_color, 0.25))
        else:
            link_colors.append("rgba(176, 183, 195, 0.25)")

    # Value format for hover
    value_format = f"{scale_display}%{{value:,.1f}}"

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=16,
            thickness=20,
            line=dict(color=theme_cols["node_border"], width=2),
            label=labels,
            color=colors,
            hovertemplate=f'%{{label}}<br>{value_format}<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=scaled_values,
            color=link_colors,
            hovertemplate=f'%{{source.label}} → %{{target.label}}<br>{value_format}<extra></extra>'
        ),
        textfont=dict(color=theme_cols["text"], size=14, family="Inter, sans-serif", weight=600)
    )])

    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 22, 'color': theme_cols["text"], 'family': 'Inter, sans-serif'}
        },
        font=dict(size=13, family="Inter, sans-serif", color=theme_cols["text"]),
        plot_bgcolor=theme_cols["plot_bg"],
        paper_bgcolor=theme_cols["paper_bg"],
        height=600,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig


def plot_fund_sankey(payload: Dict[str, Any], title: str, theme: str = "Light") -> go.Figure:
    """
    Create Plotly Sankey diagram for fund holdings or stock ownership.

    Args:
        payload: Dict with keys: labels, sources, targets, values, colors, meta
        title: Chart title
        theme: "Light" or "Dark" theme

    Returns:
        Plotly Figure
    """
    labels = payload.get('labels', [])
    sources = payload.get('sources', [])
    targets = payload.get('targets', [])
    values = payload.get('values', [])
    colors = payload.get('colors', [])

    if not labels or not values:
        return _empty_chart("No holdings data available", theme)

    # Get theme colors
    theme_cols = _theme_colors(theme)

    # Build link colors
    link_colors = []
    for src in sources:
        if src < len(colors):
            base_color = colors[src]
            link_colors.append(_hex_to_rgba(base_color, 0.31))
        else:
            link_colors.append("rgba(37, 99, 235, 0.31)")

    # Format labels with percentages for targets
    formatted_labels = []
    total_value = sum(values)

    for i, label in enumerate(labels):
        if i == 0:
            # Source node (fund or stock)
            formatted_labels.append(label)
        else:
            # Target nodes - add percentage
            # Find the value for this target
            target_value = 0
            for j, tgt in enumerate(targets):
                if tgt == i:
                    target_value = values[j]
                    break

            pct = (target_value / total_value * 100) if total_value > 0 else 0
            formatted_labels.append(f"{label}<br>{pct:.1f}%")

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=16,
            thickness=20,
            line=dict(color=theme_cols["node_border"], width=2),
            label=formatted_labels,
            color=colors,
            hovertemplate='%{label}<br>Weight: %{value:.2f}%<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>%{value:.2f}%<extra></extra>'
        ),
        textfont=dict(color=theme_cols["text"], size=14, family="Inter, sans-serif", weight=600)
    )])

    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 22, 'color': theme_cols["text"], 'family': 'Inter, sans-serif'}
        },
        font=dict(size=13, family="Inter, sans-serif", color=theme_cols["text"]),
        plot_bgcolor=theme_cols["plot_bg"],
        paper_bgcolor=theme_cols["paper_bg"],
        height=600,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig


def plot_macro_sankey(payload: Dict[str, Any], title: str = "Macro Liquidity Flows",
                       theme: str = "Light") -> go.Figure:
    """
    Create Plotly Sankey diagram for macro liquidity flows.

    Args:
        payload: Dict with keys: labels, sources, targets, values, colors, meta
        title: Chart title
        theme: "Light" or "Dark" theme

    Returns:
        Plotly Figure
    """
    labels = payload.get('labels', [])
    sources = payload.get('sources', [])
    targets = payload.get('targets', [])
    values = payload.get('values', [])
    colors = payload.get('colors', [])

    if not labels or not values:
        return _empty_chart("No macro liquidity data available", theme)

    # Get theme colors
    theme_cols = _theme_colors(theme)

    # Build link colors
    link_colors = []
    for src in sources:
        if src < len(colors):
            base_color = colors[src]
            link_colors.append(_hex_to_rgba(base_color, 0.19))
        else:
            link_colors.append("rgba(147, 51, 234, 0.19)")

    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color=theme_cols["node_border"], width=2),
            label=labels,
            color=colors,
            hovertemplate='%{label}<br>Flow: %{value:.1f}<extra></extra>'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>%{value:.1f}<extra></extra>'
        ),
        textfont=dict(color=theme_cols["text"], size=14, family="Inter, sans-serif", weight=600)
    )])

    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 22, 'color': theme_cols["text"], 'family': 'Inter, sans-serif'}
        },
        font=dict(size=13, family="Inter, sans-serif", color=theme_cols["text"]),
        plot_bgcolor=theme_cols["plot_bg"],
        paper_bgcolor=theme_cols["paper_bg"],
        height=650,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig


def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """
    Convert hex color to RGBA string.

    Args:
        hex_color: Hex color string (e.g., '#9333EA' or '9333EA')
        alpha: Alpha value (0.0 to 1.0)

    Returns:
        RGBA color string (e.g., 'rgba(147, 51, 234, 0.5)')
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')

    # Convert hex to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return f"rgba({r}, {g}, {b}, {alpha})"


def _empty_chart(message: str, theme: str = "Light") -> go.Figure:
    """Create empty chart with message."""
    theme_cols = _theme_colors(theme)

    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=16, color=theme_cols["text"])
    )

    fig.update_layout(
        plot_bgcolor=theme_cols["plot_bg"],
        paper_bgcolor=theme_cols["paper_bg"],
        height=400,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig
