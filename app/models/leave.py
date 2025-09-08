from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from enum import Enum

class LeaveType(str, Enum):
    ANNUAL = "annual"
    SICK = "sick"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    EMERGENCY = "emergency"
    UNPAID = "unpaid"

class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class LeaveBase(BaseModel):
    user_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=1, max_length=500)
    status: LeaveStatus = LeaveStatus.PENDING

class LeaveCreate(LeaveBase):
    pass

class LeaveUpdate(BaseModel):
    status: Optional[LeaveStatus] = None
    admin_notes: Optional[str] = Field(None, max_length=500)

class LeaveResponse(LeaveBase):
    id: str = Field(alias="_id")
    days_requested: int
    admin_notes: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class LeaveBalance(BaseModel):
    user_id: str
    annual_leave_balance: float
    sick_leave_balance: float
    total_leave_taken: float
    year: int