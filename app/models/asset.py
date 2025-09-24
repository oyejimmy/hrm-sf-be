from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # laptop, monitor, phone, etc.
    serial_number = Column(String, unique=True, nullable=False)
    specifications = Column(Text, nullable=True)
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Float, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    status = Column(String, default="available")  # available, assigned, maintenance, retired
    condition = Column(String, default="good")  # excellent, good, fair, poor
    location = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department")
    assignee = relationship("User", foreign_keys=[assigned_to])
    requests = relationship("AssetRequest", back_populates="asset")

class AssetRequest(Base):
    __tablename__ = "asset_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    asset_type = Column(String, nullable=False)  # For new asset requests
    request_type = Column(String, nullable=False)  # request, return, maintenance
    reason = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected, completed
    requested_date = Column(Date, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    admin_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    asset = relationship("Asset", back_populates="requests")
    approver = relationship("User", foreign_keys=[approved_by])