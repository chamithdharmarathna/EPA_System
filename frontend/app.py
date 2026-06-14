import streamlit as st
import requests

st.set_page_config(page_title="EPA System", layout="wide")

# Initialize session state for workflow tracking
if "step" not in st.session_state:
    st.session_state.step = 1
if "selected_institution" not in st.session_state:
    st.session_state.selected_institution = None
if "institutions_loaded" not in st.session_state:
    st.session_state.institutions_loaded = False

st.sidebar.title("EPA System Setup Wizard")
st.sidebar.markdown("---")

# Show workflow progress
st.sidebar.subheader("Workflow Progress")
steps = [
    "1. Institution Setup",
    "2. Project Setup",
    "3. Employee Management"
]

for i, step in enumerate(steps, 1):
    if i < st.session_state.step:
        st.sidebar.markdown(f"✅ {step}")
    elif i == st.session_state.step:
        st.sidebar.markdown(f"▶️ **{step}**")
    else:
        st.sidebar.markdown(f"⏸️ {step}")

st.sidebar.markdown("---")

# Check backend connection
try:
    requests.get("http://localhost:8000/health", timeout=2)
    backend_status = "connected"
except:
    backend_status = "disconnected"

if backend_status == "connected":
    st.sidebar.success("Backend Connected")
else:
    st.sidebar.error("Backend Not Running")
    st.error("Please start the backend server first")
    st.stop()

# Workflow routing
if st.session_state.step == 1:
    from pages.institution_setup import institution_setup_page
    institution_setup_page()

    # Check if institutions exist
    response = requests.get("http://localhost:8000/api/institutions/")
    if response.status_code == 200:
        institutions = response.json()
        if institutions:
            st.session_state.institutions_loaded = True
            if st.button("Proceed to Project Setup", type="primary"):
                st.session_state.step = 2
                st.rerun()

elif st.session_state.step == 2:
    from pages.project_setup import project_setup_page
    project_setup_page()

    # Check if projects exist
    response = requests.get("http://localhost:8000/api/projects/")
    if response.status_code == 200:
        projects = response.json()
        if projects:
            if st.button("Proceed to Employee Management", type="primary"):
                st.session_state.step = 3
                st.rerun()

    # Allow going back
    if st.button("← Back to Institution Setup", type="secondary"):
        st.session_state.step = 1
        st.rerun()

elif st.session_state.step == 3:
    from pages.employee_management import employee_management_page
    employee_management_page()

    if st.button("← Back to Project Setup", type="secondary"):
        st.session_state.step = 2
        st.rerun()