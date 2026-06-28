import streamlit as st
import requests
import time

st.set_page_config(page_title="EPA System", layout="wide")

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 1

st.sidebar.title("EPA System")
st.sidebar.markdown("---")

# Navigation - now includes View Employees
page = st.sidebar.radio(
    "Navigation",
    ["Institution Setup", "Project Setup", "Employee Management", "View Employees", "Performance Prediction","Module 4 — Conflict & Teams"]
)

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

# Page routing
if page == "Institution Setup":
    from pages.institution_setup import institution_setup_page
    institution_setup_page()
elif page == "Project Setup":
    from pages.project_setup import project_setup_page
    project_setup_page()
elif page == "Employee Management":
    from pages.employee_management import employee_management_page
    employee_management_page()
elif page == "View Employees":
    from pages.view_employee import view_employee_page
    view_employee_page()
elif page == "Performance Prediction":
    from pages.performance_prediction import performance_prediction_page
    performance_prediction_page()
elif page == "Module 4 — Conflict & Teams":
    from pages.module4 import module4_page
    module4_page()