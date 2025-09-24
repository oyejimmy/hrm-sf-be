from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime
from typing import List
from ..database import get_db
from ..models.user import User
from ..models.notification import Announcement
from ..auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    announcement_type: str
    priority: str
    publish_date: str
    is_new: bool
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[AnnouncementResponse])
def get_announcements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active announcements for the current user"""
    try:
        now = datetime.now()
        
        # Get active announcements
        announcements = db.query(Announcement).filter(
            and_(
                Announcement.is_active == True,
                Announcement.publish_date <= now,
                (Announcement.expiry_date.is_(None) | (Announcement.expiry_date >= now))
            )
        ).order_by(desc(Announcement.publish_date)).all()
        
        # Format response with isNew logic
        result = []
        for ann in announcements:
            # Calculate if announcement is new (within 20 days)
            days_since_publish = (now - ann.publish_date).days
            is_new = days_since_publish <= 20
            
            result.append({
                "id": ann.id,
                "title": ann.title,
                "content": ann.content,
                "announcement_type": ann.announcement_type or "General",
                "priority": ann.priority,
                "publish_date": ann.publish_date.strftime("%Y-%m-%d"),
                "is_new": is_new
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get announcements: {str(e)}")