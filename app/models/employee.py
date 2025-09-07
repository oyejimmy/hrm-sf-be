from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from bson import ObjectId

class EmploymentStatus(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"

class EmployeeBase(BaseModel):
    user_id: str
    employee_id: str = Field(..., min_length=1, max_length=20)
    department: str = Field(..., min_length=1, max_length=100)
    position: str = Field(..., min_length=1, max_length=100)
    employment_status: EmploymentStatus
    hire_date: date
    salary: Optional[float] = None
    manager_id: Optional[str] = None
    work_location: Optional[str] = None
    work_schedule: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[str] = Field(None, min_length=1, max_length=100)
    employment_status: Optional[EmploymentStatus] = None
    salary: Optional[float] = None
    manager_id: Optional[str] = None
    work_location: Optional[str] = None
    work_schedule: Optional[str] = None

class EmployeeInDB(EmployeeBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class EmployeeResponse(EmployeeBase):
    id: str
    created_at: datetime
    updated_at: datetime

class PersonalDetails(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

class EmployeeProfile(EmployeeResponse):
    personal_details: Optional[PersonalDetails] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    education: Optional[List[Dict[str, Any]]] = None
    work_experience: Optional[List[Dict[str, Any]]] = None
