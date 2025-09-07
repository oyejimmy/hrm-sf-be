from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date
from bson import ObjectId

from app.models.leave import (
    LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestResponse, 
    LeaveApproval, LeaveBalance, LeavePolicy
)
from app.models.user import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.post("/request", response_model=LeaveRequestResponse)
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new leave request."""
    db = get_database()
    
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
    
    # Check for overlapping leave requests
    overlapping = await db.leave_requests.find_one({
        "user_id": str(current_user["_id"]),
        "status": {"$in": ["pending", "approved"]},
        "$or": [
            {
                "start_date": {"$lte": leave_data.end_date},
                "end_date": {"$gte": leave_data.start_date}
            }
        ]
    })
    
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a leave request for this period"
        )
    
    # Create leave request document
    leave_doc = {
        "user_id": str(current_user["_id"]),
        "leave_type": leave_data.leave_type.value,
        "start_date": leave_data.start_date,
        "end_date": leave_data.end_date,
        "reason": leave_data.reason,
        "status": "pending",
        "approved_by": None,
        "approved_at": None,
        "rejection_reason": None,
        "emergency_contact": leave_data.emergency_contact,
        "documents": leave_data.documents or [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.leave_requests.insert_one(leave_doc)
    leave_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Leave request created by user {current_user['_id']}")
    
    return LeaveRequestResponse(**leave_doc)

@router.get("/my-requests", response_model=List[LeaveRequestResponse])
async def get_my_leave_requests(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user's leave requests."""
    db = get_database()
    
    cursor = db.leave_requests.find({"user_id": str(current_user["_id"])}).sort("created_at", -1)
    requests = await cursor.to_list(length=None)
    
    return [LeaveRequestResponse(**req) for req in requests]

@router.get("/pending", response_model=List[LeaveRequestResponse])
async def get_pending_leave_requests(
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Get all pending leave requests."""
    db = get_database()
    
    cursor = db.leave_requests.find({"status": "pending"}).sort("created_at", -1)
    requests = await cursor.to_list(length=None)
    
    return [LeaveRequestResponse(**req) for req in requests]

@router.put("/approve/{request_id}", response_model=LeaveRequestResponse)
async def approve_leave_request(
    request_id: str,
    approval_data: LeaveApproval,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Approve or reject a leave request."""
    db = get_database()
    
    leave_request = await db.leave_requests.find_one({"_id": ObjectId(request_id)})
    if not leave_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    if leave_request["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leave request has already been processed"
        )
    
    # Update leave request
    update_data = {
        "status": approval_data.status.value,
        "approved_by": str(current_user["_id"]),
        "approved_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    if approval_data.status.value == "rejected" and approval_data.rejection_reason:
        update_data["rejection_reason"] = approval_data.rejection_reason
    
    await db.leave_requests.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": update_data}
    )
    
    # Get updated request
    updated_request = await db.leave_requests.find_one({"_id": ObjectId(request_id)})
    
    logger.info(f"Leave request {approval_data.status.value}: {request_id}")
    
    return LeaveRequestResponse(**updated_request)

@router.get("/balance/{user_id}", response_model=List[LeaveBalance])
async def get_leave_balance(
    user_id: str,
    year: int = Query(..., ge=2020),
    current_user: dict = Depends(get_current_active_user)
):
    """Get leave balance for a user."""
    db = get_database()
    
    # Check permissions
    if (current_user["role"] == UserRole.EMPLOYEE and 
        user_id != str(current_user["_id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get leave policies (this would typically come from a configuration)
    leave_policies = {
        "annual_leave": LeavePolicy(
            leave_type="annual_leave",
            max_days_per_year=21,
            requires_approval=True,
            advance_notice_days=7,
            max_consecutive_days=10
        ),
        "sick_leave": LeavePolicy(
            leave_type="sick_leave",
            max_days_per_year=10,
            requires_approval=False,
            advance_notice_days=0,
            max_consecutive_days=3
        ),
        "personal_leave": LeavePolicy(
            leave_type="personal_leave",
            max_days_per_year=5,
            requires_approval=True,
            advance_notice_days=3,
            max_consecutive_days=2
        )
    }
    
    balances = []
    
    for leave_type, policy in leave_policies.items():
        # Calculate used days for this leave type
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        cursor = db.leave_requests.find({
            "user_id": user_id,
            "leave_type": leave_type,
            "status": "approved",
            "start_date": {"$gte": start_date},
            "end_date": {"$lte": end_date}
        })
        
        used_days = 0
        for request in await cursor.to_list(length=None):
            days = (request["end_date"] - request["start_date"]).days + 1
            used_days += days
        
        remaining_days = policy.max_days_per_year - used_days
        
        balances.append(LeaveBalance(
            user_id=user_id,
            leave_type=leave_type,
            total_days=policy.max_days_per_year,
            used_days=used_days,
            remaining_days=max(0, remaining_days),
            year=year
        ))
    
    return balances

@router.get("/team-requests", response_model=List[LeaveRequestResponse])
async def get_team_leave_requests(
    current_user: dict = Depends(require_role(UserRole.TEAM_LEAD))
):
    """Get leave requests for team members."""
    db = get_database()
    
    # Get team members
    team_members = await db.employees.find({"manager_id": str(current_user["_id"])}).to_list(length=None)
    team_user_ids = [emp["user_id"] for emp in team_members]
    
    if not team_user_ids:
        return []
    
    cursor = db.leave_requests.find({
        "user_id": {"$in": team_user_ids},
        "status": "pending"
    }).sort("created_at", -1)
    
    requests = await cursor.to_list(length=None)
    
    return [LeaveRequestResponse(**req) for req in requests]
