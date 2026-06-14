from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class EmployeeBase(BaseModel):
    institution_id: str
    project_id: str
    job_role_id: str
    dob: date
    gender: str
    years_of_experience: int
    department: str
    primary_language: Optional[str] = None
    ethnicity: Optional[str] = None
    attended_educational_institutes: Optional[List[str]] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    id: int
    employee_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True