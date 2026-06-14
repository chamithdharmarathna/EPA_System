import streamlit as st
import requests
import time

st.set_page_config(page_title="EPA System", layout="wide")

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 1

st.sidebar.title("EPA System Setup Wizard")
st.sidebar.markdown("---")

# Show workflow progress
st.sidebar.subheader("Workflow Progress")
steps = ["1. Institution Setup", "2. Project Setup", "3. Employee Management"]

for i, step in enumerate(steps, 1):
    if i < st.session_state.step:
        st.sidebar.markdown(f"✅ {step}")
    elif i == st.session_state.step:
        st.sidebar.markdown(f"▶️ **{step}**")
    else:
        st.sidebar.markdown(f"⏸️ {step}")

st.sidebar.markdown("---")

# Check backend connection
def check_backend():
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if check_backend():
    st.sidebar.success("Backend Connected")
else:
    st.sidebar.error("Backend Not Running")
    st.error("Please start the backend server: python -m uvicorn backend.main:app --reload --port 8000")
    st.stop()

# Cache functions
@st.cache_data(ttl=5)
def get_institutions():
    try:
        response = requests.get("http://localhost:8000/api/institutions/", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=5)
def get_projects():
    try:
        response = requests.get("http://localhost:8000/api/projects/", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

# Workflow routing
if st.session_state.step == 1:
    from pages.institution_setup import institution_setup_page
    institution_setup_page()

    institutions = get_institutions()
    if institutions:
        if st.button("Proceed to Project Setup", type="primary"):
            st.session_state.step = 2
            st.cache_data.clear()
            st.rerun()

elif st.session_state.step == 2:
    from pages.project_setup import project_setup_page
    project_setup_page()

    projects = get_projects()
    if projects:
        if st.button("Proceed to Employee Management", type="primary"):
            st.session_state.step = 3
            st.cache_data.clear()
            st.rerun()

    if st.button("← Back to Institution Setup", type="secondary"):
        st.session_state.step = 1
        st.cache_data.clear()
        st.rerun()

elif st.session_state.step == 3:
    from pages.employee_management import employee_management_page
    employee_management_page()

    if st.button("← Back to Project Setup", type="secondary"):
        st.session_state.step = 2
        st.cache_data.clear()
        st.rerun()