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

@router.get("/", response_model=List[LeaveResponse])
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
    return leaves

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

@router.put("/{leave_id}/approve", response_model=LeaveResponse)
def approve_leave(
    leave_id: int,
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
        
        # Team leads can only approve their team's leaves
        if current_user.role == "team_lead":
            from ..models.employee import Employee
            employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
            if not employee or employee.manager_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        leave.status = "approved"
        leave.approved_by = current_user.id
        leave.approved_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(leave)
        
        return leave
    except Exception as e:
        db.rollback()
        print(f"Error approving leave: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve leave request: {str(e)}"
        )

@router.put("/{leave_id}/reject", response_model=LeaveResponse)
def reject_leave(
    leave_id: int,
    rejection_data: LeaveUpdate,
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
        
        # Team leads can only reject their team's leaves
        if current_user.role == "team_lead":
            from ..models.employee import Employee
            employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
            if not employee or employee.manager_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        leave.status = "rejected"
        leave.approved_by = current_user.id
        leave.approved_at = datetime.now(timezone.utc)
        leave.rejection_reason = rejection_data.rejection_reason
        
        db.commit()
        db.refresh(leave)
        
        return leave
    except Exception as e:
        db.rollback()
        print(f"Error rejecting leave: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject leave request: {str(e)}"
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
        
        approved_this_month = db.query(Leave).filter(
            and_(
                Leave.status == "approved",
                func.extract('month', Leave.start_date) == current_month,
                func.extract('year', Leave.start_date) == current_year
            )
        ).count()
        
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
            employee = db.query(User).filter(User.id == leave.employee_id).first()
            result.append({
                "id": leave.id,
                "employeeId": leave.employee_id,
                "employeeName": employee.full_name if employee else "Unknown",
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
            employee = db.query(User).filter(User.id == leave.employee_id).first()
            if employee:
                notifications.append({
                    "id": f"leave_{leave.id}",
                    "type": "leave_request",
                    "employeeId": str(leave.employee_id),
                    "employeeName": employee.full_name,
                    "message": f"{employee.full_name} requested {leave.leave_type} leave from {leave.start_date} to {leave.end_date}",
                    "timestamp": leave.created_at.isoformat() if leave.created_at else datetime.now().isoformat(),
                    "read": False,
                    "priority": "medium",
                    "leaveId": leave.id
                })
        
        return notifications
    except Exception as e:
        print(f"Error in get_admin_leave_notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")