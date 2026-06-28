import os, json, joblib, statistics
import numpy as np
import pandas as pd
from datetime import datetime, date
from sqlalchemy.orm import Session
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from backend.models.employee        import Employee
from backend.models.culture_cluster import CultureCluster, TeamAnalysis
from backend.models.performance_result import PerformanceResult

MODEL_DIR    = "data/models"
M4_MODEL     = f"{MODEL_DIR}/module4_kmeans.joblib"
M4_META      = f"{MODEL_DIR}/module4_meta.json"

# ── Constants ────────────────────────────────────────────────────────────────
PDI_WEIGHTS = {'Manager': 0.45, 'Peer': 0.35, 'Subordinate': 0.20, 'Self': 0.00}
ETH_MAP  = {'Sinhalese': 0, 'Tamil': 1, 'Muslim': 2, 'Burgher': 3}
LANG_MAP = {'Sinhala': 0, 'Tamil': 1, 'English': 2}
FEATURES = ['age', 'ethnicity_enc', 'language_enc', 'years_of_experience']

# ── Helpers ──────────────────────────────────────────────────────────────────
def _age(dob):
    if dob is None: return 30
    today = date.today()
    if isinstance(dob, str):
        try: dob = date.fromisoformat(dob[:10])
        except: return 30
    try: return (today - dob).days // 365
    except: return 30

def _div_flag(std):
    if std < 0.50: return 'Consensus'
    if std < 1.00: return 'Influenced'
    return 'Genuine Conflict'

def _conflict_risk(divergence, cultural_dist):
    if divergence is None: divergence = 0
    if cultural_dist is None: cultural_dist = 0
    if divergence > 1.0 and cultural_dist > 1.5: return 'High'
    if divergence > 0.7 or cultural_dist > 1.0:  return 'Medium'
    return 'Low'

def _archetype(centroid):
    age, eth, lang, exp = centroid
    age_lbl = 'Young' if age < 28 else ('Mid-career' if age < 38 else 'Senior')
    exp_lbl = 'Junior' if exp < 3  else ('Experienced' if exp < 8 else 'Veteran')
    eth_lbl = {0:'Sinhalese', 1:'Tamil', 2:'Muslim', 3:'Burgher'}.get(round(eth), 'Mixed')
    lng_lbl = {0:'Sinhala', 1:'Tamil', 2:'English'}.get(round(lang), 'Multilingual')
    return f"{age_lbl} {eth_lbl} {exp_lbl} ({lng_lbl}-speaking)"

