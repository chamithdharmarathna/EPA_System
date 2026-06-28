from sqlalchemy import Column, String, Integer, Float, Text
from backend.database.database import Base

class Evaluation(Base):
    __tablename__ = "evaluations"

    evaluation_id     = Column(String(10), primary_key=True)
    evaluatee_id      = Column(String(10), nullable=False)
    evaluator_id      = Column(String(10), nullable=True)
    evaluation_type   = Column(String(20), nullable=False)
    relationship      = Column(String(50), nullable=True)
    institution_id    = Column(String(10), nullable=True)
    period_year       = Column(Integer, nullable=True)
    period_quarter    = Column(Integer, nullable=True)
    hierarchy_distance= Column(Integer, nullable=True)
    punctuality       = Column(Integer, nullable=True)
    problem_solving   = Column(Integer, nullable=True)
    leadership        = Column(Integer, nullable=True)
    collaboration     = Column(Integer, nullable=True)
    communication     = Column(Integer, nullable=True)
    overall_rating    = Column(Float,   nullable=True)
    feedback_text     = Column(Text,    nullable=True)
    created_at        = Column(String(50), nullable=True)