import streamlit as st

st.header("Customize input data used")
uploaded_file = st.file_uploader("Upload Custom Dataset")

st.markdown("#### Current Datasets")
