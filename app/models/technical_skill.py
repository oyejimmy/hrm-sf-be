from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class TechnicalSkill(Base):
    __tablename__ = "technical_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)