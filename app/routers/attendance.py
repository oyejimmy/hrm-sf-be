from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, time
from ..database import get_db
from ..models.user import User
from ..models.attendance import Attendance
from ..schemas.attendance import AttendanceCreate, AttendanceResponse
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])

@router.get("/", response_model=List[AttendanceResponse])
def get_attendance_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Attendance)
    
    # Role-based filtering
    if current_user.role == "employee":
        query = query.filter(Attendance.employee_id == current_user.id)
    elif current_user.role == "team_lead":
        from ..models.employee import Employee
        team_member_ids = db.query(Employee.user_id).filter(Employee.manager_id == current_user.id).all()
        team_member_ids = [id[0] for id in team_member_ids] + [current_user.id]
        query = query.filter(Attendance.employee_id.in_(team_member_ids))
    
    if employee_id and current_user.role in ["admin", "hr"]:
        query = query.filter(Attendance.employee_id == employee_id)
    
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    
    attendance = query.offset(skip).limit(limit).all()
    return attendance

@router.get("/my-attendance", response_model=List[AttendanceResponse])
def get_my_attendance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Attendance).filter(Attendance.employee_id == current_user.id)
    
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    
    if end_date:
        query = query.filter(Attendance.date <= end_date)
    
    attendance = query.all()
    return attendance

@router.get("/today", response_model=AttendanceResponse)
def get_today_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == current_user.id,
        Attendance.date == today
    ).first()
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance record for today"
        )
    
    return attendance

@router.post("/check-in", response_model=AttendanceResponse)
def check_in(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    current_time = datetime.now().time()
    
    # Check if already checked in today
    existing_attendance = db.query(Attendance).filter(
        Attendance.employee_id == current_user.id,
        Attendance.date == today
    ).first()
    
    if existing_attendance and existing_attendance.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked in today"
        )
    
    if existing_attendance:
        # Update existing record
        existing_attendance.check_in = current_time
        existing_attendance.status = "present"
        db.commit()
        db.refresh(existing_attendance)
        return existing_attendance
    else:
        # Create new attendance record
        attendance = Attendance(
            employee_id=current_user.id,
            date=today,
            check_in=current_time,
            status="present"
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

@router.post("/check-out", response_model=AttendanceResponse)
def check_out(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()
    current_time = datetime.now().time()
    
    attendance = db.query(Attendance).filter(
        Attendance.employee_id == current_user.id,
        Attendance.date == today
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
    
    attendance.check_out = current_time
    
    # Calculate hours worked
    check_in_datetime = datetime.combine(today, attendance.check_in)
    check_out_datetime = datetime.combine(today, current_time)
    hours_worked = check_out_datetime - check_in_datetime
    attendance.hours_worked = str(hours_worked)
    
    db.commit()
    db.refresh(attendance)
    
    return attendance

@router.post("/", response_model=AttendanceResponse)
def create_attendance_record(
    attendance_data: AttendanceCreate,
    current_user: User = Depends(require_role(["admin", "hr"])),
    db: Session = Depends(get_db)
):
    # Check if record already exists
    existing = db.query(Attendance).filter(
        Attendance.employee_id == attendance_data.employee_id,
        Attendance.date == attendance_data.date
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance record already exists for this date"
        )
    
    db_attendance = Attendance(**attendance_data.dict())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    
    return db_attendance

@router.put("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance_record(
    attendance_id: int,
    attendance_data: AttendanceCreate,
    current_user: User = Depends(require_role(["admin", "hr"])),
    db: Session = Depends(get_db)
):
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    for field, value in attendance_data.dict(exclude_unset=True).items():
        if field != "employee_id":  # Don't allow changing employee_id
            setattr(attendance, field, value)
    
    db.commit()
    db.refresh(attendance)
    
    return attendance