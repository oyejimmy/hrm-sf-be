from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class EmployeeRequest(Base):
    __tablename__ = "employee_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_type = Column(String, nullable=False)  # loan, document, equipment, travel, recognition
    subject = Column(String, nullable=False)
    details = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected, in_progress
    priority = Column(String, default="medium")  # low, medium, high
    amount = Column(Float, nullable=True)  # For loan requests
    document_type = Column(String, nullable=True)  # For document requests
    start_date = Column(Date, nullable=True)  # For leave/travel requests
    end_date = Column(Date, nullable=True)  # For leave/travel requests
    equipment_type = Column(String, nullable=True)  # For equipment requests
    destination = Column(String, nullable=True)  # For travel requests
    recognition_type = Column(String, nullable=True)  # For recognition requests
    attachments = Column(JSON, nullable=True)  # Array of file URLs
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approver_comments = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    approver = relationship("User", foreign_keys=[approver_id])
    logs = relationship("RequestLog", back_populates="request")

class RequestLog(Base):
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("employee_requests.id"), nullable=False)
    action = Column(String, nullable=False)  # created, approved, rejected, updated, etc.
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("EmployeeRequest", back_populates="logs")
    user = relationship("User")

class HRDocument(Base):
    __tablename__ = "hr_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    document_type = Column(String, nullable=False)  # policy, form, handbook, etc.
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True)  # Available to all employees
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)  # Department specific
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    version = Column(String, default="1.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department")
    uploader = relationship("User")