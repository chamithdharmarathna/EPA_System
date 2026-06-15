import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API = "http://localhost:8000"
BAND_COLOR = {"High": "#2ecc71", "Medium": "#f39c12", "Low": "#e74c3c"}

def performance_prediction_page():
    st.title("Performance Prediction")
    st.caption("Module 1 — Gradient Boosting Classifier + Regressor")
    st.markdown("---")

    # Model status bar
    info = requests.get(f"{API}/api/ml/performance/info").json()
    if info.get("model_exists"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Model Version",       info.get("model_version", "—")[:15])
        c2.metric("Classifier Accuracy", f"{info.get('classifier_accuracy', 0)*100:.1f}%")
        c3.metric("R² Score",            f"{info.get('r2_score', 0):.4f}")
        c4.metric("Trained On",          (info.get("trained_on") or "")[:10])
    else:
        st.warning("No trained model found. Go to the Train tab to train first.")

    st.markdown("---")
    tab_train, tab_predict, tab_results, tab_importance = st.tabs([
        "🏋️ Train Model", "🔍 Predict Employee", "📊 All Results", "📌 Feature Importance"
    ])

    # ── TRAIN ────────────────────────────────────────────────────────────────
    with tab_train:
        st.subheader("Train Performance Prediction Model")
        st.write("The model learns from KPI + behavioral data of all employees with complete records.")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("**Algorithm:** Gradient Boosting")
            st.write("**Target (Classification):** High / Medium / Low")
            st.write("**Target (Regression):** Performance Score 0–100")
            st.write("**Validation:** 5-Fold Cross Validation")
            st.write("**Train/Test Split:** 80 / 20")
            st.markdown("---")

            if st.button("🚀 Train Model", type="primary", use_container_width=True):
                with st.spinner("Training... this may take a few seconds"):
                    resp = requests.post(f"{API}/api/ml/performance/train")
                if resp.status_code == 200:
                    r = resp.json()
                    st.success("Model trained successfully!")
                    st.balloons()

                    st.markdown("### Training Results")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Classifier Accuracy", f"{r['classifier_accuracy']*100:.1f}%")
                    m2.metric("CV Mean Accuracy",    f"{r['cv_mean']*100:.1f}% ± {r['cv_std']*100:.1f}%")
                    m3.metric("R² Score",            f"{r['r2_score']:.4f}")

                    m4, m5, m6 = st.columns(3)
                    m4.metric("RMSE",                f"{r['rmse']:.2f}")
                    m5.metric("Employees Used",      r['employees_used'])
                    m6.metric("Model Version",       r['model_version'][:15])

                    st.markdown("### Class Distribution in Training Data")
                    dist = r.get("class_distribution", {})
                    if dist:
                        fig = px.pie(
                            values=list(dist.values()),
                            names=list(dist.keys()),
                            color=list(dist.keys()),
                            color_discrete_map=BAND_COLOR
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    st.rerun()
                else:
                    st.error(f"Training failed: {resp.json().get('detail', 'Unknown error')}")

        with col2:
            st.markdown("### Features Used (19 total)")
            features_info = {
                "Employee":  ["Years of Experience", "Job Role"],
                "KPI":       ["Task Completion Rate", "On-Time Delivery Rate",
                              "Defect Count", "Issue Resolution Rate",
                              "Quality Score", "Rework Count", "Blockers Count"],
                "Behavioral":["Punctuality", "Problem Solving", "Leadership",
                              "Collaboration", "Communication", "No-Pay Leave",
                              "Avg Response Time", "Meetings Attended",
                              "Learning Hours", "Team Interaction Frequency"]
            }
            for group, feats in features_info.items():
                with st.expander(f"**{group}** ({len(feats)} features)", expanded=True):
                    for f in feats:
                        st.write(f"• {f}")

    # ── PREDICT SINGLE ───────────────────────────────────────────────────────
    with tab_predict:
        st.subheader("Predict for Individual Employee")

        if not info.get("model_exists"):
            st.warning("Please train the model first.")
        else:
            try:
                emps = requests.get(f"{API}/api/employees/").json()
                if not emps:
                    st.info("No employees found.")
                else:
                    emp_options = {
                        e["employee_id"]: f"{e['employee_id']} — {e['job_role_id']} ({e['department']})"
                        for e in emps
                    }
                    selected = st.selectbox(
                        "Select Employee",
                        list(emp_options.keys()),
                        format_func=lambda x: emp_options[x]
                    )

                    if st.button("Predict Performance", type="primary"):
                        resp = requests.get(f"{API}/api/ml/performance/predict/{selected}")
                        if resp.status_code == 200:
                            r = resp.json()
                            band  = r["performance_band"]
                            score = r["performance_score"]
                            conf  = r["confidence"]
                            color = BAND_COLOR.get(band, "#888")

                            st.markdown("---")
                            col1, col2, col3 = st.columns(3)
                            col1.markdown(
                                f"<div style='text-align:center;padding:20px;"
                                f"background:{color}22;border-radius:12px;"
                                f"border:2px solid {color}'>"
                                f"<h2 style='color:{color};margin:0'>{band}</h2>"
                                f"<p style='margin:0'>Performance Band</p></div>",
                                unsafe_allow_html=True
                            )
                            col2.metric("Performance Score", f"{score:.1f} / 100")
                            col3.metric("Model Confidence",  f"{conf*100:.1f}%")

                            # Gauge
                            fig = go.Figure(go.Indicator(
                                mode="gauge+number",
                                value=score,
                                domain={"x":[0,1],"y":[0,1]},
                                title={"text": f"Performance Score — {selected}"},
                                gauge={
                                    "axis": {"range":[0,100]},
                                    "bar":  {"color": color},
                                    "steps":[
                                        {"range":[0,55],  "color":"#fde8e8"},
                                        {"range":[55,78], "color":"#fff3cd"},
                                        {"range":[78,100],"color":"#d4edda"}
                                    ],
                                    "threshold":{
                                        "line":{"color":"black","width":3},
                                        "thickness":0.75,
                                        "value": score
                                    }
                                }
                            ))
                            fig.update_layout(height=300)
                            st.plotly_chart(fig, use_container_width=True)

                            # Feature snapshot
                            snap = r.get("feature_snapshot", {})
                            if snap:
                                with st.expander("Feature values used for this prediction"):
                                    snap_df = pd.DataFrame([snap]).T.reset_index()
                                    snap_df.columns = ["Feature", "Value"]
                                    st.dataframe(snap_df, use_container_width=True, hide_index=True)
                        else:
                            st.error(resp.json().get("detail", "Prediction failed"))
            except Exception as e:
                st.error(f"Error: {e}")

    # ── ALL RESULTS ──────────────────────────────────────────────────────────
    with tab_results:
        st.subheader("All Prediction Results")

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Run Predict All", type="primary", use_container_width=True):
                if not info.get("model_exists"):
                    st.warning("Train the model first.")
                else:
                    with st.spinner("Predicting for all employees..."):
                        resp = requests.post(f"{API}/api/ml/performance/predict-all")
                    if resp.status_code == 200:
                        r = resp.json()
                        st.success(f"Predicted: {r['predicted']} | Skipped: {r['skipped']}")
                        st.rerun()
                    else:
                        st.error("Failed to run predictions")

        results = requests.get(f"{API}/api/ml/performance/results").json()

        if not results:
            st.info("No predictions yet. Click 'Run Predict All' to generate.")
        else:
            df = pd.DataFrame(results)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Predicted", len(df))
            m2.metric("High Performers",   len(df[df["performance_band"] == "High"]))
            m3.metric("Medium Performers", len(df[df["performance_band"] == "Medium"]))
            m4.metric("Low Performers",    len(df[df["performance_band"] == "Low"]))

            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                fig = px.pie(
                    df, names="performance_band",
                    title="Performance Band Distribution",
                    color="performance_band",
                    color_discrete_map=BAND_COLOR
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.histogram(
                    df, x="performance_score", nbins=20,
                    title="Performance Score Distribution",
                    color_discrete_sequence=["#3498db"]
                )
                fig.add_vline(x=78, line_dash="dash", line_color="#e74c3c",
                              annotation_text="Low/Medium")
                fig.add_vline(x=85, line_dash="dash", line_color="#2ecc71",
                              annotation_text="Medium/High")
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Result Table")
            display_df = df[["employee_id","performance_score","performance_band","confidence"]].copy()
            display_df["performance_score"] = display_df["performance_score"].round(2)
            display_df["confidence"] = (display_df["confidence"] * 100).round(1).astype(str) + "%"
            display_df = display_df.sort_values("performance_score", ascending=False)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv = display_df.to_csv(index=False)
            st.download_button("📥 Download Results (CSV)", csv,
                               "performance_results.csv", "text/csv")

    # ── FEATURE IMPORTANCE ───────────────────────────────────────────────────
    with tab_importance:
        st.subheader("Feature Importance")
        fi = info.get("feature_importance", {})
        if not fi:
            st.info("Train the model to see feature importance.")
        else:
            fi_df = (pd.DataFrame(list(fi.items()), columns=["Feature", "Importance"])
                     .sort_values("Importance", ascending=True))

            readable = {
                "task_completion_rate":       "Task Completion Rate",
                "on_time_delivery_rate":      "On-Time Delivery Rate",
                "quality_score":              "Quality Score",
                "issue_resolution_rate":      "Issue Resolution Rate",
                "defect_count":               "Defect Count",
                "rework_count":               "Rework Count",
                "blockers_count":             "Blockers Count",
                "punctuality":                "Punctuality",
                "problem_solving":            "Problem Solving",
                "leadership":                 "Leadership",
                "collaboration":              "Collaboration",
                "communication":              "Communication",
                "no_nopay_leave":             "No-Pay Leave",
                "avg_response_time":          "Avg Response Time",
                "meetings_attended":          "Meetings Attended",
                "learning_hours":             "Learning Hours",
                "team_interaction_frequency": "Team Interaction",
                "years_of_experience":        "Years of Experience",
                "job_role_encoded":           "Job Role",
            }
            fi_df["Feature"] = fi_df["Feature"].map(readable).fillna(fi_df["Feature"])

            fig = px.bar(
                fi_df, x="Importance", y="Feature", orientation="h",
                title="Feature Importance — Gradient Boosting Classifier",
                color="Importance", color_continuous_scale="Blues"
            )
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Importance Table")
            fi_df_disp = fi_df.sort_values("Importance", ascending=False).copy()
            fi_df_disp["Importance"] = (fi_df_disp["Importance"] * 100).round(2).astype(str) + "%"
            st.dataframe(fi_df_disp, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    performance_prediction_page()