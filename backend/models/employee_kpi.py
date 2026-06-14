from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from backend.database.database import Base

class EmployeeKPI(Base):
    __tablename__ = "employee_kpi"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(10), ForeignKey("employees.employee_id"), unique=True, nullable=False)
    tasks_assigned = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    task_completion_rate = Column(Float, default=0.0)
    tasks_on_time = Column(Integer, default=0)
    on_time_delivery_rate = Column(Float, default=0.0)
    defect_count = Column(Integer, default=0)
    issue_resolution_rate = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    rework_count = Column(Integer, default=0)
    blockers_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)