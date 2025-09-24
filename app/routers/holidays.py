from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.notification import Holiday
from ..auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/holidays", tags=["Holidays"])

class HolidayResponse(BaseModel):
    id: int
    name: str
    date: str
    day: str
    description: str
    holiday_type: str
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[HolidayResponse])
def get_holidays(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all holidays"""
    try:
        holidays = db.query(Holiday).order_by(Holiday.date).all()
        
        result = []
        for holiday in holidays:
            # Format date and get day name
            holiday_date = holiday.date
            day_name = holiday_date.strftime('%A')
            formatted_date = holiday_date.strftime('%B %d, %Y')
            
            result.append({
                "id": holiday.id,
                "name": holiday.name,
                "date": formatted_date,
                "day": day_name,
                "description": holiday.description or "",
                "holiday_type": holiday.holiday_type
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get holidays: {str(e)}")