"""Centralized Sankey Chart Theme Manager"""
import streamlit as st
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go


class SankeyTheme:
    """Theme manager for Sankey charts with light/dark mode support"""

    # High-contrast color palettes
    COLORS = {
        'assets': {
            'primary': '#06D6A0',      # Teal
            'current': '#26C485',       # Light teal
            'non_current': '#118AB2',  # Blue
            'breakdown': ['#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        },
        'liabilities': {
            'primary': '#EF476F',      # Red
            'current': '#F78C6B',       # Orange
            'non_current': '#E63946',  # Dark red
            'breakdown': ['#FF6B6B', '#FFB6B9', '#FEC8D8', '#FDCAE1']
        },
        'equity': {
            'primary': '#FFD166',      # Yellow
            'secondary': '#FFC857',    # Gold
            'breakdown': ['#FFE66D', '#FFB700', '#FFAA00', '#FF9800']
        },
        'income': {
            'revenue': '#06D6A0',
            'expenses': '#EF476F',
            'profit': '#FFD166'
        }
    }

    # Theme-specific settings
    LIGHT_THEME = {
        'paper_bgcolor': 'rgba(255, 255, 255, 0.95)',
        'plot_bgcolor': 'rgba(250, 250, 250, 0.95)',
        'font_color': '#2C3E50',
        'node_border_color': '#34495E',
        'title_color': '#1A1A1A'
    }

    DARK_THEME = {
        'paper_bgcolor': 'rgba(26, 26, 26, 0.95)',
        'plot_bgcolor': 'rgba(18, 18, 18, 0.95)',
        'font_color': '#E8E8E8',
        'node_border_color': '#95A5A6',
        'title_color': '#FFFFFF'
    }

    def __init__(self, theme: str = 'light'):
        """Initialize theme manager

        Args:
            theme: 'light' or 'dark'
        """
        self.theme = theme
        self.settings = self.DARK_THEME if theme == 'dark' else self.LIGHT_THEME

    @staticmethod
    def detect_theme() -> str:
        """Detect current Streamlit theme

        Returns:
            'light' or 'dark'
        """
        # Try to detect from Streamlit config
        try:
            # Check if dark mode is enabled in user's browser/settings
            theme = st.get_option("theme.base")
            return 'dark' if theme == 'dark' else 'light'
        except:
            # Default to light
            return 'light'

    def get_color_palette(self, category: str) -> Dict[str, str]:
        """Get color palette for a category

        Args:
            category: 'assets', 'liabilities', 'equity', or 'income'

        Returns:
            Dictionary of colors
        """
        return self.COLORS.get(category, self.COLORS['assets'])

    def format_value(self, value: float, scale: str = 'B', decimals: int = 2) -> str:
        """Format value with appropriate scale

        Args:
            value: Numeric value
            scale: 'B' (billions), 'M' (millions), or '' (actual)
            decimals: Number of decimal places

        Returns:
            Formatted string
        """
        if scale == 'B':
            return f"${value/1e9:.{decimals}f}B"
        elif scale == 'M':
            return f"${value/1e6:.{decimals}f}M"
        else:
            return f"${value:,.{decimals}f}"

    def create_hover_template(
        self,
        value: float,
        total: float,
        source: str,
        target: str,
        scale: str = 'B',
        show_percentage: bool = True
    ) -> str:
        """Create enhanced hover template

        Args:
            value: Flow value
            total: Total value for percentage calculation
            source: Source node name
            target: Target node name
            scale: Value scale
            show_percentage: Whether to show percentage

        Returns:
            Hover template string
        """
        formatted_value = self.format_value(value, scale)
        percentage = (value / total * 100) if total > 0 else 0

        if show_percentage:
            return (
                f"<b>{source} → {target}</b><br>"
                f"Value: {formatted_value}<br>"
                f"Percentage: {percentage:.1f}%<br>"
                "<extra></extra>"
            )
        else:
            return (
                f"<b>{source} → {target}</b><br>"
                f"Value: {formatted_value}<br>"
                "<extra></extra>"
            )

    def get_base_layout(
        self,
        title: str,
        height: int = 600,
        width: Optional[int] = None
    ) -> Dict:
        """Get base layout configuration

        Args:
            title: Chart title
            height: Chart height in pixels
            width: Chart width in pixels (None for responsive)

        Returns:
            Layout dictionary
        """
        layout = {
            'title': {
                'text': title,
                'font': {
                    'size': 18,
                    'family': 'Inter, sans-serif',
                    'color': self.settings['title_color'],
                    'weight': 600
                },
                'x': 0.5,
                'xanchor': 'center'
            },
            'font': {
                'size': 14,
                'family': 'Inter, sans-serif',
                'color': self.settings['font_color'],
                'weight': 500
            },
            'height': height,
            'paper_bgcolor': self.settings['paper_bgcolor'],
            'plot_bgcolor': self.settings['plot_bgcolor'],
            'margin': {'l': 20, 'r': 20, 't': 60, 'b': 20},
            'hovermode': 'closest'
        }

        if width:
            layout['width'] = width

        return layout

    def create_sankey_figure(
        self,
        nodes: List[str],
        sources: List[int],
        targets: List[int],
        values: List[float],
        node_colors: List[str],
        link_colors: Optional[List[str]] = None,
        title: str = "Sankey Diagram",
        height: int = 600,
        scale: str = 'B',
        show_percentage: bool = True,
        link_labels: Optional[List[str]] = None
    ) -> go.Figure:
        """Create a fully styled Sankey figure

        Args:
            nodes: List of node labels
            sources: List of source indices
            targets: List of target indices
            values: List of flow values
            node_colors: List of node colors
            link_colors: Optional list of link colors (auto-generated if None)
            title: Chart title
            height: Chart height
            scale: Value scale
            show_percentage: Show percentages in hover
            link_labels: Optional custom labels for links

        Returns:
            Plotly Figure object
        """
        # Auto-generate link colors with transparency if not provided
        if link_colors is None:
            link_colors = [self._get_link_color(node_colors[src]) for src in sources]

        # Create hover templates
        hover_templates = []
        if link_labels:
            hover_templates = link_labels
        else:
            for i, (src, tgt, val) in enumerate(zip(sources, targets, values)):
                # Calculate total for percentage
                total = sum(v for s, v in zip(sources, values) if s == src)
                template = self.create_hover_template(
                    val, total, nodes[src], nodes[tgt], scale, show_percentage
                )
                hover_templates.append(template)

        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=20,
                thickness=25,
                line=dict(
                    color=self.settings['node_border_color'],
                    width=1.5
                ),
                label=nodes,
                color=node_colors,
                hovertemplate='<b>%{label}</b><br>Total: %{value}<extra></extra>'
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors,
                hovertemplate=hover_templates
            ),
            textfont=dict(
                size=14,
                family='Inter, sans-serif',
                color=self.settings['font_color']
            )
        )])

        # Apply layout
        fig.update_layout(**self.get_base_layout(title, height))

        return fig

    def _get_link_color(self, node_color: str, alpha: float = 0.4) -> str:
        """Convert node color to link color with transparency

        Args:
            node_color: Hex color code
            alpha: Transparency (0-1)

        Returns:
            RGBA color string
        """
        # Convert hex to RGB
        hex_color = node_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'rgba({r}, {g}, {b}, {alpha})'


