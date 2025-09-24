from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class AssetBase(BaseModel):
    name: str
    asset_type: str
    serial_number: str
    specifications: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    warranty_expiry: Optional[date] = None
    status: str = "available"
    condition: str = "good"
    location: Optional[str] = None
    department_id: Optional[int] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    specifications: Optional[str] = None
    status: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    assigned_to: Optional[int] = None
    assigned_date: Optional[date] = None

class Asset(AssetBase):
    id: int
    assigned_to: Optional[int] = None
    assigned_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssetResponse(Asset):
    pass

class AssetRequestBase(BaseModel):
    asset_type: str
    request_type: str
    reason: Optional[str] = None
    requested_date: date

class AssetRequestCreate(AssetRequestBase):
    asset_id: Optional[int] = None

class AssetRequestUpdate(BaseModel):
    status: Optional[str] = None
    admin_comments: Optional[str] = None

class AssetRequest(AssetRequestBase):
    id: int
    employee_id: int
    asset_id: Optional[int] = None
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    admin_comments: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AssetRequestResponse(AssetRequest):
    pass