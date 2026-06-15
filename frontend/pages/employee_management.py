import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import json

API_URL = "http://localhost:8000"

def employee_management_page():
    st.title("Employee Management")
    st.markdown("---")

    # Check if institutions and projects exist
    inst_response = requests.get(f"{API_URL}/api/institutions/")
    if inst_response.status_code != 200 or len(inst_response.json()) == 0:
        st.warning("Please setup institutions first")
        return

    proj_response = requests.get(f"{API_URL}/api/projects/")
    if proj_response.status_code != 200 or len(proj_response.json()) == 0:
        st.warning("Please setup projects first")
        return

    # Phase selection
    phase = st.radio(
        "Select Phase",
        ["Phase 1: Demographics", "Phase 2: KPI Indicators", "Phase 3: Behavioral Appraisal"],
        horizontal=True
    )

    st.markdown("---")

    # Get existing employees for dropdown
    try:
        emp_response = requests.get(f"{API_URL}/api/employees/")
        existing_employees = emp_response.json() if emp_response.status_code == 200 else []
    except:
        existing_employees = []

    if phase == "Phase 1: Demographics":
        phase1_demographics(existing_employees)
    elif phase == "Phase 2: KPI Indicators":
        phase2_kpi(existing_employees)
    else:
        phase3_behavioral(existing_employees)

