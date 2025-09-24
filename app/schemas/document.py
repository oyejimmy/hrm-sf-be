from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class DocumentBase(BaseModel):
    document_type: str
    category: str
    file_name: str
    description: Optional[str] = None
    is_required: bool = False
    expiry_date: Optional[date] = None

class DocumentCreate(DocumentBase):
    employee_id: int
    file_path: str
    file_size: int
    mime_type: str

class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    expiry_date: Optional[date] = None

class Document(DocumentBase):
    id: int
    employee_id: int
    file_path: str
    file_size: int
    mime_type: str
    status: str
    uploaded_by: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DocumentResponse(Document):
    pass

class DocumentVersionBase(BaseModel):
    version_number: int
    file_path: str
    file_size: int
    changes_description: Optional[str] = None

class DocumentVersionCreate(DocumentVersionBase):
    document_id: int

class DocumentVersion(DocumentVersionBase):
    id: int
    document_id: int
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentVersionResponse(DocumentVersion):
    pass

class DocumentTypeBase(BaseModel):
    name: str
    category: str
    is_required: bool = False
    description: Optional[str] = None
    allowed_formats: Optional[List[str]] = None
    max_file_size: Optional[int] = None

class DocumentTypeCreate(DocumentTypeBase):
    pass

class DocumentType(DocumentTypeBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentTypeResponse(DocumentType):
    pass