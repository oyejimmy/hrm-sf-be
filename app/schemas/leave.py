from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class LeaveBase(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    days_requested: float
    reason: Optional[str] = None

class LeaveCreate(LeaveBase):
    pass

class LeaveUpdate(BaseModel):
    status: str
    rejection_reason: Optional[str] = None

class LeaveResponse(LeaveBase):
    id: int
    employee_id: int
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True