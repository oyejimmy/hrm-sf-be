from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class JobPostingBase(BaseModel):
    title: str
    department_id: int
    position_level: str
    employment_type: str
    location: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    job_description: str
    requirements: str
    responsibilities: str
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    benefits: Optional[str] = None
    application_deadline: Optional[date] = None

class JobPostingCreate(JobPostingBase):
    hiring_manager_id: Optional[int] = None

class JobPostingUpdate(BaseModel):
    status: Optional[str] = None
    application_deadline: Optional[date] = None

class JobPosting(JobPostingBase):
    id: int
    status: str
    posted_by: int
    hiring_manager_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    total_experience_years: Optional[float] = None
    current_salary: Optional[float] = None
    expected_salary: Optional[float] = None
    notice_period_days: Optional[int] = None
    skills: Optional[List[str]] = None
    education: Optional[List[dict]] = None
    work_experience: Optional[List[dict]] = None

class CandidateCreate(CandidateBase):
    resume_url: Optional[str] = None
    cover_letter_url: Optional[str] = None

class Candidate(CandidateBase):
    id: int
    resume_url: Optional[str] = None
    cover_letter_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobApplicationBase(BaseModel):
    application_date: date
    source: Optional[str] = None
    notes: Optional[str] = None

class JobApplicationCreate(JobApplicationBase):
    job_posting_id: int
    candidate_id: int
    referrer_id: Optional[int] = None

class JobApplicationUpdate(BaseModel):
    status: Optional[str] = None
    current_stage: Optional[str] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    offer_details: Optional[dict] = None

class JobApplication(JobApplicationBase):
    id: int
    job_posting_id: int
    candidate_id: int
    status: str
    current_stage: Optional[str] = None
    referrer_id: Optional[int] = None
    rejection_reason: Optional[str] = None
    offer_details: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InterviewBase(BaseModel):
    interview_type: str
    scheduled_date: datetime
    duration_minutes: int = 60
    location: Optional[str] = None

class InterviewCreate(InterviewBase):
    application_id: int
    interviewer_id: int

class InterviewUpdate(BaseModel):
    status: Optional[str] = None
    feedback: Optional[str] = None
    rating: Optional[int] = None
    recommendation: Optional[str] = None

class Interview(InterviewBase):
    id: int
    application_id: int
    interviewer_id: int
    status: str
    feedback: Optional[str] = None
    rating: Optional[int] = None
    recommendation: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobPostingResponse(JobPosting):
    pass

class CandidateResponse(Candidate):
    pass

class JobApplicationResponse(JobApplication):
    pass

class InterviewResponse(Interview):
    pass
class JobPostingResponse(BaseModel):
    id: int
    title: str
    department: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class JobApplicationResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class InterviewResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    status: str
    scheduled_date: datetime
    class Config:
        from_attributes = True
