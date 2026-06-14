from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.models.institution import Institution
from pydantic import BaseModel

router = APIRouter()

class InstitutionCreate(BaseModel):
    name: str
    size: str

class InstitutionResponse(BaseModel):
    id: int
    institution_id: str
    name: str
    size: str

def generate_institution_id(db: Session) -> str:
    last = db.query(Institution).order_by(Institution.id.desc()).first()
    if last:
        num = int(last.institution_id[1:]) + 1
    else:
        num = 1
    return f"I{num:02d}"

@router.post("/", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_institution(institution: InstitutionCreate, db: Session = Depends(get_db)):
    existing = db.query(Institution).filter(Institution.name == institution.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Institution '{institution.name}' already exists"
        )

    inst_id = generate_institution_id(db)
    db_inst = Institution(
        institution_id=inst_id,
        name=institution.name,
        size=institution.size
    )

    db.add(db_inst)
    db.commit()
    db.refresh(db_inst)
    return db_inst

@router.get("/", response_model=List[InstitutionResponse])
def get_institutions(db: Session = Depends(get_db)):
    return db.query(Institution).all()

@router.delete("/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_institution(institution_id: str, db: Session = Depends(get_db)):
    inst = db.query(Institution).filter(Institution.institution_id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    db.delete(inst)
    db.commit()
    return None