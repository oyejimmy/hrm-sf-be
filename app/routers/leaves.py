from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime, timezone
from ..database import get_db
from ..models.user import User
from ..models.leave import Leave, LeaveBalance
from ..schemas.leave import LeaveCreate, LeaveResponse, LeaveUpdate
from datetime import datetime
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/leaves", tags=["Leave Management"])

@router.get("/")
def get_leaves(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    employee_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Leave)
    
    # Role-based filtering
    if current_user.role == "employee":
        query = query.filter(Leave.employee_id == current_user.id)
    elif current_user.role == "team_lead":
        # Team leads can see their team's leave requests
        from ..models.employee import Employee
        team_member_ids = db.query(Employee.user_id).filter(Employee.manager_id == current_user.id).all()
        team_member_ids = [id[0] for id in team_member_ids] + [current_user.id]
        query = query.filter(Leave.employee_id.in_(team_member_ids))
    
    if status:
        query = query.filter(Leave.status == status)
    
    if employee_id and current_user.role in ["admin", "hr"]:
        query = query.filter(Leave.employee_id == employee_id)
    
    leaves = query.offset(skip).limit(limit).all()
    
    # Format response with employee details
    result = []
    for leave in leaves:
        from ..models.employee import Employee
        from ..models.department import Department
        from ..models.position import Position
        user = db.query(User).filter(User.id == leave.employee_id).first()
        employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
        department = None
        position = None
        if employee:
            if employee.department_id:
                department = db.query(Department).filter(Department.id == employee.department_id).first()
            if employee.position_id:
                position = db.query(Position).filter(Position.id == employee.position_id).first()
        result.append({
            "id": leave.id,
            "employee_id": leave.employee_id,
            "leave_type": leave.leave_type,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "days_requested": leave.days_requested,
            "reason": leave.reason,
            "status": leave.status,
            "created_at": leave.created_at,
            "approved_by": leave.approved_by,
            "approved_at": leave.approved_at,
            "rejection_reason": leave.rejection_reason,
            "employeeName": user.full_name if user else "Unknown",
            "employeeId": employee.employee_id if employee else str(leave.employee_id),
            "department": department.name if department else None,
            "position": position.title if position else employee.position if employee else None,
            "leaveType": leave.leave_type,
            "startDate": leave.start_date.isoformat(),
            "endDate": leave.end_date.isoformat(),
            "daysRequested": leave.days_requested
        })
    
    return result

@router.get("/my-leaves", response_model=List[LeaveResponse])
def get_my_leaves(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        leaves = db.query(Leave).filter(Leave.employee_id == current_user.id).order_by(Leave.created_at.desc()).all()
        
        # Create response with duration field for each leave
        response_leaves = []
        for leave in leaves:
            response_dict = {
                "id": leave.id,
                "employee_id": leave.employee_id,
                "leave_type": leave.leave_type,
                "start_date": leave.start_date,
                "end_date": leave.end_date,
                "days_requested": leave.days_requested,
                "duration": leave.days_requested,
                "reason": leave.reason,
                "status": leave.status,
                "approved_by": leave.approved_by,
                "approved_at": leave.approved_at,
                "rejection_reason": leave.rejection_reason,
                "created_at": leave.created_at
            }
            response_leaves.append(response_dict)
        
        return response_leaves
    except Exception as e:
        print(f"Error fetching my leaves: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leave requests: {str(e)}"
        )



@router.get("/balance")
def get_leave_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's leave balance"""
    try:
        from datetime import datetime
        current_year = datetime.now().year
        
        balances = db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == current_user.id,
                LeaveBalance.year == current_year
            )
        ).all()
        
        return [{
            "leave_type": balance.leave_type,
            "total_allocated": balance.total_allocated,
            "taken": balance.taken,
            "remaining": balance.remaining
        } for balance in balances]
    except Exception as e:
        print(f"Error in get_leave_balance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get leave balance: {str(e)}")

@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Check permissions
    if current_user.role == "employee" and leave.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    elif current_user.role == "team_lead":
        from ..models.employee import Employee
        employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
        if employee and employee.manager_id != current_user.id and leave.employee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return leave

