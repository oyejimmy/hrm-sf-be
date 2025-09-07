from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from bson import ObjectId

class LeaveType(str, Enum):
    SICK_LEAVE = "sick_leave"
    ANNUAL_LEAVE = "annual_leave"
    PERSONAL_LEAVE = "personal_leave"
    MATERNITY_LEAVE = "maternity_leave"
    PATERNITY_LEAVE = "paternity_leave"
    EMERGENCY_LEAVE = "emergency_leave"
    UNPAID_LEAVE = "unpaid_leave"

class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class LeaveRequestBase(BaseModel):
    user_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=1, max_length=500)
    status: LeaveStatus = LeaveStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    emergency_contact: Optional[str] = None
    documents: Optional[List[str]] = None

class LeaveRequestCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=1, max_length=500)
    emergency_contact: Optional[str] = None
    documents: Optional[List[str]] = None

class LeaveRequestUpdate(BaseModel):
    leave_type: Optional[LeaveType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = Field(None, min_length=1, max_length=500)
    emergency_contact: Optional[str] = None
    documents: Optional[List[str]] = None

class LeaveRequestInDB(LeaveRequestBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class LeaveRequestResponse(LeaveRequestBase):
    id: str
    created_at: datetime
    updated_at: datetime

class LeaveApproval(BaseModel):
    status: LeaveStatus
    rejection_reason: Optional[str] = None

class LeaveBalance(BaseModel):
    user_id: str
    leave_type: LeaveType
    total_days: int
    used_days: int
    remaining_days: int
    year: int

class LeavePolicy(BaseModel):
    leave_type: LeaveType
    max_days_per_year: int
    requires_approval: bool
    advance_notice_days: int
    max_consecutive_days: Optional[int] = None
    carry_forward_days: int = 0
