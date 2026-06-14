from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.models.institution import Institution
from pydantic import BaseModel
import time

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
    max_retries = 3
    for attempt in range(max_retries):
        try:
            last = db.query(Institution).order_by(Institution.id.desc()).first()
            if last:
                num = int(last.institution_id[1:]) + 1
            else:
                num = 1
            return f"I{num:02d}"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                db.rollback()
            else:
                raise e

@router.post("/", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
def create_institution(institution: InstitutionCreate, db: Session = Depends(get_db)):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Check if institution exists
            existing = db.query(Institution).filter(Institution.name == institution.name).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Institution '{institution.name}' already exists"
                )

            # Generate ID and create
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

        except Exception as e:
            db.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            raise e

@router.get("/", response_model=List[InstitutionResponse])
def get_institutions(db: Session = Depends(get_db)):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return db.query(Institution).all()
        except Exception as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            raise e

@router.delete("/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_institution(institution_id: str, db: Session = Depends(get_db)):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            inst = db.query(Institution).filter(Institution.institution_id == institution_id).first()
            if not inst:
                raise HTTPException(status_code=404, detail="Institution not found")
            db.delete(inst)
            db.commit()
            return None
        except Exception as e:
            db.rollback()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            raise e