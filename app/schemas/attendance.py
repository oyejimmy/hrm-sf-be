from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime

class BreakRecordBase(BaseModel):
    break_type: str = "general"
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None

class BreakRecordCreate(BreakRecordBase):
    pass

class BreakRecordResponse(BreakRecordBase):
    id: int
    attendance_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class AttendanceBase(BaseModel):
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: str
    hours_worked: Optional[str] = None
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    employee_id: int

class AttendanceUpdate(BaseModel):
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: Optional[str] = None
    hours_worked: Optional[str] = None
    notes: Optional[str] = None

class AttendanceResponse(AttendanceBase):
    id: int
    employee_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    break_records: List[BreakRecordResponse] = []
    
    class Config:
        from_attributes = True

class CheckInResponse(BaseModel):
    message: str
    attendance_id: int
    check_in_time: time
    status: str

class CheckOutResponse(BaseModel):
    message: str
    attendance_id: int
    check_out_time: time
    hours_worked: str
    status: str

class BreakStartResponse(BaseModel):
    message: str
    break_id: int
    start_time: datetime
    break_type: str

class BreakEndResponse(BaseModel):
    message: str
    break_id: int
    end_time: datetime
    duration_minutes: int

class AttendanceStatsResponse(BaseModel):
    total_present_days: int
    total_absent_days: int
    total_late_days: int
    total_hours_worked: float
    average_hours_per_day: float
    current_month_attendance: float
    break_time_today: int
    status_today: str

class TodayAttendanceResponse(BaseModel):
    attendance: Optional[AttendanceResponse] = None
    current_status: str
    can_check_in: bool
    can_check_out: bool
    can_start_break: bool
    can_end_break: bool
    active_break: Optional[BreakRecordResponse] = None
    total_break_time: int = 0
    hours_worked_today: str = "0:00"