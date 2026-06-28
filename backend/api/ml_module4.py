from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.services import module4_service as svc
from backend.schemas.module4_schema import (
    PipelineResponse, InfoResponse, ClusterRecord,
    TeamRecord, RecommendRequest
)
from typing import List

router = APIRouter()

@router.post("/run", response_model=PipelineResponse)
def run_pipeline(db: Session = Depends(get_db)):
    try:
        return svc.run_pipeline(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

@router.get("/info", response_model=InfoResponse)
def get_info():
    return svc.get_info()

@router.get("/clusters", response_model=List[ClusterRecord])
def get_clusters(db: Session = Depends(get_db)):
    return svc.get_clusters(db)

@router.get("/teams", response_model=List[TeamRecord])
def get_teams(db: Session = Depends(get_db)):
    return svc.get_teams(db)

@router.get("/employee/{employee_id}")
def get_employee_detail(employee_id: str, db: Session = Depends(get_db)):
    try:
        return svc.get_employee_detail(employee_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/recommend-team")
def recommend_team(req: RecommendRequest, db: Session = Depends(get_db)):
    try:
        return svc.recommend_team(req.project_id, req.required_size, db)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))