from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Performance, User, Employee
from ..schemas.performance import PerformanceCreate, PerformanceUpdate, PerformanceResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.get("/", response_model=List[PerformanceResponse])
def get_performance_reviews(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    reviewer_id: Optional[int] = None,
    review_period: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Performance)
    
    if current_user.role == "employee":
        query = query.filter(Performance.employee_id == current_user.id)
    elif current_user.role == "team_lead":
        # Team leads can see reviews for their team members
        team_members = db.query(Employee).filter(Employee.supervisor_id == current_user.id).all()
        team_member_ids = [member.user_id for member in team_members]
        query = query.filter(Performance.employee_id.in_(team_member_ids))
    
    if employee_id:
        query = query.filter(Performance.employee_id == employee_id)
    if reviewer_id:
        query = query.filter(Performance.reviewer_id == reviewer_id)
    if review_period:
        query = query.filter(Performance.review_period == review_period)
    if status:
        query = query.filter(Performance.status == status)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{review_id}", response_model=PerformanceResponse)
def get_performance_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Performance).filter(Performance.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Performance review not found")
    
    # Check authorization
    if current_user.role == "employee" and review.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return review

@router.post("/", response_model=PerformanceResponse)
def create_performance_review(
    review: PerformanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_review = Performance(**review.dict(), reviewer_id=current_user.id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.put("/{review_id}", response_model=PerformanceResponse)
def update_performance_review(
    review_id: int,
    review: PerformanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_review = db.query(Performance).filter(Performance.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Performance review not found")
    
    # Check authorization
    if current_user.role not in ["admin", "hr"] and db_review.reviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    for field, value in review.dict(exclude_unset=True).items():
        setattr(db_review, field, value)
    
    db.commit()
    db.refresh(db_review)
    return db_review

@router.delete("/{review_id}")
def delete_performance_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_review = db.query(Performance).filter(Performance.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Performance review not found")
    
    db.delete(db_review)
    db.commit()
    return {"message": "Performance review deleted successfully"}

@router.put("/{review_id}/submit")
def submit_performance_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = db.query(Performance).filter(Performance.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Performance review not found")
    
    if review.reviewer_id != current_user.id and current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    review.status = "submitted"
    db.commit()
    return {"message": "Performance review submitted successfully"}

@router.put("/{review_id}/approve")
def approve_performance_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    review = db.query(Performance).filter(Performance.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Performance review not found")
    
    review.status = "approved"
    db.commit()
    return {"message": "Performance review approved successfully"}

@router.put("/{review_id}/complete")
def complete_performance_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    review = db.query(Performance).filter(Performance.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Performance review not found")
    
    review.status = "completed"
    db.commit()
    return {"message": "Performance review completed successfully"}

@router.get("/employee/{employee_id}/history", response_model=List[PerformanceResponse])
def get_employee_performance_history(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check authorization
    if current_user.role == "employee" and employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return db.query(Performance).filter(Performance.employee_id == employee_id).all()

@router.get("/stats/overview")
def get_performance_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_reviews = db.query(Performance).count()
    completed_reviews = db.query(Performance).filter(Performance.status == "completed").count()
    pending_reviews = db.query(Performance).filter(Performance.status.in_(["draft", "submitted"])).count()
    
    # Calculate average rating
    avg_rating = db.query(Performance.overall_rating).filter(Performance.overall_rating.isnot(None)).all()
    average_rating = sum([r[0] for r in avg_rating]) / len(avg_rating) if avg_rating else 0
    
    return {
        "total_reviews": total_reviews,
        "completed_reviews": completed_reviews,
        "pending_reviews": pending_reviews,
        "average_rating": round(average_rating, 2)
    }