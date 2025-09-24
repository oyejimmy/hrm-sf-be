from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import EmployeeRequest, RequestLog, HRDocument, User
from ..schemas.request import (
    EmployeeRequestCreate, EmployeeRequestUpdate, EmployeeRequestResponse,
    RequestLogResponse, HRDocumentResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/requests", tags=["requests"])

# Employee Requests
@router.get("/", response_model=List[EmployeeRequestResponse])
def get_employee_requests(
    skip: int = 0,
    limit: int = 100,
    request_type: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(EmployeeRequest)
    
    if current_user.role == "employee":
        query = query.filter(EmployeeRequest.employee_id == current_user.id)
    
    if request_type:
        query = query.filter(EmployeeRequest.request_type == request_type)
    if status:
        query = query.filter(EmployeeRequest.status == status)
    if priority:
        query = query.filter(EmployeeRequest.priority == priority)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{request_id}", response_model=EmployeeRequestResponse)
def get_employee_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    request = db.query(EmployeeRequest).filter(EmployeeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if current_user.role == "employee" and request.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return request

@router.get("/my-requests/", response_model=List[EmployeeRequestResponse])
def get_my_requests(
    request_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(EmployeeRequest).filter(EmployeeRequest.employee_id == current_user.id)
    
    if request_type:
        query = query.filter(EmployeeRequest.request_type == request_type)
    if status:
        query = query.filter(EmployeeRequest.status == status)
    
    return query.order_by(EmployeeRequest.created_at.desc()).all()

@router.post("/", response_model=EmployeeRequestResponse)
def create_employee_request(
    request: EmployeeRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_request = EmployeeRequest(**request.dict(), employee_id=current_user.id)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    # Create initial log entry
    log_entry = RequestLog(
        request_id=db_request.id,
        action="created",
        performed_by=current_user.id,
        details=f"Request created: {request.subject}"
    )
    db.add(log_entry)
    db.commit()
    
    return db_request

@router.put("/{request_id}", response_model=EmployeeRequestResponse)
def update_employee_request(
    request_id: int,
    request: EmployeeRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_request = db.query(EmployeeRequest).filter(EmployeeRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Only allow employee to update their own pending requests
    if current_user.role == "employee":
        if db_request.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if db_request.status != "pending":
            raise HTTPException(status_code=400, detail="Cannot update non-pending request")
    
    for field, value in request.dict(exclude_unset=True).items():
        setattr(db_request, field, value)
    
    db.commit()
    db.refresh(db_request)
    
    # Create log entry
    log_entry = RequestLog(
        request_id=request_id,
        action="updated",
        performed_by=current_user.id,
        details="Request updated"
    )
    db.add(log_entry)
    db.commit()
    
    return db_request

@router.delete("/{request_id}")
def delete_employee_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_request = db.query(EmployeeRequest).filter(EmployeeRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Only allow employee to delete their own pending requests
    if current_user.role == "employee":
        if db_request.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if db_request.status != "pending":
            raise HTTPException(status_code=400, detail="Cannot delete non-pending request")
    
    db.delete(db_request)
    db.commit()
    return {"message": "Request deleted successfully"}

@router.put("/{request_id}/approve")
def approve_request(
    request_id: int,
    approver_comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    request = db.query(EmployeeRequest).filter(EmployeeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = "approved"
    request.approver_id = current_user.id
    request.approver_comments = approver_comments
    db.commit()
    
    # Create log entry
    log_entry = RequestLog(
        request_id=request_id,
        action="approved",
        performed_by=current_user.id,
        details=f"Request approved. Comments: {approver_comments or 'None'}"
    )
    db.add(log_entry)
    db.commit()
    
    return {"message": "Request approved successfully"}

@router.put("/{request_id}/reject")
def reject_request(
    request_id: int,
    approver_comments: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    request = db.query(EmployeeRequest).filter(EmployeeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = "rejected"
    request.approver_id = current_user.id
    request.approver_comments = approver_comments
    db.commit()
    
    # Create log entry
    log_entry = RequestLog(
        request_id=request_id,
        action="rejected",
        performed_by=current_user.id,
        details=f"Request rejected. Comments: {approver_comments}"
    )
    db.add(log_entry)
    db.commit()
    
    return {"message": "Request rejected successfully"}

@router.put("/{request_id}/in-progress")
def mark_request_in_progress(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    request = db.query(EmployeeRequest).filter(EmployeeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = "in_progress"
    db.commit()
    
    # Create log entry
    log_entry = RequestLog(
        request_id=request_id,
        action="in_progress",
        performed_by=current_user.id,
        details="Request marked as in progress"
    )
    db.add(log_entry)
    db.commit()
    
    return {"message": "Request marked as in progress"}

# Request Logs
@router.get("/{request_id}/logs", response_model=List[RequestLogResponse])
def get_request_logs(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    request = db.query(EmployeeRequest).filter(EmployeeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if current_user.role == "employee" and request.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return db.query(RequestLog).filter(RequestLog.request_id == request_id).order_by(RequestLog.timestamp.desc()).all()

# HR Documents
@router.get("/hr-documents/", response_model=List[HRDocumentResponse])
def get_hr_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(HRDocument)
    if document_type:
        query = query.filter(HRDocument.document_type == document_type)
    return query.offset(skip).limit(limit).all()

@router.post("/hr-documents/", response_model=HRDocumentResponse)
def upload_hr_document(
    document_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_document = HRDocument(**document_data, uploaded_by=current_user.id)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

# Request Statistics
@router.get("/stats/overview")
def get_request_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_requests = db.query(EmployeeRequest).count()
    pending_requests = db.query(EmployeeRequest).filter(EmployeeRequest.status == "pending").count()
    approved_requests = db.query(EmployeeRequest).filter(EmployeeRequest.status == "approved").count()
    rejected_requests = db.query(EmployeeRequest).filter(EmployeeRequest.status == "rejected").count()
    in_progress_requests = db.query(EmployeeRequest).filter(EmployeeRequest.status == "in_progress").count()
    
    # Request types breakdown
    request_types = db.query(EmployeeRequest.request_type, db.func.count(EmployeeRequest.id)).group_by(EmployeeRequest.request_type).all()
    request_types_dict = {req_type: count for req_type, count in request_types}
    
    return {
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
        "in_progress_requests": in_progress_requests,
        "request_types": request_types_dict
    }

@router.get("/stats/my-requests")
def get_my_request_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_requests = db.query(EmployeeRequest).filter(EmployeeRequest.employee_id == current_user.id).count()
    pending_requests = db.query(EmployeeRequest).filter(
        EmployeeRequest.employee_id == current_user.id,
        EmployeeRequest.status == "pending"
    ).count()
    approved_requests = db.query(EmployeeRequest).filter(
        EmployeeRequest.employee_id == current_user.id,
        EmployeeRequest.status == "approved"
    ).count()
    rejected_requests = db.query(EmployeeRequest).filter(
        EmployeeRequest.employee_id == current_user.id,
        EmployeeRequest.status == "rejected"
    ).count()
    
    return {
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests
    }