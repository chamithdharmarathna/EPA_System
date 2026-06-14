from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmployeeKPICreate(BaseModel):
    employee_id: str
    tasks_assigned: int = 0
    tasks_completed: int = 0
    task_completion_rate: float = 0.0
    tasks_on_time: int = 0
    on_time_delivery_rate: float = 0.0
    defect_count: int = 0
    issue_resolution_rate: float = 0.0
    quality_score: float = 0.0
    rework_count: int = 0
    blockers_count: int = 0

class EmployeeKPIResponse(EmployeeKPICreate):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True