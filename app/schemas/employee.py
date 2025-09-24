from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class EmployeeBase(BaseModel):
    employee_id: str
    position: Optional[str] = None
    employment_status: str = "full_time"
    hire_date: Optional[date] = None
    salary: Optional[float] = None
    work_location: str = "office"
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    marital_status: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    # Profile enhancement fields
    blood_group: Optional[str] = None
    qualification: Optional[str] = None
    work_schedule: Optional[str] = "Standard (9:00 AM - 6:00 PM)"
    team_size: Optional[int] = 0
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    
    # Emergency contact details
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_work_phone: Optional[str] = None
    emergency_contact_home_phone: Optional[str] = None
    emergency_contact_address: Optional[str] = None
    
    # Compensation details
    bonus_target: Optional[str] = None
    stock_options: Optional[str] = None
    last_salary_increase: Optional[str] = None
    next_review_date: Optional[str] = None
    
    # Additional profile fields
    personal_email: Optional[str] = None
    nationality: Optional[str] = None
    religion: Optional[str] = None
    languages_known: Optional[str] = None
    hobbies: Optional[str] = None
    skills_summary: Optional[str] = None
    certifications: Optional[str] = None
    education_level: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None

class EmployeeCreate(EmployeeBase):
    user_id: int
    department_id: Optional[int] = None
    manager_id: Optional[int] = None

class EmployeeUpdate(BaseModel):
    position: Optional[str] = None
    employment_status: Optional[str] = None
    salary: Optional[float] = None
    work_location: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    blood_group: Optional[str] = None
    qualification: Optional[str] = None
    work_schedule: Optional[str] = None
    team_size: Optional[int] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_work_phone: Optional[str] = None
    emergency_contact_home_phone: Optional[str] = None
    emergency_contact_address: Optional[str] = None
    bonus_target: Optional[str] = None
    stock_options: Optional[str] = None
    last_salary_increase: Optional[str] = None
    next_review_date: Optional[str] = None
    personal_email: Optional[str] = None
    nationality: Optional[str] = None
    religion: Optional[str] = None
    languages_known: Optional[str] = None
    hobbies: Optional[str] = None
    skills_summary: Optional[str] = None
    certifications: Optional[str] = None
    education_level: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None

class EmployeeResponse(EmployeeBase):
    id: int
    user_id: int
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ProfileData(BaseModel):
    """Enhanced profile data for frontend integration"""
    personalInfo: dict
    emergencyContacts: list
    jobInfo: dict
    compensation: dict
    skills: list
    documents: list