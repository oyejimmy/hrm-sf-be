from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from bson import ObjectId

from app.models.user import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_active_user)
):
    """Get dashboard statistics."""
    db = get_database()
    
    # Get total employees
    total_employees = await db.employees.count_documents({})
    
    # Get active employees today
    today = date.today()
    active_today = await db.attendance.count_documents({
        "date": today,
        "status": "present"
    })
    
    # Get employees on leave today
    on_leave = await db.leave_requests.count_documents({
        "start_date": {"$lte": today},
        "end_date": {"$gte": today},
        "status": "approved"
    })
    
    # Get pending approvals
    pending_leave_requests = await db.leave_requests.count_documents({
        "status": "pending"
    })
    
    # Get recent activities (last 7 days)
    week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = week_ago.replace(day=week_ago.day - 7)
    
    recent_activities = []
    
    # Recent leave requests
    recent_leaves = await db.leave_requests.find({
        "created_at": {"$gte": week_ago}
    }).sort("created_at", -1).limit(5).to_list(length=5)
    
    for leave in recent_leaves:
        user = await db.users.find_one({"_id": ObjectId(leave["user_id"])})
        recent_activities.append({
            "type": "leave_request",
            "message": f"{user['first_name']} {user['last_name']} requested {leave['leave_type']} leave",
            "timestamp": leave["created_at"],
            "status": leave["status"]
        })
    
    # Recent attendance logs
    recent_attendance = await db.attendance.find({
        "created_at": {"$gte": week_ago}
    }).sort("created_at", -1).limit(5).to_list(length=5)
    
    for attendance in recent_attendance:
        user = await db.users.find_one({"_id": ObjectId(attendance["user_id"])})
        recent_activities.append({
            "type": "attendance",
            "message": f"{user['first_name']} {user['last_name']} logged {attendance['status']} attendance",
            "timestamp": attendance["created_at"],
            "status": attendance["status"]
        })
    
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activities = recent_activities[:10]
    
    return {
        "total_employees": total_employees,
        "active_today": active_today,
        "on_leave": on_leave,
        "pending_approvals": pending_leave_requests,
        "recent_activities": recent_activities
    }

@router.get("/attendance-report")
async def get_attendance_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department: Optional[str] = None,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Generate attendance report for a date range."""
    db = get_database()
    
    # Build filter
    filter_dict = {
        "date": {"$gte": start_date, "$lte": end_date}
    }
    
    if department:
        # Get employees in department
        employees = await db.employees.find({"department": department}).to_list(length=None)
        employee_user_ids = [emp["user_id"] for emp in employees]
        filter_dict["user_id"] = {"$in": employee_user_ids}
    
    # Get attendance records
    cursor = db.attendance.find(filter_dict)
    records = await cursor.to_list(length=None)
    
    # Group by user and calculate statistics
    user_stats = {}
    for record in records:
        user_id = record["user_id"]
        if user_id not in user_stats:
            user_stats[user_id] = {
                "user_id": user_id,
                "total_days": 0,
                "present_days": 0,
                "absent_days": 0,
                "late_days": 0,
                "half_days": 0,
                "total_work_hours": 0,
                "total_overtime_hours": 0
            }
        
        user_stats[user_id]["total_days"] += 1
        user_stats[user_id]["total_work_hours"] += record.get("work_hours", 0)
        user_stats[user_id]["total_overtime_hours"] += record.get("overtime_hours", 0)
        
        if record["status"] == "present":
            user_stats[user_id]["present_days"] += 1
        elif record["status"] == "absent":
            user_stats[user_id]["absent_days"] += 1
        elif record["status"] == "late":
            user_stats[user_id]["late_days"] += 1
        elif record["status"] == "half_day":
            user_stats[user_id]["half_days"] += 1
    
    # Add user information
    report_data = []
    for user_id, stats in user_stats.items():
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        employee = await db.employees.find_one({"user_id": user_id})
        
        if user and employee:
            attendance_percentage = (stats["present_days"] / stats["total_days"] * 100) if stats["total_days"] > 0 else 0
            
            report_data.append({
                "user_id": user_id,
                "employee_id": employee.get("employee_id"),
                "name": f"{user['first_name']} {user['last_name']}",
                "department": employee.get("department"),
                "position": employee.get("position"),
                **stats,
                "attendance_percentage": round(attendance_percentage, 2)
            })
    
    return {
        "report_period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "department": department,
        "total_records": len(report_data),
        "data": report_data
    }

@router.get("/leave-report")
async def get_leave_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department: Optional[str] = None,
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Generate leave report for a date range."""
    db = get_database()
    
    # Build filter
    filter_dict = {
        "start_date": {"$gte": start_date},
        "end_date": {"$lte": end_date}
    }
    
    if department:
        # Get employees in department
        employees = await db.employees.find({"department": department}).to_list(length=None)
        employee_user_ids = [emp["user_id"] for emp in employees]
        filter_dict["user_id"] = {"$in": employee_user_ids}
    
    # Get leave requests
    cursor = db.leave_requests.find(filter_dict)
    requests = await cursor.to_list(length=None)
    
    # Group by leave type and status
    leave_stats = {}
    for request in requests:
        leave_type = request["leave_type"]
        status = request["status"]
        
        if leave_type not in leave_stats:
            leave_stats[leave_type] = {
                "total_requests": 0,
                "approved": 0,
                "rejected": 0,
                "pending": 0,
                "total_days": 0
            }
        
        leave_stats[leave_type]["total_requests"] += 1
        leave_stats[leave_type][status] += 1
        
        days = (request["end_date"] - request["start_date"]).days + 1
        leave_stats[leave_type]["total_days"] += days
    
    # Add user information to requests
    report_data = []
    for request in requests:
        user = await db.users.find_one({"_id": ObjectId(request["user_id"])})
        employee = await db.employees.find_one({"user_id": request["user_id"]})
        
        if user and employee:
            days = (request["end_date"] - request["start_date"]).days + 1
            
            report_data.append({
                "request_id": str(request["_id"]),
                "user_id": request["user_id"],
                "employee_id": employee.get("employee_id"),
                "name": f"{user['first_name']} {user['last_name']}",
                "department": employee.get("department"),
                "leave_type": request["leave_type"],
                "start_date": request["start_date"],
                "end_date": request["end_date"],
                "days": days,
                "status": request["status"],
                "reason": request["reason"],
                "created_at": request["created_at"]
            })
    
    return {
        "report_period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "department": department,
        "leave_statistics": leave_stats,
        "total_requests": len(report_data),
        "data": report_data
    }

