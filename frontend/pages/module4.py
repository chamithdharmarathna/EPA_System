import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API = "http://localhost:8000"
CLUSTER_PALETTE = ["#3498db","#2ecc71","#e67e22","#9b59b6","#e74c3c","#1abc9c"]
FLAG_COLOR  = {"Consensus":"#2ecc71","Influenced":"#f39c12","Genuine Conflict":"#e74c3c","No Data":"#bdc3c7"}
RISK_COLOR  = {"Low":"#2ecc71","Medium":"#f39c12","High":"#e74c3c","Unknown":"#bdc3c7"}

def module4_page():
    st.title("Module 4 — Conflict Resolution & Team Composition")
    st.caption("CAPAF · Sub-culture Clustering · Power Distance Arbitration · Opinion Dynamics · Team Recommender")
    st.markdown("---")

    info_r = requests.get(f"{API}/api/ml/module4/info")
    info   = info_r.json() if info_r.status_code == 200 else {"model_exists": False}

    # ── Status bar ────────────────────────────────────────────────────────────
    if info.get("model_exists"):
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Clusters (K)",        info.get("final_k","—"))
        c2.metric("Silhouette Score",    f"{info.get('best_silhouette',0):.4f}")
        c3.metric("Employees Analysed",  info.get("employees_analyzed","—"))
        corr = info.get("diversity_performance_corr")
        c4.metric("Diversity-Perf Corr", f"{corr:.4f}" if corr else "—")
    else:
        st.warning("Pipeline not yet run. Go to the Run tab.")

    st.markdown("---")

    tab_run, tab_clusters, tab_pdi, tab_dynamics, tab_teams, tab_recommend = st.tabs([
        "⚙️ Run Pipeline",
        "🧬 Sub-culture Clusters",
        "⚖️ Power Distance",
        "🌊 Opinion Dynamics",
        "🏗️ Team Composition",
        "💡 Team Recommender",
    ])

    # ══ TAB 1 — RUN ══════════════════════════════════════════════════════════
    with tab_run:
        st.subheader("Run Module 4 Pipeline")
        col1, col2 = st.columns([1,2])

        with col1:
            st.markdown("**What this pipeline does:**")
            st.write("1. K-Means sub-culture clustering on demographics")
            st.write("2. Hofstede PDI-weighted 360° score per employee")
            st.write("3. DeGroot opinion divergence scoring")
            st.write("4. Team diversity-performance correlation")
            st.write("5. Conflict risk flagging")
            st.markdown("---")
            if st.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
                with st.spinner("Running all four engines..."):
                    resp = requests.post(f"{API}/api/ml/module4/run")
                if resp.status_code == 200:
                    r = resp.json()
                    st.success("Pipeline complete!")
                    st.balloons()
                    m1,m2,m3 = st.columns(3)
                    m1.metric("Optimal K",         r["final_k"])
                    m2.metric("Silhouette Score",  f"{r['best_silhouette']:.4f}")
                    m3.metric("Employees",         r["employees_analyzed"])

                    st.markdown("### Silhouette scores by K")
                    sil_df = pd.DataFrame(
                        list(r["silhouette_scores"].items()),
                        columns=["K","Silhouette"]
                    )
                    sil_df["K"] = sil_df["K"].astype(int)
                    fig = px.line(sil_df, x="K", y="Silhouette", markers=True,
                                  title="Silhouette Score vs Number of Clusters")
                    fig.add_vline(x=r["final_k"], line_dash="dash", line_color="#e74c3c",
                                  annotation_text=f"Optimal K={r['final_k']}")
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("### Archetype labels")
                    for k,v in r["archetype_labels"].items():
                        color = CLUSTER_PALETTE[int(k) % len(CLUSTER_PALETTE)]
                        st.markdown(
                            f"<span style='background:{color};color:white;"
                            f"padding:4px 10px;border-radius:12px;margin:4px;display:inline-block'>"
                            f"Cluster {k}</span> &nbsp; {v}",
                            unsafe_allow_html=True
                        )
                    st.rerun()
                else:
                    try:   st.error(resp.json().get("detail","Unknown error"))
                    except: st.error(f"HTTP {resp.status_code}: {resp.text[:200]}")

        with col2:
            st.markdown("### Clustering features used")
            feat_data = {
                "Feature":["Age (from DOB)","Ethnicity","Primary Language","Years of Experience"],
                "Type":["Continuous","Categorical","Categorical","Continuous"],
                "Rationale":[
                    "Generational sub-culture patterns",
                    "Core Sri Lankan cultural dimension",
                    "Communication preference and cultural alignment",
                    "Seniority and organizational socialization"
                ]
            }
            st.dataframe(pd.DataFrame(feat_data), use_container_width=True, hide_index=True)

            st.markdown("### PDI weights (Hofstede Sri Lanka PDI = 80)")
            pdi_df = pd.DataFrame({
                "Evaluator Type":["Manager","Peer","Subordinate"],
                "Weight":        [0.45, 0.35, 0.20],
                "Reason":        [
                    "Highest authority, most informative in high-PDI culture",
                    "Independent view, moderate social influence",
                    "Deferential in high-PDI — weight adjusted down"
                ]
            })
            st.dataframe(pdi_df, use_container_width=True, hide_index=True)

            st.markdown("### Opinion dynamics flags")
            flag_df = pd.DataFrame({
                "Flag":["Consensus","Influenced","Genuine Conflict"],
                "Divergence (std)":["< 0.5","0.5 – 1.0","> 1.0"],
                "Interpretation":[
                    "All evaluator types agree — rating is reliable",
                    "Some convergence toward dominant opinion — check for social influence",
                    "Evaluator types strongly disagree — warrants review"
                ]
            })
            st.dataframe(flag_df, use_container_width=True, hide_index=True)

    # ══ TAB 2 — CLUSTERS ═════════════════════════════════════════════════════
    with tab_clusters:
        st.subheader("Sub-culture Cluster Profiles")
        clusters_r = requests.get(f"{API}/api/ml/module4/clusters")
        if clusters_r.status_code != 200 or not clusters_r.json():
            st.info("Run the pipeline first.")
        else:
            df = pd.DataFrame(clusters_r.json())

            # Distribution pie
            col1,col2 = st.columns(2)
            with col1:
                dist = df.groupby(["cluster_id","archetype_label"]).size().reset_index(name="count")
                dist["label"] = "Cluster " + dist["cluster_id"].astype(str)
                fig = px.pie(dist, values="count", names="label",
                             title="Employee distribution across sub-culture clusters",
                             color="cluster_id",
                             color_discrete_sequence=CLUSTER_PALETTE)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = px.bar(dist.sort_values("cluster_id"),
                              x="label", y="count", color="cluster_id",
                              title="Cluster sizes",
                              color_discrete_sequence=CLUSTER_PALETTE)
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

            # Archetype labels
            st.markdown("### Cluster archetypes")
            if info.get("archetype_labels"):
                for k, v in info["archetype_labels"].items():
                    color = CLUSTER_PALETTE[int(k) % len(CLUSTER_PALETTE)]
                    cnt   = int((df["cluster_id"] == int(k)).sum())
                    st.markdown(
                        f"<div style='background:{color}18;border-left:4px solid {color};"
                        f"padding:10px 16px;border-radius:6px;margin:6px 0'>"
                        f"<b style='color:{color}'>Cluster {k}</b> — {v} &nbsp;"
                        f"<span style='color:gray'>({cnt} employees)</span></div>",
                        unsafe_allow_html=True
                    )

            # Table
            st.markdown("### All employees")
            disp = df[["employee_id","cluster_id","archetype_label","conflict_risk","cultural_distance"]].copy()
            disp["cultural_distance"] = disp["cultural_distance"].round(3)
            st.dataframe(disp, use_container_width=True, hide_index=True)

    # ══ TAB 3 — POWER DISTANCE ═══════════════════════════════════════════════
    with tab_pdi:
        st.subheader("Power Distance Analysis")
        st.caption("Compares raw average rating vs PDI-corrected score using Hofstede weights")

        clusters_r = requests.get(f"{API}/api/ml/module4/clusters")
        if clusters_r.status_code != 200 or not clusters_r.json():
            st.info("Run the pipeline first.")
        else:
            df = pd.DataFrame(clusters_r.json()).dropna(subset=["pdi_corrected_score"])

            col1,col2 = st.columns(2)
            with col1:
                # Scatter: raw vs PDI
                fig = px.scatter(df, x="raw_avg_score", y="pdi_corrected_score",
                                 color="cluster_id", hover_data=["employee_id"],
                                 title="Raw average vs PDI-corrected score",
                                 labels={"raw_avg_score":"Raw Average (equal weights)",
                                         "pdi_corrected_score":"PDI-Corrected Score"},
                                 color_discrete_sequence=CLUSTER_PALETTE)
                fig.add_shape(type="line", x0=1, y0=1, x1=5, y1=5,
                              line=dict(dash="dash", color="gray"))
                fig.add_annotation(x=4.5, y=4.3, text="No change line",
                                   showarrow=False, font=dict(color="gray"))
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Delta distribution
                fig2 = px.histogram(df, x="pdi_delta", nbins=30,
                                    title="PDI delta distribution (Corrected − Raw)",
                                    color_discrete_sequence=["#3498db"])
                fig2.add_vline(x=0, line_dash="dash", line_color="#e74c3c",
                               annotation_text="No change")
                fig2.add_vline(x=df["pdi_delta"].mean(), line_dash="dot", line_color="#2ecc71",
                               annotation_text=f"Mean={df['pdi_delta'].mean():.3f}")
                st.plotly_chart(fig2, use_container_width=True)

            # Bar: Manager vs Peer vs Subordinate average by cluster
            st.markdown("### Average rating by evaluator type per cluster")
            melt = df[["cluster_id","manager_avg","peer_avg","subordinate_avg"]].dropna()
            melt = melt.melt(id_vars="cluster_id",
                             var_name="Evaluator Type", value_name="Avg Rating")
            melt["Evaluator Type"] = melt["Evaluator Type"].str.replace("_avg","")
            melt["Cluster"] = "Cluster " + melt["cluster_id"].astype(str)
            fig3 = px.bar(melt, x="Cluster", y="Avg Rating", color="Evaluator Type",
                          barmode="group", title="Rating by evaluator type per sub-culture cluster",
                          color_discrete_sequence=["#3498db","#2ecc71","#e74c3c"])
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown("### Summary metrics")
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Employees with PDI data", len(df))
            m2.metric("Mean PDI delta",  f"{df['pdi_delta'].mean():.4f}")
            m3.metric("Max PDI delta",   f"{df['pdi_delta'].max():.3f}")
            m4.metric("Min PDI delta",   f"{df['pdi_delta'].min():.3f}")

    # ══ TAB 4 — OPINION DYNAMICS ══════════════════════════════════════════════
    with tab_dynamics:
        st.subheader("Opinion Dynamics — DeGroot Divergence Model")
        st.caption("Measures how much Manager, Peer, and Subordinate ratings converge or diverge per employee")

        clusters_r = requests.get(f"{API}/api/ml/module4/clusters")
        if clusters_r.status_code != 200 or not clusters_r.json():
            st.info("Run the pipeline first.")
        else:
            df = pd.DataFrame(clusters_r.json())

            col1,col2 = st.columns(2)
            with col1:
                flag_counts = df["opinion_flag"].value_counts().reset_index()
                flag_counts.columns = ["Flag","Count"]
                flag_counts["Color"] = flag_counts["Flag"].map(FLAG_COLOR)
                fig = px.pie(flag_counts, values="Count", names="Flag",
                             title="Opinion dynamics flag distribution",
                             color="Flag",
                             color_discrete_map=FLAG_COLOR)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = px.histogram(df.dropna(subset=["divergence_score"]),
                                    x="divergence_score", nbins=30,
                                    color="opinion_flag",
                                    color_discrete_map=FLAG_COLOR,
                                    title="Divergence score distribution",
                                    labels={"divergence_score":"Divergence (std dev across evaluator types)"})
                fig2.add_vline(x=0.5,  line_dash="dash", line_color="#f39c12",
                               annotation_text="Consensus | Influenced")
                fig2.add_vline(x=1.0,  line_dash="dash", line_color="#e74c3c",
                               annotation_text="Influenced | Genuine Conflict")
                st.plotly_chart(fig2, use_container_width=True)

            # Divergence by cluster
            st.markdown("### Divergence by sub-culture cluster")
            valid = df.dropna(subset=["divergence_score","cluster_id"])
            fig3 = px.box(valid, x="cluster_id", y="divergence_score",
                          color="cluster_id",
                          color_discrete_sequence=CLUSTER_PALETTE,
                          title="Divergence score distribution per cluster",
                          labels={"cluster_id":"Cluster","divergence_score":"Divergence (std)"})
            fig3.add_hline(y=0.5, line_dash="dash", line_color="#f39c12")
            fig3.add_hline(y=1.0, line_dash="dash", line_color="#e74c3c")
            st.plotly_chart(fig3, use_container_width=True)

            # Flag counts
            st.markdown("### Flag summary")
            for flag, color in FLAG_COLOR.items():
                cnt  = int((df["opinion_flag"] == flag).sum())
                pct  = cnt / len(df) * 100
                st.markdown(
                    f"<div style='background:{color}18;border-left:4px solid {color};"
                    f"padding:8px 14px;border-radius:6px;margin:4px 0'>"
                    f"<b style='color:{color}'>{flag}</b> — {cnt} employees ({pct:.1f}%)</div>",
                    unsafe_allow_html=True
                )

    # ══ TAB 5 — TEAM COMPOSITION ═════════════════════════════════════════════
    with tab_teams:
        st.subheader("Team Composition Analysis")
        st.caption("Correlation between sub-culture diversity and team performance")

        teams_r = requests.get(f"{API}/api/ml/module4/teams")
        if teams_r.status_code != 200 or not teams_r.json():
            st.info("Run the pipeline first.")
        else:
            df = pd.DataFrame(teams_r.json()).dropna(subset=["avg_performance_score"])

            corr = info.get("diversity_performance_corr")
            col1,col2,col3 = st.columns(3)
            col1.metric("Teams Analysed",          len(df))
            col2.metric("Diversity-Performance ρ", f"{corr:.4f}" if corr else "—")
            col3.metric("High-conflict Teams",      int((df["conflict_risk_count"] > 0).sum()))

            col1,col2 = st.columns(2)
            with col1:
                fig = px.scatter(df, x="diversity_index", y="avg_performance_score",
                                 size="team_size", color="unique_clusters",
                                 hover_data=["project_id","conflict_risk_count"],
                                 title="Team diversity vs average performance",
                                 labels={"diversity_index":"Diversity Index",
                                         "avg_performance_score":"Avg Performance Score",
                                         "unique_clusters":"Unique Clusters"},
                                 color_continuous_scale="Blues")
                if corr:
                    fig.add_annotation(x=0.5, y=df["avg_performance_score"].max() - 2,
                                       text=f"Pearson ρ = {corr:.4f}",
                                       showarrow=False,
                                       bgcolor="white", bordercolor="gray")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig2 = px.histogram(df, x="unique_clusters",
                                    title="Number of unique sub-cultures per team",
                                    color_discrete_sequence=["#3498db"])
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("### Team table")
            disp = df[["project_id","institution_id","team_size",
                       "unique_clusters","diversity_index",
                       "avg_performance_score","conflict_risk_count"]].copy()
            disp = disp.sort_values("avg_performance_score", ascending=False)
            st.dataframe(disp, use_container_width=True, hide_index=True)

    # ══ TAB 6 — TEAM RECOMMENDER ═════════════════════════════════════════════
    with tab_recommend:
        st.subheader("Team Composition Recommender")
        st.caption("Given a project and required team size, suggests the optimal diverse team")

        if not info.get("model_exists"):
            st.warning("Run the pipeline first.")
        else:
            col1,col2 = st.columns([1,2])
            with col1:
                proj_resp = requests.get(f"{API}/api/projects/")
                projects  = proj_resp.json() if proj_resp.status_code == 200 else []
                proj_opts = {p["project_id"]: f"{p.get('name',p['project_id'])} ({p['project_id']})"
                             for p in projects}

                selected_proj = st.selectbox("Select project to staff",
                                             list(proj_opts.keys()),
                                             format_func=lambda x: proj_opts[x])
                required_size = st.number_input("Required team size", min_value=2, max_value=30, value=5)

                if st.button("🔍 Recommend Team", type="primary", use_container_width=True):
                    resp = requests.post(f"{API}/api/ml/module4/recommend-team",
                                         json={"project_id": selected_proj,
                                               "required_size": required_size})
                    if resp.status_code == 200:
                        r = resp.json()
                        st.session_state["rec_result"] = r
                    else:
                        try:    st.error(resp.json().get("detail","Failed"))
                        except: st.error(resp.text[:200])

            with col2:
                if "rec_result" in st.session_state:
                    r = st.session_state["rec_result"]

                    m1,m2,m3 = st.columns(3)
                    m1.metric("Diversity Index",          r["diversity_index"])
                    m2.metric("Predicted Avg Performance",f"{r['predicted_avg_performance']:.1f}")
                    m3.metric("Sub-cultures Represented", r["unique_sub_cultures"])

                    st.markdown("### Suggested team")
                    team_df = pd.DataFrame(r["suggested_team"])
                    if "cluster_id" in team_df.columns:
                        if info.get("archetype_labels"):
                            team_df["archetype"] = team_df["cluster_id"].astype(str).map(
                                info["archetype_labels"]
                            )
                        disp_cols = [c for c in ["employee_id","role","cluster_id",
                                                 "archetype","perf_score","conflict_risk"]
                                     if c in team_df.columns]
                        st.dataframe(team_df[disp_cols], use_container_width=True, hide_index=True)

                    # Cluster mix
                    mix = r.get("cluster_mix", {})
                    if mix:
                        mix_df = pd.DataFrame(list(mix.items()), columns=["Cluster","Count"])
                        mix_df["Cluster"] = "Cluster " + mix_df["Cluster"]
                        fig = px.pie(mix_df, values="Count", names="Cluster",
                                     title="Sub-culture mix in suggested team",
                                     color_discrete_sequence=CLUSTER_PALETTE)
                        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    module4_page()