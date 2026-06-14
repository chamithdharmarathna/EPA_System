import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

def project_setup_page():
    st.title("Project Setup")
    st.markdown("---")

    # First, ensure institutions exist
    response = requests.get(f"{API_URL}/api/institutions/")
    if response.status_code != 200:
        st.error("Cannot load institutions")
        return

    institutions = response.json()

    if not institutions:
        st.warning("No institutions found. Please setup institutions first.")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Add New Project")

        with st.form("add_project_form"):
            name = st.text_input("Project Name")
            institution = st.selectbox(
                "Select Institution",
                options=[(inst["institution_id"], inst["name"]) for inst in institutions],
                format_func=lambda x: f"{x[1]} ({x[0]})"
            )
            team_size = st.number_input("Team Size", min_value=1, max_value=50, value=5)
            relative_effort = st.number_input("Relative Effort", min_value=1.0, max_value=1000.0, value=100.0, step=10.0)
            duration_weeks = st.number_input("Duration (weeks)", min_value=1, max_value=52, value=12)

            # Show calculated complexity preview
            if team_size and duration_weeks and relative_effort:
                complexity_preview = relative_effort / (team_size * duration_weeks)
                st.info(f"📊 Project Complexity will be: {complexity_preview:.2f}")

            submitted = st.form_submit_button("Add Project")

            if submitted and name:
                try:
                    payload = {
                        "name": name,
                        "institution_id": institution[0],
                        "team_size": team_size,
                        "relative_effort": relative_effort,
                        "duration_weeks": duration_weeks
                    }
                    response = requests.post(
                        f"{API_URL}/api/projects/",
                        json=payload
                    )
                    if response.status_code == 201:
                        st.success(f"Project '{name}' added successfully")
                        st.rerun()
                    else:
                        error = response.json().get("detail", "Unknown error")
                        st.error(f"Failed: {error}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col2:
        st.subheader("Current Projects")

        try:
            response = requests.get(f"{API_URL}/api/projects/")
            if response.status_code == 200:
                projects = response.json()
                if projects:
                    # Display all projects with full details
                    for proj in projects:
                        with st.container():
                            st.markdown(f"**{proj['name']}** `{proj['project_id']}`")
                            st.write(f"🏢 Institution: {proj['institution_id']}")
                            st.write(f"👥 Team Size: {proj['team_size']}")
                            st.write(f"📈 Relative Effort: {proj.get('relative_effort', 'N/A')}")
                            st.write(f"⏱️ Duration: {proj['duration_weeks']} weeks")
                            st.write(f"⚡ Complexity: {proj.get('project_complexity', 'N/A')}")
                            st.markdown("---")

                    # Also show as dataframe for tabular view
                    st.subheader("Projects Summary Table")
                    df = pd.DataFrame(projects)
                    display_cols = ["project_id", "name", "institution_id", "team_size", "relative_effort", "duration_weeks", "project_complexity"]
                    df = df[[col for col in display_cols if col in df.columns]]
                    if "project_complexity" in df.columns:
                        df["project_complexity"] = df["project_complexity"].round(2)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    st.info(f"📊 Total Projects: {len(projects)}")

                    # Show complexity statistics
                    if "project_complexity" in df.columns and len(df) > 0:
                        st.subheader("Complexity Statistics")
                        col1_stat, col2_stat, col3_stat = st.columns(3)
                        with col1_stat:
                            st.metric("Average Complexity", f"{df['project_complexity'].mean():.2f}")
                        with col2_stat:
                            st.metric("Min Complexity", f"{df['project_complexity'].min():.2f}")
                        with col3_stat:
                            st.metric("Max Complexity", f"{df['project_complexity'].max():.2f}")
                else:
                    st.info("No projects yet")
        except Exception as e:
            st.error(f"Error loading projects: {str(e)}")

    st.markdown("---")
    with st.expander("Delete Project"):
        try:
            response = requests.get(f"{API_URL}/api/projects/")
            if response.status_code == 200:
                projects = response.json()
                if projects:
                    options = {f"{proj['name']} ({proj['project_id']})": proj['project_id'] for proj in projects}
                    selected = st.selectbox("Select project to delete", list(options.keys()))
                    if st.button("Delete Project"):
                        proj_id = options[selected]
                        delete_resp = requests.delete(f"{API_URL}/api/projects/{proj_id}")
                        if delete_resp.status_code == 204:
                            st.success("Project deleted successfully")
                            st.rerun()
                        else:
                            st.error("Delete failed")
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    project_setup_page()