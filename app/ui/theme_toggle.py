"""
Theme Toggle - Dark/Light Mode
Custom Streamlit theming without config.toml modifications
"""

import streamlit as st


def apply_theme(theme="dark"):
    """
    Apply custom dark or light theme using CSS
    Theme persists in session state
    """

    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = theme

    current_theme = st.session_state.theme

    if current_theme == "dark":
        css = """
        <style>
            :root {
                --bg-color: #0e1117;
                --secondary-bg: #1e2130;
                --text-color: #fafafa;
                --border-color: #2e3247;
                --accent-color: #667eea;
            }

            .stApp {
                background-color: var(--bg-color);
                color: var(--text-color);
            }

            .main .block-container {
                background-color: var(--bg-color);
            }

            .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
                color: var(--text-color) !important;
            }

            .stMetric {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white !important;
            }

            .stMetric label, .stMetric div {
                color: white !important;
            }

            .stButton>button {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-weight: 600;
                transition: all 0.3s ease;
            }

            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }

            .stDataFrame, .stTable {
                background-color: var(--secondary-bg);
                border-radius: 10px;
                border: 1px solid var(--border-color);
            }

            .sidebar .sidebar-content {
                background-color: var(--secondary-bg);
            }

            /* Tabs styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
                border-radius: 10px;
                padding: 0.5rem;
            }

            .stTabs [data-baseweb="tab"] {
                background: rgba(255,255,255,0.1);
                border-radius: 6px;
                color: white;
                font-weight: 600;
            }

            .stTabs [aria-selected="true"] {
                background: rgba(255,255,255,0.3) !important;
            }
        </style>
        """
    else:  # Light theme
        css = """
        <style>
            :root {
                --bg-color: #ffffff;
                --secondary-bg: #f0f2f6;
                --text-color: #262730;
                --border-color: #d4d4d8;
                --accent-color: #667eea;
            }

            .stApp {
                background-color: var(--bg-color);
                color: var(--text-color);
            }

            .main .block-container {
                background-color: var(--bg-color);
            }

            .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {
                color: var(--text-color) !important;
            }

            .stMetric {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white !important;
            }

            .stMetric label, .stMetric div {
                color: white !important;
            }

            .stButton>button {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-weight: 600;
                transition: all 0.3s ease;
            }

            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }

            .stDataFrame, .stTable {
                background-color: var(--secondary-bg);
                border-radius: 10px;
                border: 1px solid var(--border-color);
            }

            .sidebar .sidebar-content {
                background-color: var(--secondary-bg);
            }

            /* Tabs styling */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                padding: 0.5rem;
            }

            .stTabs [data-baseweb="tab"] {
                background: rgba(255,255,255,0.3);
                border-radius: 6px;
                color: white;
                font-weight: 600;
            }

            .stTabs [aria-selected="true"] {
                background: rgba(255,255,255,0.5) !important;
            }
        </style>
        """

    st.markdown(css, unsafe_allow_html=True)


def create_theme_toggle():
    """Create theme toggle button in sidebar"""

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🌓 Theme")

        current_theme = st.session_state.get('theme', 'dark')

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🌙 Dark", use_container_width=True,
                        type="primary" if current_theme == "dark" else "secondary"):
                st.session_state.theme = "dark"
                st.rerun()

        with col2:
            if st.button("☀️ Light", use_container_width=True,
                        type="primary" if current_theme == "light" else "secondary"):
                st.session_state.theme = "light"
                st.rerun()


if __name__ == "__main__":
    st.title("Theme Toggle Demo")

    apply_theme()
    create_theme_toggle()

    st.markdown("### Sample Content")
    st.write("This is sample text to demonstrate the theme.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Value", "$100,000", delta="+5.2%")
    with col2:
        st.metric("Return", "15.3%", delta="+2.1%")
    with col3:
        st.metric("Sharpe Ratio", "1.85", delta="+0.3")

    st.button("Sample Button")

    st.dataframe({
        'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'Price': [178.50, 378.91, 140.22],
        'Change': ['+2.3%', '-0.8%', '+1.5%']
    })
