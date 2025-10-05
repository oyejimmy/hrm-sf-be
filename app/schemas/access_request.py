from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.access_request import RequestStatus

class AccessRequestCreate(BaseModel):
    full_name: str
    personal_email: EmailStr
    phone: str
    department: str
    message: Optional[str] = None

class AccessRequestResponse(BaseModel):
    id: int
    full_name: str
    personal_email: str
    phone: str
    department: str
    message: Optional[str]
    status: RequestStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True