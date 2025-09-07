from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date, time
from app.models.sql_models import (
    UserRole, UserStatus, EmploymentStatus, AttendanceStatus, 
    LeaveType, LeaveStatus, Gender, MaritalStatus, Department,
    PositionLevel, WorkLocation, DocumentType, NotificationType,
    NotificationStatus
)

# User Models
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    team_id: Optional[int] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    team_id: Optional[int] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

# Employee Models
class EmployeeBase(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=20)
    department: Department
    position: str = Field(..., min_length=1, max_length=100)
    position_level: PositionLevel
    employment_status: EmploymentStatus
    hire_date: date
    salary: Optional[float] = None
    manager_id: Optional[int] = None
    work_location: Optional[WorkLocation] = None
    work_schedule: Optional[str] = None
    
    # Personal Details
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    user_id: int

class EmployeeUpdate(BaseModel):
    department: Optional[Department] = None
    position: Optional[str] = Field(None, min_length=1, max_length=100)
    position_level: Optional[PositionLevel] = None
    employment_status: Optional[EmploymentStatus] = None
    salary: Optional[float] = None
    manager_id: Optional[int] = None
    work_location: Optional[WorkLocation] = None
    work_schedule: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmployeeProfile(EmployeeResponse):
    user: UserResponse

# Attendance Models
class AttendanceBase(BaseModel):
    date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: AttendanceStatus = AttendanceStatus.ABSENT
    work_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    user_id: int

class AttendanceUpdate(BaseModel):
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    status: Optional[AttendanceStatus] = None
    work_hours: Optional[float] = None
    overtime_hours: Optional[float] = None
    notes: Optional[str] = None

class AttendanceResponse(AttendanceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AttendanceSummary(BaseModel):
    user_id: int
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

# Leave Models
class LeaveRequestBase(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(..., min_length=1, max_length=500)
    emergency_contact: Optional[str] = None
    documents: Optional[List[str]] = None

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestUpdate(BaseModel):
    leave_type: Optional[LeaveType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reason: Optional[str] = Field(None, min_length=1, max_length=500)
    emergency_contact: Optional[str] = None
    documents: Optional[List[str]] = None

class LeaveRequestResponse(LeaveRequestBase):
    id: int
    user_id: int
    status: LeaveStatus
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LeaveApproval(BaseModel):
    status: LeaveStatus
    rejection_reason: Optional[str] = None

class LeaveBalance(BaseModel):
    user_id: int
    leave_type: LeaveType
    total_days: int
    used_days: int
    remaining_days: int
    year: int

# Document Models
class DocumentBase(BaseModel):
    filename: str
    document_type: DocumentType
    description: Optional[str] = None
    is_public: bool = False

class DocumentCreate(DocumentBase):
    file_path: str
    file_size: int
    content_type: str

class DocumentResponse(DocumentBase):
    id: int
    user_id: int
    file_path: str
    file_size: int
    content_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Notification Models
class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str
    type: NotificationType

class NotificationCreate(NotificationBase):
    recipient_id: int

class NotificationResponse(NotificationBase):
    id: int
    recipient_id: int
    sender_id: int
    status: NotificationStatus
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Announcement Models
class AnnouncementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str
    priority: str = "normal"
    target_audience: Optional[str] = None
    target_id: Optional[int] = None
    expires_at: Optional[datetime] = None

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementResponse(AnnouncementBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
