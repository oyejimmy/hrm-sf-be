from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=False)  # leave, attendance, announcement, etc.
    priority = Column(String, default="medium")  # low, medium, high
    is_read = Column(Boolean, default=False)
    is_system_generated = Column(Boolean, default=False)
    related_entity_type = Column(String, nullable=True)  # leave_request, complaint, etc.
    related_entity_id = Column(Integer, nullable=True)
    action_url = Column(String, nullable=True)  # URL to navigate to
    extra_data = Column(JSON, nullable=True)  # Additional data
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id])
    sender = relationship("User", foreign_keys=[sender_id])

class Announcement(Base):
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    announcement_type = Column(String, nullable=False)  # general, urgent, policy, event
    priority = Column(String, default="medium")  # low, medium, high
    target_audience = Column(String, default="all")  # all, department, role
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    target_roles = Column(JSON, nullable=True)  # Array of roles
    is_active = Column(Boolean, default=True)
    publish_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    attachments = Column(JSON, nullable=True)  # Array of file URLs
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department")
    creator = relationship("User")
    reads = relationship("AnnouncementRead", back_populates="announcement")

class AnnouncementRead(Base):
    __tablename__ = "announcement_reads"
    
    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(Integer, ForeignKey("announcements.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    read_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    announcement = relationship("Announcement", back_populates="reads")
    user = relationship("User")

class Holiday(Base):
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    holiday_type = Column(String, nullable=False)  # national, religious, company
    is_optional = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    applicable_locations = Column(JSON, nullable=True)  # Array of locations
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    creator = relationship("User")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignee = relationship("User", foreign_keys=[assigned_to])
    assigner = relationship("User", foreign_keys=[assigned_by])