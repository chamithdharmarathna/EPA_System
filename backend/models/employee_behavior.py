from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from backend.database.database import Base

class EmployeeBehavior(Base):
    __tablename__ = "employee_behavior"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(10), ForeignKey("employees.employee_id"), unique=True, nullable=False)
    punctuality = Column(Integer, default=3)
    problem_solving = Column(Integer, default=3)
    leadership = Column(Integer, default=3)
    collaboration = Column(Integer, default=3)
    communication = Column(Integer, default=3)
    no_nopay_leave = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    meetings_attended = Column(Integer, default=0)
    learning_hours = Column(Float, default=0.0)
    team_interaction_frequency = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    