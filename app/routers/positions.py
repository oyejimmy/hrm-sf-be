from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.position import Position
from app.models.department import Department
from app.models.user import User
from app.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class PositionCreate(BaseModel):
    title: str
    description: str = None
    level: str = None
    department_id: int

class PositionResponse(BaseModel):
    id: int
    title: str
    description: str = None
    level: str = None
    department_id: int
    department_name: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[PositionResponse])
def get_positions(
    department_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all positions, optionally filtered by department"""
    try:
        query = db.query(Position, Department.name).join(Department, Position.department_id == Department.id)
        if department_id:
            query = query.filter(Position.department_id == department_id)
        
        results = query.all()
        return [
            PositionResponse(
                id=pos.id,
                title=pos.title,
                description=pos.description,
                level=pos.level,
                department_id=pos.department_id,
                department_name=dept_name or "Unknown"
            )
            for pos, dept_name in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching positions: {str(e)}")

@router.post("/", response_model=PositionResponse)
def create_position(
    position: PositionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new position (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_position = Position(
        title=position.title,
        description=position.description,
        level=position.level,
        department_id=position.department_id
    )
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    
    # Get department name
    department = db.query(Department).filter(Department.id == db_position.department_id).first()
    
    return PositionResponse(
        id=db_position.id,
        title=db_position.title,
        description=db_position.description,
        level=db_position.level,
        department_id=db_position.department_id,
        department_name=department.name if department else "Unknown"
    )