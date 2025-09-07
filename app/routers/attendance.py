from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date, time
from bson import ObjectId

from app.models.attendance import AttendanceCreate, AttendanceUpdate, AttendanceResponse, AttendanceSummary
from app.models.user import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.post("/log", response_model=AttendanceResponse)
async def log_attendance(
    attendance_data: AttendanceCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Log attendance for a user."""
    db = get_database()
    
    # Check if attendance already exists for this date
    existing = await db.attendance.find_one({
        "user_id": attendance_data.user_id,
        "date": attendance_data.date
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already logged for this date"
        )
    
    # Create attendance document
    attendance_doc = {
        **attendance_data.dict(),
        "date": attendance_data.date,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.attendance.insert_one(attendance_doc)
    attendance_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Attendance logged for user {attendance_data.user_id} on {attendance_data.date}")
    
    return AttendanceResponse(**attendance_doc)

@router.get("/today", response_model=List[AttendanceResponse])
async def get_today_attendance(
    current_user: dict = Depends(get_current_active_user)
):
    """Get today's attendance records."""
    db = get_database()
    today = date.today()
    
    filter_dict = {"date": today}
    
    # Apply role-based filtering
    if current_user["role"] == UserRole.EMPLOYEE:
        filter_dict["user_id"] = str(current_user["_id"])
    elif current_user["role"] == UserRole.TEAM_LEAD:
        # Get team members
        team_members = await db.employees.find({"manager_id": str(current_user["_id"])}).to_list(length=None)
        team_user_ids = [emp["user_id"] for emp in team_members]
        filter_dict["user_id"] = {"$in": team_user_ids}
    
    cursor = db.attendance.find(filter_dict)
    attendance_records = await cursor.to_list(length=None)
    
    return [AttendanceResponse(**record) for record in attendance_records]

@router.get("/user/{user_id}", response_model=List[AttendanceResponse])
async def get_user_attendance(
    user_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get attendance records for a specific user."""
    db = get_database()
    
    # Check permissions
    if (current_user["role"] == UserRole.EMPLOYEE and 
        user_id != str(current_user["_id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    filter_dict = {"user_id": user_id}
    
    if start_date:
        filter_dict["date"] = {"$gte": start_date}
    if end_date:
        if "date" in filter_dict:
            filter_dict["date"]["$lte"] = end_date
        else:
            filter_dict["date"] = {"$lte": end_date}
    
    cursor = db.attendance.find(filter_dict).sort("date", -1)
    attendance_records = await cursor.to_list(length=None)
    
    return [AttendanceResponse(**record) for record in attendance_records]

@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: str,
    attendance_data: AttendanceUpdate,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Update attendance record."""
    db = get_database()
    
    attendance = await db.attendance.find_one({"_id": ObjectId(attendance_id)})
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Prepare update data
    update_data = {k: v for k, v in attendance_data.dict().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        await db.attendance.update_one(
            {"_id": ObjectId(attendance_id)},
            {"$set": update_data}
        )
        
        # Get updated attendance
        updated_attendance = await db.attendance.find_one({"_id": ObjectId(attendance_id)})
        
        logger.info(f"Attendance updated: {attendance_id}")
        
        return AttendanceResponse(**updated_attendance)
    
    return AttendanceResponse(**attendance)

@router.get("/summary/{user_id}", response_model=AttendanceSummary)
async def get_attendance_summary(
    user_id: str,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    current_user: dict = Depends(get_current_active_user)
):
    """Get monthly attendance summary for a user."""
    db = get_database()
    
    # Check permissions
    if (current_user["role"] == UserRole.EMPLOYEE and 
        user_id != str(current_user["_id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Calculate date range for the month
    from datetime import datetime
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    # Get attendance records for the month
    cursor = db.attendance.find({
        "user_id": user_id,
        "date": {"$gte": start_date, "$lt": end_date}
    })
    records = await cursor.to_list(length=None)
    
    # Calculate summary
    total_days = len(records)
    present_days = len([r for r in records if r["status"] == "present"])
    absent_days = len([r for r in records if r["status"] == "absent"])
    late_days = len([r for r in records if r["status"] == "late"])
    half_days = len([r for r in records if r["status"] == "half_day"])
    
    total_work_hours = sum(r.get("work_hours", 0) for r in records)
    total_overtime_hours = sum(r.get("overtime_hours", 0) for r in records)
    
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
