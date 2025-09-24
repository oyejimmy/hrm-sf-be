from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Performance(Base):
    __tablename__ = "performance_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_period_start = Column(Date, nullable=False)
    review_period_end = Column(Date, nullable=False)
    overall_rating = Column(String, nullable=False)  # excellent, good, satisfactory, needs_improvement, unsatisfactory
    goals_achievement = Column(Float, nullable=True)  # Percentage
    strengths = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    goals_next_period = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft, submitted, approved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id], back_populates="performance_reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])