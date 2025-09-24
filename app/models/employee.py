from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String, unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    position = Column(String, nullable=True)
    employment_status = Column(String, default="full_time")  # full_time, part_time, contract, intern
    hire_date = Column(Date, nullable=True)
    salary = Column(Float, nullable=True)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    work_location = Column(String, default="office")  # office, remote, hybrid, field
    gender = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    marital_status = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    
    # Profile enhancement fields
    blood_group = Column(String, nullable=True)
    qualification = Column(String, nullable=True)
    work_schedule = Column(String, default="Standard (9:00 AM - 6:00 PM)")
    team_size = Column(Integer, default=0)
    avatar_url = Column(String, nullable=True)
    cover_image_url = Column(String, nullable=True)
    
    # Emergency contact details
    emergency_contact_relationship = Column(String, nullable=True)
    emergency_contact_work_phone = Column(String, nullable=True)
    emergency_contact_home_phone = Column(String, nullable=True)
    emergency_contact_address = Column(Text, nullable=True)
    
    # Compensation details
    bonus_target = Column(String, nullable=True)
    stock_options = Column(String, nullable=True)
    last_salary_increase = Column(String, nullable=True)
    next_review_date = Column(String, nullable=True)
    
    # Additional profile fields
    personal_email = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    religion = Column(String, nullable=True)
    languages_known = Column(String, nullable=True)
    hobbies = Column(String, nullable=True)
    skills_summary = Column(Text, nullable=True)
    certifications = Column(String, nullable=True)
    education_level = Column(String, nullable=True)
    university = Column(String, nullable=True)
    graduation_year = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    manager = relationship("Employee", remote_side=[id])
    subordinates = relationship("Employee", back_populates="manager")
    skills = relationship("EmployeeSkill", back_populates="employee")