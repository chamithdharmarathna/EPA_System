import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
from sklearn.pipeline import Pipeline

from backend.models.employee import Employee
from backend.models.employee_kpi import EmployeeKPI
from backend.models.performance_result import PerformanceResult

MODEL_DIR = "data/models"
REG_PATH  = f"{MODEL_DIR}/perf_regressor.joblib"
META_PATH = f"{MODEL_DIR}/perf_meta.json"

# KPI weights — transparent and explainable
KPI_WEIGHTS = {
    "task_completion_rate":  0.30,
    "on_time_delivery_rate": 0.25,
    "quality_score_norm":    0.20,   # quality_score / 10
    "issue_resolution_rate": 0.10,
    "defect_penalty":        0.08,   # 1 - min(defect_count/50, 1)
    "rework_penalty":        0.04,   # 1 - min(rework_count/20, 1)
    "blocker_penalty":       0.03,   # 1 - min(blockers_count/15, 1)
}

FEATURE_COLS = [
    "task_completion_rate", "on_time_delivery_rate",
    "defect_count", "issue_resolution_rate", "quality_score",
    "rework_count", "blockers_count"
]


def _current_score(kpi: EmployeeKPI) -> float:
    """Rule-based score directly from KPI weights. Fully explainable."""
    tc  = kpi.task_completion_rate or 0
    ot  = kpi.on_time_delivery_rate or 0
    qs  = (kpi.quality_score or 0) / 10
    ir  = kpi.issue_resolution_rate or 0
    dp  = 1 - min((kpi.defect_count or 0) / 50, 1.0)
    rp  = 1 - min((kpi.rework_count or 0) / 20, 1.0)
    bp  = 1 - min((kpi.blockers_count or 0) / 15, 1.0)

    score = (tc*0.30 + ot*0.25 + qs*0.20 + ir*0.10 +
             dp*0.08 + rp*0.04 + bp*0.03) * 100
    return round(float(np.clip(score, 0, 100)), 2)


def _band(score: float) -> str:
    if score >= 88: return "High"
    if score >= 84: return "Medium"
    return "Low"


def _features(kpi: EmployeeKPI) -> dict:
    return {
        "task_completion_rate":  kpi.task_completion_rate or 0,
        "on_time_delivery_rate": kpi.on_time_delivery_rate or 0,
        "defect_count":          kpi.defect_count or 0,
        "issue_resolution_rate": kpi.issue_resolution_rate or 0,
        "quality_score":         kpi.quality_score or 0,
        "rework_count":          kpi.rework_count or 0,
        "blockers_count":        kpi.blockers_count or 0,
    }


def _latest_kpi(employee_id: str, db: Session) -> EmployeeKPI | None:
    return db.query(EmployeeKPI).filter(
        EmployeeKPI.employee_id == employee_id
    ).order_by(
        EmployeeKPI.period_year.desc(),
        EmployeeKPI.period_quarter.desc()
    ).first()


# ── Training ──────────────────────────────────────────────────────────────────

