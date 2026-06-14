from sqlalchemy import Column, String, Integer, Float, Date, DateTime, JSON
from datetime import datetime
from backend.database.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(10), unique=True, nullable=False)
    institution_id = Column(String(10), nullable=False)
    project_id = Column(String(10), nullable=False)
    job_role_id = Column(String(50), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    years_of_experience = Column(Integer, nullable=False)
    department = Column(String(100), nullable=False)
    primary_language = Column(String(50), nullable=True)
    ethnicity = Column(String(50), nullable=True)
    attended_educational_institutes = Column(JSON, nullable=True)  # Store as JSON list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)