# ── Main Pipeline ─────────────────────────────────────────────────────────────
def run_pipeline(db: Session, k_override: int = None) -> dict:
    os.makedirs(MODEL_DIR, exist_ok=True)
    version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    employees = db.query(Employee).all()
    if len(employees) < 20:
        raise ValueError(f"Need at least 20 employees, found {len(employees)}.")

    # ── ENGINE 1 — Sub-culture Clustering ────────────────────────────────────
    rows = []
    for e in employees:
        rows.append({
            'employee_id':        e.employee_id,
            'age':                _age(e.dob),
            'ethnicity_enc':      ETH_MAP.get(e.ethnicity or 'Sinhalese', 0),
            'language_enc':       LANG_MAP.get(e.primary_language or 'Sinhala', 0),
            'years_of_experience': e.years_of_experience or 0,
            'project_id':         e.project_id,
            'institution_id':     e.institution_id,
        })
    emp_df = pd.DataFrame(rows)

    X = emp_df[FEATURES].values
    scaler = StandardScaler()
    X_sc   = scaler.fit_transform(X)

    # Silhouette sweep K=3..6
    sil_scores = {}
    best_k, best_sil = 4, -1
    for k in range(3, 7):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        lbl = km.fit_predict(X_sc)
        s   = silhouette_score(X_sc, lbl)
        sil_scores[k] = round(s, 4)
        if s > best_sil:
            best_sil, best_k = s, k

    final_k = k_override if k_override else best_k
    km_final = KMeans(n_clusters=final_k, random_state=42, n_init=10)
    emp_df['cluster_id'] = km_final.fit_predict(X_sc)

    centroids_orig = scaler.inverse_transform(km_final.cluster_centers_)
    archetype_map  = {i: _archetype(c) for i, c in enumerate(centroids_orig)}
    emp_df['archetype_label'] = emp_df['cluster_id'].map(archetype_map)

    # Cultural distance from centroid (for conflict engine)
    dists = []
    for i, row in emp_df.iterrows():
        cid   = int(row['cluster_id'])
        point = X_sc[emp_df.index.get_loc(i)]
        dist  = float(np.linalg.norm(point - km_final.cluster_centers_[cid]))
        dists.append(dist)
    emp_df['cultural_distance'] = dists

    joblib.dump({'kmeans': km_final, 'scaler': scaler}, M4_MODEL)

    # ── ENGINE 2 & 3 — PDI Weighting + Opinion Dynamics ─────────────────────
    eval_df = pd.read_sql(
        "SELECT evaluatee_id, evaluation_type, overall_rating "
        "FROM evaluations WHERE evaluation_type != 'Self'",
        db.bind
    )

    engine23 = []
    for eid in emp_df['employee_id']:
        sub = eval_df[eval_df['evaluatee_id'] == eid]
        if sub.empty:
            engine23.append({
                'employee_id': eid,
                'pdi_corrected_score': None, 'raw_avg_score': None, 'pdi_delta': None,
                'manager_avg': None, 'peer_avg': None, 'subordinate_avg': None,
                'divergence_score': None, 'opinion_flag': 'No Data'
            })
            continue

        type_avgs = {}
        for et in ['Manager', 'Peer', 'Subordinate']:
            t = sub[sub['evaluation_type'] == et]
            if not t.empty:
                type_avgs[et] = round(t['overall_rating'].mean(), 3)

        ws = sum(type_avgs[t] * PDI_WEIGHTS[t] for t in type_avgs)
        wt = sum(PDI_WEIGHTS[t] for t in type_avgs)
        pdi  = round(ws / wt, 3) if wt else None
        raw  = round(sub['overall_rating'].mean(), 3)
        vals = list(type_avgs.values())
        div  = round(statistics.stdev(vals), 3) if len(vals) > 1 else 0.0

        engine23.append({
            'employee_id':        eid,
            'pdi_corrected_score': pdi,
            'raw_avg_score':       raw,
            'pdi_delta':           round(pdi - raw, 3) if pdi else None,
            'manager_avg':         type_avgs.get('Manager'),
            'peer_avg':            type_avgs.get('Peer'),
            'subordinate_avg':     type_avgs.get('Subordinate'),
            'divergence_score':    div,
            'opinion_flag':        _div_flag(div),
        })

    e23_df = pd.DataFrame(engine23)
    merged = emp_df.merge(e23_df, on='employee_id', how='left')

    # ── ENGINE 4 — Team Composition + Conflict Risk ───────────────────────────
    perf_df = pd.read_sql(
        "SELECT employee_id, performance_score FROM performance_results", db.bind
    )
    merged = merged.merge(perf_df, on='employee_id', how='left')

    merged['conflict_risk'] = merged.apply(
        lambda r: _conflict_risk(r['divergence_score'], r['cultural_distance']), axis=1
    )

    # Team-level aggregation
    team_rows = []
    for proj, grp in merged.groupby('project_id'):
        unique_cl  = int(grp['cluster_id'].nunique())
        t_size     = len(grp)
        div_idx    = round(unique_cl / t_size, 3)
        avg_perf   = round(grp['performance_score'].mean(), 2) \
            if grp['performance_score'].notna().any() else None
        conf_cnt   = int((grp['conflict_risk'] == 'High').sum())
        comp       = grp['cluster_id'].value_counts().to_dict()
        inst       = grp['institution_id'].iloc[0]
        team_rows.append({
            'project_id':            proj,
            'institution_id':        inst,
            'team_size':             t_size,
            'cluster_composition':   {str(k): int(v) for k, v in comp.items()},
            'unique_clusters':       unique_cl,
            'diversity_index':       div_idx,
            'avg_performance_score': avg_perf,
            'conflict_risk_count':   conf_cnt,
            'model_version':         version,
        })
    team_df = pd.DataFrame(team_rows)

    valid = team_df.dropna(subset=['avg_performance_score'])
    div_perf_corr = round(
        valid['diversity_index'].corr(valid['avg_performance_score']), 4
    ) if len(valid) > 2 else None

    # ── Persist ───────────────────────────────────────────────────────────────
    db.query(CultureCluster).delete()
    db.query(TeamAnalysis).delete()

    for _, r in merged.iterrows():
        db.add(CultureCluster(
            employee_id          = r['employee_id'],
            cluster_id           = int(r['cluster_id']) if pd.notna(r['cluster_id']) else None,
            archetype_label      = r.get('archetype_label'),
            pdi_corrected_score  = r.get('pdi_corrected_score'),
            raw_avg_score        = r.get('raw_avg_score'),
            pdi_delta            = r.get('pdi_delta'),
            manager_avg          = r.get('manager_avg'),
            peer_avg             = r.get('peer_avg'),
            subordinate_avg      = r.get('subordinate_avg'),
            divergence_score     = r.get('divergence_score'),
            opinion_flag         = r.get('opinion_flag'),
            conflict_risk        = r.get('conflict_risk'),
            cultural_distance    = r.get('cultural_distance'),
            model_version        = version,
        ))

    for _, r in team_df.iterrows():
        db.add(TeamAnalysis(
            project_id            = r['project_id'],
            institution_id        = r['institution_id'],
            team_size             = int(r['team_size']),
            cluster_composition   = r['cluster_composition'],
            unique_clusters       = int(r['unique_clusters']),
            diversity_index       = float(r['diversity_index']),
            avg_performance_score = float(r['avg_performance_score']) if r['avg_performance_score'] else None,
            conflict_risk_count   = int(r['conflict_risk_count']),
            model_version         = version,
        ))
    db.commit()

    # Save meta
    meta = {
        'version':                      version,
        'analyzed_on':                  datetime.utcnow().isoformat(),
        'employees_analyzed':           len(merged),
        'final_k':                      final_k,
        'silhouette_scores':            {str(k): v for k, v in sil_scores.items()},
        'best_silhouette':              round(best_sil, 4),
        'archetype_labels':             {str(k): v for k, v in archetype_map.items()},
        'diversity_performance_corr':   div_perf_corr,
        'opinion_flag_distribution':    merged['opinion_flag'].value_counts().to_dict(),
        'conflict_risk_distribution':   merged['conflict_risk'].value_counts().to_dict(),
        'cluster_distribution':         {str(k): int(v) for k, v in
                                         merged['cluster_id'].value_counts().sort_index().items()},
        'teams_analyzed':               len(team_df),
    }
    with open(M4_META, 'w') as f:
        json.dump(meta, f, indent=2)

    return {**meta, 'status': 'success'}


