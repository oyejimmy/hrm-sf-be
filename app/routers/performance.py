from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.sql_models import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.get("/reviews")
async def get_performance_reviews(
    current_user: dict = Depends(get_current_active_user)
):
    """Get performance reviews."""
    db = get_database()
    
    filter_dict = {}
    if current_user["role"] == UserRole.EMPLOYEE:
        filter_dict["employee_id"] = str(current_user["_id"])
    elif current_user["role"] == UserRole.TEAM_LEAD:
        # Get team members
        team_members = await db.employees.find({"manager_id": str(current_user["_id"])}).to_list(length=None)
        team_user_ids = [emp["user_id"] for emp in team_members]
        filter_dict["employee_id"] = {"$in": team_user_ids}
    
    cursor = db.performance_reviews.find(filter_dict).sort("created_at", -1)
    reviews = await cursor.to_list(length=None)
    
    return reviews

@router.post("/reviews")
async def create_performance_review(
    review_data: dict,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Create a performance review."""
    db = get_database()
    
    review_doc = {
        **review_data,
        "created_by": str(current_user["_id"]),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.performance_reviews.insert_one(review_doc)
    review_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Performance review created for employee {review_data.get('employee_id')}")
    
    return review_doc
