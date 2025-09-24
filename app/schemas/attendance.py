from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime

class AttendanceBase(BaseModel):
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str
    hours_worked: Optional[str] = None
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    employee_id: int

class AttendanceResponse(AttendanceBase):
    id: int
    employee_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True