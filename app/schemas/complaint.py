from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ComplaintBase(BaseModel):
    title: str
    description: str
    category: str
    priority: str = "medium"

class ComplaintCreate(ComplaintBase):
    attachments: Optional[List[str]] = None

class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    resolution: Optional[str] = None

class Complaint(ComplaintBase):
    id: int
    employee_id: int
    tracking_id: str
    status: str
    assigned_to: Optional[int] = None
    resolution: Optional[str] = None
    attachments: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ComplaintResponse(Complaint):
    pass

class ComplaintCommentBase(BaseModel):
    content: str
    is_internal: bool = False

class ComplaintCommentCreate(ComplaintCommentBase):
    complaint_id: int

class ComplaintComment(ComplaintCommentBase):
    id: int
    complaint_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ComplaintCommentResponse(ComplaintComment):
    pass