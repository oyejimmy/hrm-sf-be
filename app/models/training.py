from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class TrainingProgram(Base):
    __tablename__ = "training_programs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)  # technical, soft_skills, compliance, etc.
    level = Column(String, nullable=False)  # beginner, intermediate, advanced
    duration_hours = Column(Float, nullable=False)
    instructor = Column(String, nullable=True)
    max_participants = Column(Integer, nullable=True)
    prerequisites = Column(Text, nullable=True)
    learning_objectives = Column(JSON, nullable=True)  # Array of objectives
    materials = Column(JSON, nullable=True)  # Array of material URLs
    is_mandatory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")
    enrollments = relationship("TrainingEnrollment", back_populates="program")
    sessions = relationship("TrainingSession", back_populates="program")

class TrainingSession(Base):
    __tablename__ = "training_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    session_name = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)  # room or online link
    instructor = Column(String, nullable=True)
    max_participants = Column(Integer, nullable=True)
    status = Column(String, default="scheduled")  # scheduled, ongoing, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    program = relationship("TrainingProgram", back_populates="sessions")
    enrollments = relationship("TrainingEnrollment", back_populates="session")

class TrainingEnrollment(Base):
    __tablename__ = "training_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=True)
    enrollment_date = Column(Date, nullable=False)
    status = Column(String, default="enrolled")  # enrolled, in_progress, completed, dropped
    progress_percentage = Column(Float, default=0.0)
    completion_date = Column(Date, nullable=True)
    certificate_issued = Column(Boolean, default=False)
    certificate_url = Column(String, nullable=True)
    feedback_rating = Column(Integer, nullable=True)  # 1-5 stars
    feedback_comments = Column(Text, nullable=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    program = relationship("TrainingProgram", back_populates="enrollments")
    session = relationship("TrainingSession", back_populates="enrollments")
    assigner = relationship("User", foreign_keys=[assigned_by])

class TrainingRoadmap(Base):
    __tablename__ = "training_roadmaps"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    position = Column(String, nullable=True)
    milestones = Column(JSON, nullable=False)  # Array of milestone objects
    estimated_duration_months = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department")
    creator = relationship("User")