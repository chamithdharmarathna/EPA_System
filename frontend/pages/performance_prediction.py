import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API = "http://localhost:8000"
BAND_COLOR = {"High": "#2ecc71", "Medium": "#f39c12", "Low": "#e74c3c"}

KPI_WEIGHT_TABLE = {
    "Task Completion Rate":   ("task_completion_rate",  "30%", "Tasks completed ÷ tasks assigned"),
    "On-Time Delivery Rate":  ("on_time_delivery_rate", "25%", "Tasks on time ÷ tasks completed"),
    "Quality Score":          ("quality_score",         "20%", "Score out of 10, normalised to 0-1"),
    "Issue Resolution Rate":  ("issue_resolution_rate", "10%", "Issues resolved ÷ issues raised"),
    "Defect Penalty":         ("defect_count",          "8%",  "1 − min(defects÷50, 1)  — lower is better"),
    "Rework Penalty":         ("rework_count",          "4%",  "1 − min(reworks÷20, 1)  — lower is better"),
    "Blocker Penalty":        ("blockers_count",        "3%",  "1 − min(blockers÷15, 1) — lower is better"),
}

def performance_prediction_page():
    st.title("Performance Prediction")
    st.caption("KPI-based scoring — current formula score vs ML predicted score")
    st.markdown("---")

    info_resp = requests.get(f"{API}/api/ml/performance/info")
    info = info_resp.json() if info_resp.status_code == 200 else {"model_exists": False}

    if info.get("model_exists"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Model Version",   (info.get("model_version") or "")[:15])
        c2.metric("R² Score",        f"{info.get('r2_score', 0):.4f}")
        c3.metric("RMSE",            f"{info.get('rmse', 0):.2f}")
        c4.metric("Band Accuracy",   f"{info.get('band_accuracy', 0)*100:.1f}%")
    else:
        st.warning("No trained model found. Train the model in the Train tab first.")

    st.markdown("---")

    tab_train, tab_kpi_method, tab_predict, tab_quarterly, tab_results, tab_importance = st.tabs([
        "🏋️ Train", "📐 KPI Methodology", "🔍 Predict Employee",
        "📅 Quarterly Trend", "📊 All Results", "📌 Feature Importance"
    ])

    # ── TRAIN ────────────────────────────────────────────────────────────────
    with tab_train:
        st.subheader("Train Performance Prediction Model")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("**Uses only KPI data — no demographics, no subjective scores**")
            st.write("- Algorithm: Gradient Boosting Regressor")
            st.write("- Training label: Formula-based KPI score")
            st.write("- Validation: 5-Fold Cross Validation (R²)")
            st.write("- Split: 80% train / 20% test")
            st.markdown("---")

            if st.button("🚀 Train Model", type="primary", use_container_width=True):
                with st.spinner("Training..."):
                    resp = requests.post(f"{API}/api/ml/performance/train")

                if resp.status_code == 200:
                    r = resp.json()
                    st.success("Model trained successfully!")

                    m1, m2, m3 = st.columns(3)
                    m1.metric("R² Score",       f"{r['r2_score']:.4f}")
                    m2.metric("RMSE",           f"{r['rmse']:.2f}")
                    m3.metric("Band Accuracy",  f"{r['band_accuracy']*100:.1f}%")

                    m4, m5, m6 = st.columns(3)
                    m4.metric("CV R² Mean",     f"{r['cv_r2_mean']:.4f}")
                    m5.metric("CV R² Std",      f"±{r['cv_r2_std']:.4f}")
                    m6.metric("Employees Used", r['employees_used'])

                    dist = r.get("class_distribution", {})
                    if dist:
                        st.markdown("### Performance Band Distribution")
                        fig = px.pie(
                            values=list(dist.values()), names=list(dist.keys()),
                            color=list(dist.keys()), color_discrete_map=BAND_COLOR
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    st.rerun()
                else:
                    try:
                        detail = resp.json().get("detail", "Unknown error")
                    except Exception:
                        detail = resp.text or f"HTTP {resp.status_code} — empty response"
                    st.error(f"Training failed: {detail}")

        with col2:
            st.markdown("### KPI Features Used")
            st.caption("Only objective, measurable work output is used for prediction.")
            for label, (col, weight, desc) in KPI_WEIGHT_TABLE.items():
                st.markdown(
                    f"**{label}** &nbsp; `{weight}` &nbsp; — {desc}"
                )

    # ── KPI METHODOLOGY ──────────────────────────────────────────────────────
    with tab_kpi_method:
        st.subheader("How the KPI Score Is Calculated")
        st.markdown(
            "The **Current Score** is computed directly from this transparent formula. "
            "The **Predicted Score** is what the ML model learns to estimate from the same inputs."
        )
        st.latex(r"""
\text{Score} = \left(
  R_{tc} \times 0.30 +
  R_{ot} \times 0.25 +
  \frac{Q}{10} \times 0.20 +
  R_{ir} \times 0.10 +
  P_{d} \times 0.08 +
  P_{r} \times 0.04 +
  P_{b} \times 0.03
\right) \times 100
""")

        st.markdown("---")
        st.markdown("**Variable definitions:**")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("| Variable | Meaning |")
            st.markdown("|---|---|")
            st.markdown("| $R_{tc}$ | Task Completion Rate (0–1) |")
            st.markdown("| $R_{ot}$ | On-Time Delivery Rate (0–1) |")
            st.markdown("| $Q$ | Quality Score (0–10) |")
            st.markdown("| $R_{ir}$ | Issue Resolution Rate (0–1) |")
        with col2:
            st.markdown("| Variable | Meaning |")
            st.markdown("|---|---|")
            st.markdown("| $P_d$ | $1 - \\min(\\text{defects}/50,\\; 1)$ |")
            st.markdown("| $P_r$ | $1 - \\min(\\text{reworks}/20,\\; 1)$ |")
            st.markdown("| $P_b$ | $1 - \\min(\\text{blockers}/15,\\; 1)$ |")

        st.markdown("---")
        st.markdown("**Performance Band thresholds:**")
        col1, col2, col3 = st.columns(3)
        col1.markdown(
            "<div style='background:#d4edda;padding:15px;border-radius:8px;text-align:center'>"
            "<b>High</b><br>Score ≥ 80</div>", unsafe_allow_html=True
        )
        col2.markdown(
            "<div style='background:#fff3cd;padding:15px;border-radius:8px;text-align:center'>"
            "<b>Medium</b><br>60 ≤ Score < 80</div>", unsafe_allow_html=True
        )
        col3.markdown(
            "<div style='background:#f8d7da;padding:15px;border-radius:8px;text-align:center'>"
            "<b>Low</b><br>Score < 60</div>", unsafe_allow_html=True
        )

        st.markdown("---")
        st.markdown("**Why two scores?**")
        st.info(
            "**Current Score** = the formula above applied directly. Always explainable. "
            "Useful for HR transparency.\n\n"
            "**Predicted Score** = what the Gradient Boosting model estimates based on "
            "patterns it learned across all employees. May differ slightly because the model "
            "detects non-linear relationships between KPI variables. "
            "The **delta** between them flags employees where the formula and model disagree — "
            "these are worth closer review."
        )

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
                        e["employee_id"]:
                            f"{e['employee_id']} — {e['job_role_id']} ({e['department']})"
                        for e in emps
                    }
                    selected = st.selectbox(
                        "Select Employee",
                        list(emp_options.keys()),
                        format_func=lambda x: emp_options[x]
                    )

                    if st.button("Predict Performance", type="primary"):
                        resp = requests.get(
                            f"{API}/api/ml/performance/predict/{selected}"
                        )
                        if resp.status_code == 200:
                            r    = resp.json()
                            curr = r.get("current_score", 0)
                            pred = r.get("predicted_score", r.get("performance_score", 0))
                            delta = r.get("score_delta", 0)
                            band  = r.get("performance_band", "Medium")
                            color = BAND_COLOR.get(band, "#888")

                            st.markdown("---")

                            # Band pill
                            st.markdown(
                                f"<div style='text-align:center;padding:16px;"
                                f"background:{color}22;border-radius:12px;"
                                f"border:2px solid {color};margin-bottom:16px'>"
                                f"<h2 style='color:{color};margin:0'>{band}</h2>"
                                f"<p style='margin:0'>Performance Band</p></div>",
                                unsafe_allow_html=True
                            )

                            # Score comparison
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Current Score (formula)",   f"{curr:.1f} / 100")
                            c2.metric("Predicted Score (ML)",      f"{pred:.1f} / 100",
                                      delta=f"{delta:+.1f}")
                            c3.metric("Agreement",
                                      "✅ High" if abs(delta) < 5 else
                                      "⚠️ Moderate" if abs(delta) < 12 else
                                      "🔍 Review")

                            # Side-by-side gauges
                            fig = go.Figure()
                            for val, title, clr in [
                                (curr, "Current Score", "#3498db"),
                                (pred, "Predicted Score", color)
                            ]:
                                fig.add_trace(go.Indicator(
                                    mode="gauge+number",
                                    value=val,
                                    title={"text": title},
                                    gauge={
                                        "axis": {"range":[0,100]},
                                        "bar":  {"color": clr},
                                        "steps":[
                                            {"range":[0,60],   "color":"#fde8e8"},
                                            {"range":[60,80],  "color":"#fff3cd"},
                                            {"range":[80,100], "color":"#d4edda"}
                                        ]
                                    },
                                    domain={"x": [0, 0.45] if title == "Current Score"
                                    else [0.55, 1], "y": [0, 1]}
                                ))
                            fig.update_layout(height=280)
                            st.plotly_chart(fig, use_container_width=True)

                            # KPI breakdown
                            snap = r.get("feature_snapshot", {})
                            if snap:
                                st.markdown("### KPI Breakdown for This Prediction")
                                kpi_display = {
                                    "Task Completion Rate":  f"{snap.get('task_completion_rate', 0)*100:.1f}%",
                                    "On-Time Delivery Rate": f"{snap.get('on_time_delivery_rate', 0)*100:.1f}%",
                                    "Quality Score":         f"{snap.get('quality_score', 0):.1f}/10",
                                    "Issue Resolution Rate": f"{snap.get('issue_resolution_rate', 0)*100:.1f}%",
                                    "Defect Count":          snap.get("defect_count", 0),
                                    "Rework Count":          snap.get("rework_count", 0),
                                    "Blockers Count":        snap.get("blockers_count", 0),
                                }
                                kpi_df = pd.DataFrame(
                                    list(kpi_display.items()),
                                    columns=["KPI", "Value"]
                                )
                                st.dataframe(kpi_df, use_container_width=True, hide_index=True)
                        else:
                            st.error(resp.json().get("detail", "Prediction failed"))
            except Exception as e:
                st.error(f"Error: {e}")

    # ── QUARTERLY TREND ───────────────────────────────────────────────────────
    with tab_quarterly:
        st.subheader("Quarterly Performance Trend")
        st.caption(
            "Select an employee to see how their KPI score changed across quarters. "
            "Compares the rule-based current score against the ML predicted score per quarter."
        )

        if not info.get("model_exists"):
            st.warning("Please train the model first.")
        else:
            try:
                emps = requests.get(f"{API}/api/employees/").json()
                if not emps:
                    st.info("No employees found.")
                else:
                    emp_options = {
                        e["employee_id"]:
                            f"{e['employee_id']} — {e['job_role_id']} ({e['department']})"
                        for e in emps
                    }
                    selected_q = st.selectbox(
                        "Select Employee",
                        list(emp_options.keys()),
                        format_func=lambda x: emp_options[x],
                        key="quarterly_select"
                    )

                    resp = requests.get(
                        f"{API}/api/ml/performance/quarterly/{selected_q}"
                    )

                    if resp.status_code == 200:
                        trend = resp.json()

                        if len(trend) < 2:
                            st.info(
                                "Only one quarter of data available. "
                                "Add more quarterly KPI records to see trends."
                            )

                        df_trend = pd.DataFrame(trend)

                        # Main trend chart
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_trend["period_label"],
                            y=df_trend["current_score"],
                            name="Current Score (formula)",
                            mode="lines+markers",
                            line=dict(color="#3498db", width=2, dash="dot"),
                            marker=dict(size=8)
                        ))
                        fig.add_trace(go.Scatter(
                            x=df_trend["period_label"],
                            y=df_trend["predicted_score"],
                            name="Predicted Score (ML)",
                            mode="lines+markers",
                            line=dict(color="#e67e22", width=2),
                            marker=dict(size=8)
                        ))

                        # Band threshold lines
                        fig.add_hline(y=80, line_dash="dash",
                                      line_color="#2ecc71", opacity=0.5,
                                      annotation_text="High threshold (80)")
                        fig.add_hline(y=60, line_dash="dash",
                                      line_color="#e74c3c", opacity=0.5,
                                      annotation_text="Low threshold (60)")

                        fig.update_layout(
                            title=f"Performance Score Trend — {selected_q}",
                            xaxis_title="Quarter",
                            yaxis_title="Score (0–100)",
                            yaxis=dict(range=[0, 105]),
                            legend=dict(orientation="h", y=-0.2),
                            height=420
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # KPI sub-metrics trend
                        st.markdown("### Underlying KPI Trends")
                        col1, col2 = st.columns(2)

                        with col1:
                            fig2 = px.line(
                                df_trend, x="period_label",
                                y=["task_completion_rate","on_time_delivery_rate"],
                                title="Completion & On-Time Rate",
                                labels={"value":"Rate","variable":"Metric"}
                            )
                            fig2.update_yaxes(range=[0, 1.05])
                            st.plotly_chart(fig2, use_container_width=True)

                        with col2:
                            fig3 = px.bar(
                                df_trend, x="period_label",
                                y="defect_count",
                                title="Defect Count per Quarter",
                                color_discrete_sequence=["#e74c3c"]
                            )
                            st.plotly_chart(fig3, use_container_width=True)

                        # Score delta trend
                        fig4 = px.bar(
                            df_trend, x="period_label", y="score_delta",
                            title="Score Delta (Predicted − Current) per Quarter",
                            color="score_delta",
                            color_continuous_scale=["#e74c3c","#f39c12","#2ecc71"],
                        )
                        fig4.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.3)
                        st.plotly_chart(fig4, use_container_width=True)

                        # Quarter summary table
                        st.markdown("### Quarter-by-Quarter Summary")
                        disp = df_trend[[
                            "period_label","current_score","predicted_score",
                            "score_delta","performance_band",
                            "task_completion_rate","on_time_delivery_rate",
                            "quality_score","defect_count"
                        ]].copy()
                        disp["task_completion_rate"]  = (disp["task_completion_rate"]*100).round(1).astype(str) + "%"
                        disp["on_time_delivery_rate"] = (disp["on_time_delivery_rate"]*100).round(1).astype(str) + "%"
                        disp.columns = ["Quarter","Current","Predicted","Delta",
                                        "Band","Completion%","OnTime%","Quality","Defects"]
                        st.dataframe(disp, use_container_width=True, hide_index=True)

                    elif resp.status_code == 404:
                        st.info(resp.json().get("detail", "No KPI records found."))
                    else:
                        st.error("Failed to load quarterly data.")

            except Exception as e:
                st.error(f"Error: {e}")

    # ── ALL RESULTS ──────────────────────────────────────────────────────────
    with tab_results:
        st.subheader("All Prediction Results")

        col1, col2 = st.columns([3,1])
        with col2:
            if st.button("🔄 Predict All", type="primary", use_container_width=True):
                if not info.get("model_exists"):
                    st.warning("Train the model first.")
                else:
                    with st.spinner("Running predictions..."):
                        resp = requests.post(f"{API}/api/ml/performance/predict-all")
                    if resp.status_code == 200:
                        r = resp.json()
                        st.success(f"Predicted: {r['predicted']} | Skipped: {r['skipped']}")
                        st.rerun()

        results = requests.get(f"{API}/api/ml/performance/results").json()
        if not results:
            st.info("No predictions yet. Click Predict All.")
        else:
            df = pd.DataFrame(results)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total", len(df))
            m2.metric("High",   len(df[df["performance_band"] == "High"]))
            m3.metric("Medium", len(df[df["performance_band"] == "Medium"]))
            m4.metric("Low",    len(df[df["performance_band"] == "Low"]))

            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(df, names="performance_band", title="Band Distribution",
                             color="performance_band", color_discrete_map=BAND_COLOR)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                if "current_score" in df.columns and "predicted_score" in df.columns:
                    fig = px.scatter(
                        df, x="current_score", y="predicted_score",
                        color="performance_band", color_discrete_map=BAND_COLOR,
                        title="Current Score vs Predicted Score",
                        labels={"current_score":"Formula Score",
                                "predicted_score":"ML Score"},
                        hover_data=["employee_id"]
                    )
                    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                                  line=dict(dash="dash", color="gray"))
                    st.plotly_chart(fig, use_container_width=True)

            disp = df[["employee_id","current_score","predicted_score",
                       "score_delta","performance_band"]].copy()
            disp = disp.sort_values("predicted_score", ascending=False)
            st.dataframe(disp, use_container_width=True, hide_index=True)
            st.download_button("📥 Download CSV", df.to_csv(index=False),
                               "performance_results.csv", "text/csv")

    # ── FEATURE IMPORTANCE ────────────────────────────────────────────────────
    with tab_importance:
        st.subheader("Feature Importance")
        fi = info.get("feature_importance", {})
        if not fi:
            st.info("Train the model first.")
        else:
            readable = {
                "task_completion_rate":  "Task Completion Rate",
                "on_time_delivery_rate": "On-Time Delivery Rate",
                "quality_score":         "Quality Score",
                "issue_resolution_rate": "Issue Resolution Rate",
                "defect_count":          "Defect Count",
                "rework_count":          "Rework Count",
                "blockers_count":        "Blockers Count",
            }
            fi_df = (pd.DataFrame(list(fi.items()), columns=["Feature","Importance"])
                     .assign(Feature=lambda d: d["Feature"].map(readable).fillna(d["Feature"]))
                     .sort_values("Importance"))

            fig = px.bar(fi_df, x="Importance", y="Feature", orientation="h",
                         title="Feature Importance — Gradient Boosting Regressor",
                         color="Importance", color_continuous_scale="Blues")
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### KPI Weight vs Model Importance")
            weight_map = {
                "Task Completion Rate":  0.30, "On-Time Delivery Rate": 0.25,
                "Quality Score": 0.20, "Issue Resolution Rate": 0.10,
                "Defect Count": 0.08, "Rework Count": 0.04, "Blockers Count": 0.03,
            }
            fi_df["Formula Weight"] = fi_df["Feature"].map(weight_map)
            fig2 = go.Figure()
            fig2.add_bar(name="Formula Weight", x=fi_df["Feature"],
                         y=fi_df["Formula Weight"], marker_color="#3498db")
            fig2.add_bar(name="Model Importance", x=fi_df["Feature"],
                         y=fi_df["Importance"], marker_color="#e67e22")
            fig2.update_layout(barmode="group", height=380,
                               title="What we assumed vs what the model learned")
            st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    performance_prediction_page()