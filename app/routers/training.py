from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sql_models import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_db
from app.core.logger import logger

router = APIRouter()

@router.get("/programs")
async def get_training_programs(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all training programs."""
    return {"message": "Training programs endpoint - SQLite implementation needed"}

@router.post("/programs")
async def create_training_program(
    program_data: dict,
    current_user: dict = Depends(require_role(UserRole.HR)),
    db: AsyncSession = Depends(get_db)
):
    """Create a new training program."""
    logger.info(f"Training program creation requested: {program_data.get('title')}")
    return {"message": "Create training program endpoint - SQLite implementation needed"}

@router.get("/enrollments")
async def get_training_enrollments(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get training enrollments."""
    return {"message": "Training enrollments endpoint - SQLite implementation needed"}
