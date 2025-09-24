from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tracking_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # harassment, discrimination, workplace_safety, etc.
    priority = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="pending")  # pending, in-progress, resolved, closed
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)  # Array of file URLs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    comments = relationship("ComplaintComment", back_populates="complaint")

class ComplaintComment(Base):
    __tablename__ = "complaint_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal HR comments
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    complaint = relationship("Complaint", back_populates="comments")
    user = relationship("User")