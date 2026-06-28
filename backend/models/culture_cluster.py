from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from datetime import datetime
from backend.database.database import Base

class CultureCluster(Base):
    __tablename__ = "culture_clusters"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    employee_id         = Column(String(10), unique=True, nullable=False)
    # Engine 1 — clustering
    cluster_id          = Column(Integer, nullable=True)
    archetype_label     = Column(String(120), nullable=True)
    # Engine 2 — power distance
    pdi_corrected_score = Column(Float, nullable=True)
    raw_avg_score       = Column(Float, nullable=True)
    pdi_delta           = Column(Float, nullable=True)
    manager_avg         = Column(Float, nullable=True)
    peer_avg            = Column(Float, nullable=True)
    subordinate_avg     = Column(Float, nullable=True)
    # Engine 3 — opinion dynamics
    divergence_score    = Column(Float, nullable=True)
    opinion_flag        = Column(String(30), nullable=True)
    # Engine 4 — conflict
    conflict_risk       = Column(String(20), nullable=True)
    cultural_distance   = Column(Float, nullable=True)
    model_version       = Column(String(50), nullable=True)
    analyzed_at         = Column(DateTime, default=datetime.utcnow)


class TeamAnalysis(Base):
    __tablename__ = "team_analysis"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    project_id            = Column(String(10), unique=True, nullable=False)
    institution_id        = Column(String(10), nullable=True)
    team_size             = Column(Integer, nullable=True)
    cluster_composition   = Column(JSON, nullable=True)
    unique_clusters       = Column(Integer, nullable=True)
    diversity_index       = Column(Float, nullable=True)
    avg_performance_score = Column(Float, nullable=True)
    conflict_risk_count   = Column(Integer, nullable=True)
    model_version         = Column(String(50), nullable=True)
    analyzed_at           = Column(DateTime, default=datetime.utcnow)