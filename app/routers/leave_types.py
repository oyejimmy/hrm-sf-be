from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.leave_type import LeaveType
from ..models.leave import LeaveBalance
from ..auth import get_current_user, require_role
from datetime import datetime

router = APIRouter(prefix="/api/leave-types", tags=["Leave Types"])

@router.get("/")
def get_leave_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    leave_types = db.query(LeaveType).filter(LeaveType.is_active == True).all()
    return leave_types

@router.post("/")
def create_leave_type(
    leave_type_data: dict,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    # Check if leave type already exists
    existing = db.query(LeaveType).filter(LeaveType.name == leave_type_data["name"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Leave type already exists")
    
    leave_type = LeaveType(
        name=leave_type_data["name"],
        description=leave_type_data.get("description"),
        default_allocation=leave_type_data["default_allocation"],
        created_by=current_user.id
    )
    
    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)
    
    # Create balances for all users
    users = db.query(User).all()
    current_year = datetime.now().year
    
    for user in users:
        balance = LeaveBalance(
            employee_id=user.id,
            leave_type=leave_type.name,
            year=current_year,
            total_allocated=leave_type.default_allocation,
            taken=0.0,
            remaining=leave_type.default_allocation
        )
        db.add(balance)
    
    db.commit()
    return leave_type

@router.put("/{leave_type_id}")
def update_leave_type(
    leave_type_id: int,
    leave_type_data: dict,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    leave_type.name = leave_type_data.get("name", leave_type.name)
    leave_type.description = leave_type_data.get("description", leave_type.description)
    leave_type.default_allocation = leave_type_data.get("default_allocation", leave_type.default_allocation)
    
    db.commit()
    return leave_type

@router.delete("/{leave_type_id}")
def delete_leave_type(
    leave_type_id: int,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    leave_type.is_active = False
    db.commit()
    return {"message": "Leave type deactivated successfully"}