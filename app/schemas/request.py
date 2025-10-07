from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class RequestType(str, Enum):
    LEAVE = "leave"
    EQUIPMENT = "equipment"
    DOCUMENT = "document"
    LOAN = "loan"
    TRAVEL = "travel"
    RECOGNITION = "recognition"
    OTHER = "other"

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"

class RequestPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RequestBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    request_type: RequestType
    priority: Optional[RequestPriority] = RequestPriority.MEDIUM
    amount: Optional[float] = None
    document_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    equipment_type: Optional[str] = None
    destination: Optional[str] = None
    recognition_type: Optional[str] = None

class RequestCreate(RequestBase):
    pass

class RequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[RequestPriority] = None
    status: Optional[RequestStatus] = None
    amount: Optional[float] = None
    document_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    equipment_type: Optional[str] = None
    destination: Optional[str] = None
    recognition_type: Optional[str] = None
    approver_comments: Optional[str] = None

class RequestResponse(RequestBase):
    id: int
    user_id: int
    status: RequestStatus
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approver_comments: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RequestStats(BaseModel):
    total_requests: int
    pending: int
    approved: int
    rejected: int
    in_progress: int

class RequestFilters(BaseModel):
    skip: int = 0
    limit: int = 100
    status: Optional[str] = None
    request_type: Optional[str] = None
    priority: Optional[str] = None
    search: Optional[str] = None