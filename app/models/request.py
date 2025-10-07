from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base

class RequestType(str, enum.Enum):
    LEAVE = "leave"
    EQUIPMENT = "equipment"
    DOCUMENT = "document"
    LOAN = "loan"
    TRAVEL = "travel"
    RECOGNITION = "recognition"
    OTHER = "other"

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"

class RequestPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    request_type = Column(Enum(RequestType), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    priority = Column(Enum(RequestPriority), default=RequestPriority.MEDIUM)
    
    # Optional fields based on request type
    amount = Column(Float, nullable=True)  # For loan requests
    document_type = Column(String(100), nullable=True)  # For document requests
    start_date = Column(Date, nullable=True)  # For leave/travel requests
    end_date = Column(Date, nullable=True)  # For leave/travel requests
    equipment_type = Column(String(100), nullable=True)  # For equipment requests
    destination = Column(String(200), nullable=True)  # For travel requests
    recognition_type = Column(String(100), nullable=True)  # For recognition requests
    
    # Approval fields
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approver_comments = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="requests")
    approver = relationship("User", foreign_keys=[approved_by])