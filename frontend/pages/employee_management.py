import streamlit as st

def employee_management_page():
    st.title("Employee Management")
    st.markdown("---")

    st.info("Employee management will be implemented after project setup is complete")

    # Display selected institution and projects
    st.subheader("Selected Context")

    # Get institutions
    import requests
    response = requests.get("http://localhost:8000/api/institutions/")
    if response.status_code == 200:
        institutions = response.json()
        inst_options = {inst["name"]: inst["institution_id"] for inst in institutions}
        selected_inst = st.selectbox("Select Institution", list(inst_options.keys()))

        if selected_inst:
            inst_id = inst_options[selected_inst]
            # Get projects for this institution
            proj_response = requests.get(f"http://localhost:8000/api/projects/")
            if proj_response.status_code == 200:
                all_projects = proj_response.json()
                inst_projects = [p for p in all_projects if p["institution_id"] == inst_id]
                if inst_projects:
                    st.write(f"Projects for {selected_inst}:")
                    for proj in inst_projects:
                        st.write(f"- {proj['name']} (Team Size: {proj['team_size']})")
                else:
                    st.warning("No projects found for this institution")

if __name__ == "__main__":
    employee_management_page()