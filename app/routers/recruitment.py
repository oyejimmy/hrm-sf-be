from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.sql_models import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.get("/jobs")
async def get_job_openings(
    current_user: dict = Depends(get_current_active_user)
):
    """Get all job openings."""
    db = get_database()
    
    cursor = db.job_openings.find({"status": "active"})
    jobs = await cursor.to_list(length=None)
    
    return jobs

@router.post("/jobs")
async def create_job_opening(
    job_data: dict,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Create a new job opening."""
    db = get_database()
    
    job_doc = {
        **job_data,
        "status": "active",
        "created_by": str(current_user["_id"]),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.job_openings.insert_one(job_doc)
    job_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Job opening created: {job_data.get('title')}")
    
    return job_doc

@router.get("/applications")
async def get_applications(
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Get all job applications."""
    db = get_database()
    
    cursor = db.job_applications.find().sort("created_at", -1)
    applications = await cursor.to_list(length=None)
    
    return applications
