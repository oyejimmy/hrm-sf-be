from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, date

from ..database import get_db
from ..auth import get_current_user, require_role
from ..models.user import User
from ..models.employee import Employee
from ..models.request import Request, RequestType, RequestStatus
from ..schemas.request import (
    RequestCreate, RequestUpdate, RequestResponse, 
    RequestStats, RequestFilters
)

router = APIRouter(prefix="/api/requests", tags=["requests"])

# Specific routes must come before parameterized routes
@router.get("/my-requests", response_model=List[RequestResponse])
def get_my_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's requests"""
    requests = db.query(Request).filter(Request.user_id == current_user.id).all()
    return requests

@router.get("/stats", response_model=RequestStats)
def get_request_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get request statistics"""
    base_query = db.query(Request)
    
    # Role-based filtering for stats
    if current_user.role not in ['admin', 'hr']:
        base_query = base_query.filter(Request.user_id == current_user.id)
    
    total_requests = base_query.count()
    pending = base_query.filter(Request.status == 'pending').count()
    approved = base_query.filter(Request.status == 'approved').count()
    rejected = base_query.filter(Request.status == 'rejected').count()
    in_progress = base_query.filter(Request.status == 'in_progress').count()
    
    return RequestStats(
        total_requests=total_requests,
        pending=pending,
        approved=approved,
        rejected=rejected,
        in_progress=in_progress
    )

@router.get("/types")
def get_request_types():
    """Get available request types"""
    return [
        {"value": "leave", "label": "Leave Request"},
        {"value": "equipment", "label": "Equipment Request"},
        {"value": "document", "label": "Document Request"},
        {"value": "loan", "label": "Loan Request"},
        {"value": "travel", "label": "Travel Request"},
        {"value": "recognition", "label": "Recognition Request"},
        {"value": "other", "label": "Other"}
    ]

@router.get("/", response_model=List[RequestResponse])
async def get_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get requests based on user role"""
    query = db.query(Request)
    
    # Role-based filtering
    if current_user.role in ['admin', 'hr']:
        # Admin/HR can see all requests
        pass
    else:
        # Employees can only see their own requests
        query = query.filter(Request.user_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Request.status == status)
    if request_type:
        query = query.filter(Request.request_type == request_type)
    if priority:
        query = query.filter(Request.priority == priority)
    if search:
        query = query.filter(
            or_(
                Request.title.ilike(f"%{search}%"),
                Request.description.ilike(f"%{search}%")
            )
        )
    
    requests = query.offset(skip).limit(limit).all()
    return requests

@router.get("/{request_id}", response_model=RequestResponse)
async def get_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific request"""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions
    if current_user.role not in ['admin', 'hr'] and request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")
    
    return request

@router.post("/", response_model=RequestResponse)
async def create_request(
    request_data: RequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new request"""
    request = Request(
        user_id=current_user.id,
        title=request_data.title,
        description=request_data.description,
        request_type=request_data.request_type,
        priority=request_data.priority or 'medium',
        status='pending',
        amount=request_data.amount,
        document_type=request_data.document_type,
        start_date=request_data.start_date,
        end_date=request_data.end_date,
        equipment_type=request_data.equipment_type,
        destination=request_data.destination,
        recognition_type=request_data.recognition_type,
        created_at=datetime.utcnow()
    )
    
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

@router.put("/{request_id}", response_model=RequestResponse)
async def update_request(
    request_id: int,
    request_data: RequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update request"""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions
    if current_user.role not in ['admin', 'hr'] and request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this request")
    
    # Update fields
    for field, value in request_data.dict(exclude_unset=True).items():
        setattr(request, field, value)
    
    request.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(request)
    return request

@router.put("/{request_id}/approve")
async def approve_request(
    request_id: int,
    comments: Optional[str] = None,
    current_user: User = Depends(require_role(['admin', 'hr'])),
    db: Session = Depends(get_db)
):
    """Approve request (Admin/HR only)"""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = 'approved'
    request.approved_by = current_user.id
    request.approved_at = datetime.utcnow()
    if comments:
        request.approver_comments = comments
    
    db.commit()
    db.refresh(request)
    return {"message": "Request approved successfully"}

@router.put("/{request_id}/reject")
async def reject_request(
    request_id: int,
    comments: Optional[str] = None,
    current_user: User = Depends(require_role(['admin', 'hr'])),
    db: Session = Depends(get_db)
):
    """Reject request (Admin/HR only)"""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = 'rejected'
    request.approved_by = current_user.id
    request.approved_at = datetime.utcnow()
    if comments:
        request.approver_comments = comments
    
    db.commit()
    db.refresh(request)
    return {"message": "Request rejected successfully"}

@router.delete("/{request_id}")
async def delete_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete request"""
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions - only owner or admin/hr can delete
    if current_user.role not in ['admin', 'hr'] and request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this request")
    
    # Only allow deletion of pending requests
    if request.status != 'pending':
        raise HTTPException(status_code=400, detail="Can only delete pending requests")
    
    db.delete(request)
    db.commit()
    return {"message": "Request deleted successfully"}