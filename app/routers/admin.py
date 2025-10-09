from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List
from datetime import date

from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.employee import Employee
from ..models.attendance import Attendance
from ..schemas.attendance import AttendanceResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/attendance")
async def get_admin_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all attendance records with employee details (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Join attendance with user and employee tables to get complete information
    records = db.query(Attendance).join(User, Attendance.employee_id == User.id).outerjoin(Employee, User.id == Employee.user_id).order_by(Attendance.date.desc()).all()
    
    # Format response with employee information
    formatted_records = []
    for record in records:
        user = db.query(User).filter(User.id == record.employee_id).first()
        employee = db.query(Employee).filter(Employee.user_id == record.employee_id).first() if user else None
        
        formatted_record = {
            "id": record.id,
            "employee_id": record.employee_id,
            "employeeName": f"{user.first_name} {user.last_name}" if user else "Unknown",
            "employee_name": f"{user.first_name} {user.last_name}" if user else "Unknown",
            "date": record.date.isoformat(),
            "check_in": record.check_in.isoformat() if record.check_in else None,
            "check_out": record.check_out.isoformat() if record.check_out else None,
            "status": record.status,
            "hours_worked": record.hours_worked,
            "totalHours": float(record.hours_worked.split(':')[0]) + float(record.hours_worked.split(':')[1])/60 if record.hours_worked and ':' in record.hours_worked else 0,
            "total_hours": float(record.hours_worked.split(':')[0]) + float(record.hours_worked.split(':')[1])/60 if record.hours_worked and ':' in record.hours_worked else 0,
            "notes": getattr(record, 'notes', ''),
            "remarks": getattr(record, 'remarks', ''),
            "department": employee.department if employee else None,
            "position": employee.position if employee else None,
            "avatar_url": employee.avatar_url if employee else None
        }
        formatted_records.append(formatted_record)
    
    return formatted_records

@router.get("/attendance/stats")
async def get_admin_attendance_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance statistics for admin dashboard"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    today = date.today()
    
    # Get today's stats
    today_present = db.query(Attendance).filter(
        and_(Attendance.date == today, Attendance.status == "present")
    ).count()
    
    today_absent = db.query(Attendance).filter(
        and_(Attendance.date == today, Attendance.status == "absent")
    ).count()
    
    today_late = db.query(Attendance).filter(
        and_(Attendance.date == today, Attendance.status == "late")
    ).count()
    
    # Get total employees
    total_employees = db.query(User).filter(User.role == "employee").count()
    
    return {
        "todayPresent": today_present,
        "todayAbsent": today_absent,
        "todayLate": today_late,
        "totalEmployees": total_employees,
        "attendanceRate": round((today_present / max(total_employees, 1)) * 100, 1)
    }