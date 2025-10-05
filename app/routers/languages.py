from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Language

router = APIRouter(prefix="/api", tags=["Languages"])

@router.get("/languages")
def get_languages(db: Session = Depends(get_db)):
    """Get all languages"""
    languages = db.query(Language).all()
    return [{"id": lang.id, "name": lang.name} for lang in languages]