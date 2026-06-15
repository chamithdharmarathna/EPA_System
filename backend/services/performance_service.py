import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from backend.models.employee import Employee
from backend.models.employee_kpi import EmployeeKPI
from backend.models.employee_behavior import EmployeeBehavior
from backend.models.performance_result import PerformanceResult

MODEL_DIR = "data/models"
CLF_PATH  = f"{MODEL_DIR}/perf_classifier.joblib"
REG_PATH  = f"{MODEL_DIR}/perf_regressor.joblib"
META_PATH = f"{MODEL_DIR}/perf_meta.json"

ROLE_MAP = {"PM":0,"SE":1,"QA":2,"DevOps":3,"BA":4,
            "UI/UX":5,"Support":6,"Admin":7,"Manager":8}

FEATURE_COLS = [
    "years_of_experience","job_role_encoded",
    "task_completion_rate","on_time_delivery_rate","defect_count",
    "issue_resolution_rate","quality_score","rework_count","blockers_count",
    "punctuality","problem_solving","leadership","collaboration","communication",
    "no_nopay_leave","avg_response_time","meetings_attended",
    "learning_hours","team_interaction_frequency"
]

def _compute_score(kpi: EmployeeKPI, beh: EmployeeBehavior) -> float:
    """Composite performance score 0-100 with small noise."""
    tc  = kpi.task_completion_rate or 0
    ot  = kpi.on_time_delivery_rate or 0
    qs  = (kpi.quality_score or 0) / 10
    ir  = kpi.issue_resolution_rate or 0
    dp  = min((kpi.defect_count or 0) / 50, 1.0)
    rp  = min((kpi.rework_count or 0) / 20, 1.0)
    bp  = min((kpi.blockers_count or 0) / 15, 1.0)

    kpi_score = (tc*0.30 + ot*0.25 + qs*0.20 + ir*0.10 +
                 (1-dp)*0.08 + (1-rp)*0.04 + (1-bp)*0.03)

    soft_avg  = ((beh.punctuality or 3) + (beh.problem_solving or 3) +
                 (beh.leadership or 3) + (beh.collaboration or 3) +
                 (beh.communication or 3)) / 25          # /25 → 0-1
    meets     = min((beh.meetings_attended or 0) / 30, 1.0)
    learn     = min((beh.learning_hours or 0) / 20, 1.0)
    interact  = (beh.team_interaction_frequency or 3) / 5
    leave_pen = min((beh.no_nopay_leave or 0) / 10, 1.0)
    resp      = 1 - min((beh.avg_response_time or 30) / 120, 1.0)

    beh_score = (soft_avg*0.50 + meets*0.10 + learn*0.15 +
                 interact*0.10 + (1-leave_pen)*0.10 + resp*0.05)

    raw = (kpi_score*0.60 + beh_score*0.40) * 100
    noise = np.random.normal(0, 2.5)
    return round(float(np.clip(raw + noise, 0, 100)), 2)

def _band(score: float) -> str:
    if score >= 85: return "High"
    if score >= 78: return "Medium"
    return "Low"

def _features(emp: Employee, kpi: EmployeeKPI, beh: EmployeeBehavior) -> dict:
    return {
        "years_of_experience":       emp.years_of_experience or 0,
        "job_role_encoded":          ROLE_MAP.get(emp.job_role_id, 0),
        "task_completion_rate":      kpi.task_completion_rate or 0,
        "on_time_delivery_rate":     kpi.on_time_delivery_rate or 0,
        "defect_count":              kpi.defect_count or 0,
        "issue_resolution_rate":     kpi.issue_resolution_rate or 0,
        "quality_score":             kpi.quality_score or 0,
        "rework_count":              kpi.rework_count or 0,
        "blockers_count":            kpi.blockers_count or 0,
        "punctuality":               beh.punctuality or 3,
        "problem_solving":           beh.problem_solving or 3,
        "leadership":                beh.leadership or 3,
        "collaboration":             beh.collaboration or 3,
        "communication":             beh.communication or 3,
        "no_nopay_leave":            beh.no_nopay_leave or 0,
        "avg_response_time":         beh.avg_response_time or 30,
        "meetings_attended":         beh.meetings_attended or 0,
        "learning_hours":            beh.learning_hours or 0,
        "team_interaction_frequency":beh.team_interaction_frequency or 3,
    }

# ── Training ──────────────────────────────────────────────────────────────────

