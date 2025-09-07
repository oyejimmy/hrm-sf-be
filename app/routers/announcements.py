from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.user import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.get("/")
async def get_announcements(
    current_user: dict = Depends(get_current_active_user)
):
    """Get all announcements."""
    db = get_database()
    
    cursor = db.announcements.find({"status": "active"}).sort("created_at", -1)
    announcements = await cursor.to_list(length=None)
    
    return announcements

@router.post("/")
async def create_announcement(
    announcement_data: dict,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Create a new announcement."""
    db = get_database()
    
    announcement_doc = {
        **announcement_data,
        "status": "active",
        "created_by": str(current_user["_id"]),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.announcements.insert_one(announcement_doc)
    announcement_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Announcement created: {announcement_data.get('title')}")
    
    return announcement_doc

@router.put("/{announcement_id}")
async def update_announcement(
    announcement_id: str,
    announcement_data: dict,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Update an announcement."""
    db = get_database()
    
    update_data = {
        **announcement_data,
        "updated_at": datetime.utcnow()
    }
    
    result = await db.announcements.update_one(
        {"_id": ObjectId(announcement_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    
    logger.info(f"Announcement updated: {announcement_id}")
    
    return {"message": "Announcement updated successfully"}

@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Delete an announcement."""
    db = get_database()
    
    result = await db.announcements.update_one(
        {"_id": ObjectId(announcement_id)},
        {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    
    logger.info(f"Announcement deleted: {announcement_id}")
    
    return {"message": "Announcement deleted successfully"}
