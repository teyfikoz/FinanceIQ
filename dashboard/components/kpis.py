"""
KPI Components Module
Reusable KPI card components for Streamlit dashboards.
"""

import streamlit as st
from typing import Optional, Union


def kpi(label: str,
        value: Union[str, float, int],
        delta: Optional[Union[str, float]] = None,
        help_text: Optional[str] = None,
        format_type: str = "number"):
    """
    Display a KPI metric card.

    Args:
        label: KPI label
        value: KPI value
        delta: Change value (YoY, MoM, etc.)
        help_text: Tooltip help text
        format_type: 'number', 'currency', 'percent'
    """
    # Format value
    if format_type == "currency" and isinstance(value, (int, float)):
        formatted_value = f"${value:,.0f}"
    elif format_type == "percent" and isinstance(value, (int, float)):
        formatted_value = f"{value:.2f}%"
    elif isinstance(value, float):
        formatted_value = f"{value:,.2f}"
    elif isinstance(value, int):
        formatted_value = f"{value:,}"
    else:
        formatted_value = str(value)

    # Format delta
    formatted_delta = None
    delta_color = "off"

    if delta is not None:
        if isinstance(delta, (int, float)):
            if delta > 0:
                formatted_delta = f"+{delta:.2f}%"
                delta_color = "normal"
            elif delta < 0:
                formatted_delta = f"{delta:.2f}%"
                delta_color = "inverse"
            else:
                formatted_delta = "0.00%"
        else:
            formatted_delta = str(delta)

    # Display metric
    st.metric(
        label=label,
        value=formatted_value,
        delta=formatted_delta,
        delta_color=delta_color,
        help=help_text
    )


def kpi_row(kpis_data: list, columns: Optional[int] = None):
    """
    Display a row of KPI metrics.

    Args:
        kpis_data: List of dicts with keys: label, value, delta, help, format_type
        columns: Number of columns (default: auto based on kpis count)
    """
    if not kpis_data:
        return

    num_kpis = len(kpis_data)
    num_cols = columns or min(num_kpis, 5)

    cols = st.columns(num_cols)

    for i, kpi_data in enumerate(kpis_data):
        with cols[i % num_cols]:
            kpi(
                label=kpi_data.get('label', 'N/A'),
                value=kpi_data.get('value', 'N/A'),
                delta=kpi_data.get('delta'),
                help_text=kpi_data.get('help'),
                format_type=kpi_data.get('format_type', 'number')
            )


def styled_kpi_card(label: str,
                     value: str,
                     subtitle: Optional[str] = None,
                     color: str = "#2563EB"):
    """
    Display a styled KPI card with custom HTML/CSS.

    Args:
        label: KPI label
        value: KPI value (pre-formatted)
        subtitle: Optional subtitle text
        color: Accent color (hex)
    """
    subtitle_html = f'<p style="margin: 0; font-size: 14px; color: #6B7280;">{subtitle}</p>' if subtitle else ''

    card_html = f"""
    <div style="
        background: white;
        border: 1px solid #E5E7EB;
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    ">
        <p style="margin: 0; font-size: 12px; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px;">
            {label}
        </p>
        <p style="margin: 8px 0 4px 0; font-size: 28px; font-weight: 700; color: #1F2937;">
            {value}
        </p>
        {subtitle_html}
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def metrics_table(data: dict, title: Optional[str] = None):
    """
    Display metrics in a clean table format.

    Args:
        data: Dict of metric_name → value
        title: Optional table title
    """
    if title:
        st.subheader(title)

    table_html = """
    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
    """

    for key, value in data.items():
        table_html += f"""
        <tr style="border-bottom: 1px solid #E5E7EB;">
            <td style="padding: 12px 8px; color: #6B7280; font-weight: 500;">{key}</td>
            <td style="padding: 12px 8px; text-align: right; color: #1F2937; font-weight: 600;">{value}</td>
        </tr>
        """

    table_html += "</table>"

    st.markdown(table_html, unsafe_allow_html=True)
