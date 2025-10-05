from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TechnicalSkill

router = APIRouter(prefix="/api", tags=["Technical Skills"])

@router.get("/technical-skills")
def get_technical_skills(db: Session = Depends(get_db)):
    """Get all technical skills"""
    skills = db.query(TechnicalSkill).all()
    return [{"id": skill.id, "name": skill.name} for skill in skills]