@router.post("/", response_model=LeaveResponse)
def create_leave_request(
    leave_data: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Calculate days requested if not provided
        if leave_data.days_requested is None or leave_data.days_requested == 0:
            days_requested = (leave_data.end_date - leave_data.start_date).days + 1
        else:
            days_requested = leave_data.days_requested
        
        db_leave = Leave(
            employee_id=current_user.id,
            leave_type=leave_data.leave_type,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            days_requested=days_requested,
            reason=leave_data.reason,
            admin_notified=True  # Mark as notified since we'll create notification
        )
        
        db.add(db_leave)
        db.commit()
        db.refresh(db_leave)
        
        # Create notification for admin/HR
        from ..models.notification import Notification
        
        # Get all admin and HR users
        admin_users = db.query(User).filter(User.role.in_(["admin", "hr"])).all()
        
        for admin_user in admin_users:
            notification = Notification(
                recipient_id=admin_user.id,
                sender_id=current_user.id,
                title="New Leave Request",
                message=f"{current_user.first_name} {current_user.last_name} has requested {leave_data.leave_type} leave from {leave_data.start_date} to {leave_data.end_date}",
                notification_type="leave_request",
                priority="medium",
                is_system_generated=True,
                related_entity_type="leave_request",
                related_entity_id=db_leave.id,
                action_url=f"/admin/leaves/{db_leave.id}"
            )
            db.add(notification)
        
        db.commit()
        
        # Create response with duration field
        response_dict = {
            "id": db_leave.id,
            "employee_id": db_leave.employee_id,
            "leave_type": db_leave.leave_type,
            "start_date": db_leave.start_date,
            "end_date": db_leave.end_date,
            "days_requested": db_leave.days_requested,
            "duration": db_leave.days_requested,
            "reason": db_leave.reason,
            "status": db_leave.status,
            "approved_by": db_leave.approved_by,
            "approved_at": db_leave.approved_at,
            "rejection_reason": db_leave.rejection_reason,
            "created_at": db_leave.created_at
        }
        return response_dict
        
    except Exception as e:
        db.rollback()
        print(f"Error creating leave request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create leave request: {str(e)}"
        )

@router.put("/{leave_id}/approve")
def approve_leave(
    leave_id: int,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    try:
        print(f"Attempting to approve leave ID: {leave_id}")
        print(f"Current user: {current_user.email}, Role: {current_user.role}")
        
        # Check if leave exists
        leave = db.query(Leave).filter(Leave.id == leave_id).first()
        if not leave:
            print(f"Leave with ID {leave_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        print(f"Found leave: ID={leave.id}, Status={leave.status}, Employee={leave.employee_id}")
        
        if leave.status != "pending":
            print(f"Leave status is {leave.status}, not pending")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve leave with status: {leave.status}"
            )
        
        # Update leave status
        print("Updating leave status to approved")
        leave.status = "approved"
        leave.approved_by = current_user.id
        leave.approved_at = datetime.now(timezone.utc)
        
        print("Committing changes to database")
        db.commit()
        db.refresh(leave)
        
        print("Leave approved successfully")
        return {
            "message": "Leave request approved successfully",
            "leave_id": leave.id,
            "status": leave.status
        }
        
    except HTTPException as he:
        print(f"HTTP Exception: {he.detail}")
        db.rollback()
        raise
    except Exception as e:
        print(f"Unexpected error approving leave: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/{leave_id}/reject")
def reject_leave(
    leave_id: int,
    rejection_data: dict,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    try:
        leave = db.query(Leave).filter(Leave.id == leave_id).first()
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        if leave.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending leave requests can be rejected"
            )
        
        # Team leads can only reject their team's leaves
        if current_user.role == "team_lead":
            from ..models.employee import Employee
            employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
            if not employee or employee.manager_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        # Update leave status
        leave.status = "rejected"
        leave.approved_by = current_user.id
        leave.approved_at = datetime.now(timezone.utc)
        leave.rejection_reason = rejection_data.get('rejection_reason', '')
        
        # Commit the changes
        db.commit()
        db.refresh(leave)
        
        return leave
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Error rejecting leave: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject leave request"
        )

@router.delete("/{leave_id}")
def cancel_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Leave request not found"
        )
    
    # Only the employee who created the leave or admin/hr can cancel
    if current_user.role not in ["admin", "hr"] and leave.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Can only cancel pending leaves
    if leave.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending leave requests"
        )
    
    leave.status = "cancelled"
    db.commit()
    
    return {"message": "Leave request cancelled successfully"}

