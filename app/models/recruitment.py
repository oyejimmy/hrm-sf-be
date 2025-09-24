from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class JobPosting(Base):
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    position_level = Column(String, nullable=False)  # entry, junior, mid, senior
    employment_type = Column(String, nullable=False)  # full_time, part_time, contract, intern
    location = Column(String, nullable=False)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    job_description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    responsibilities = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)  # Array of skills
    preferred_skills = Column(JSON, nullable=True)  # Array of skills
    benefits = Column(Text, nullable=True)
    application_deadline = Column(Date, nullable=True)
    status = Column(String, default="active")  # active, inactive, closed, on_hold
    posted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    hiring_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department")
    posted_by_user = relationship("User", foreign_keys=[posted_by])
    hiring_manager = relationship("User", foreign_keys=[hiring_manager_id])
    applications = relationship("JobApplication", back_populates="job_posting")

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    linkedin_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)
    cover_letter_url = Column(String, nullable=True)
    total_experience_years = Column(Float, nullable=True)
    current_salary = Column(Float, nullable=True)
    expected_salary = Column(Float, nullable=True)
    notice_period_days = Column(Integer, nullable=True)
    skills = Column(JSON, nullable=True)  # Array of skills
    education = Column(JSON, nullable=True)  # Array of education objects
    work_experience = Column(JSON, nullable=True)  # Array of experience objects
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    applications = relationship("JobApplication", back_populates="candidate")

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    application_date = Column(Date, nullable=False)
    status = Column(String, default="applied")  # applied, screening, interview, offer, hired, rejected
    current_stage = Column(String, nullable=True)  # phone_screen, technical_interview, final_interview
    source = Column(String, nullable=True)  # website, referral, linkedin, etc.
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    offer_details = Column(JSON, nullable=True)  # Salary, benefits, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    job_posting = relationship("JobPosting", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    referrer = relationship("User")
    interviews = relationship("Interview", back_populates="application")

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False)
    interview_type = Column(String, nullable=False)  # phone, video, in_person, technical
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60)
    interviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location = Column(String, nullable=True)  # Room or video link
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled, no_show
    feedback = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    recommendation = Column(String, nullable=True)  # hire, reject, next_round
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    application = relationship("JobApplication", back_populates="interviews")
    interviewer = relationship("User")