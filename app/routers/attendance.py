from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, date, time
from typing import Optional
from ..database import get_db
from ..models.user import User
from ..models.attendance import Attendance, BreakRecord
from ..auth import get_current_user
from pydantic import BaseModel
import re

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

class AttendanceResponse(BaseModel):
    id: int
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str
    hours_worked: Optional[str] = None
    is_on_break: bool = False
    total_break_time: int = 0  # in minutes
    
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            time: lambda v: v.strftime('%H:%M:%S') if v else None
        }

class BreakResponse(BaseModel):
    id: int
    start_time: str
    end_time: Optional[str]
    duration_minutes: Optional[int]
    break_type: str
    
    class Config:
        from_attributes = True

@router.get("/today")
def get_today_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's attendance record for the current user"""
    try:
        today = date.today()
        
        attendance = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == current_user.id,
                Attendance.date == today
            )
        ).first()
        
        if not attendance:
            # Create a new attendance record for today
            attendance = Attendance(
                employee_id=current_user.id,
                date=today,
                status="absent"
            )
            db.add(attendance)
            db.commit()
            db.refresh(attendance)
        
        # Check if currently on break
        active_break = db.query(BreakRecord).filter(
            and_(
                BreakRecord.attendance_id == attendance.id,
                BreakRecord.end_time.is_(None)
            )
        ).first()
        
        # Calculate total break time
        break_records = db.query(BreakRecord).filter(
            BreakRecord.attendance_id == attendance.id
        ).all()
        
        total_break_minutes = sum([
            br.duration_minutes for br in break_records 
            if br.duration_minutes is not None
        ])
        
        # Helper function to format time
        def format_time(time_value):
            if not time_value:
                return None
            if isinstance(time_value, str):
                # Handle datetime string format like '2025-09-24 09:00:00'
                if ' ' in time_value:
                    return time_value.split(' ')[1]
                return time_value
            return time_value.strftime('%H:%M:%S')
        
        return {
            "id": attendance.id,
            "date": attendance.date.isoformat(),
            "check_in": format_time(attendance.check_in),
            "check_out": format_time(attendance.check_out),
            "status": attendance.status,
            "hours_worked": attendance.hours_worked,
            "is_on_break": active_break is not None,
            "total_break_time": total_break_minutes
        }
    except Exception as e:
        print(f"Error in get_today_attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get attendance: {str(e)}")

@router.post("/check-in")
def check_in(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check in for today"""
    try:
        today = date.today()
        now = datetime.now()
        
        # Get or create today's attendance record
        attendance = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == current_user.id,
                Attendance.date == today
            )
        ).first()
        
        if not attendance:
            attendance = Attendance(
                employee_id=current_user.id,
                date=today,
                status="present"
            )
            db.add(attendance)
        
        if attendance.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked in today"
            )
        
        attendance.check_in = now.time()
        attendance.status = "present"
        
        db.commit()
        db.refresh(attendance)
        
        # Helper function to format time
        def format_time(time_value):
            if not time_value:
                return None
            if isinstance(time_value, str):
                if ' ' in time_value:
                    return time_value.split(' ')[1]
                return time_value
            return time_value.strftime('%H:%M:%S')
        
        return {
            "message": "Checked in successfully",
            "check_in_time": format_time(attendance.check_in),
            "status": attendance.status
        }
    except Exception as e:
        db.rollback()
        print(f"Error in check_in: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check in: {str(e)}")

@router.post("/check-out")
def check_out(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check out for today"""
    try:
        today = date.today()
        now = datetime.now()
        
        attendance = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == current_user.id,
                Attendance.date == today
            )
        ).first()
        
        if not attendance or not attendance.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must check in first"
            )
        
        if attendance.check_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked out today"
            )
        
        # End any active break
        active_break = db.query(BreakRecord).filter(
            and_(
                BreakRecord.attendance_id == attendance.id,
                BreakRecord.end_time.is_(None)
            )
        ).first()
        
        if active_break:
            active_break.end_time = now
            active_break.duration_minutes = int((now - active_break.start_time).total_seconds() / 60)
        
        attendance.check_out = now.time()
        
        # Calculate hours worked
        check_in_datetime = datetime.combine(today, attendance.check_in)
        check_out_datetime = datetime.combine(today, attendance.check_out)
        
        # Subtract break time
        total_break_minutes = sum([
            br.duration_minutes for br in attendance.break_records 
            if br.duration_minutes is not None
        ])
        
        work_duration = check_out_datetime - check_in_datetime
        work_minutes = int(work_duration.total_seconds() / 60) - total_break_minutes
        hours = work_minutes // 60
        minutes = work_minutes % 60
        
        attendance.hours_worked = f"{hours}h {minutes}m"
        
        db.commit()
        db.refresh(attendance)
        
        # Helper function to format time
        def format_time(time_value):
            if not time_value:
                return None
            if isinstance(time_value, str):
                if ' ' in time_value:
                    return time_value.split(' ')[1]
                return time_value
            return time_value.strftime('%H:%M:%S')
        
        return {
            "message": "Checked out successfully",
            "check_out_time": format_time(attendance.check_out),
            "hours_worked": attendance.hours_worked
        }
    except Exception as e:
        db.rollback()
        print(f"Error in check_out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check out: {str(e)}")

