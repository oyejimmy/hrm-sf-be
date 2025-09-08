from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date, time
from enum import Enum

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    WORK_FROM_HOME = "work_from_home"

class AttendanceBase(BaseModel):
    user_id: str
    date: date
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    status: AttendanceStatus
    work_hours: Optional[float] = Field(None, ge=0, le=24)
    overtime_hours: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    status: Optional[AttendanceStatus] = None
    work_hours: Optional[float] = Field(None, ge=0, le=24)
    overtime_hours: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)

class AttendanceResponse(AttendanceBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class AttendanceSummary(BaseModel):
    user_id: str
    month: int
    year: int
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    half_days: int
    total_work_hours: float
    total_overtime_hours: float
    attendance_percentage: float