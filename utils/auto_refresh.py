"""Auto-refresh component for real-time updates"""
import streamlit.components.v1 as components

def add_auto_refresh(interval_seconds=30):
    """Add auto-refresh to Streamlit app

    Args:
        interval_seconds: Refresh interval in seconds
    """
    components.html(
        f"""
        <script>
            setTimeout(function(){{
                window.parent.location.reload();
            }}, {interval_seconds * 1000});
        </script>
        """,
        height=0
    )
