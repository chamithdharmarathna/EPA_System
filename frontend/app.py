import streamlit as st
import requests

st.set_page_config(page_title="EPA System", layout="wide")

st.sidebar.title("EPA System")
page = st.sidebar.radio("Navigation", ["Institution Setup", "Employees", "Dashboard", "Reports"])

try:
    requests.get("http://localhost:8000/health", timeout=2)
    st.sidebar.success("Backend Connected")
except:
    st.sidebar.error("Backend Not Running")

if page == "Institution Setup":
    from pages.institution_setup import institution_setup_page
    institution_setup_page()
else:
    st.header(page)
    st.info("Coming soon")