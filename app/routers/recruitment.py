from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import JobPosting, Candidate, JobApplication, Interview, User
from ..schemas.recruitment import (
    JobPostingCreate, JobPostingUpdate, JobPostingResponse,
    CandidateCreate, CandidateResponse, JobApplicationResponse,
    InterviewCreate, InterviewResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/recruitment", tags=["recruitment"])

# Job Postings
@router.get("/jobs/", response_model=List[JobPostingResponse])
def get_job_postings(
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    employment_type: Optional[str] = None,
    experience_level: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(JobPosting)
    if department:
        query = query.filter(JobPosting.department == department)
    if employment_type:
        query = query.filter(JobPosting.employment_type == employment_type)
    if experience_level:
        query = query.filter(JobPosting.experience_level == experience_level)
    if status:
        query = query.filter(JobPosting.status == status)
    if location:
        query = query.filter(JobPosting.location == location)
    return query.offset(skip).limit(limit).all()

@router.get("/jobs/{job_id}", response_model=JobPostingResponse)
def get_job_posting(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    return job

@router.post("/jobs/", response_model=JobPostingResponse)
def create_job_posting(
    job: JobPostingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_job = JobPosting(**job.dict(), created_by=current_user.id)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.put("/jobs/{job_id}", response_model=JobPostingResponse)
def update_job_posting(
    job_id: int,
    job: JobPostingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    for field, value in job.dict(exclude_unset=True).items():
        setattr(db_job, field, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job

@router.delete("/jobs/{job_id}")
def delete_job_posting(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    db.delete(db_job)
    db.commit()
    return {"message": "Job posting deleted successfully"}

@router.put("/jobs/{job_id}/activate")
def activate_job_posting(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    job.status = "active"
    db.commit()
    return {"message": "Job posting activated successfully"}

@router.put("/jobs/{job_id}/deactivate")
def deactivate_job_posting(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    job.status = "inactive"
    db.commit()
    return {"message": "Job posting deactivated successfully"}

# Candidates
@router.get("/candidates/", response_model=List[CandidateResponse])
def get_candidates(
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Candidate)
    if job_id:
        # Filter candidates who applied for specific job
        applications = db.query(JobApplication).filter(JobApplication.job_posting_id == job_id).all()
        candidate_ids = [app.candidate_id for app in applications]
        query = query.filter(Candidate.id.in_(candidate_ids))
    return query.offset(skip).limit(limit).all()

@router.get("/candidates/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.post("/candidates/", response_model=CandidateResponse)
def create_candidate(
    candidate: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_candidate = Candidate(**candidate.dict())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

# Job Applications
@router.get("/applications/", response_model=List[JobApplicationResponse])
def get_job_applications(
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    candidate_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(JobApplication)
    if job_id:
        query = query.filter(JobApplication.job_posting_id == job_id)
    if candidate_id:
        query = query.filter(JobApplication.candidate_id == candidate_id)
    if status:
        query = query.filter(JobApplication.status == status)
    return query.offset(skip).limit(limit).all()

# Hiring pipeline state machine: forward movement plus rejection/withdrawal.
VALID_TRANSITIONS = {
    "applied": {"screening", "rejected", "withdrawn"},
    "screening": {"interview", "rejected", "withdrawn"},
    "interview": {"offer", "rejected", "withdrawn"},
    "offer": {"hired", "rejected", "withdrawn"},
    "hired": set(),
    "rejected": set(),
    "withdrawn": set(),
}


@router.put("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    current = application.status or "applied"
    if status not in VALID_TRANSITIONS:
        raise HTTPException(status_code=422, detail=f"Unknown status '{status}'. Valid statuses: {', '.join(VALID_TRANSITIONS)}")
    if status not in VALID_TRANSITIONS.get(current, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot move an application from '{current}' to '{status}'. Allowed next steps: {', '.join(VALID_TRANSITIONS.get(current, set())) or 'none'}",
        )

    application.status = status
    db.commit()
    return {"message": "Application status updated", "status": status}


# ── Offers ──────────────────────────────────────────────────────────────────

@router.post("/applications/{application_id}/offer")
def extend_offer(
    application_id: int,
    offer: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Extend an offer to a candidate whose application is at the interview stage.

    Body: { "salary": number, "start_date": "YYYY-MM-DD",
            "expiry_date": "YYYY-MM-DD", "notes": str, "benefits": str }
    """
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if application.status != "interview":
        raise HTTPException(status_code=409, detail=f"Offers can only be extended after interviews (current stage: {application.status})")
    if not offer.get("salary"):
        raise HTTPException(status_code=422, detail="An offer must include a salary")

    application.status = "offer"
    application.offer_details = {
        "salary": offer.get("salary"),
        "start_date": offer.get("start_date"),
        "expiry_date": offer.get("expiry_date"),
        "benefits": offer.get("benefits"),
        "notes": offer.get("notes"),
        "extended_by": current_user.id,
        "extended_at": datetime.utcnow().isoformat(),
        "decision": None,
    }
    db.commit()
    return {"message": "Offer extended", "application_id": application.id, "offer": application.offer_details}


@router.put("/applications/{application_id}/offer/accept")
def accept_offer(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if application.status != "offer":
        raise HTTPException(status_code=409, detail="Only applications with an extended offer can be accepted")

    application.status = "hired"
    details = dict(application.offer_details or {})
    details["decision"] = "accepted"
    details["decided_at"] = datetime.utcnow().isoformat()
    application.offer_details = details
    db.commit()
    return {
        "message": "Offer accepted — candidate marked as hired. Create their employee record from Employee Management to start onboarding.",
        "application_id": application.id,
        "candidate_id": application.candidate_id,
    }


@router.put("/applications/{application_id}/offer/decline")
def decline_offer(
    application_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if application.status != "offer":
        raise HTTPException(status_code=409, detail="Only applications with an extended offer can be declined")

    application.status = "rejected"
    application.rejection_reason = (body or {}).get("reason") or "Offer declined by candidate"
    details = dict(application.offer_details or {})
    details["decision"] = "declined"
    details["decided_at"] = datetime.utcnow().isoformat()
    application.offer_details = details
    db.commit()
    return {"message": "Offer declined", "application_id": application.id}

# Interviews
@router.get("/interviews/", response_model=List[InterviewResponse])
def get_interviews(
    skip: int = 0,
    limit: int = 100,
    candidate_id: Optional[int] = None,
    interviewer_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Interview)
    if candidate_id:
        query = query.filter(Interview.candidate_id == candidate_id)
    if interviewer_id:
        query = query.filter(Interview.interviewer_id == interviewer_id)
    if status:
        query = query.filter(Interview.status == status)
    return query.offset(skip).limit(limit).all()

@router.post("/interviews/", response_model=InterviewResponse)
def schedule_interview(
    interview: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_interview = Interview(**interview.dict(), scheduled_by=current_user.id)
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview

@router.put("/interviews/{interview_id}/complete")
def complete_interview(
    interview_id: int,
    feedback: str,
    rating: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview.status = "completed"
    interview.feedback = feedback
    interview.rating = rating
    db.commit()
    return {"message": "Interview completed successfully"}

@router.get("/stats/overview")
def get_recruitment_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_jobs = db.query(JobPosting).count()
    active_jobs = db.query(JobPosting).filter(JobPosting.status == "active").count()
    total_applications = db.query(JobApplication).count()
    total_candidates = db.query(Candidate).count()
    
    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "total_candidates": total_candidates
    }