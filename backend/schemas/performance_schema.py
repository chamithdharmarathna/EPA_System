from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class TrainResponse(BaseModel):
    status: str
    employees_used: int
    classifier_accuracy: float
    cv_mean: float
    cv_std: float
    r2_score: float
    rmse: float
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
    classifier_accuracy: Optional[float] = None
    r2_score: Optional[float] = None