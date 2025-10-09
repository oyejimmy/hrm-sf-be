from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from typing import List, Optional
from datetime import date, datetime, time, timedelta
import calendar

from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.attendance import Attendance, BreakRecord
from ..schemas.attendance import (
    AttendanceResponse, AttendanceCreate, AttendanceUpdate,
    CheckInResponse, CheckOutResponse, BreakStartResponse, BreakEndResponse,
    AttendanceStatsResponse, TodayAttendanceResponse, BreakRecordResponse
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])

def calculate_hours_worked(check_in: time, check_out: time, break_minutes: int = 0) -> str:
    """Calculate hours worked between check-in and check-out times"""
    if not check_in or not check_out:
        return "0:00"
    
    # Convert times to datetime for calculation
    today = datetime.now().date()
    check_in_dt = datetime.combine(today, check_in)
    check_out_dt = datetime.combine(today, check_out)
    
    # Handle overnight shifts
    if check_out_dt < check_in_dt:
        check_out_dt += timedelta(days=1)
    
    # Calculate total minutes worked
    total_minutes = int((check_out_dt - check_in_dt).total_seconds() / 60)
    
    # Subtract break time
    working_minutes = max(0, total_minutes - break_minutes)
    
    # Convert to hours:minutes format
    hours = working_minutes // 60
    minutes = working_minutes % 60
    
    return f"{hours}:{minutes:02d}"

def get_total_break_minutes(attendance_id: int, db: Session) -> int:
    """Calculate total break minutes for an attendance record"""
    break_records = db.query(BreakRecord).filter(
        BreakRecord.attendance_id == attendance_id,
        BreakRecord.end_time.isnot(None)
    ).all()
    
    total_minutes = 0
    for break_record in break_records:
        if break_record.duration_minutes:
            total_minutes += break_record.duration_minutes
    
    return total_minutes

@router.get("/today", response_model=TodayAttendanceResponse)
async def get_today_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get today's attendance status for the current user"""
    today = date.today()
    
    # Get today's attendance record
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == current_user.id,
            Attendance.date == today
        )
    ).first()
    
    # Get active break if any
    active_break = None
    total_break_time = 0
    
    if attendance:
        # Get active break (break without end_time)
        active_break = db.query(BreakRecord).filter(
            and_(
                BreakRecord.attendance_id == attendance.id,
                BreakRecord.end_time.is_(None)
            )
        ).first()
        
        # Calculate total break time
        total_break_time = get_total_break_minutes(attendance.id, db)
    
    # Determine current status and available actions
    current_status = "not_checked_in"
    can_check_in = True
    can_check_out = False
    can_start_break = False
    can_end_break = False
    hours_worked_today = "0:00"
    
    if attendance:
        if attendance.check_in and not attendance.check_out:
            if active_break:
                current_status = "on_break"
                can_check_in = False
                can_check_out = False
                can_start_break = False
                can_end_break = True
            else:
                current_status = "checked_in"
                can_check_in = False
                can_check_out = True
                can_start_break = True
                can_end_break = False
        elif attendance.check_in and attendance.check_out:
            current_status = "checked_out"
            can_check_in = False
            can_check_out = False
            can_start_break = False
            can_end_break = False
            hours_worked_today = attendance.hours_worked or "0:00"
        else:
            current_status = "not_checked_in"
    
    return TodayAttendanceResponse(
        attendance=attendance,
        current_status=current_status,
        can_check_in=can_check_in,
        can_check_out=can_check_out,
        can_start_break=can_start_break,
        can_end_break=can_end_break,
        active_break=active_break,
        total_break_time=total_break_time,
        hours_worked_today=hours_worked_today
    )

