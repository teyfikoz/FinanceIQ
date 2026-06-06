"""
Simple test to verify tabs work on Streamlit Cloud
"""
import streamlit as st

st.set_page_config(page_title="Tab Test", layout="wide")

st.title("🧪 Tab Rendering Test")

tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1:
    st.success("✅ Tab 1 is working!")
    st.write("If you see this, tabs are rendering correctly.")

with tab2:
    st.success("✅ Tab 2 is working!")
    st.write("This tab also works.")

with tab3:
    st.success("✅ Tab 3 is working!")
    st.write("All tabs work correctly.")

st.markdown("---")
st.info("If all 3 tabs show content, the problem is NOT with tabs themselves.")