# ── Read helpers ──────────────────────────────────────────────────────────────
def get_info() -> dict:
    if not os.path.exists(M4_META): return {'model_exists': False}
    with open(M4_META) as f: meta = json.load(f)
    return {'model_exists': True, **meta}

def get_clusters(db: Session) -> list:
    return [
        {c: getattr(r, c) for c in [
            'employee_id','cluster_id','archetype_label',
            'pdi_corrected_score','raw_avg_score','pdi_delta',
            'manager_avg','peer_avg','subordinate_avg',
            'divergence_score','opinion_flag','conflict_risk','cultural_distance'
        ]}
        for r in db.query(CultureCluster).all()
    ]

def get_teams(db: Session) -> list:
    return [
        {
            'project_id':            r.project_id,
            'institution_id':        r.institution_id,
            'team_size':             r.team_size,
            'cluster_composition':   r.cluster_composition,
            'unique_clusters':       r.unique_clusters,
            'diversity_index':       r.diversity_index,
            'avg_performance_score': r.avg_performance_score,
            'conflict_risk_count':   r.conflict_risk_count,
        }
        for r in db.query(TeamAnalysis).all()
    ]

def recommend_team(project_id: str, required_size: int, db: Session) -> dict:
    if not os.path.exists(M4_META):
        raise FileNotFoundError("Run Module 4 pipeline first.")

    clusters  = {r.employee_id: r for r in db.query(CultureCluster).all()}
    perfs     = {r.employee_id: r.performance_score for r in db.query(PerformanceResult).all()}
    employees = {e.employee_id: e for e in db.query(Employee).all()}
    on_proj   = {e.employee_id for e in db.query(Employee).filter(Employee.project_id == project_id)}

    candidates = []
    for eid, c in clusters.items():
        if eid in on_proj: continue
        candidates.append({
            'employee_id':    eid,
            'cluster_id':     c.cluster_id,
            'archetype_label':c.archetype_label,
            'conflict_risk':  c.conflict_risk,
            'perf_score':     perfs.get(eid, 70),
            'role':           employees[eid].job_role_id if eid in employees else 'SE',
        })

    if len(candidates) < required_size:
        raise ValueError(f"Not enough candidates ({len(candidates)} available).")

    cdf = pd.DataFrame(candidates).sort_values('perf_score', ascending=False)
    selected, seen_ids, seen_clusters = [], set(), set()

    # Pass 1: one best performer per cluster (diversity first)
    for cid in sorted(cdf['cluster_id'].unique()):
        if len(selected) >= required_size: break
        pool = cdf[(cdf['cluster_id']==cid) & (cdf['conflict_risk']!='High')]
        if not pool.empty:
            row = pool.iloc[0]
            selected.append(row.to_dict())
            seen_ids.add(row['employee_id'])
            seen_clusters.add(cid)

    # Pass 2: fill with top performers (avoid High conflict)
    fill = cdf[(~cdf['employee_id'].isin(seen_ids)) & (cdf['conflict_risk']!='High')]
    for _, row in fill.iterrows():
        if len(selected) >= required_size: break
        selected.append(row.to_dict())
        seen_ids.add(row['employee_id'])

    # Pass 3: relax conflict constraint if still not full
    if len(selected) < required_size:
        relax = cdf[~cdf['employee_id'].isin(seen_ids)]
        for _, row in relax.iterrows():
            if len(selected) >= required_size: break
            selected.append(row.to_dict())

    selected = selected[:required_size]
    sdf = pd.DataFrame(selected)

    return {
        'project_id':               project_id,
        'required_size':            required_size,
        'suggested_team':           selected,
        'diversity_index':          round(sdf['cluster_id'].nunique() / required_size, 3),
        'predicted_avg_performance':round(sdf['perf_score'].mean(), 2),
        'unique_sub_cultures':      int(sdf['cluster_id'].nunique()),
        'cluster_mix':              {str(k): int(v) for k, v in sdf['cluster_id'].value_counts().items()},
    }

def get_employee_detail(employee_id: str, db: Session) -> dict:
    r = db.query(CultureCluster).filter(CultureCluster.employee_id == employee_id).first()
    if not r: raise ValueError(f"No Module 4 data for {employee_id}.")
    return {c: getattr(r, c) for c in [
        'employee_id','cluster_id','archetype_label',
        'pdi_corrected_score','raw_avg_score','pdi_delta',
        'manager_avg','peer_avg','subordinate_avg',
        'divergence_score','opinion_flag','conflict_risk','cultural_distance'
    ]}