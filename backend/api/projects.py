from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database.database import get_db
from backend.models.project import Project
from backend.models.institution import Institution
from backend.schemas.project_schema import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter()

def generate_project_id(db: Session) -> str:
    last = db.query(Project).order_by(Project.id.desc()).first()
    if last:
        num = int(last.project_id[1:]) + 1
    else:
        num = 1
    return f"P{num:03d}"

def calculate_complexity(relative_effort: float, team_size: int, duration_weeks: int) -> float:
    """Calculate project complexity: effort / (team_size * duration)"""
    denominator = team_size * duration_weeks
    if denominator == 0:
        return 0.0
    return round(relative_effort / denominator, 2)

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    # Check if institution exists
    institution = db.query(Institution).filter(Institution.institution_id == project.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Check if project name already exists for this institution
    existing = db.query(Project).filter(
        Project.name == project.name,
        Project.institution_id == project.institution_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project name already exists for this institution")

    # Calculate complexity
    complexity = calculate_complexity(
        project.relative_effort,
        project.team_size,
        project.duration_weeks
    )

    proj_id = generate_project_id(db)
    db_project = Project(
        project_id=proj_id,
        name=project.name,
        institution_id=project.institution_id,
        team_size=project.team_size,
        relative_effort=project.relative_effort,
        duration_weeks=project.duration_weeks,
        project_complexity=complexity
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=List[ProjectResponse])
def get_projects(
        skip: int = 0,
        limit: int = 100,
        institution_id: Optional[str] = None,
        db: Session = Depends(get_db)
):
    query = db.query(Project)
    if institution_id:
        query = query.filter(Project.institution_id == institution_id)
    projects = query.offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
        project_id: str,
        project_update: ProjectUpdate,
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    if project_update.name is not None:
        existing = db.query(Project).filter(
            Project.name == project_update.name,
            Project.institution_id == project.institution_id,
            Project.project_id != project_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Project name already exists for this institution")
        project.name = project_update.name

    if project_update.team_size is not None:
        project.team_size = project_update.team_size

    if project_update.relative_effort is not None:
        project.relative_effort = project_update.relative_effort

    if project_update.duration_weeks is not None:
        project.duration_weeks = project_update.duration_weeks

    # Recalculate complexity if any of the three factors changed
    if (project_update.team_size is not None or
            project_update.relative_effort is not None or
            project_update.duration_weeks is not None):
        project.project_complexity = calculate_complexity(
            project.relative_effort,
            project.team_size,
            project.duration_weeks
        )

    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None