@router.post("/break/start")
def start_break(
    break_type: str = "general",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a break"""
    try:
        today = date.today()
        now = datetime.now()
        
        attendance = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == current_user.id,
                Attendance.date == today
            )
        ).first()
        
        if not attendance or not attendance.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must check in first"
            )
        
        if attendance.check_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already checked out"
            )
        
        # Check if already on break
        active_break = db.query(BreakRecord).filter(
            and_(
                BreakRecord.attendance_id == attendance.id,
                BreakRecord.end_time.is_(None)
            )
        ).first()
        
        if active_break:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already on break"
            )
        
        break_record = BreakRecord(
            attendance_id=attendance.id,
            break_type=break_type,
            start_time=now
        )
        
        db.add(break_record)
        db.commit()
        db.refresh(break_record)
        
        return {
            "message": "Break started",
            "break_start_time": break_record.start_time.strftime('%H:%M:%S')
        }
    except Exception as e:
        db.rollback()
        print(f"Error in start_break: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start break: {str(e)}")

@router.post("/break/end")
def end_break(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End current break"""
    try:
        today = date.today()
        now = datetime.now()
        
        attendance = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == current_user.id,
                Attendance.date == today
            )
        ).first()
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No attendance record found"
            )
        
        active_break = db.query(BreakRecord).filter(
            and_(
                BreakRecord.attendance_id == attendance.id,
                BreakRecord.end_time.is_(None)
            )
        ).first()
        
        if not active_break:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not currently on break"
            )
        
        active_break.end_time = now
        active_break.duration_minutes = int((now - active_break.start_time).total_seconds() / 60)
        
        db.commit()
        db.refresh(active_break)
        
        return {
            "message": "Break ended",
            "break_duration": f"{active_break.duration_minutes} minutes"
        }
    except Exception as e:
        db.rollback()
        print(f"Error in end_break: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to end break: {str(e)}")

@router.get("/calendar")
def get_attendance_calendar(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance calendar for a specific month"""
    try:
        attendance_records = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == current_user.id,
                func.extract('year', Attendance.date) == year,
                func.extract('month', Attendance.date) == month
            )
        ).all()
        
        # Helper function to format time for calendar
        def format_calendar_time(time_value):
            if not time_value:
                return None
            if isinstance(time_value, str):
                if ' ' in time_value:
                    return time_value.split(' ')[1][:5]  # Get HH:MM
                return time_value[:5] if len(time_value) >= 5 else time_value
            return time_value.strftime('%H:%M')
        
        calendar_data = {}
        for record in attendance_records:
            calendar_data[record.date.isoformat()] = {
                "status": record.status,
                "check_in": format_calendar_time(record.check_in),
                "check_out": format_calendar_time(record.check_out),
                "hours_worked": record.hours_worked
            }
        
        return calendar_data
    except Exception as e:
        print(f"Error in get_attendance_calendar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get calendar data: {str(e)}")