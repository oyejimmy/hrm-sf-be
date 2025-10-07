from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime
import uuid
from ..database import get_db
from ..models import Complaint, ComplaintComment, User, Employee
from ..schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintResponse, ComplaintCommentCreate, ComplaintCommentResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

@router.get("/", response_model=List[ComplaintResponse])
def get_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Complaint)
    
    # Role-based filtering
    if current_user.role == "employee":
        query = query.filter(Complaint.employee_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    if priority:
        query = query.filter(Complaint.priority == priority)
    if search:
        query = query.filter(
            or_(
                Complaint.title.ilike(f"%{search}%"),
                Complaint.description.ilike(f"%{search}%"),
                Complaint.tracking_id.ilike(f"%{search}%")
            )
        )
    
    return query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/my-complaints", response_model=List[ComplaintResponse])
def get_my_complaints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Complaint).filter(
        Complaint.employee_id == current_user.id
    ).order_by(Complaint.created_at.desc()).all()

@router.get("/stats")
def get_complaint_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee":
        # Employee stats
        my_complaints = db.query(Complaint).filter(Complaint.employee_id == current_user.id).count()
        pending = db.query(Complaint).filter(
            and_(Complaint.employee_id == current_user.id, Complaint.status == "pending")
        ).count()
        in_progress = db.query(Complaint).filter(
            and_(Complaint.employee_id == current_user.id, Complaint.status == "in_progress")
        ).count()
        resolved = db.query(Complaint).filter(
            and_(Complaint.employee_id == current_user.id, Complaint.status == "resolved")
        ).count()
        
        return {
            "total_complaints": my_complaints,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved
        }
    else:
        # Admin/HR stats
        total = db.query(Complaint).count()
        pending = db.query(Complaint).filter(Complaint.status == "pending").count()
        in_progress = db.query(Complaint).filter(Complaint.status == "in_progress").count()
        resolved = db.query(Complaint).filter(Complaint.status == "resolved").count()
        
        return {
            "total_complaints": total,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved
        }

@router.get("/categories")
def get_complaint_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get distinct categories
    if current_user.role == "employee":
        categories = db.query(Complaint.category).filter(
            Complaint.employee_id == current_user.id
        ).distinct().all()
    else:
        categories = db.query(Complaint.category).distinct().all()
    
    return [cat[0] for cat in categories if cat[0]]

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if current_user.role == "employee" and complaint.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return complaint

@router.post("/", response_model=ComplaintResponse)
def create_complaint(
    complaint: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validate input
        if not complaint.title or not complaint.title.strip():
            raise HTTPException(status_code=422, detail="Title is required")
        if not complaint.description or not complaint.description.strip():
            raise HTTPException(status_code=422, detail="Description is required")
        if not complaint.category or not complaint.category.strip():
            raise HTTPException(status_code=422, detail="Category is required")
        if complaint.priority not in ["low", "medium", "high"]:
            raise HTTPException(status_code=422, detail="Priority must be low, medium, or high")
        
        # Generate unique tracking ID
        tracking_id = f"CMP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        db_complaint = Complaint(
            title=complaint.title.strip(),
            description=complaint.description.strip(),
            category=complaint.category.strip(),
            priority=complaint.priority,
            employee_id=current_user.id,
            tracking_id=tracking_id
        )
        db.add(db_complaint)
        db.commit()
        db.refresh(db_complaint)
        return db_complaint
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create complaint: {str(e)}")

@router.put("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: int,
    complaint: ComplaintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not db_complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Role-based access control
    if current_user.role == "employee":
        if db_complaint.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Employees can only update certain fields
        allowed_fields = {"description"}
        update_data = {k: v for k, v in complaint.dict(exclude_unset=True).items() if k in allowed_fields}
    else:
        # Admin/HR can update all fields
        update_data = complaint.dict(exclude_unset=True)
        
        # Handle status changes
        if "status" in update_data and update_data["status"] == "resolved":
            db_complaint.resolved_at = datetime.now()
    
    for field, value in update_data.items():
        setattr(db_complaint, field, value)
    
    db.commit()
    db.refresh(db_complaint)
    return db_complaint

@router.delete("/{complaint_id}")
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not db_complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Role-based access control
    if current_user.role == "employee":
        if db_complaint.employee_id != current_user.id or db_complaint.status != "pending":
            raise HTTPException(status_code=403, detail="Can only delete pending complaints")
    elif current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(db_complaint)
    db.commit()
    return {"message": "Complaint deleted successfully"}

# Complaint Comments
@router.get("/{complaint_id}/comments", response_model=List[ComplaintCommentResponse])
def get_complaint_comments(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if current_user.role == "employee" and complaint.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return db.query(ComplaintComment).filter(ComplaintComment.complaint_id == complaint_id).all()

@router.post("/{complaint_id}/comments", response_model=ComplaintCommentResponse)
def add_complaint_comment(
    complaint_id: int,
    comment: ComplaintCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Role-based access control
    if current_user.role == "employee" and complaint.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Set internal flag for admin/HR comments
    is_internal = current_user.role in ["admin", "hr"] and comment.is_internal
    
    db_comment = ComplaintComment(
        complaint_id=complaint_id,
        user_id=current_user.id,
        content=comment.content,
        is_internal=is_internal
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.put("/{complaint_id}/assign")
def assign_complaint(
    complaint_id: int,
    assigned_to: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Verify assigned user exists
    assigned_user = db.query(User).filter(User.id == assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="Assigned user not found")
    
    complaint.assigned_to = assigned_to
    complaint.status = "in_progress"
    db.commit()
    return {"message": "Complaint assigned successfully"}

@router.put("/{complaint_id}/resolve")
def resolve_complaint(
    complaint_id: int,
    resolution: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = "resolved"
    complaint.resolved_at = datetime.now()
    if resolution:
        complaint.resolution = resolution
    
    db.commit()
    return {"message": "Complaint resolved successfully"}

@router.put("/{complaint_id}/close")
def close_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = "closed"
    db.commit()
    return {"message": "Complaint closed successfully"}