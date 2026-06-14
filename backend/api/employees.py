from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.models.employee import Employee
from backend.models.employee_kpi import EmployeeKPI
from backend.models.employee_behavior import EmployeeBehavior
from backend.schemas.employee_schema import EmployeeCreate, EmployeeResponse
from backend.schemas.employee_kpi_schema import EmployeeKPICreate, EmployeeKPIResponse
from backend.schemas.employee_behavior_schema import EmployeeBehaviorCreate, EmployeeBehaviorResponse

router = APIRouter()

def generate_employee_id(db: Session) -> str:
    last = db.query(Employee).order_by(Employee.id.desc()).first()
    if last:
        num = int(last.employee_id[1:]) + 1
    else:
        num = 1
    return f"E{num:03d}"

# Employee endpoints
@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    emp_id = generate_employee_id(db)

    db_employee = Employee(
        employee_id=emp_id,
        institution_id=employee.institution_id,
        project_id=employee.project_id,
        job_role_id=employee.job_role_id,
        dob=employee.dob,
        gender=employee.gender,
        years_of_experience=employee.years_of_experience,
        department=employee.department,
        primary_language=employee.primary_language,
        ethnicity=employee.ethnicity,
        attended_educational_institutes=employee.attended_educational_institutes
    )

    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.get("/", response_model=List[EmployeeResponse])
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# KPI endpoints - Note the prefix is now /kpi (not /employee-kpi)
@router.post("/kpi/", response_model=EmployeeKPIResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_kpi(kpi: EmployeeKPICreate, db: Session = Depends(get_db)):
    existing = db.query(EmployeeKPI).filter(EmployeeKPI.employee_id == kpi.employee_id).first()

    if existing:
        for key, value in kpi.dict().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_kpi = EmployeeKPI(**kpi.dict())
        db.add(db_kpi)
        db.commit()
        db.refresh(db_kpi)
        return db_kpi

@router.get("/kpi/{employee_id}", response_model=EmployeeKPIResponse)
def get_kpi(employee_id: str, db: Session = Depends(get_db)):
    kpi = db.query(EmployeeKPI).filter(EmployeeKPI.employee_id == employee_id).first()
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found for this employee")
    return kpi

# Behavior endpoints - Note the prefix is now /behavior (not /employee-behavior)
@router.post("/behavior/", response_model=EmployeeBehaviorResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_behavior(behavior: EmployeeBehaviorCreate, db: Session = Depends(get_db)):
    existing = db.query(EmployeeBehavior).filter(EmployeeBehavior.employee_id == behavior.employee_id).first()

    if existing:
        for key, value in behavior.dict().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_behavior = EmployeeBehavior(**behavior.dict())
        db.add(db_behavior)
        db.commit()
        db.refresh(db_behavior)
        return db_behavior

@router.get("/behavior/{employee_id}", response_model=EmployeeBehaviorResponse)
def get_behavior(employee_id: str, db: Session = Depends(get_db)):
    behavior = db.query(EmployeeBehavior).filter(EmployeeBehavior.employee_id == employee_id).first()
    if not behavior:
        raise HTTPException(status_code=404, detail="Behavior data not found for this employee")
    return behavior