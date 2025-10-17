"""
Export Utilities Module
Provides export functionality for charts and data.
"""

import io
import base64
from typing import Optional
import plotly.graph_objects as go
import pandas as pd


def export_chart_to_image(fig: go.Figure,
                          format: str = "png",
                          width: int = 1200,
                          height: int = 800,
                          scale: int = 2) -> bytes:
    """
    Export Plotly figure to image bytes.

    Args:
        fig: Plotly figure
        format: 'png', 'jpeg', or 'svg'
        width: Image width in pixels
        height: Image height in pixels
        scale: Scale factor for resolution

    Returns:
        Image bytes
    """
    try:
        img_bytes = fig.to_image(
            format=format,
            width=width,
            height=height,
            scale=scale
        )
        return img_bytes
    except Exception as e:
        raise RuntimeError(f"Failed to export chart: {e}")


def get_download_link(data: bytes,
                      filename: str,
                      mime_type: str,
                      link_text: str = "Download") -> str:
    """
    Generate HTML download link for data.

    Args:
        data: Binary data
        filename: Download filename
        mime_type: MIME type (e.g., 'image/png', 'text/csv')
        link_text: Link display text

    Returns:
        HTML download link
    """
    b64 = base64.b64encode(data).decode()

    html = f'''
    <a href="data:{mime_type};base64,{b64}"
       download="{filename}"
       style="
           display: inline-block;
           padding: 8px 16px;
           background-color: #2563EB;
           color: white;
           text-decoration: none;
           border-radius: 6px;
           font-weight: 500;
           font-size: 14px;
           margin: 4px;
       ">
        📥 {link_text}
    </a>
    '''

    return html


def export_dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to CSV bytes.

    Args:
        df: DataFrame to export

    Returns:
        CSV bytes
    """
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode('utf-8')


def export_dataframe_to_excel(df: pd.DataFrame) -> bytes:
    """
    Export DataFrame to Excel bytes.

    Args:
        df: DataFrame to export

    Returns:
        Excel bytes
    """
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    return excel_buffer.read()


def _sanitize_filename(name: str) -> str:
    """
    Sanitize filename by removing/replacing unsafe characters.

    Args:
        name: Original filename

    Returns:
        Safe filename
    """
    import re
    # Remove unsafe characters
    safe = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces with underscores
    safe = re.sub(r'[\s]+', '_', safe)
    # Trim to reasonable length
    return safe[:100].lower()


def create_export_section(fig: go.Figure,
                          df: Optional[pd.DataFrame] = None,
                          base_name: str = "chart"):
    """
    Create export section with download buttons (for Streamlit).
    Provides PNG, HTML, and CSV exports with safety guards.

    Args:
        fig: Plotly figure to export
        df: Optional DataFrame to export
        base_name: Base name for exported files (will be sanitized)
    """
    import streamlit as st

    # Sanitize filename
    safe_name = _sanitize_filename(base_name)

    st.markdown("### 📥 Export Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        # PNG Export (with fallback to HTML if Kaleido missing)
        try:
            png_bytes = export_chart_to_image(fig, format='png', width=1400, height=900, scale=2)
            st.download_button(
                label="📊 Download PNG",
                data=png_bytes,
                file_name=f"{safe_name}.png",
                mime="image/png",
                help="Download chart as PNG image (high resolution)"
            )
        except Exception as e:
            # Fallback: show HTML export instead
            st.caption("⚠️ PNG export unavailable (install kaleido)")
            html_str = fig.to_html(include_plotlyjs='cdn')
            st.download_button(
                label="🌐 Download HTML",
                data=html_str.encode('utf-8'),
                file_name=f"{safe_name}_fallback.html",
                mime="text/html",
                help="Interactive HTML (PNG unavailable)"
            )

    with col2:
        # HTML Export
        html_str = fig.to_html(include_plotlyjs='cdn')
        st.download_button(
            label="🌐 Download HTML",
            data=html_str.encode('utf-8'),
            file_name=f"{safe_name}.html",
            mime="text/html",
            help="Download interactive HTML chart"
        )

    with col3:
        # CSV Export with size guard
        if df is not None and not df.empty:
            # Warn if DataFrame is very large
            row_count = len(df)
            if row_count > 250000:
                st.warning(f"⚠️ Large dataset ({row_count:,} rows). Export may be slow.")

            csv_bytes = export_dataframe_to_csv(df)
            st.download_button(
                label="📄 Download CSV",
                data=csv_bytes,
                file_name=f"{safe_name}_data.csv",
                mime="text/csv",
                help=f"Download underlying data as CSV ({row_count:,} rows)"
            )
        else:
            st.caption("No data available for CSV export")
