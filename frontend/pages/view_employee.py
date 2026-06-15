import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "http://localhost:8000"

def view_employee_page():
    st.title("View Employees")
    st.markdown("---")

    # Fetch all data
    try:
        # Get employees
        emp_response = requests.get(f"{API_URL}/api/employees/")
        if emp_response.status_code != 200:
            st.error("Failed to fetch employees")
            return

        employees = emp_response.json()

        if not employees:
            st.info("No employees found. Please add employees first.")
            return

        # Get KPI data for all employees
        kpi_data = {}
        for emp in employees:
            try:
                kpi_response = requests.get(f"{API_URL}/api/employees/kpi/{emp['employee_id']}")
                if kpi_response.status_code == 200:
                    kpi_data[emp['employee_id']] = kpi_response.json()
            except:
                pass

        # Get Behavior data for all employees
        behavior_data = {}
        for emp in employees:
            try:
                behavior_response = requests.get(f"{API_URL}/api/employees/behavior/{emp['employee_id']}")
                if behavior_response.status_code == 200:
                    behavior_data[emp['employee_id']] = behavior_response.json()
            except:
                pass

        # Get institutions and projects for reference
        inst_response = requests.get(f"{API_URL}/api/institutions/")
        institutions = {inst['institution_id']: inst['name'] for inst in inst_response.json()} if inst_response.status_code == 200 else {}

        proj_response = requests.get(f"{API_URL}/api/projects/")
        projects = {proj['project_id']: proj['name'] for proj in proj_response.json()} if proj_response.status_code == 200 else {}

        # Build combined dataframe
        combined_data = []

        for emp in employees:
            emp_id = emp['employee_id']
            kpi = kpi_data.get(emp_id, {})
            behavior = behavior_data.get(emp_id, {})

            # Calculate derived metrics
            task_completion_rate = kpi.get('task_completion_rate', 0)
            on_time_rate = kpi.get('on_time_delivery_rate', 0)

            # Competency scores
            competency_scores = [
                behavior.get('punctuality', 0),
                behavior.get('problem_solving', 0),
                behavior.get('leadership', 0),
                behavior.get('collaboration', 0),
                behavior.get('communication', 0)
            ]
            avg_competency = sum(competency_scores) / 5 if competency_scores else 0

            # Overall performance score (weighted average)
            # KPI contributes 60%, Behavior contributes 40%
            kpi_score = (task_completion_rate * 0.3 + on_time_rate * 0.3 +
                         (kpi.get('quality_score', 0) / 10) * 0.2 +
                         (1 - min(kpi.get('defect_count', 0) / 50, 1)) * 0.2)
            behavior_score = avg_competency / 5
            overall_score = (kpi_score * 0.6 + behavior_score * 0.4) * 100

            # Determine rating
            if overall_score >= 90:
                rating = "Excellent"
                rating_color = "green"
            elif overall_score >= 75:
                rating = "Good"
                rating_color = "blue"
            elif overall_score >= 60:
                rating = "Satisfactory"
                rating_color = "orange"
            else:
                rating = "Needs Improvement"
                rating_color = "red"

            row = {
                "Employee ID": emp_id,
                "Institution": institutions.get(emp.get('institution_id', ''), emp.get('institution_id', '')),
                "Project": projects.get(emp.get('project_id', ''), emp.get('project_id', '')),
                "Job Role": emp.get('job_role_id', ''),
                "Department": emp.get('department', ''),
                "Gender": emp.get('gender', ''),
                "Experience (Years)": emp.get('years_of_experience', 0),
                "Primary Language": emp.get('primary_language', ''),
                "Ethnicity": emp.get('ethnicity', ''),

                # KPI Metrics
                "Tasks Assigned": kpi.get('tasks_assigned', 0),
                "Tasks Completed": kpi.get('tasks_completed', 0),
                "Task Completion %": f"{task_completion_rate * 100:.1f}%" if task_completion_rate else "0%",
                "Tasks On Time": kpi.get('tasks_on_time', 0),
                "On-Time Delivery %": f"{on_time_rate * 100:.1f}%" if on_time_rate else "0%",
                "Defect Count": kpi.get('defect_count', 0),
                "Issue Resolution %": f"{kpi.get('issue_resolution_rate', 0) * 100:.1f}%" if kpi.get('issue_resolution_rate') else "0%",
                "Quality Score": f"{kpi.get('quality_score', 0):.1f}/10",
                "Rework Count": kpi.get('rework_count', 0),
                "Blockers Count": kpi.get('blockers_count', 0),

                # Behavioral Metrics
                "Punctuality (1-5)": behavior.get('punctuality', 0),
                "Problem Solving (1-5)": behavior.get('problem_solving', 0),
                "Leadership (1-5)": behavior.get('leadership', 0),
                "Collaboration (1-5)": behavior.get('collaboration', 0),
                "Communication (1-5)": behavior.get('communication', 0),
                "Avg Competency Score": f"{avg_competency:.1f}/5",
                "Non-Pay Leaves": behavior.get('no_nopay_leave', 0),
                "Avg Response Time": f"{behavior.get('avg_response_time', 0):.0f} min",
                "Meetings/Month": behavior.get('meetings_attended', 0),
                "Learning Hours/Month": behavior.get('learning_hours', 0),
                "Team Interaction": behavior.get('team_interaction_frequency', 0),

                # Overall Performance
                "Overall Score": f"{overall_score:.1f}%",
                "Rating": rating
            }
            combined_data.append(row)

        # Create DataFrame
        df = pd.DataFrame(combined_data)

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary View", "📋 Detailed View", "📈 Performance Analytics", "📥 Export Data"])

        with tab1:
            st.subheader("Employee Summary")

            # Summary statistics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Employees", len(employees))
            with col2:
                avg_score = df['Overall Score'].str.rstrip('%').astype(float).mean() if len(df) > 0 else 0
                st.metric("Avg Performance Score", f"{avg_score:.1f}%")
            with col3:
                excellent_count = df[df['Rating'] == 'Excellent'].shape[0]
                st.metric("Excellent Performers", excellent_count)
            with col4:
                total_tasks = df['Tasks Assigned'].sum()
                st.metric("Total Tasks Assigned", total_tasks)
            with col5:
                total_defects = df['Defect Count'].sum()
                st.metric("Total Defects", total_defects)

            st.markdown("---")

            # Display summary table (key columns only)
            summary_cols = ["Employee ID", "Institution", "Project", "Job Role", "Task Completion %",
                            "On-Time Delivery %", "Quality Score", "Avg Competency Score", "Overall Score", "Rating"]
            summary_df = df[summary_cols]
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("Complete Employee Details")
            st.info("Scroll horizontally to view all 40+ columns")

            # Format for better display
            display_df = df.copy()

            # Highlight ratings
            def highlight_rating(val):
                if val == "Excellent":
                    return 'background-color: #90EE90'
                elif val == "Good":
                    return 'background-color: #ADD8E6'
                elif val == "Satisfactory":
                    return 'background-color: #FFE4B5'
                elif val == "Needs Improvement":
                    return 'background-color: #FFB6C1'
                return ''

            styled_df = display_df.style.applymap(highlight_rating, subset=['Rating'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

        with tab3:
            st.subheader("Performance Analytics")

            col1, col2 = st.columns(2)

            with col1:
                # Rating distribution
                st.write("**Performance Rating Distribution**")
                rating_counts = df['Rating'].value_counts()
                st.bar_chart(rating_counts)

                # Department performance
                st.write("**Performance by Department**")
                dept_perf = df.groupby('Department')['Overall Score'].apply(
                    lambda x: x.str.rstrip('%').astype(float).mean()
                ).sort_values(ascending=False)
                st.bar_chart(dept_perf)

            with col2:
                # Job role performance
                st.write("**Performance by Job Role**")
                role_perf = df.groupby('Job Role')['Overall Score'].apply(
                    lambda x: x.str.rstrip('%').astype(float).mean()
                ).sort_values(ascending=False)
                st.bar_chart(role_perf)

                # Top performers
                st.write("**Top 5 Performers**")
                df['Score_Numeric'] = df['Overall Score'].str.rstrip('%').astype(float)
                top_5 = df.nlargest(5, 'Score_Numeric')[['Employee ID', 'Job Role', 'Overall Score', 'Rating']]
                st.dataframe(top_5, use_container_width=True, hide_index=True)

            # Scatter plot: Quality vs Competency
            st.markdown("---")
            st.write("**Quality Score vs Competency Score Correlation**")
            chart_df = df[df['Quality Score'].str.split('/').str[0].astype(float).notna()].copy()
            chart_df['Quality_Num'] = chart_df['Quality Score'].str.split('/').str[0].astype(float)
            chart_df['Competency_Num'] = chart_df['Avg Competency Score'].str.split('/').str[0].astype(float)
            st.scatter_chart(chart_df[['Quality_Num', 'Competency_Num']])

        with tab4:
            st.subheader("Export Data")

            col1, col2 = st.columns(2)

            with col1:
                # CSV Export
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Data (CSV)",
                    data=csv,
                    file_name=f"employee_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with col2:
                # Excel Export (requires openpyxl)
                try:
                    from io import BytesIO
                    with pd.ExcelWriter('temp.xlsx', engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Employees', index=False)
                    with open('temp.xlsx', 'rb') as f:
                        excel_data = f.read()
                    import os
                    os.remove('temp.xlsx')

                    st.download_button(
                        label="📊 Download Full Data (Excel)",
                        data=excel_data,
                        file_name=f"employee_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except:
                    st.warning("Excel export requires openpyxl. Install with: pip install openpyxl")

            # Summary statistics export
            st.write("**Summary Statistics**")
            summary_stats = pd.DataFrame({
                'Metric': ['Total Employees', 'Avg Performance Score', 'Excellent', 'Good', 'Satisfactory', 'Needs Improvement'],
                'Value': [
                    len(employees),
                    f"{avg_score:.1f}%",
                    df[df['Rating'] == 'Excellent'].shape[0],
                    df[df['Rating'] == 'Good'].shape[0],
                    df[df['Rating'] == 'Satisfactory'].shape[0],
                    df[df['Rating'] == 'Needs Improvement'].shape[0]
                ]
            })
            st.dataframe(summary_stats, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

if __name__ == "__main__":
    view_employee_page()