@router.post("/check-in", response_model=CheckInResponse)
async def check_in(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check in for the current user"""
    today = date.today()
    current_time = datetime.now().time()
    
    # Check if already checked in today
    existing_attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == current_user.id,
            Attendance.date == today
        )
    ).first()
    
    if existing_attendance and existing_attendance.check_in:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Create or update attendance record
    if existing_attendance:
        existing_attendance.check_in = current_time
        existing_attendance.status = "present"
        attendance = existing_attendance
    else:
        attendance = Attendance(
            employee_id=current_user.id,
            date=today,
            check_in=current_time,
            status="present"
        )
        db.add(attendance)
    
    db.commit()
    db.refresh(attendance)
    
    return CheckInResponse(
        message="Checked in successfully",
        attendance_id=attendance.id,
        check_in_time=current_time,
        status="present"
    )

@router.post("/check-out", response_model=CheckOutResponse)
async def check_out(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check out for the current user"""
    today = date.today()
    current_time = datetime.now().time()
    
    # Get today's attendance record
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == current_user.id,
            Attendance.date == today
        )
    ).first()
    
    if not attendance or not attendance.check_in:
        raise HTTPException(status_code=400, detail="Must check in first")
    
    if attendance.check_out:
        raise HTTPException(status_code=400, detail="Already checked out today")
    
    # Check if there's an active break
    active_break = db.query(BreakRecord).filter(
        and_(
            BreakRecord.attendance_id == attendance.id,
            BreakRecord.end_time.is_(None)
        )
    ).first()
    
    if active_break:
        raise HTTPException(status_code=400, detail="Please end your break before checking out")
    
    # Calculate total break time and hours worked
    total_break_minutes = get_total_break_minutes(attendance.id, db)
    hours_worked = calculate_hours_worked(attendance.check_in, current_time, total_break_minutes)
    
    # Update attendance record
    attendance.check_out = current_time
    attendance.hours_worked = hours_worked
    
    db.commit()
    
    return CheckOutResponse(
        message="Checked out successfully",
        attendance_id=attendance.id,
        check_out_time=current_time,
        hours_worked=hours_worked,
        status="present"
    )

@router.post("/break/start", response_model=BreakStartResponse)
async def start_break(
    break_type: str = Query("general", description="Type of break"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a break for the current user"""
    today = date.today()
    current_time = datetime.now()
    
    # Get today's attendance record
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == current_user.id,
            Attendance.date == today
        )
    ).first()
    
    if not attendance or not attendance.check_in:
        raise HTTPException(status_code=400, detail="Must check in first")
    
    if attendance.check_out:
        raise HTTPException(status_code=400, detail="Cannot start break after checking out")
    
    # Check if there's already an active break
    active_break = db.query(BreakRecord).filter(
        and_(
            BreakRecord.attendance_id == attendance.id,
            BreakRecord.end_time.is_(None)
        )
    ).first()
    
    if active_break:
        raise HTTPException(status_code=400, detail="Break already in progress")
    
    # Create new break record
    break_record = BreakRecord(
        attendance_id=attendance.id,
        break_type=break_type,
        start_time=current_time
    )
    
    db.add(break_record)
    db.commit()
    db.refresh(break_record)
    
    return BreakStartResponse(
        message="Break started successfully",
        break_id=break_record.id,
        start_time=current_time,
        break_type=break_type
    )

@router.post("/break/end", response_model=BreakEndResponse)
async def end_break(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End the current break for the user"""
    today = date.today()
    current_time = datetime.now()
    
    # Get today's attendance record
    attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == current_user.id,
            Attendance.date == today
        )
    ).first()
    
    if not attendance:
        raise HTTPException(status_code=400, detail="No attendance record found for today")
    
    # Get active break
    active_break = db.query(BreakRecord).filter(
        and_(
            BreakRecord.attendance_id == attendance.id,
            BreakRecord.end_time.is_(None)
        )
    ).first()
    
    if not active_break:
        raise HTTPException(status_code=400, detail="No active break found")
    
    # Calculate break duration
    duration_minutes = int((current_time - active_break.start_time).total_seconds() / 60)
    
    # Update break record
    active_break.end_time = current_time
    active_break.duration_minutes = duration_minutes
    
    db.commit()
    
    return BreakEndResponse(
        message="Break ended successfully",
        break_id=active_break.id,
        end_time=current_time,
        duration_minutes=duration_minutes
    )

