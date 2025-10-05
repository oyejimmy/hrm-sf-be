from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, text
from datetime import datetime
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.notification import Holiday
from ..auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class HolidayResponse(BaseModel):
    id: int
    name: str
    date: str
    day: str
    description: str
    holiday_type: str
    
    class Config:
        from_attributes = True

@router.get("/")
def get_holidays(db: Session = Depends(get_db)):
    """Get all holidays"""
    try:
        # Use raw SQL to get holidays data
        result = db.execute("SELECT id, name, date, holiday_type, description FROM holidays ORDER BY date").fetchall()
        
        holidays = []
        for row in result:
            holidays.append({
                "id": row[0],
                "name": row[1], 
                "date": str(row[2]),
                "holiday_type": row[3] or "general",
                "description": row[4] or ""
            })
        
        print(f"Found {len(holidays)} holidays")
        return holidays
        
    except Exception as e:
        print(f"Database error: {e}")
        # Try alternative query
        try:
            from sqlalchemy import text
            result = db.execute(text("SELECT id, name, date, holiday_type, description FROM holidays ORDER BY date")).fetchall()
            
            holidays = []
            for row in result:
                holidays.append({
                    "id": row[0],
                    "name": row[1], 
                    "date": str(row[2]),
                    "holiday_type": row[3] or "general",
                    "description": row[4] or ""
                })
            
            print(f"Found {len(holidays)} holidays (alternative query)")
            return holidays
        except Exception as e2:
            print(f"Alternative query error: {e2}")
            return []