def train(db: Session) -> dict:
    os.makedirs(MODEL_DIR, exist_ok=True)
    np.random.seed(42)

    employees = db.query(Employee).all()
    rows = []

    for emp in employees:
        kpi = _latest_kpi(emp.employee_id, db)
        if not kpi:
            continue
        feat = _features(kpi)
        score = _current_score(kpi)   # use formula score as training label
        rows.append({**feat, "score": score, "band": _band(score)})

    if len(rows) < 20:
        raise ValueError(f"Need at least 20 employees with KPI records, found {len(rows)}.")

    df = pd.DataFrame(rows)
    X  = df[FEATURE_COLS]
    y  = df["score"]
    yb = df["band"]

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20, random_state=42)

    reg = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  GradientBoostingRegressor(
            n_estimators=200, max_depth=4,
            learning_rate=0.07, subsample=0.85,
            random_state=42))
    ])
    reg.fit(X_tr, y_tr)

    y_pred  = reg.predict(X_te)
    r2      = round(r2_score(y_te, y_pred), 4)
    rmse    = round(float(np.sqrt(mean_squared_error(y_te, y_pred))), 4)
    cv      = cross_val_score(reg, X, y, cv=5, scoring="r2")

    # Band accuracy
    pred_bands   = [_band(s) for s in y_pred]
    actual_bands = [_band(s) for s in y_te]
    band_acc     = round(accuracy_score(actual_bands, pred_bands), 4)

    version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    joblib.dump(reg, REG_PATH)

    meta = {
        "version":             version,
        "trained_on":          datetime.utcnow().isoformat(),
        "employees_trained":   len(rows),
        "r2_score":            r2,
        "rmse":                rmse,
        "cv_r2_mean":          round(float(cv.mean()), 4),
        "cv_r2_std":           round(float(cv.std()), 4),
        "band_accuracy":       band_acc,
        "class_distribution":  yb.value_counts().to_dict(),
        "kpi_weights":         KPI_WEIGHTS,
        "feature_importance":  dict(zip(
            FEATURE_COLS,
            reg.named_steps["model"].feature_importances_.round(4).tolist()
        ))
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    return {
        "status":             "success",
        "employees_used":     len(rows),
        "r2_score":           r2,
        "rmse":               rmse,
        "cv_r2_mean":         meta["cv_r2_mean"],
        "cv_r2_std":          meta["cv_r2_std"],
        "band_accuracy":      band_acc,
        "class_distribution": meta["class_distribution"],
        "model_version":      version
    }


# ── Prediction ────────────────────────────────────────────────────────────────

def predict_one(employee_id: str, db: Session) -> dict:
    if not os.path.exists(REG_PATH):
        raise FileNotFoundError("Model not trained yet.")

    emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not emp:
        raise ValueError(f"Employee {employee_id} not found.")

    kpi = _latest_kpi(employee_id, db)
    if not kpi:
        raise ValueError(f"Employee {employee_id} has no KPI records.")

    reg  = joblib.load(REG_PATH)
    feat = _features(kpi)
    X    = pd.DataFrame([feat])[FEATURE_COLS]

    current_score   = _current_score(kpi)
    predicted_score = round(float(np.clip(reg.predict(X)[0], 0, 100)), 2)
    score_delta     = round(predicted_score - current_score, 2)
    performance_band = _band(predicted_score)

    with open(META_PATH) as f:
        meta = json.load(f)

    result_data = dict(
        employee_id=employee_id,
        performance_score=predicted_score,
        performance_band=performance_band,
        confidence=round(1 - abs(score_delta) / 100, 4),
        feature_snapshot={
            **feat,
            "current_score":    current_score,
            "predicted_score":  predicted_score,
            "score_delta":      score_delta,
            "period_year":      kpi.period_year,
            "period_quarter":   kpi.period_quarter,
        },
        model_version=meta.get("version"),
        predicted_at=datetime.utcnow()
    )

    existing = db.query(PerformanceResult).filter(
        PerformanceResult.employee_id == employee_id
    ).first()
    if existing:
        for k, v in result_data.items():
            setattr(existing, k, v)
    else:
        db.add(PerformanceResult(**result_data))
    db.commit()

    return {
        **result_data,
        "current_score":   current_score,
        "predicted_score": predicted_score,
        "score_delta":     score_delta,
        "predicted_at":    result_data["predicted_at"].isoformat()
    }


def predict_all(db: Session) -> dict:
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
    return {"model_exists": True, **meta}


def get_all_results(db: Session) -> list:
    rows = db.query(PerformanceResult).order_by(
        PerformanceResult.predicted_at.desc()
    ).all()
    return [
        {
            "employee_id":       r.employee_id,
            "performance_score": r.performance_score,
            "performance_band":  r.performance_band,
            "current_score":     (r.feature_snapshot or {}).get("current_score"),
            "predicted_score":   (r.feature_snapshot or {}).get("predicted_score"),
            "score_delta":       (r.feature_snapshot or {}).get("score_delta"),
            "period_year":       (r.feature_snapshot or {}).get("period_year"),
            "period_quarter":    (r.feature_snapshot or {}).get("period_quarter"),
            "predicted_at":      r.predicted_at.isoformat() if r.predicted_at else None
        }
        for r in rows
    ]


def get_quarterly_trend(employee_id: str, db: Session) -> list:
    """All quarters for one employee with both current and predicted scores."""
    if not os.path.exists(REG_PATH):
        raise FileNotFoundError("Model not trained yet.")

    kpi_records = db.query(EmployeeKPI).filter(
        EmployeeKPI.employee_id == employee_id
    ).order_by(EmployeeKPI.period_year, EmployeeKPI.period_quarter).all()

    if not kpi_records:
        raise ValueError(f"No KPI records found for {employee_id}.")

    reg = joblib.load(REG_PATH)
    trend = []

    for kpi in kpi_records:
        feat  = _features(kpi)
        X     = pd.DataFrame([feat])[FEATURE_COLS]
        curr  = _current_score(kpi)
        pred  = round(float(np.clip(reg.predict(X)[0], 0, 100)), 2)
        label = f"Q{kpi.period_quarter} {kpi.period_year}"

        trend.append({
            "period_label":    label,
            "period_year":     kpi.period_year,
            "period_quarter":  kpi.period_quarter,
            "current_score":   curr,
            "predicted_score": pred,
            "score_delta":     round(pred - curr, 2),
            "performance_band": _band(pred),
            "task_completion_rate":  kpi.task_completion_rate,
            "on_time_delivery_rate": kpi.on_time_delivery_rate,
            "quality_score":         kpi.quality_score,
            "defect_count":          kpi.defect_count,
        })

    return trend