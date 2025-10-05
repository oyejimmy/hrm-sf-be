from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timezone
from typing import List
import traceback
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
        now = datetime.now(timezone.utc)
        
        # Get all announcements for debugging
        announcements = db.query(Announcement).order_by(desc(Announcement.id)).all()
        print(f"Found {len(announcements)} announcements in database")
        for ann in announcements:
            print(f"Announcement {ann.id}: {ann.title}, active: {ann.is_active}, publish_date: {ann.publish_date}")
        
        # Format response with isNew logic
        result = []
        for ann in announcements:
            try:
                # Handle timezone-aware datetime
                publish_date = ann.publish_date
                if publish_date and publish_date.tzinfo is None:
                    publish_date = publish_date.replace(tzinfo=timezone.utc)
                
                # Calculate if announcement is new (within 20 days)
                if publish_date:
                    days_since_publish = (now - publish_date).days
                    is_new = days_since_publish <= 20
                else:
                    is_new = False
                    publish_date = now
                
                announcement_data = {
                    "id": ann.id,
                    "title": ann.title or "",
                    "content": ann.content or "",
                    "announcement_type": ann.announcement_type or "General",
                    "priority": ann.priority or "medium",
                    "publish_date": publish_date.strftime("%Y-%m-%d"),
                    "is_new": is_new
                }
                print(f"Adding announcement to result: {announcement_data}")
                result.append(announcement_data)
            except Exception as item_error:
                print(f"Error processing announcement {ann.id}: {str(item_error)}")
                continue
        
        print(f"Returning {len(result)} announcements")
        return result
        
    except Exception as e:
        print(f"Announcements error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return []  # Return empty list instead of raising error