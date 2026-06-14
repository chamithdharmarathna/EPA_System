from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from datetime import datetime
from backend.database.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(10), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    institution_id = Column(String(10), ForeignKey("institutions.institution_id"), nullable=False)
    team_size = Column(Integer, nullable=False)
    relative_effort = Column(Float, nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    project_complexity = Column(Float, nullable=True)  # Calculated field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)