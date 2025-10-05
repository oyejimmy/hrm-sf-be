from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Leave(Base):
    __tablename__ = "leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(String, nullable=False)  # annual, sick, casual, maternity, paternity, unpaid
    duration_type = Column(String, default="full_day")  # full_day, half_day_morning, half_day_afternoon
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected, on_hold, cancelled
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    admin_comments = Column(Text, nullable=True)
    attachment_url = Column(String, nullable=True)
    recipient_details = Column(JSON, nullable=True)  # Array of recipients
    notification_sent = Column(Boolean, default=False)
    admin_notified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id], back_populates="leave_requests")
    approver = relationship("User", foreign_keys=[approved_by])

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    total_allocated = Column(Float, nullable=False)
    taken = Column(Float, default=0.0)
    remaining = Column(Float, nullable=False)
    carried_forward = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User")

class LeavePolicy(Base):
    __tablename__ = "leave_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    leave_type = Column(String, nullable=False)
    annual_allocation = Column(Float, nullable=False)
    max_consecutive_days = Column(Integer, nullable=True)
    min_notice_days = Column(Integer, nullable=True)
    carry_forward_allowed = Column(Boolean, default=False)
    max_carry_forward = Column(Float, nullable=True)
    eligibility_criteria = Column(Text, nullable=True)
    approval_workflow = Column(JSON, nullable=True)  # Array of approval steps
    documentation_required = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())