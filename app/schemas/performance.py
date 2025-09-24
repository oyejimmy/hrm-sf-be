from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class PerformanceBase(BaseModel):
    review_period_start: date
    review_period_end: date
    overall_rating: str
    goals_achievement: Optional[float] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    goals_next_period: Optional[str] = None
    comments: Optional[str] = None

class PerformanceCreate(PerformanceBase):
    employee_id: int

class PerformanceUpdate(BaseModel):
    overall_rating: Optional[str] = None
    goals_achievement: Optional[float] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    goals_next_period: Optional[str] = None
    comments: Optional[str] = None
    status: Optional[str] = None

class PerformanceResponse(PerformanceBase):
    id: int
    employee_id: int
    reviewer_id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True