# Admin endpoints for leave management
@router.get("/admin/stats")
def get_admin_leave_stats(
    current_user: User = Depends(require_role(["admin", "hr"])),
    db: Session = Depends(get_db)
):
    """Get leave statistics for admin dashboard"""
    try:
        # Get pending leave requests count
        pending_count = db.query(Leave).filter(Leave.status == "pending").count()
        
        # Get approved leaves for this month
        from datetime import datetime
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Use strftime for SQLite compatibility
        print(f"DEBUG: Looking for approved leaves in month {current_month:02d} year {current_year}")
        approved_this_month = db.query(Leave).filter(
            and_(
                Leave.status == "approved",
                Leave.approved_at.isnot(None),
                func.strftime('%m', Leave.approved_at) == f"{current_month:02d}",
                func.strftime('%Y', Leave.approved_at) == str(current_year)
            )
        ).count()
        print(f"DEBUG: Found {approved_this_month} approved leaves this month")
        
        # Get rejected leaves count
        rejected_count = db.query(Leave).filter(Leave.status == "rejected").count()
        
        return {
            "pendingRequests": pending_count,
            "approvedThisMonth": approved_this_month,
            "rejectedRequests": rejected_count,
            "totalRequests": db.query(Leave).count()
        }
    except Exception as e:
        print(f"Error in get_admin_leave_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get leave stats: {str(e)}")

@router.get("/admin/pending")
def get_pending_leave_requests(
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    """Get all pending leave requests for admin/HR"""
    try:
        query = db.query(Leave).filter(Leave.status == "pending")
        
        # Team leads can only see their team's requests
        if current_user.role == "team_lead":
            from ..models.employee import Employee
            team_member_ids = db.query(Employee.user_id).filter(Employee.manager_id == current_user.id).all()
            team_member_ids = [id[0] for id in team_member_ids]
            query = query.filter(Leave.employee_id.in_(team_member_ids))
        
        leaves = query.all()
        
        # Format response with employee details
        result = []
        for leave in leaves:
            from ..models.employee import Employee
            from ..models.department import Department
            from ..models.position import Position
            user = db.query(User).filter(User.id == leave.employee_id).first()
            employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
            department = None
            position = None
            if employee:
                if employee.department_id:
                    department = db.query(Department).filter(Department.id == employee.department_id).first()
                if employee.position_id:
                    position = db.query(Position).filter(Position.id == employee.position_id).first()
            result.append({
                "id": leave.id,
                "employeeId": employee.employee_id if employee else str(leave.employee_id),
                "employeeName": user.full_name if user else "Unknown",
                "department": department.name if department else None,
                "position": position.title if position else employee.position if employee else None,
                "leaveType": leave.leave_type,
                "startDate": leave.start_date.isoformat(),
                "endDate": leave.end_date.isoformat(),
                "daysRequested": leave.days_requested,
                "reason": leave.reason,
                "status": leave.status,
                "createdAt": leave.created_at.isoformat() if leave.created_at else None
            })
        
        return result
    except Exception as e:
        print(f"Error in get_pending_leave_requests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending requests: {str(e)}")

@router.get("/debug/{leave_id}")
def debug_leave(
    leave_id: int,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check leave data"""
    try:
        leave = db.query(Leave).filter(Leave.id == leave_id).first()
        if not leave:
            return {"error": f"Leave {leave_id} not found"}
        
        from ..models.employee import Employee
        user = db.query(User).filter(User.id == leave.employee_id).first()
        employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
        
        return {
            "leave_id": leave.id,
            "employee_id": leave.employee_id,
            "employee_name": user.full_name if user else "Unknown",
            "employee_code": employee.employee_id if employee else str(leave.employee_id),
            "leave_type": leave.leave_type,
            "status": leave.status,
            "start_date": str(leave.start_date),
            "end_date": str(leave.end_date),
            "approved_by": leave.approved_by,
            "approved_at": str(leave.approved_at) if leave.approved_at else None,
            "created_at": str(leave.created_at) if leave.created_at else None
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/admin/notifications")
def get_admin_leave_notifications(
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db)
):
    """Get leave notifications for admin"""
    try:
        notifications = []
        
        # Get recent pending leave requests
        recent_leaves = db.query(Leave).filter(
            Leave.status == "pending"
        ).order_by(Leave.created_at.desc()).limit(10).all()
        
        for leave in recent_leaves:
            from ..models.employee import Employee
            user = db.query(User).filter(User.id == leave.employee_id).first()
            employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
            if user:
                notifications.append({
                    "id": f"leave_{leave.id}",
                    "type": "leave_request",
                    "employeeId": employee.employee_id if employee else str(leave.employee_id),
                    "employeeName": user.full_name,
                    "message": f"{user.full_name} requested {leave.leave_type} leave from {leave.start_date} to {leave.end_date}",
                    "timestamp": leave.created_at.isoformat() if leave.created_at else datetime.now().isoformat(),
                    "read": False,
                    "priority": "medium",
                    "leaveId": leave.id
                })
        
        return notifications
    except Exception as e:
        print(f"Error in get_admin_leave_notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")