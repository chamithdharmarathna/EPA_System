from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    institution_id: str = Field(..., description="Institution ID (e.g., I01)")
    team_size: int = Field(..., ge=1, le=100, description="Team size (1-100 employees)")
    relative_effort: float = Field(..., ge=0, description="Relative effort estimate")
    duration_weeks: int = Field(..., ge=1, le=520, description="Project duration in weeks")

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    project_id: str = Field(..., description="Auto-generated project ID (e.g., P001)")
    project_complexity: Optional[float] = Field(None, description="Calculated: effort / (team_size * duration)")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    team_size: Optional[int] = Field(None, ge=1, le=100)
    relative_effort: Optional[float] = Field(None, ge=0)
    duration_weeks: Optional[int] = Field(None, ge=1, le=520)