from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmployeeBehaviorCreate(BaseModel):
    employee_id: str
    punctuality: int = 3
    problem_solving: int = 3
    leadership: int = 3
    collaboration: int = 3
    communication: int = 3
    no_nopay_leave: int = 0
    avg_response_time: float = 0.0
    meetings_attended: int = 0
    learning_hours: float = 0.0
    team_interaction_frequency: int = 3

class EmployeeBehaviorResponse(EmployeeBehaviorCreate):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True