from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Complaint, ComplaintComment, User
from ..schemas.complaint import ComplaintCreate, ComplaintUpdate, ComplaintResponse, ComplaintCommentCreate, ComplaintCommentResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

@router.get("/", response_model=List[ComplaintResponse])
def get_complaints(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Complaint)
    if current_user.role == "employee":
        query = query.filter(Complaint.employee_id == current_user.id)
    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    if priority:
        query = query.filter(Complaint.priority == priority)
    return query.offset(skip).limit(limit).all()

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
    db_complaint = Complaint(**complaint.dict(), employee_id=current_user.id)
    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)
    return db_complaint

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
    
    if current_user.role == "employee" and db_complaint.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    for field, value in complaint.dict(exclude_unset=True).items():
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
    
    if current_user.role == "employee" and db_complaint.employee_id != current_user.id:
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
    
    if current_user.role == "employee" and complaint.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_comment = ComplaintComment(
        **comment.dict(),
        complaint_id=complaint_id,
        user_id=current_user.id
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
    
    complaint.assigned_to = assigned_to
    complaint.status = "in_progress"
    db.commit()
    return {"message": "Complaint assigned successfully"}

@router.put("/{complaint_id}/resolve")
def resolve_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = "resolved"
    db.commit()
    return {"message": "Complaint resolved successfully"}