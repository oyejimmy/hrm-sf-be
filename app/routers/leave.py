from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.leave import LeaveCreate, LeaveUpdate, LeaveResponse, LeaveBalance
from app.models.sql_models import UserRole, LeaveStatus
from app.routers.auth import get_current_active_user, require_role
from app.database import get_db
from app.db.sqlite import SQLiteService
from app.core.logger import logger

router = APIRouter()

@router.post("/request", response_model=LeaveResponse)
async def create_leave_request(
    leave_data: LeaveCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new leave request."""
    # Validate dates
    if leave_data.start_date > leave_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date"
        )
    
    if leave_data.start_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be in the past"
        )
    
    # Create leave request
    leave_dict = {
        **leave_data.dict(),
        "user_id": current_user.id
    }
    
    leave_request = await SQLiteService.create_leave_request(db, leave_dict)
    
    logger.info(f"Leave request created by user {current_user.id}")
    
    return LeaveResponse(
        id=str(leave_request.id),
        user_id=leave_request.user_id,
        leave_type=leave_request.leave_type,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        reason=leave_request.reason,
        status=leave_request.status,
        approved_by=leave_request.approved_by,
        approved_at=leave_request.approved_at,
        rejection_reason=leave_request.rejection_reason,
        emergency_contact=leave_request.emergency_contact,
        documents=leave_request.documents,
        created_at=leave_request.created_at,
        updated_at=leave_request.updated_at
    )

@router.get("/my-requests", response_model=List[LeaveResponse])
async def get_my_leave_requests(
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's leave requests."""
    requests = await SQLiteService.get_user_leave_requests(db, current_user.id)
    
    return [LeaveResponse(
        id=str(req.id),
        user_id=req.user_id,
        leave_type=req.leave_type,
        start_date=req.start_date,
        end_date=req.end_date,
        reason=req.reason,
        status=req.status,
        approved_by=req.approved_by,
        approved_at=req.approved_at,
        rejection_reason=req.rejection_reason,
        emergency_contact=req.emergency_contact,
        documents=req.documents,
        created_at=req.created_at,
        updated_at=req.updated_at
    ) for req in requests]

@router.get("/pending", response_model=List[LeaveResponse])
async def get_pending_leave_requests(
    current_user = Depends(require_role(UserRole.HR)),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending leave requests."""
    requests = await SQLiteService.get_pending_leave_requests(db)
    
    return [LeaveResponse(
        id=str(req.id),
        user_id=req.user_id,
        leave_type=req.leave_type,
        start_date=req.start_date,
        end_date=req.end_date,
        reason=req.reason,
        status=req.status,
        approved_by=req.approved_by,
        approved_at=req.approved_at,
        rejection_reason=req.rejection_reason,
        emergency_contact=req.emergency_contact,
        documents=req.documents,
        created_at=req.created_at,
        updated_at=req.updated_at
    ) for req in requests]

@router.put("/approve/{request_id}", response_model=LeaveResponse)
async def approve_leave_request(
    request_id: str,
    approval_data: LeaveUpdate,
    current_user = Depends(require_role(UserRole.HR)),
    db: AsyncSession = Depends(get_db)
):
    """Approve or reject a leave request."""
    leave_request = await SQLiteService.get_leave_request_by_id(db, int(request_id))
    if not leave_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave request has already been processed"
        )
    
    # Update leave request
    update_data = {k: v for k, v in approval_data.dict().items() if v is not None}
    update_data.update({
        "approved_by": current_user.id,
        "approved_at": datetime.utcnow()
    })
    
    updated_request = await SQLiteService.update_leave_request(db, int(request_id), update_data)
    
    logger.info(f"Leave request updated: {request_id}")
    
    return LeaveResponse(
        id=str(updated_request.id),
        user_id=updated_request.user_id,
        leave_type=updated_request.leave_type,
        start_date=updated_request.start_date,
        end_date=updated_request.end_date,
        reason=updated_request.reason,
        status=updated_request.status,
        approved_by=updated_request.approved_by,
        approved_at=updated_request.approved_at,
        rejection_reason=updated_request.rejection_reason,
        emergency_contact=updated_request.emergency_contact,
        documents=updated_request.documents,
        created_at=updated_request.created_at,
        updated_at=updated_request.updated_at
    )

@router.get("/balance/{user_id}", response_model=LeaveBalance)
async def get_leave_balance(
    user_id: str,
    year: int = Query(2024, ge=2020),
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get leave balance for a user."""
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE and 
        int(user_id) != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Calculate leave balance (simplified)
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    requests = await SQLiteService.get_approved_leave_requests_for_year(
        db, int(user_id), start_date, end_date
    )
    
    total_leave_taken = 0
    for request in requests:
        days = (request.end_date - request.start_date).days + 1
        total_leave_taken += days
    
    return LeaveBalance(
        user_id=user_id,
        annual_leave_balance=21 - total_leave_taken,  # Assuming 21 days annual leave
        sick_leave_balance=10,  # Assuming 10 days sick leave
        total_leave_taken=total_leave_taken,
        year=year
    )