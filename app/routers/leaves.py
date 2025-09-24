from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..models.user import User
from ..models.leave import Leave
from ..schemas.leave import LeaveCreate, LeaveResponse, LeaveUpdate
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/leaves", tags=["Leave Management"])

@router.get("/", response_model=List[LeaveResponse])
def get_leaves(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Leave)
    
    # Role-based filtering
    if current_user.role == "employee":
        query = query.filter(Leave.employee_id == current_user.id)
    elif current_user.role == "team_lead":
        # Team leads can see their team's leave requests
        from ..models.employee import Employee
        team_member_ids = db.query(Employee.user_id).filter(Employee.manager_id == current_user.id).all()
        team_member_ids = [id[0] for id in team_member_ids] + [current_user.id]
        query = query.filter(Leave.employee_id.in_(team_member_ids))
    
    if status:
        query = query.filter(Leave.status == status)
    
    if employee_id and current_user.role in ["admin", "hr"]:
        query = query.filter(Leave.employee_id == employee_id)
    
    leaves = query.offset(skip).limit(limit).all()
    return leaves

@router.get("/my-leaves", response_model=List[LeaveResponse])
def get_my_leaves(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    leaves = db.query(Leave).filter(Leave.employee_id == current_user.id).all()
    return leaves

@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Check permissions
    if current_user.role == "employee" and leave.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif current_user.role == "team_lead":
        from ..models.employee import Employee
        employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
        if employee and employee.manager_id != current_user.id and leave.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return leave

@router.post("/", response_model=LeaveResponse)
def create_leave_request(
    leave_data: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Calculate days requested
    days_requested = (leave_data.end_date - leave_data.start_date).days + 1
    
    db_leave = Leave(
        employee_id=current_user.id,
        leave_type=leave_data.leave_type,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        days_requested=days_requested,
        reason=leave_data.reason
    )
    
    db.add(db_leave)
    db.commit()
    db.refresh(db_leave)
    
    return db_leave

@router.put("/{leave_id}/approve", response_model=LeaveResponse)
def approve_leave(
    leave_id: int,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Team leads can only approve their team's leaves
    if current_user.role == "team_lead":
        from ..models.employee import Employee
        employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
        if not employee or employee.manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    leave.status = "approved"
    leave.approved_by = current_user.id
    leave.approved_at = db.func.now()
    
    db.commit()
    db.refresh(leave)
    
    return leave

@router.put("/{leave_id}/reject", response_model=LeaveResponse)
def reject_leave(
    leave_id: int,
    rejection_data: LeaveUpdate,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Team leads can only reject their team's leaves
    if current_user.role == "team_lead":
        from ..models.employee import Employee
        employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
        if not employee or employee.manager_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    leave.status = "rejected"
    leave.approved_by = current_user.id
    leave.approved_at = db.func.now()
    leave.rejection_reason = rejection_data.rejection_reason
    
    db.commit()
    db.refresh(leave)
    
    return leave

@router.delete("/{leave_id}")
def cancel_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Only the employee who created the leave or admin/hr can cancel
    if current_user.role not in ["admin", "hr"] and leave.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Can only cancel pending leaves
    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending leave requests"
        )
    
    leave.status = "cancelled"
    db.commit()
    
    return {"message": "Leave request cancelled successfully"}