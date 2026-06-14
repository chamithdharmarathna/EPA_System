from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from backend.database.database import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution_id = Column(String(10), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    size = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)