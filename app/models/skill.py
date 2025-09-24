from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from ..database import Base

class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    proficiency_level = Column(Float, nullable=False)  # 0-100
    
    # Relationships
    employee = relationship("Employee", back_populates="skills")