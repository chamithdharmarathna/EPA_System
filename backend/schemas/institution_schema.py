from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InstitutionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Institution name")
    size: str = Field(..., description="Institution size: Small, Medium, or Large")

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionResponse(InstitutionBase):
    id: int
    institution_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    size: Optional[str] = None