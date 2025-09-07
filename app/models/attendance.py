from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date, time
from enum import Enum
from bson import ObjectId

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"

class AttendanceBase(BaseModel):
    user_id: str
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: AttendanceStatus = AttendanceStatus.ABSENT
    work_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: Optional[AttendanceStatus] = None
    work_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    notes: Optional[str] = None

class AttendanceInDB(AttendanceBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class AttendanceResponse(AttendanceBase):
    id: str
    created_at: datetime
    updated_at: datetime

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
