from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(String, default="employee")  # admin, hr, team_lead, employee
    status = Column(String, default="active")  # active, inactive, suspended
    is_profile_complete = Column(Boolean, default=False)
    profile_picture = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False)
    leave_requests = relationship("Leave", foreign_keys="Leave.employee_id", back_populates="employee")
    attendance_records = relationship("Attendance", foreign_keys="Attendance.employee_id", back_populates="employee")
    performance_reviews = relationship("Performance", foreign_keys="Performance.employee_id", back_populates="employee")