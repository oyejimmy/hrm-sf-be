from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str
    priority: str = "medium"

class NotificationCreate(NotificationBase):
    recipient_id: int
    sender_id: Optional[int] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    action_url: Optional[str] = None
    metadata: Optional[dict] = None
    expires_at: Optional[datetime] = None

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

class Notification(NotificationBase):
    id: int
    recipient_id: int
    sender_id: Optional[int] = None
    is_read: bool
    is_system_generated: bool
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    action_url: Optional[str] = None
    metadata: Optional[dict] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True



class AnnouncementBase(BaseModel):
    title: str
    content: str
    announcement_type: str
    priority: str = "medium"
    target_audience: str = "all"
    publish_date: datetime

class AnnouncementCreate(AnnouncementBase):
    department_id: Optional[int] = None
    target_roles: Optional[List[str]] = None
    expiry_date: Optional[datetime] = None
    attachments: Optional[List[str]] = None

class AnnouncementUpdate(BaseModel):
    is_active: Optional[bool] = None
    expiry_date: Optional[datetime] = None

class Announcement(AnnouncementBase):
    id: int
    department_id: Optional[int] = None
    target_roles: Optional[List[str]] = None
    is_active: bool
    expiry_date: Optional[datetime] = None
    attachments: Optional[List[str]] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class HolidayBase(BaseModel):
    name: str
    date: datetime
    holiday_type: str
    is_optional: bool = False
    description: Optional[str] = None

class HolidayCreate(HolidayBase):
    applicable_locations: Optional[List[str]] = None

class Holiday(HolidayBase):
    id: int
    applicable_locations: Optional[List[str]] = None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    assigned_to: int

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None

class Task(TaskBase):
    id: int
    assigned_to: int
    assigned_by: int
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationResponse(Notification):
    pass

class AnnouncementResponse(Announcement):
    pass

class HolidayResponse(Holiday):
    pass

class TaskResponse(Task):
    pass