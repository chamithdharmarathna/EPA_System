from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.services import performance_service as svc
from backend.schemas.performance_schema import TrainResponse, PredictionResponse, ModelInfoResponse

router = APIRouter()

@router.post("/train", response_model=TrainResponse)
def train_model(db: Session = Depends(get_db)):
    try:
        return svc.train(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@router.get("/info", response_model=ModelInfoResponse)
def model_info():
    return svc.get_model_info()

@router.get("/predict/{employee_id}")
def predict_employee(employee_id: str, db: Session = Depends(get_db)):
    try:
        return svc.predict_one(employee_id, db)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/predict-all")
def predict_all(db: Session = Depends(get_db)):
    try:
        return svc.predict_all(db)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/results")
def get_results(db: Session = Depends(get_db)):
    return svc.get_all_results(db)

@router.get("/quarterly/{employee_id}")
def quarterly_trend(employee_id: str, db: Session = Depends(get_db)):
    try:
        return svc.get_quarterly_trend(employee_id, db)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))