@router.get("/employee-summary/{user_id}")
async def get_employee_summary(
    user_id: str,
    year: int = Query(..., ge=2020),
    current_user: dict = Depends(get_current_active_user)
):
    """Get comprehensive employee summary."""
    db = get_database()
    
    # Check permissions
    if (current_user["role"] == UserRole.EMPLOYEE and 
        user_id != str(current_user["_id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get user and employee info
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    employee = await db.employees.find_one({"user_id": user_id})
    
    if not user or not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or employee not found"
        )
    
    # Get attendance summary for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    attendance_cursor = db.attendance.find({
        "user_id": user_id,
        "date": {"$gte": start_date, "$lte": end_date}
    })
    attendance_records = await attendance_cursor.to_list(length=None)
    
    # Calculate attendance stats
    total_days = len(attendance_records)
    present_days = len([r for r in attendance_records if r["status"] == "present"])
    absent_days = len([r for r in attendance_records if r["status"] == "absent"])
    late_days = len([r for r in attendance_records if r["status"] == "late"])
    half_days = len([r for r in attendance_records if r["status"] == "half_day"])
    
    total_work_hours = sum(r.get("work_hours", 0) for r in attendance_records)
    total_overtime_hours = sum(r.get("overtime_hours", 0) for r in attendance_records)
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Get leave summary for the year
    leave_cursor = db.leave_requests.find({
        "user_id": user_id,
        "start_date": {"$gte": start_date},
        "end_date": {"$lte": end_date}
    })
    leave_records = await leave_cursor.to_list(length=None)
    
    # Calculate leave stats
    total_leave_days = sum((r["end_date"] - r["start_date"]).days + 1 for r in leave_records)
    approved_leaves = len([r for r in leave_records if r["status"] == "approved"])
    pending_leaves = len([r for r in leave_records if r["status"] == "pending"])
    rejected_leaves = len([r for r in leave_records if r["status"] == "rejected"])
    
    return {
        "employee_info": {
            "user_id": user_id,
            "employee_id": employee.get("employee_id"),
            "name": f"{user['first_name']} {user['last_name']}",
            "email": user["email"],
            "department": employee.get("department"),
            "position": employee.get("position"),
            "hire_date": employee.get("hire_date")
        },
        "year": year,
        "attendance_summary": {
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": absent_days,
            "late_days": late_days,
            "half_days": half_days,
            "total_work_hours": total_work_hours,
            "total_overtime_hours": total_overtime_hours,
            "attendance_percentage": round(attendance_percentage, 2)
        },
        "leave_summary": {
            "total_requests": len(leave_records),
            "approved_leaves": approved_leaves,
            "pending_leaves": pending_leaves,
            "rejected_leaves": rejected_leaves,
            "total_leave_days": total_leave_days
        }
    }
