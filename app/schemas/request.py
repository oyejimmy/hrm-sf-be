from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class EmployeeRequestBase(BaseModel):
    request_type: str
    subject: str
    details: str
    priority: str = "medium"
    amount: Optional[float] = None
    document_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    equipment_type: Optional[str] = None
    destination: Optional[str] = None
    recognition_type: Optional[str] = None

class EmployeeRequestCreate(EmployeeRequestBase):
    attachments: Optional[List[str]] = None

class EmployeeRequestUpdate(BaseModel):
    status: Optional[str] = None
    approver_comments: Optional[str] = None

class EmployeeRequest(EmployeeRequestBase):
    id: int
    employee_id: int
    status: str
    attachments: Optional[List[str]] = None
    approver_id: Optional[int] = None
    approver_comments: Optional[str] = None
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RequestLogBase(BaseModel):
    action: str
    details: Optional[str] = None

class RequestLogCreate(RequestLogBase):
    request_id: int

class RequestLog(RequestLogBase):
    id: int
    request_id: int
    performed_by: int
    timestamp: datetime

    class Config:
        from_attributes = True

class HRDocumentBase(BaseModel):
    name: str
    document_type: str
    description: Optional[str] = None
    is_public: bool = True
    version: str = "1.0"

class HRDocumentCreate(HRDocumentBase):
    file_path: str
    file_size: int
    department_id: Optional[int] = None

class HRDocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class HRDocument(HRDocumentBase):
    id: int
    file_path: str
    file_size: int
    department_id: Optional[int] = None
    uploaded_by: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmployeeRequestResponse(EmployeeRequest):
    pass

class RequestLogResponse(RequestLog):
    pass

class HRDocumentResponse(HRDocument):
    pass
class EmployeeRequestResponse(BaseModel):
    id: int
    employee_id: int
    request_type: str
    subject: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class RequestLogResponse(BaseModel):
    id: int
    request_id: int
    action: str
    performed_by: int
    timestamp: datetime
    class Config:
        from_attributes = True

class HRDocumentResponse(BaseModel):
    id: int
    name: str
    document_type: str
    upload_date: datetime
    class Config:
        from_attributes = True
