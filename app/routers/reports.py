from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from ..models.department import Department
from ..models.attendance import Attendance
from ..models.leave import Leave
from ..models.performance import Performance
from ..models.payroll import Payslip
from ..models.request import EmployeeRequest
from ..models.complaint import Complaint
from ..models.training import TrainingEnrollment
from ..models.asset import Asset
from ..models.health_insurance import InsuranceClaim
from ..models.notification import Notification, Announcement
from ..auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/dashboard/admin")
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        if current_user.role not in ["admin", "hr"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Employee Statistics
        total_employees = db.query(Employee).count()
        active_employees = db.query(Employee).filter(Employee.employment_status == "full_time").count()
        
        # Basic stats only
        return {
            "employees": {
                "total": total_employees,
                "active": active_employees,
                "on_leave_today": 0
            },
            "attendance": {
                "present_today": 0,
                "attendance_rate": 0
            },
            "leaves": {
                "pending": 0,
                "approved_this_month": 0
            },
            "requests": {
                "pending": 0
            },
            "complaints": {
                "pending": 0
            },
            "departments": [],
            "recent_notifications": [],
            "recent_announcements": []
        }
    except Exception as e:
        print(f"Admin dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/employee")
def get_employee_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Get employee record first
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # My Leave Balance using raw SQL to avoid ORM issues
        leave_result = db.execute(
            text("SELECT COALESCE(SUM(days_requested), 0) FROM leaves WHERE employee_id = :emp_id AND status = 'approved' AND strftime('%Y', start_date) = :year"),
            {"emp_id": employee.id, "year": str(current_year)}
        ).fetchone()
        total_leave_days = float(leave_result[0]) if leave_result[0] else 0.0
        
        # Personal and Sick leave breakdown
        personal_leave_result = db.execute(
            text("SELECT COALESCE(SUM(days_requested), 0) FROM leaves WHERE employee_id = :emp_id AND status = 'approved' AND leave_type = 'personal' AND strftime('%Y', start_date) = :year"),
            {"emp_id": employee.id, "year": str(current_year)}
        ).fetchone()
        personal_used = float(personal_leave_result[0]) if personal_leave_result[0] else 0.0
        
        sick_leave_result = db.execute(
            text("SELECT COALESCE(SUM(days_requested), 0) FROM leaves WHERE employee_id = :emp_id AND status = 'approved' AND leave_type = 'sick' AND strftime('%Y', start_date) = :year"),
            {"emp_id": employee.id, "year": str(current_year)}
        ).fetchone()
        sick_used = float(sick_leave_result[0]) if sick_leave_result[0] else 0.0
        
        # My Attendance This Month using raw SQL
        attendance_result = db.execute(
            text("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present FROM attendance WHERE employee_id = :emp_id AND strftime('%m', date) = :month AND strftime('%Y', date) = :year"),
            {"emp_id": employee.id, "month": f"{current_month:02d}", "year": str(current_year)}
        ).fetchone()
        
        total_working_days = int(attendance_result[0]) if attendance_result[0] else 0
        present_days = int(attendance_result[1]) if attendance_result[1] else 0
        
        # Last month attendance for comparison
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        
        last_month_attendance_result = db.execute(
            text("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present FROM attendance WHERE employee_id = :emp_id AND strftime('%m', date) = :month AND strftime('%Y', date) = :year"),
            {"emp_id": employee.id, "month": f"{last_month:02d}", "year": str(last_month_year)}
        ).fetchone()
        
        last_month_total = int(last_month_attendance_result[0]) if last_month_attendance_result[0] else 0
        last_month_present = int(last_month_attendance_result[1]) if last_month_attendance_result[1] else 0
        last_month_rate = round((last_month_present / last_month_total * 100) if last_month_total > 0 else 0, 2)
        
        # My Requests using raw SQL - Leave requests
        leave_requests_result = db.execute(
            text("SELECT COUNT(*) FROM leaves WHERE employee_id = :emp_id AND status = 'pending'"),
            {"emp_id": employee.id}
        ).fetchone()
        pending_leave_requests = int(leave_requests_result[0]) if leave_requests_result[0] else 0
        
        # Other requests
        other_requests_result = db.execute(
            text("SELECT COUNT(*) FROM employee_requests WHERE employee_id = :emp_id AND status = 'pending'"),
            {"emp_id": employee.id}
        ).fetchone()
        pending_other_requests = int(other_requests_result[0]) if other_requests_result[0] else 0
        
        my_pending_requests = pending_leave_requests + pending_other_requests
        
        # My Training Progress using raw SQL
        training_result = db.execute(
            text("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed FROM training_enrollments WHERE employee_id = :emp_id"),
            {"emp_id": employee.id}
        ).fetchone()
        
        total_trainings = int(training_result[0]) if training_result[0] else 0
        completed_trainings = int(training_result[1]) if training_result[1] else 0
        
        return {
            "leave_balance": {
                "used_days": total_leave_days,
                "remaining_days": max(0, 25 - total_leave_days),
                "personal_remaining": max(0, 15 - personal_used),
                "sick_remaining": max(0, 10 - sick_used)
            },
            "attendance": {
                "present_days": present_days,
                "total_working_days": total_working_days,
                "attendance_rate": round((present_days / total_working_days * 100) if total_working_days > 0 else 0, 2),
                "last_month_rate": last_month_rate
            },
            "requests": {
                "pending": my_pending_requests,
                "pending_leaves": pending_leave_requests,
                "pending_other": pending_other_requests
            },
            "training": {
                "completed": completed_trainings,
                "total": total_trainings,
                "completion_rate": round((completed_trainings / total_trainings * 100) if total_trainings > 0 else 0, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data error: {str(e)}")

@router.get("/attendance/monthly")
def get_monthly_attendance_report(
    year: int,
    month: int = 0,  # 0 means all months
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if month == 0:
        # Return yearly data with monthly breakdown
        monthly_rates = []
        for m in range(1, 13):
            query = db.query(Attendance).filter(
                extract('year', Attendance.date) == year,
                extract('month', Attendance.date) == m
            )
            
            if department:
                query = query.join(Employee, Attendance.employee_id == Employee.user_id).filter(
                    Employee.department == department
                )
            
            total_records = query.count()
            present_records = query.filter(Attendance.status.in_(["present", "late"])).count()
            
            rate = round((present_records / total_records * 100) if total_records > 0 else 0, 1)
            monthly_rates.append(rate)
        
        return {"monthly_rates": monthly_rates}
    else:
        # Return specific month data
        query = db.query(Attendance).filter(
            extract('year', Attendance.date) == year,
            extract('month', Attendance.date) == month
        )
        
        if department:
            query = query.join(Employee, Attendance.employee_id == Employee.user_id).filter(
                Employee.department == department
            )
        
        attendance_records = query.all()
        
        # Group by employee
        employee_attendance = {}
        for record in attendance_records:
            emp_id = record.employee_id
            if emp_id not in employee_attendance:
                employee_attendance[emp_id] = {
                    "employee_id": emp_id,
                    "present_days": 0,
                    "absent_days": 0,
                    "late_days": 0,
                    "total_hours": 0
                }
            
            if record.status == "present":
                employee_attendance[emp_id]["present_days"] += 1
            elif record.status == "absent":
                employee_attendance[emp_id]["absent_days"] += 1
            elif record.status == "late":
                employee_attendance[emp_id]["late_days"] += 1
            
            employee_attendance[emp_id]["total_hours"] += float(record.hours_worked) if record.hours_worked else 0
        
        return list(employee_attendance.values())

@router.get("/leave/summary")
def get_leave_summary_report(
    year: int,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr", "team_lead"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Leave).filter(
        extract('year', Leave.start_date) == year,
        Leave.status == "approved"
    )
    
    if department:
        query = query.join(Employee, Leave.employee_id == Employee.user_id).filter(
            Employee.department == department
        )
    
    leaves = query.all()
    
    # Group by leave type
    leave_summary = {}
    for leave in leaves:
        leave_type = leave.leave_type
        if leave_type not in leave_summary:
            leave_summary[leave_type] = {
                "leave_type": leave_type,
                "total_requests": 0,
                "total_days": 0
            }
        
        leave_summary[leave_type]["total_requests"] += 1
        leave_summary[leave_type]["total_days"] += leave.days_requested
    
    return list(leave_summary.values())

@router.get("/payroll/summary")
def get_payroll_summary_report(
    year: int,
    month: Optional[int] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Payslip).filter(
        Payslip.pay_period.like(f"{year}%")
    )
    
    if month:
        query = query.filter(Payslip.pay_period.like(f"{year}-{month:02d}%"))
    
    if department:
        query = query.join(Employee, Payslip.employee_id == Employee.user_id).filter(
            Employee.department == department
        )
    
    payslips = query.all()
    
    total_gross_pay = sum([p.gross_pay for p in payslips])
    total_net_pay = sum([p.net_pay for p in payslips])
    total_deductions = sum([p.total_deductions for p in payslips])
    
    return {
        "total_payslips": len(payslips),
        "total_gross_pay": total_gross_pay,
        "total_net_pay": total_net_pay,
        "total_deductions": total_deductions,
        "average_gross_pay": round(total_gross_pay / len(payslips), 2) if payslips else 0,
        "average_net_pay": round(total_net_pay / len(payslips), 2) if payslips else 0
    }

@router.get("/performance/summary")
def get_performance_summary_report(
    year: int,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Performance).filter(
        extract('year', Performance.created_at) == year,
        Performance.status == "completed"
    )
    
    if department:
        query = query.join(Employee, Performance.employee_id == Employee.user_id).filter(
            Employee.department == department
        )
    
    reviews = query.all()
    
    if not reviews:
        return {
            "total_reviews": 0,
            "average_rating": 0,
            "rating_distribution": {}
        }
    
    total_reviews = len(reviews)
    average_rating = sum([r.overall_rating for r in reviews if r.overall_rating]) / total_reviews
    
    # Rating distribution
    rating_distribution = {}
    for review in reviews:
        if review.overall_rating:
            rating = int(review.overall_rating)
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
    
    return {
        "total_reviews": total_reviews,
        "average_rating": round(average_rating, 2),
        "rating_distribution": rating_distribution
    }

@router.get("/training/progress")
def get_training_progress_report(
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(TrainingEnrollment)
    
    if department:
        query = query.join(Employee, TrainingEnrollment.employee_id == Employee.user_id).filter(
            Employee.department == department
        )
    
    enrollments = query.all()
    
    total_enrollments = len(enrollments)
    completed_trainings = len([e for e in enrollments if e.status == "completed"])
    in_progress_trainings = len([e for e in enrollments if e.status == "in_progress"])
    not_started_trainings = len([e for e in enrollments if e.status == "enrolled"])
    
    return {
        "total_enrollments": total_enrollments,
        "completed_trainings": completed_trainings,
        "in_progress_trainings": in_progress_trainings,
        "not_started_trainings": not_started_trainings,
        "completion_rate": round((completed_trainings / total_enrollments * 100) if total_enrollments > 0 else 0, 2)
    }

@router.get("/assets/utilization")
def get_asset_utilization_report(
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Asset)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    
    assets = query.all()
    
    total_assets = len(assets)
    assigned_assets = len([a for a in assets if a.status == "assigned"])
    available_assets = len([a for a in assets if a.status == "available"])
    maintenance_assets = len([a for a in assets if a.status == "maintenance"])
    
    return {
        "total_assets": total_assets,
        "assigned_assets": assigned_assets,
        "available_assets": available_assets,
        "maintenance_assets": maintenance_assets,
        "utilization_rate": round((assigned_assets / total_assets * 100) if total_assets > 0 else 0, 2)
    }

@router.get("/complaints/analysis")
def get_complaints_analysis_report(
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    complaints = db.query(Complaint).filter(
        extract('year', Complaint.created_at) == year
    ).all()
    
    total_complaints = len(complaints)
    resolved_complaints = len([c for c in complaints if c.status == "resolved"])
    pending_complaints = len([c for c in complaints if c.status == "pending"])
    in_progress_complaints = len([c for c in complaints if c.status == "in_progress"])
    
    # Category breakdown
    category_breakdown = {}
    for complaint in complaints:
        category = complaint.category
        category_breakdown[category] = category_breakdown.get(category, 0) + 1
    
    # Priority breakdown
    priority_breakdown = {}
    for complaint in complaints:
        priority = complaint.priority
        priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
    
    return {
        "total_complaints": total_complaints,
        "resolved_complaints": resolved_complaints,
        "pending_complaints": pending_complaints,
        "in_progress_complaints": in_progress_complaints,
        "resolution_rate": round((resolved_complaints / total_complaints * 100) if total_complaints > 0 else 0, 2),
        "category_breakdown": category_breakdown,
        "priority_breakdown": priority_breakdown
    }

@router.get("/export/attendance")
def export_attendance_data(
    year: int,
    month: int,
    format: str = "json",  # json, csv
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    attendance_data = db.query(Attendance).filter(
        extract('year', Attendance.date) == year,
        extract('month', Attendance.date) == month
    ).all()
    
    # For now, return JSON format
    # In a real implementation, you would generate CSV files
    return {
        "data": [
            {
                "employee_id": att.employee_id,
                "date": att.date.isoformat(),
                "status": att.status,
                "check_in": str(att.check_in) if att.check_in else None,
                "check_out": str(att.check_out) if att.check_out else None,
                "hours_worked": att.hours_worked
            }
            for att in attendance_data
        ],
        "total_records": len(attendance_data)
    }