@router.get("/my-attendance", response_model=dict)
async def get_my_attendance(
    year: Optional[int] = Query(None, description="Year filter"),
    month: Optional[int] = Query(None, description="Month filter"),
    limit: Optional[int] = Query(30, description="Limit number of records"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance records for the current user"""
    query = db.query(Attendance).filter(Attendance.employee_id == current_user.id)
    
    # Apply filters
    if year:
        query = query.filter(extract('year', Attendance.date) == year)
    if month:
        query = query.filter(extract('month', Attendance.date) == month)
    
    # Get records with limit
    records = query.order_by(Attendance.date.desc()).limit(limit).all()
    
    # Calculate statistics
    total_records = query.count()
    present_days = query.filter(Attendance.status == "present").count()
    absent_days = query.filter(Attendance.status == "absent").count()
    late_days = query.filter(Attendance.status == "late").count()
    
    # Calculate total hours worked
    total_hours = 0.0
    for record in records:
        if record.hours_worked:
            try:
                hours, minutes = record.hours_worked.split(":")
                total_hours += float(hours) + float(minutes) / 60
            except:
                pass
    
    return {
        "records": records,
        "statistics": {
            "total_records": total_records,
            "present_days": present_days,
            "absent_days": absent_days,
            "late_days": late_days,
            "total_hours_worked": round(total_hours, 2),
            "average_hours_per_day": round(total_hours / max(present_days, 1), 2)
        }
    }

@router.get("/records", response_model=List[AttendanceResponse])
async def get_attendance_records(
    limit: int = Query(30, description="Number of records to fetch"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance records for the current user (for history table)"""
    records = db.query(Attendance).filter(
        Attendance.employee_id == current_user.id
    ).order_by(Attendance.date.desc()).limit(limit).all()
    
    return records

@router.get("/stats", response_model=AttendanceStatsResponse)
async def get_attendance_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance statistics for the current user"""
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Get current month's records
    month_records = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == current_user.id,
            extract('year', Attendance.date) == current_year,
            extract('month', Attendance.date) == current_month
        )
    ).all()
    
    # Calculate statistics
    total_present = len([r for r in month_records if r.status == "present"])
    total_absent = len([r for r in month_records if r.status == "absent"])
    total_late = len([r for r in month_records if r.status == "late"])
    
    # Calculate total hours worked
    total_hours = 0.0
    for record in month_records:
        if record.hours_worked:
            try:
                hours, minutes = record.hours_worked.split(":")
                total_hours += float(hours) + float(minutes) / 60
            except:
                pass
    
    # Get today's attendance
    today_attendance = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == current_user.id,
            Attendance.date == today
        )
    ).first()
    
    status_today = today_attendance.status if today_attendance else "absent"
    break_time_today = 0
    
    if today_attendance:
        break_time_today = get_total_break_minutes(today_attendance.id, db)
    
    # Calculate attendance percentage
    working_days = calendar.monthrange(current_year, current_month)[1]
    attendance_percentage = (total_present / working_days) * 100 if working_days > 0 else 0
    
    return AttendanceStatsResponse(
        total_present_days=total_present,
        total_absent_days=total_absent,
        total_late_days=total_late,
        total_hours_worked=round(total_hours, 2),
        average_hours_per_day=round(total_hours / max(total_present, 1), 2),
        current_month_attendance=round(attendance_percentage, 1),
        break_time_today=break_time_today,
        status_today=status_today
    )

# Admin/HR endpoints
@router.get("/", response_model=List[AttendanceResponse])
async def get_all_attendance(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(1000, description="Number of records to fetch"),
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all attendance records (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    query = db.query(Attendance)
    
    # Apply filters only if provided
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if date_from:
        query = query.filter(Attendance.date >= date_from)
    if date_to:
        query = query.filter(Attendance.date <= date_to)
    
    # Get all records without skip/limit if no filters applied
    if not employee_id and not date_from and not date_to and skip == 0:
        records = query.order_by(Attendance.date.desc()).all()
    else:
        records = query.order_by(Attendance.date.desc()).offset(skip).limit(limit).all()
    
    return records

@router.post("/", response_model=AttendanceResponse)
async def create_attendance_record(
    attendance_data: AttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create attendance record (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if record already exists
    existing = db.query(Attendance).filter(
        and_(
            Attendance.employee_id == attendance_data.employee_id,
            Attendance.date == attendance_data.date
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Attendance record already exists for this date")
    
    attendance = Attendance(**attendance_data.dict())
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return attendance

# Admin endpoints for compatibility




@router.get("/admin/notifications", response_model=List[dict])
async def get_admin_attendance_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get attendance notifications for admin (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Mock notifications for now
    notifications = [
        {
            "id": "1",
            "type": "warning",
            "title": "Late Arrivals",
            "message": "5 employees arrived late today",
            "time": "Today",
            "read": False
        }
    ]
    return notifications

@router.post("/admin/export-report", response_model=dict)
async def export_attendance_report(
    filters: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export attendance report (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"message": "Report export initiated", "status": "success"}

@router.post("/admin/process-auto-absence", response_model=dict)
async def process_auto_absence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process auto-absence for employees (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"message": "Auto-absence processing completed", "status": "success"}

@router.get("/all", response_model=List[dict])
async def get_all_attendance_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all attendance records with employee details"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    records = db.query(Attendance).join(User, Attendance.employee_id == User.id).all()
    
    result = []
    for record in records:
        result.append({
            "id": record.id,
            "employee_id": record.employee_id,
            "employee_email": record.employee.email,
            "employee_name": f"{record.employee.first_name} {record.employee.last_name}",
            "date": record.date,
            "check_in": record.check_in,
            "check_out": record.check_out,
            "status": record.status,
            "hours_worked": record.hours_worked,
            "notes": record.notes,
            "created_at": record.created_at
        })
    
    return result