def phase1_demographics(existing_employees):
    st.subheader("Phase 1: Employee Demographics")

    col1, col2 = st.columns(2)

    with col1:
        with st.form("demographics_form"):
            st.write("### Basic Information")

            # Institution and Project
            institutions = get_institutions()
            institution_id = st.selectbox(
                "Institution *",
                options=institutions,
                format_func=lambda x: f"{x['name']} ({x['institution_id']})"
            )

            projects = get_projects_by_institution(institution_id['institution_id'] if institution_id else None)
            project_id = st.selectbox(
                "Project *",
                options=projects,
                format_func=lambda x: f"{x['name']} ({x['project_id']})"
            )

            # Job Role
            job_role_id = st.selectbox(
                "Job Role *",
                ["PM", "SE", "QA", "DevOps", "BA", "UI/UX", "Support", "Admin", "Manager"]
            )

            # Demographics
            dob = st.date_input(
                "Date of Birth *",
                min_value=date(1960, 1, 1),
                max_value=date(2005, 12, 31),
                value=date(1990, 1, 1)
            )

            gender = st.selectbox("Gender *", ["M", "F", "Other"])

            years_of_experience = st.number_input("Years of Experience *", min_value=0, max_value=50, value=5)

            # Department (auto-filled based on role)
            department = get_department_from_role(job_role_id)
            st.text_input("Department", value=department, disabled=True)

            st.write("### Additional Information")

            primary_language = st.selectbox("Primary Language", ["English", "Sinhala", "Tamil", "Other"])

            ethnicity = st.selectbox("Ethnicity", ["Sinhalese", "Tamil", "Moor", "Burgher", "Malay", "Other"])

            # Educational Institutes as multi-select
            edu_options = [
                "University of Colombo", "University of Moratuwa", "University of Peradeniya",
                "University of Kelaniya", "University of Sri Jayewardenepura", "University of Ruhuna",
                "Nalanda College", "Royal College", "Ananda College", "Visakha Vidyalaya",
                "Holy Family Convent", "St. John's College", "DS Senanayake College",
                "Jaffna Hindu College", "Musaeus College"
            ]
            attended_educational_institutes = st.multiselect(
                "Attended Educational Institutes",
                options=edu_options
            )

            submitted = st.form_submit_button("Save Demographics", type="primary")

            if submitted:
                if not institution_id or not project_id:
                    st.error("Please select institution and project")
                else:
                    employee_data = {
                        "institution_id": institution_id['institution_id'],
                        "project_id": project_id['project_id'],
                        "job_role_id": job_role_id,
                        "dob": dob.strftime("%Y-%m-%d"),
                        "gender": gender,
                        "years_of_experience": years_of_experience,
                        "department": department,
                        "primary_language": primary_language if primary_language != "Other" else None,
                        "ethnicity": ethnicity if ethnicity != "Other" else None,
                        "attended_educational_institutes": attended_educational_institutes if attended_educational_institutes else None
                    }

                    try:
                        response = requests.post(
                            f"{API_URL}/api/employees/",
                            json=employee_data
                        )
                        if response.status_code == 201:
                            emp_data = response.json()
                            st.success(f"Employee added successfully! ID: {emp_data['employee_id']}")
                            st.rerun()
                        else:
                            error = response.json().get("detail", "Unknown error")
                            st.error(f"Failed: {error}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with col2:
        st.subheader("Existing Employees")

        try:
            response = requests.get(f"{API_URL}/api/employees/")
            if response.status_code == 200:
                employees = response.json()
                if employees:
                    df = pd.DataFrame(employees)
                    display_cols = ["employee_id", "institution_id", "project_id", "job_role_id", "gender", "years_of_experience", "department"]
                    df = df[[col for col in display_cols if col in df.columns]]
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Show stats
                    st.info(f"Total Employees: {len(employees)}")

                    # Role distribution
                    if "job_role_id" in df.columns:
                        st.write("**Role Distribution:**")
                        role_counts = df["job_role_id"].value_counts()
                        for role, count in role_counts.items():
                            st.write(f"- {role}: {count}")
                else:
                    st.info("No employees added yet")
        except Exception as e:
            st.error(f"Error loading employees: {str(e)}")

def phase2_kpi(existing_employees):
    st.subheader("Phase 2: KPI Indicators")
    st.write("Key Performance Indicators for employee evaluation")

    if not existing_employees:
        st.warning("No employees found. Please complete Phase 1 first.")
        return

    # Select employee
    employee_options = {emp['employee_id']: f"{emp['employee_id']} - {emp.get('job_role_id', 'N/A')} - {emp.get('department', 'N/A')}"
                        for emp in existing_employees}
    selected_employee = st.selectbox("Select Employee", list(employee_options.keys()), format_func=lambda x: employee_options[x])

    if selected_employee:
        # Check if KPIs already exist
        try:
            kpi_response = requests.get(f"{API_URL}/api/employees/kpi/{selected_employee}")
            existing_kpi = kpi_response.json() if kpi_response.status_code == 200 else None
        except:
            existing_kpi = None

        if existing_kpi:
            st.info(f"Updating existing KPI records for {selected_employee}")

        with st.form("kpi_form"):
            st.write("### Task Performance Metrics")

            col1, col2, col3 = st.columns(3)

            # Get default values
            default_tasks_assigned = existing_kpi.get('tasks_assigned', 0) if existing_kpi else 0
            default_tasks_completed = existing_kpi.get('tasks_completed', 0) if existing_kpi else 0
            default_tasks_on_time = existing_kpi.get('tasks_on_time', 0) if existing_kpi else 0
            default_defect_count = existing_kpi.get('defect_count', 0) if existing_kpi else 0
            default_issue_rate = existing_kpi.get('issue_resolution_rate', 0.95) if existing_kpi else 0.95
            default_quality_score = existing_kpi.get('quality_score', 7.0) if existing_kpi else 7.0
            default_rework_count = existing_kpi.get('rework_count', 0) if existing_kpi else 0
            default_blockers_count = existing_kpi.get('blockers_count', 0) if existing_kpi else 0

            with col1:
                tasks_assigned = st.number_input(
                    "Tasks Assigned",
                    min_value=0,
                    max_value=500,
                    value=default_tasks_assigned,
                    step=1,
                    key="tasks_assigned_input"
                )

                tasks_completed = st.number_input(
                    "Tasks Completed",
                    min_value=0,
                    max_value=500,
                    value=default_tasks_completed,
                    step=1,
                    key="tasks_completed_input"
                )

                if tasks_assigned > 0:
                    task_completion_rate = tasks_completed / tasks_assigned
                    st.metric("Task Completion Rate", f"{task_completion_rate:.2%}")
                else:
                    task_completion_rate = 0
                    st.metric("Task Completion Rate", "N/A")

                tasks_on_time = st.number_input(
                    "Tasks Completed On Time",
                    min_value=0,
                    max_value=500,
                    value=default_tasks_on_time,
                    step=1,
                    key="tasks_on_time_input"
                )

                if tasks_assigned > 0:
                    on_time_delivery_rate = tasks_on_time / tasks_assigned
                    st.metric("On-Time Delivery Rate", f"{on_time_delivery_rate:.2%}")
                else:
                    on_time_delivery_rate = 0
                    st.metric("On-Time Delivery Rate", "N/A")

            with col2:
                defect_count = st.number_input(
                    "Defect Count",
                    min_value=0,
                    max_value=200,
                    value=default_defect_count,
                    step=1,
                    key="defect_count_input"
                )

                issue_resolution_rate = st.slider(
                    "Issue Resolution Rate",
                    min_value=0.0,
                    max_value=1.0,
                    value=default_issue_rate,
                    step=0.01,
                    format="%.2f",
                    key="issue_rate_slider"
                )

                quality_score = st.slider(
                    "Quality Score",
                    min_value=0.0,
                    max_value=10.0,
                    value=default_quality_score,
                    step=0.1,
                    key="quality_score_slider"
                )

            with col3:
                rework_count = st.number_input(
                    "Rework Count",
                    min_value=0,
                    max_value=50,
                    value=default_rework_count,
                    step=1,
                    key="rework_count_input"
                )

                blockers_count = st.number_input(
                    "Blockers Count",
                    min_value=0,
                    max_value=50,
                    value=default_blockers_count,
                    step=1,
                    key="blockers_count_input"
                )

            st.write("### Performance Summary")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if tasks_assigned > 0:
                    st.metric("Completion Rate", f"{task_completion_rate:.1%}")
                else:
                    st.metric("Completion Rate", "N/A")
            with col_b:
                st.metric("Quality Score", f"{quality_score:.1f}/10")
            with col_c:
                st.metric("Defects", defect_count)

            submitted = st.form_submit_button("Save KPI Indicators", type="primary")

            if submitted:
                kpi_data = {
                    "employee_id": selected_employee,
                    "tasks_assigned": tasks_assigned,
                    "tasks_completed": tasks_completed,
                    "task_completion_rate": round(task_completion_rate, 2),
                    "tasks_on_time": tasks_on_time,
                    "on_time_delivery_rate": round(on_time_delivery_rate, 2),
                    "defect_count": defect_count,
                    "issue_resolution_rate": issue_resolution_rate,
                    "quality_score": quality_score,
                    "rework_count": rework_count,
                    "blockers_count": blockers_count
                }

                try:
                    response = requests.post(f"{API_URL}/api/employees/kpi/", json=kpi_data)
                    if response.status_code == 201:
                        st.success("KPI indicators saved successfully!")
                    else:
                        error_msg = response.json().get("detail", "Unknown error")
                        st.error(f"Failed to save KPI: {error_msg}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def phase3_behavioral(existing_employees):
    st.subheader("Phase 3: Behavioral Self-Appraisal")
    st.write("Rate yourself on behavioral competencies (1-5 scale)")

    if not existing_employees:
        st.warning("No employees found. Please complete Phase 1 first.")
        return

    # Select employee
    employee_options = {emp['employee_id']: f"{emp['employee_id']} - {emp.get('job_role_id', 'N/A')}"
                        for emp in existing_employees}
    selected_employee = st.selectbox("Select Employee", list(employee_options.keys()), format_func=lambda x: employee_options[x])

    if selected_employee:
        # Check if behavioral data already exists
        try:
            behavior_response = requests.get(f"{API_URL}/api/employees/behavior/{selected_employee}")
            existing_behavior = behavior_response.json() if behavior_response.status_code == 200 else None
        except:
            existing_behavior = None

        if existing_behavior:
            st.info(f"Updating existing behavioral record for {selected_employee}")

        # Create form
        with st.form(key="behavioral_form"):
            st.write("### Behavioral Competencies")
            st.caption("1 = Poor | 2 = Below Average | 3 = Average | 4 = Good | 5 = Excellent")

            col1, col2 = st.columns(2)

            with col1:
                st.write("#### Core Competencies")

                punctuality = st.select_slider(
                    "Punctuality",
                    options=[1, 2, 3, 4, 5],
                    value=existing_behavior.get('punctuality', 3) if existing_behavior else 3,
                    key="punctuality_slider"
                )

                problem_solving = st.select_slider(
                    "Problem Solving",
                    options=[1, 2, 3, 4, 5],
                    value=existing_behavior.get('problem_solving', 3) if existing_behavior else 3,
                    key="problem_solving_slider"
                )

                leadership = st.select_slider(
                    "Leadership",
                    options=[1, 2, 3, 4, 5],
                    value=existing_behavior.get('leadership', 3) if existing_behavior else 3,
                    key="leadership_slider"
                )

                collaboration = st.select_slider(
                    "Collaboration",
                    options=[1, 2, 3, 4, 5],
                    value=existing_behavior.get('collaboration', 3) if existing_behavior else 3,
                    key="collaboration_slider"
                )

                communication = st.select_slider(
                    "Communication",
                    options=[1, 2, 3, 4, 5],
                    value=existing_behavior.get('communication', 3) if existing_behavior else 3,
                    key="communication_slider"
                )

            with col2:
                st.write("#### Work Habits")

                # Number inputs - all using integers
                no_nopay_leave = st.number_input(
                    "Number of Non-Pay Leaves",
                    min_value=0,
                    max_value=50,
                    value=int(existing_behavior.get('no_nopay_leave', 0)) if existing_behavior else 0,
                    step=1,
                    key="no_nopay_leave_input"
                )

                # Use int for response time (store as int, convert to float later if needed)
                avg_response_time = st.number_input(
                    "Average Response Time (minutes)",
                    min_value=0,
                    max_value=120,
                    value=int(existing_behavior.get('avg_response_time', 30)) if existing_behavior else 30,
                    step=1,
                    key="avg_response_time_input"
                )

                meetings_attended = st.number_input(
                    "Meetings Attended (per month)",
                    min_value=0,
                    max_value=50,
                    value=int(existing_behavior.get('meetings_attended', 15)) if existing_behavior else 15,
                    step=1,
                    key="meetings_attended_input"
                )

                learning_hours = st.number_input(
                    "Learning Hours (per month)",
                    min_value=0,
                    max_value=50,
                    value=int(existing_behavior.get('learning_hours', 5)) if existing_behavior else 5,
                    step=1,
                    key="learning_hours_input"
                )

                team_interaction_frequency = st.select_slider(
                    "Team Interaction Frequency",
                    options=[1, 2, 3, 4, 5],
                    value=existing_behavior.get('team_interaction_frequency', 3) if existing_behavior else 3,
                    key="team_interaction_slider"
                )

            # Calculate scores
            total_competency = punctuality + problem_solving + leadership + collaboration + communication
            avg_competency = total_competency / 5

            st.write("### Summary")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Avg Competency Score", f"{avg_competency:.1f}/5")
            with col_b:
                st.metric("Meetings/Month", meetings_attended)
            with col_c:
                st.metric("Learning Hours", learning_hours)

            # Submit button - MUST be inside the form
            submitted = st.form_submit_button("Save Behavioral Appraisal", type="primary", use_container_width=True)

            if submitted:
                behavior_data = {
                    "employee_id": selected_employee,
                    "punctuality": punctuality,
                    "problem_solving": problem_solving,
                    "leadership": leadership,
                    "collaboration": collaboration,
                    "communication": communication,
                    "no_nopay_leave": no_nopay_leave,
                    "avg_response_time": float(avg_response_time),
                    "meetings_attended": meetings_attended,
                    "learning_hours": float(learning_hours),
                    "team_interaction_frequency": team_interaction_frequency
                }

                try:
                    response = requests.post(f"{API_URL}/api/employees/behavior/", json=behavior_data)
                    if response.status_code == 201:
                        st.success("Behavioral appraisal saved successfully!")

                        # Show rating interpretation
                        if avg_competency >= 4.5:
                            st.balloons()
                            st.success("Excellent! Outstanding performance!")
                        elif avg_competency >= 3.5:
                            st.success("Good performance! Keep it up!")
                        elif avg_competency >= 2.5:
                            st.info("Satisfactory - Room for improvement")
                        else:
                            st.warning("Needs significant improvement")
                    else:
                        error_msg = response.json().get("detail", "Unknown error") if response.text else "Unknown error"
                        st.error(f"Failed to save: {error_msg}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
def get_institutions():
    try:
        response = requests.get(f"{API_URL}/api/institutions/")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def get_projects_by_institution(institution_id):
    if not institution_id:
        return []
    try:
        response = requests.get(f"{API_URL}/api/projects/?institution_id={institution_id}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def get_department_from_role(job_role):
    departments = {
        "PM": "Management",
        "SE": "Engineering",
        "QA": "Quality Assurance",
        "DevOps": "Operations",
        "BA": "Business Analysis",
        "UI/UX": "Design",
        "Support": "Customer Support",
        "Admin": "Administration",
        "Manager": "Management"
    }
    return departments.get(job_role, "Other")

if __name__ == "__main__":
    employee_management_page()