def create_theme_selector() -> SankeyTheme:
    """Create theme selector widget and return SankeyTheme

    Returns:
        SankeyTheme instance
    """
    col1, col2 = st.columns([3, 1])

    with col2:
        theme_option = st.selectbox(
            "Chart Theme",
            options=['Auto', 'Light', 'Dark'],
            index=0,
            help="Select color theme for Sankey charts"
        )

    if theme_option == 'Auto':
        theme = SankeyTheme.detect_theme()
    else:
        theme = theme_option.lower()

    return SankeyTheme(theme)


def create_scale_selector() -> Tuple[str, bool]:
    """Create value scale and percentage selector widgets

    Returns:
        Tuple of (scale, show_percentage)
    """
    col1, col2 = st.columns(2)

    with col1:
        scale = st.selectbox(
            "Value Scale",
            options=['Billions ($B)', 'Millions ($M)', 'Actual ($)'],
            index=0,
            help="Select value display scale"
        )
        scale_map = {
            'Billions ($B)': 'B',
            'Millions ($M)': 'M',
            'Actual ($)': ''
        }
        scale_key = scale_map[scale]

    with col2:
        show_pct = st.checkbox(
            "Show Percentages",
            value=True,
            help="Display percentages in hover information"
        )

    return scale_key, show_pct
