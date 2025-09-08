from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from enum import Enum

class EmploymentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"

class EmployeeBase(BaseModel):
    user_id: str
    employee_id: str = Field(..., min_length=1, max_length=20)
    department: str = Field(..., min_length=1, max_length=100)
    position: str = Field(..., min_length=1, max_length=100)
    manager_id: Optional[str] = None
    hire_date: date
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    salary: Optional[float] = Field(None, ge=0)
    work_location: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[str] = Field(None, min_length=1, max_length=100)
    manager_id: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None
    salary: Optional[float] = Field(None, ge=0)
    work_location: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class EmployeeProfile(EmployeeResponse):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    profile_picture: Optional[str] = None