from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import TrainingProgram, TrainingSession, TrainingEnrollment, TrainingRoadmap, User, Employee
from ..schemas.training import (
    TrainingProgramCreate, TrainingProgramUpdate, TrainingProgramResponse,
    TrainingSessionCreate, TrainingSessionResponse, TrainingEnrollmentResponse,
    TrainingRoadmapCreate, TrainingRoadmapResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/training", tags=["training"])

# Training Programs
@router.get("/programs/", response_model=List[TrainingProgramResponse])
def get_training_programs(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(TrainingProgram)
    if category:
        query = query.filter(TrainingProgram.category == category)
    if status:
        query = query.filter(TrainingProgram.status == status)
    return query.offset(skip).limit(limit).all()

@router.get("/programs/{program_id}", response_model=TrainingProgramResponse)
def get_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
    return program

@router.post("/programs/", response_model=TrainingProgramResponse)
def create_training_program(
    program: TrainingProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_program = TrainingProgram(**program.dict(), created_by=current_user.id)
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program

@router.put("/programs/{program_id}", response_model=TrainingProgramResponse)
def update_training_program(
    program_id: int,
    program: TrainingProgramUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    if not db_program:
        raise HTTPException(status_code=404, detail="Training program not found")
    
    for field, value in program.dict(exclude_unset=True).items():
        setattr(db_program, field, value)
    
    db.commit()
    db.refresh(db_program)
    return db_program

@router.delete("/programs/{program_id}")
def delete_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    if not db_program:
        raise HTTPException(status_code=404, detail="Training program not found")
    
    db.delete(db_program)
    db.commit()
    return {"message": "Training program deleted successfully"}

# Training Sessions
@router.get("/sessions/", response_model=List[TrainingSessionResponse])
def get_training_sessions(
    skip: int = 0,
    limit: int = 100,
    program_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(TrainingSession)
    if program_id:
        query = query.filter(TrainingSession.program_id == program_id)
    if instructor_id:
        query = query.filter(TrainingSession.instructor_id == instructor_id)
    if status:
        query = query.filter(TrainingSession.status == status)
    return query.offset(skip).limit(limit).all()

@router.post("/sessions/", response_model=TrainingSessionResponse)
def create_training_session(
    session: TrainingSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_session = TrainingSession(**session.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

# Training Enrollments
@router.get("/enrollments/", response_model=List[TrainingEnrollmentResponse])
def get_training_enrollments(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    program_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(TrainingEnrollment)
    
    if current_user.role == "employee":
        query = query.filter(TrainingEnrollment.employee_id == current_user.id)
    elif current_user.role == "team_lead":
        # Team leads can see enrollments for their team members
        team_members = db.query(Employee).filter(Employee.supervisor_id == current_user.id).all()
        team_member_ids = [member.user_id for member in team_members]
        query = query.filter(TrainingEnrollment.employee_id.in_(team_member_ids))
    
    if employee_id:
        query = query.filter(TrainingEnrollment.employee_id == employee_id)
    if program_id:
        query = query.filter(TrainingEnrollment.program_id == program_id)
    if status:
        query = query.filter(TrainingEnrollment.status == status)
    
    return query.offset(skip).limit(limit).all()

@router.post("/enrollments/", response_model=TrainingEnrollmentResponse)
def enroll_in_training(
    enrollment_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    program_id = enrollment_data.get("program_id")
    employee_id = enrollment_data.get("employee_id", current_user.id)
    
    # Check if already enrolled
    existing_enrollment = db.query(TrainingEnrollment).filter(
        TrainingEnrollment.employee_id == employee_id,
        TrainingEnrollment.program_id == program_id
    ).first()
    
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Already enrolled in this program")
    
    db_enrollment = TrainingEnrollment(
        employee_id=employee_id,
        program_id=program_id,
        enrolled_by=current_user.id,
        status="enrolled"
    )
    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)
    return db_enrollment

@router.put("/enrollments/{enrollment_id}/progress")
def update_training_progress(
    enrollment_id: int,
    progress: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    if current_user.role == "employee" and enrollment.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    enrollment.progress = progress
    if progress >= 100:
        enrollment.status = "completed"
    elif progress > 0:
        enrollment.status = "in_progress"
    
    db.commit()
    return {"message": "Training progress updated successfully"}

@router.put("/enrollments/{enrollment_id}/complete")
def complete_training(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    if current_user.role == "employee" and enrollment.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    enrollment.status = "completed"
    enrollment.progress = 100
    db.commit()
    return {"message": "Training completed successfully"}

# Training Roadmaps
@router.get("/roadmaps/", response_model=List[TrainingRoadmapResponse])
def get_training_roadmaps(
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(TrainingRoadmap)
    if department:
        query = query.filter(TrainingRoadmap.department == department)
    if role:
        query = query.filter(TrainingRoadmap.role == role)
    return query.offset(skip).limit(limit).all()

@router.get("/roadmaps/{roadmap_id}", response_model=TrainingRoadmapResponse)
def get_training_roadmap(
    roadmap_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    roadmap = db.query(TrainingRoadmap).filter(TrainingRoadmap.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Training roadmap not found")
    return roadmap

@router.post("/roadmaps/", response_model=TrainingRoadmapResponse)
def create_training_roadmap(
    roadmap: TrainingRoadmapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_roadmap = TrainingRoadmap(**roadmap.dict(), created_by=current_user.id)
    db.add(db_roadmap)
    db.commit()
    db.refresh(db_roadmap)
    return db_roadmap

@router.get("/my-trainings/", response_model=List[TrainingEnrollmentResponse])
def get_my_trainings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(TrainingEnrollment).filter(TrainingEnrollment.employee_id == current_user.id).all()

@router.get("/stats/overview")
def get_training_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_programs = db.query(TrainingProgram).count()
    active_programs = db.query(TrainingProgram).filter(TrainingProgram.status == "active").count()
    total_enrollments = db.query(TrainingEnrollment).count()
    completed_trainings = db.query(TrainingEnrollment).filter(TrainingEnrollment.status == "completed").count()
    
    return {
        "total_programs": total_programs,
        "active_programs": active_programs,
        "total_enrollments": total_enrollments,
        "completed_trainings": completed_trainings
    }