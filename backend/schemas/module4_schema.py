from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class PipelineResponse(BaseModel):
    status: str
    version: str
    employees_analyzed: int
    final_k: int
    best_silhouette: float
    silhouette_scores: Dict[str, float]
    archetype_labels: Dict[str, str]
    diversity_performance_corr: Optional[float]
    opinion_flag_distribution: Dict[str, int]
    conflict_risk_distribution: Dict[str, int]
    cluster_distribution: Dict[str, int]
    teams_analyzed: int

class ClusterRecord(BaseModel):
    employee_id: str
    cluster_id: Optional[int]
    archetype_label: Optional[str]
    pdi_corrected_score: Optional[float]
    raw_avg_score: Optional[float]
    pdi_delta: Optional[float]
    manager_avg: Optional[float]
    peer_avg: Optional[float]
    subordinate_avg: Optional[float]
    divergence_score: Optional[float]
    opinion_flag: Optional[str]
    conflict_risk: Optional[str]
    cultural_distance: Optional[float]

    class Config:
        from_attributes = True

class TeamRecord(BaseModel):
    project_id: str
    institution_id: Optional[str]
    team_size: Optional[int]
    cluster_composition: Optional[Any]
    unique_clusters: Optional[int]
    diversity_index: Optional[float]
    avg_performance_score: Optional[float]
    conflict_risk_count: Optional[int]

class RecommendRequest(BaseModel):
    project_id: str
    required_size: int

class InfoResponse(BaseModel):
    model_exists: bool
    version: Optional[str] = None
    analyzed_on: Optional[str] = None
    employees_analyzed: Optional[int] = None
    final_k: Optional[int] = None
    best_silhouette: Optional[float] = None
    diversity_performance_corr: Optional[float] = None
    opinion_flag_distribution: Optional[Dict[str, int]] = None
    conflict_risk_distribution: Optional[Dict[str, int]] = None
    cluster_distribution: Optional[Dict[str, int]] = None
    archetype_labels: Optional[Dict[str, str]] = None
    silhouette_scores: Optional[Dict[str, float]] = None