from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.user import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.get("/programs")
async def get_training_programs(
    current_user: dict = Depends(get_current_active_user)
):
    """Get all training programs."""
    db = get_database()
    
    cursor = db.training_programs.find({"status": "active"})
    programs = await cursor.to_list(length=None)
    
    return programs

@router.post("/programs")
async def create_training_program(
    program_data: dict,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Create a new training program."""
    db = get_database()
    
    program_doc = {
        **program_data,
        "status": "active",
        "created_by": str(current_user["_id"]),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.training_programs.insert_one(program_doc)
    program_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Training program created: {program_data.get('title')}")
    
    return program_doc

@router.get("/enrollments")
async def get_training_enrollments(
    current_user: dict = Depends(get_current_active_user)
):
    """Get training enrollments."""
    db = get_database()
    
    filter_dict = {}
    if current_user["role"] == UserRole.EMPLOYEE:
        filter_dict["employee_id"] = str(current_user["_id"])
    
    cursor = db.training_enrollments.find(filter_dict).sort("created_at", -1)
    enrollments = await cursor.to_list(length=None)
    
    return enrollments
