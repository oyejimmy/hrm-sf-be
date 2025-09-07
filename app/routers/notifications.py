from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.user import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.get("/my-notifications")
async def get_my_notifications(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user's notifications."""
    db = get_database()
    
    cursor = db.notifications.find({
        "recipient_id": str(current_user["_id"])
    }).sort("created_at", -1)
    
    notifications = await cursor.to_list(length=None)
    
    return notifications

@router.post("/send")
async def send_notification(
    notification_data: dict,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Send a notification."""
    db = get_database()
    
    notification_doc = {
        **notification_data,
        "sender_id": str(current_user["_id"]),
        "status": "unread",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.notifications.insert_one(notification_doc)
    notification_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Notification sent to {notification_data.get('recipient_id')}")
    
    return notification_doc

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Mark notification as read."""
    db = get_database()
    
    result = await db.notifications.update_one(
        {
            "_id": ObjectId(notification_id),
            "recipient_id": str(current_user["_id"])
        },
        {"$set": {"status": "read", "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification marked as read"}