def train(db: Session) -> dict:
    os.makedirs(MODEL_DIR, exist_ok=True)
    np.random.seed(42)

    employees = db.query(Employee).all()
    rows = []
    for emp in employees:
        kpi = db.query(EmployeeKPI).filter(EmployeeKPI.employee_id == emp.employee_id).first()
        beh = db.query(EmployeeBehavior).filter(EmployeeBehavior.employee_id == emp.employee_id).first()
        if not kpi or not beh:
            continue
        feat = _features(emp, kpi, beh)
        score = _compute_score(kpi, beh)
        rows.append({**feat, "score": score, "band": _band(score)})

    if len(rows) < 20:
        raise ValueError(f"Need at least 20 complete employee records, found {len(rows)}.")

    df = pd.DataFrame(rows)
    X  = df[FEATURE_COLS]
    ys = df["score"]
    yb = df["band"]

    # Stratified split
    X_tr, X_te, ys_tr, ys_te, yb_tr, yb_te = train_test_split(
        X, ys, yb, test_size=0.20, random_state=42, stratify=yb
    )

    # Classifier
    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  GradientBoostingClassifier(
            n_estimators=150, max_depth=4, learning_rate=0.08, random_state=42))
    ])
    clf.fit(X_tr, yb_tr)
    acc = accuracy_score(yb_te, clf.predict(X_te))
    cv  = cross_val_score(clf, X, yb, cv=5, scoring="accuracy")

    # Regressor
    reg = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  GradientBoostingRegressor(
            n_estimators=150, max_depth=4, learning_rate=0.08, random_state=42))
    ])
    reg.fit(X_tr, ys_tr)
    ys_pred = reg.predict(X_te)
    r2   = round(r2_score(ys_te, ys_pred), 4)
    rmse = round(float(np.sqrt(mean_squared_error(ys_te, ys_pred))), 4)

    # Save
    version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    joblib.dump(clf, CLF_PATH)
    joblib.dump(reg, REG_PATH)
    meta = {
        "version": version,
        "trained_on": datetime.utcnow().isoformat(),
        "employees_trained": len(rows),
        "classifier_accuracy": round(acc, 4),
        "cv_mean": round(float(cv.mean()), 4),
        "cv_std":  round(float(cv.std()), 4),
        "r2_score": r2,
        "rmse": rmse,
        "class_distribution": yb.value_counts().to_dict(),
        "feature_importance": dict(zip(
            FEATURE_COLS,
            clf.named_steps["model"].feature_importances_.round(4).tolist()
        ))
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    return {
        "status": "success",
        "employees_used": len(rows),
        "classifier_accuracy": round(acc, 4),
        "cv_mean": meta["cv_mean"],
        "cv_std":  meta["cv_std"],
        "r2_score": r2,
        "rmse": rmse,
        "class_distribution": meta["class_distribution"],
        "model_version": version
    }

# ── Prediction ────────────────────────────────────────────────────────────────

def predict_one(employee_id: str, db: Session) -> dict:
    if not os.path.exists(CLF_PATH):
        raise FileNotFoundError("Model not trained yet. Please train first.")

    emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not emp:
        raise ValueError(f"Employee {employee_id} not found.")
    kpi = db.query(EmployeeKPI).filter(EmployeeKPI.employee_id == employee_id).first()
    beh = db.query(EmployeeBehavior).filter(EmployeeBehavior.employee_id == employee_id).first()
    if not kpi or not beh:
        raise ValueError(f"Employee {employee_id} has incomplete KPI or behavior data.")

    clf = joblib.load(CLF_PATH)
    reg = joblib.load(REG_PATH)

    feat = _features(emp, kpi, beh)
    X    = pd.DataFrame([feat])[FEATURE_COLS]

    band       = clf.predict(X)[0]
    proba      = clf.predict_proba(X)[0]
    confidence = round(float(proba.max()), 4)
    score      = round(float(reg.predict(X)[0]), 2)
    score      = float(np.clip(score, 0, 100))

    # Upsert result
    existing = db.query(PerformanceResult).filter(
        PerformanceResult.employee_id == employee_id
    ).first()

    with open(META_PATH) as f:
        meta = json.load(f)

    result_data = dict(
        employee_id=employee_id,
        performance_score=score,
        performance_band=band,
        confidence=confidence,
        feature_snapshot=feat,
        model_version=meta.get("version"),
        predicted_at=datetime.utcnow()
    )
    if existing:
        for k, v in result_data.items():
            setattr(existing, k, v)
    else:
        db.add(PerformanceResult(**result_data))
    db.commit()

    return {**result_data, "predicted_at": result_data["predicted_at"].isoformat()}

def predict_all(db: Session) -> list:
    employees = db.query(Employee).all()
    results, errors = [], []
    for emp in employees:
        try:
            results.append(predict_one(emp.employee_id, db))
        except Exception as e:
            errors.append({"employee_id": emp.employee_id, "error": str(e)})
    return {"predicted": len(results), "skipped": len(errors), "errors": errors}

def get_model_info() -> dict:
    if not os.path.exists(META_PATH):
        return {"model_exists": False}
    with open(META_PATH) as f:
        meta = json.load(f)
    return {
        "model_exists": True,
        "model_version":        meta.get("version"),
        "trained_on":           meta.get("trained_on"),
        "employees_trained":    meta.get("employees_trained"),
        "classifier_accuracy":  meta.get("classifier_accuracy"),
        "r2_score":             meta.get("r2_score"),
        "feature_importance":   meta.get("feature_importance", {})
    }

def get_all_results(db: Session) -> list:
    rows = db.query(PerformanceResult).order_by(PerformanceResult.predicted_at.desc()).all()
    return [
        {
            "employee_id":      r.employee_id,
            "performance_score": r.performance_score,
            "performance_band": r.performance_band,
            "confidence":       r.confidence,
            "predicted_at":     r.predicted_at.isoformat() if r.predicted_at else None
        }
        for r in rows
    ]

