from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class TrainResponse(BaseModel):
    status: str
    employees_used: int
    r2_score: float
    rmse: float
    cv_r2_mean: float
    cv_r2_std: float
    band_accuracy: float
    class_distribution: Dict[str, int]
    model_version: str

class PredictionResponse(BaseModel):
    employee_id: str
    performance_score: float
    performance_band: str
    confidence: float
    feature_snapshot: Optional[Dict[str, Any]] = None
    predicted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModelInfoResponse(BaseModel):
    model_exists: bool
    model_version: Optional[str] = None
    trained_on: Optional[str] = None
    employees_trained: Optional[int] = None
    r2_score: Optional[float] = None
    rmse: Optional[float] = None
    band_accuracy: Optional[float] = None
    cv_r2_mean: Optional[float] = None
    cv_r2_std: Optional[float] = None
    feature_importance: Optional[Dict[str, float]] = None
    class_distribution: Optional[Dict[str, int]] = None
    kpi_weights: Optional[Dict[str, float]] = None