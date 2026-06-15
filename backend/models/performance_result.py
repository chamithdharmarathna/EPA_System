from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from datetime import datetime
from backend.database.database import Base

class PerformanceResult(Base):
    __tablename__ = "performance_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(10), nullable=False)
    performance_score = Column(Float, nullable=False)
    performance_band = Column(String(20), nullable=False)  # High / Medium / Low
    confidence = Column(Float, nullable=True)
    feature_snapshot = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    predicted_at = Column(DateTime, default=datetime.utcnow)