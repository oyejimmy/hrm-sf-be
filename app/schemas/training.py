from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class TrainingProgramBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    level: str
    duration_hours: float
    instructor: Optional[str] = None
    max_participants: Optional[int] = None
    prerequisites: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    is_mandatory: bool = False

class TrainingProgramCreate(TrainingProgramBase):
    pass

class TrainingProgramUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    is_active: Optional[bool] = None

class TrainingProgram(TrainingProgramBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TrainingSessionBase(BaseModel):
    session_name: str
    start_date: datetime
    end_date: datetime
    location: Optional[str] = None
    instructor: Optional[str] = None
    max_participants: Optional[int] = None

class TrainingSessionCreate(TrainingSessionBase):
    program_id: int

class TrainingSession(TrainingSessionBase):
    id: int
    program_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class TrainingEnrollmentBase(BaseModel):
    enrollment_date: date
    status: str = "enrolled"

class TrainingEnrollmentCreate(TrainingEnrollmentBase):
    employee_id: int
    program_id: int
    session_id: Optional[int] = None

class TrainingEnrollmentUpdate(BaseModel):
    status: Optional[str] = None
    progress_percentage: Optional[float] = None
    completion_date: Optional[date] = None
    certificate_issued: Optional[bool] = None
    feedback_rating: Optional[int] = None
    feedback_comments: Optional[str] = None

class TrainingEnrollment(TrainingEnrollmentBase):
    id: int
    employee_id: int
    program_id: int
    session_id: Optional[int] = None
    progress_percentage: float
    completion_date: Optional[date] = None
    certificate_issued: bool
    certificate_url: Optional[str] = None
    feedback_rating: Optional[int] = None
    feedback_comments: Optional[str] = None
    assigned_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TrainingRoadmapBase(BaseModel):
    title: str
    description: Optional[str] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    milestones: List[dict]
    estimated_duration_months: Optional[int] = None

class TrainingRoadmapCreate(TrainingRoadmapBase):
    pass

class TrainingRoadmap(TrainingRoadmapBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TrainingProgramResponse(TrainingProgram):
    pass

class TrainingSessionResponse(TrainingSession):
    pass

class TrainingEnrollmentResponse(TrainingEnrollment):
    pass

class TrainingRoadmapResponse(TrainingRoadmap):
    pass
class TrainingProgramResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class TrainingSessionResponse(BaseModel):
    id: int
    program_id: int
    session_name: str
    status: str
    start_date: datetime
    class Config:
        from_attributes = True

class TrainingEnrollmentResponse(BaseModel):
    id: int
    employee_id: int
    program_id: int
    status: str
    progress: float
    class Config:
        from_attributes = True

class TrainingRoadmapResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime
    class Config:
        from_attributes = True
