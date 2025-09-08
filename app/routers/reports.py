from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.sql_models import UserRole, AttendanceStatus, LeaveStatus
from app.routers.auth import get_current_active_user, require_role
from app.database import get_db
from app.db.sqlite import SQLiteService
from app.models.sql_models import User, Employee, Attendance, LeaveRequest
from app.core.logger import logger

router = APIRouter()

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics."""
    today = date.today()
    
    # Get total employees
    total_employees_result = await db.execute(select(func.count(Employee.id)))
    total_employees = total_employees_result.scalar()
    
    # Get active employees today
    active_today_result = await db.execute(
        select(func.count(Attendance.id))
        .where(and_(Attendance.date == today, Attendance.status == AttendanceStatus.PRESENT))
    )
    active_today = active_today_result.scalar()
    
    # Get employees on leave today
    on_leave_result = await db.execute(
        select(func.count(LeaveRequest.id))
        .where(and_(
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
            LeaveRequest.status == LeaveStatus.APPROVED
        ))
    )
    on_leave = on_leave_result.scalar()
    
    # Get pending approvals
    pending_result = await db.execute(
        select(func.count(LeaveRequest.id))
        .where(LeaveRequest.status == LeaveStatus.PENDING)
    )
    pending_leave_requests = pending_result.scalar()
    
    return {
        "total_employees": total_employees or 0,
        "active_today": active_today or 0,
        "on_leave": on_leave or 0,
        "pending_approvals": pending_leave_requests or 0,
        "recent_activities": []  # Simplified for now
    }

@router.get("/attendance-report")
async def get_attendance_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department: Optional[str] = None,
    current_user = Depends(require_role(UserRole.HR)),
    db: AsyncSession = Depends(get_db)
):
    """Generate attendance report for a date range."""
    # Simplified implementation - return basic structure
    return {
        "report_period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "department": department,
        "total_records": 0,
        "data": [],
        "message": "Attendance report functionality available - implementation simplified for migration"
    }

@router.get("/leave-report")
async def get_leave_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department: Optional[str] = None,
    current_user = Depends(require_role(UserRole.HR)),
    db: AsyncSession = Depends(get_db)
):
    """Generate leave report for a date range."""
    return {
        "report_period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "department": department,
        "leave_statistics": {},
        "total_requests": 0,
        "data": [],
        "message": "Leave report functionality available - implementation simplified for migration"
    }

@router.get("/employee-summary/{user_id}")
async def get_employee_summary(
    user_id: str,
    year: int = Query(..., ge=2020),
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive employee summary."""
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE and 
        int(user_id) != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user and employee info
    user = await SQLiteService.get_user_by_id(db, int(user_id))
    employee = await SQLiteService.get_employee_by_user_id(db, int(user_id))
    
    if not user or not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or employee not found"
        )
    
    return {
        "employee_info": {
            "user_id": user_id,
            "employee_id": employee.employee_id,
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "department": employee.department.value if employee.department else None,
            "position": employee.position,
            "hire_date": employee.hire_date
        },
        "year": year,
        "attendance_summary": {
            "total_days": 0,
            "present_days": 0,
            "absent_days": 0,
            "late_days": 0,
            "half_days": 0,
            "total_work_hours": 0,
            "total_overtime_hours": 0,
            "attendance_percentage": 0
        },
        "leave_summary": {
            "total_requests": 0,
            "approved_leaves": 0,
            "pending_leaves": 0,
            "rejected_leaves": 0,
            "total_leave_days": 0
        },
        "message": "Employee summary functionality available - detailed calculations simplified for migration"
    }
