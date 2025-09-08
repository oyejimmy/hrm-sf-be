from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date, time
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceCreate, AttendanceUpdate, AttendanceResponse, AttendanceSummary
from app.models.sql_models import UserRole, AttendanceStatus
from app.routers.auth import get_current_active_user, require_role
from app.database import get_db
from app.db.sqlite import SQLiteService
from app.core.logger import logger
from app.core.security import sanitize_log_input

router = APIRouter()

@router.post("/log", response_model=AttendanceResponse)
async def log_attendance(
    attendance_data: AttendanceCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Log attendance for a user."""
    # Check if attendance already exists for this date
    existing = await SQLiteService.get_attendance_by_user_date(db, attendance_data.user_id, attendance_data.date)
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already logged for this date"
        )
    
    # Create attendance record
    attendance_dict = attendance_data.dict()
    attendance = await SQLiteService.create_attendance(db, attendance_dict)
    
    logger.info(f"Attendance logged for user {sanitize_log_input(str(attendance_data.user_id))} on {attendance_data.date}")
    
    return AttendanceResponse(
        id=str(attendance.id),
        user_id=attendance.user_id,
        date=attendance.date,
        check_in=attendance.check_in,
        check_out=attendance.check_out,
        status=attendance.status,
        work_hours=attendance.work_hours,
        overtime_hours=attendance.overtime_hours,
        notes=attendance.notes,
        created_at=attendance.created_at,
        updated_at=attendance.updated_at
    )

@router.get("/today", response_model=List[AttendanceResponse])
async def get_today_attendance(
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get today's attendance records."""
    today = date.today()
    user_ids = None
    
    # Apply role-based filtering
    if current_user.role == UserRole.EMPLOYEE:
        user_ids = [current_user.id]
    elif current_user.role == UserRole.TEAM_LEAD:
        # Get team members
        team_members = await SQLiteService.get_team_members_by_manager(db, current_user.id)
        user_ids = [emp.user_id for emp in team_members]
    
    attendance_records = await SQLiteService.get_today_attendance(db, today, user_ids)
    
    return [AttendanceResponse(
        id=str(record.id),
        user_id=record.user_id,
        date=record.date,
        check_in=record.check_in,
        check_out=record.check_out,
        status=record.status,
        work_hours=record.work_hours,
        overtime_hours=record.overtime_hours,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at
    ) for record in attendance_records]

@router.get("/user/{user_id}", response_model=List[AttendanceResponse])
async def get_user_attendance(
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get attendance records for a specific user."""
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE and 
        int(user_id) != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    attendance_records = await SQLiteService.get_user_attendance(
        db, int(user_id), start_date, end_date
    )
    
    return [AttendanceResponse(
        id=str(record.id),
        user_id=record.user_id,
        date=record.date,
        check_in=record.check_in,
        check_out=record.check_out,
        status=record.status,
        work_hours=record.work_hours,
        overtime_hours=record.overtime_hours,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at
    ) for record in attendance_records]

@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: str,
    attendance_data: AttendanceUpdate,
    current_user = Depends(require_role(UserRole.HR)),
    db: AsyncSession = Depends(get_db)
):
    """Update attendance record."""
    # Prepare update data
    update_data = {k: v for k, v in attendance_data.dict().items() if v is not None}
    if update_data:
        updated_attendance = await SQLiteService.update_attendance(db, int(attendance_id), update_data)
        
        if not updated_attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        
        logger.info(f"Attendance updated: {sanitize_log_input(attendance_id)}")
        
        return AttendanceResponse(
            id=str(updated_attendance.id),
            user_id=updated_attendance.user_id,
            date=updated_attendance.date,
            check_in=updated_attendance.check_in,
            check_out=updated_attendance.check_out,
            status=updated_attendance.status,
            work_hours=updated_attendance.work_hours,
            overtime_hours=updated_attendance.overtime_hours,
            notes=updated_attendance.notes,
            created_at=updated_attendance.created_at,
            updated_at=updated_attendance.updated_at
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No update data provided"
    )

@router.get("/summary/{user_id}", response_model=AttendanceSummary)
async def get_attendance_summary(
    user_id: str,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get monthly attendance summary for a user."""
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE and 
        int(user_id) != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Calculate date range for the month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    # Get attendance records for the month
    records = await SQLiteService.get_attendance_summary(db, int(user_id), start_date, end_date)
    
    # Calculate summary
    total_days = len(records)
    present_days = len([r for r in records if r.status == AttendanceStatus.PRESENT])
    absent_days = len([r for r in records if r.status == AttendanceStatus.ABSENT])
    late_days = len([r for r in records if r.status == AttendanceStatus.LATE])
    half_days = len([r for r in records if r.status == AttendanceStatus.HALF_DAY])
    
    total_work_hours = sum(r.work_hours or 0 for r in records)
    total_overtime_hours = sum(r.overtime_hours or 0 for r in records)
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return AttendanceSummary(
        user_id=user_id,
        month=month,
        year=year,
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        late_days=late_days,
        half_days=half_days,
        total_work_hours=total_work_hours,
        total_overtime_hours=total_overtime_hours,
        attendance_percentage=attendance_percentage
    )
