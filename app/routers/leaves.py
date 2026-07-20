"""Leave management API.

Workflow rules enforced here (HR best practice):
- Requested days = working days (weekends and company holidays excluded),
  honoring half-day duration types.
- A request is blocked if it overlaps an existing pending/approved leave.
- Paid leave requires sufficient balance at request time; the balance is
  decremented on approval and restored if an approved leave is cancelled.
- Team leads may approve/reject only their own team's requests.
- The employee is notified on approval and rejection.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, datetime, timezone, timedelta

from ..database import get_db
from ..models.user import User
from ..models.leave import Leave, LeaveBalance
from ..models.employee import Employee
from ..models.department import Department
from ..models.position import Position
from ..models.notification import Notification, Holiday
from ..schemas.leave import LeaveCreate, LeaveResponse
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/leaves", tags=["Leave Management"])

# Leave types that do not consume a paid-leave balance
UNPAID_TYPES = {"unpaid"}


# ── Helpers ────────────────────────────────────────────────────────────────

def _holiday_dates(db: Session, start: date, end: date) -> set:
    holidays = db.query(Holiday).filter(
        Holiday.date >= datetime.combine(start, datetime.min.time()),
        Holiday.date <= datetime.combine(end, datetime.max.time()),
    ).all()
    return {h.date.date() if isinstance(h.date, datetime) else h.date for h in holidays}


def working_days(db: Session, start: date, end: date, duration_type: str = "full_day") -> float:
    """Count working days between start and end inclusive.

    Excludes weekends and company holidays. Half-day types count as 0.5
    (only meaningful for single-day requests).
    """
    if end < start:
        return 0.0
    holidays = _holiday_dates(db, start, end)
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in holidays:
            days += 1
        current += timedelta(days=1)
    if duration_type in ("half_day_morning", "half_day_afternoon") and days > 0:
        return 0.5
    return float(days)


def _is_team_member(db: Session, lead_user_id: int, employee_user_id: int) -> bool:
    """True if the employee reports to the given team lead.

    manager_id historically stored either the lead's user id or their
    employee-record id depending on the writer, so both are accepted.
    """
    employee = db.query(Employee).filter(Employee.user_id == employee_user_id).first()
    if not employee or employee.manager_id is None:
        return False
    if employee.manager_id == lead_user_id:
        return True
    lead_employee = db.query(Employee).filter(Employee.user_id == lead_user_id).first()
    return bool(lead_employee and employee.manager_id == lead_employee.id)


def _notify(db: Session, recipient_id: int, sender_id: int, title: str, message: str,
            leave_id: int, priority: str = "medium", action_url: str = ""):
    db.add(Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        title=title,
        message=message,
        notification_type="leave_request",
        priority=priority,
        is_system_generated=True,
        related_entity_type="leave_request",
        related_entity_id=leave_id,
        action_url=action_url,
    ))


def _balance_for(db: Session, employee_id: int, leave_type: str, year: int) -> Optional[LeaveBalance]:
    return db.query(LeaveBalance).filter(
        and_(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type,
            LeaveBalance.year == year,
        )
    ).first()


def _leave_row(db: Session, leave: Leave) -> dict:
    user = db.query(User).filter(User.id == leave.employee_id).first()
    employee = db.query(Employee).filter(Employee.user_id == leave.employee_id).first()
    department = position = None
    if employee:
        if employee.department_id:
            department = db.query(Department).filter(Department.id == employee.department_id).first()
        if employee.position_id:
            position = db.query(Position).filter(Position.id == employee.position_id).first()
    return {
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
        "position": position.title if position else (employee.position if employee else None),
        "leaveType": leave.leave_type,
        "startDate": leave.start_date.isoformat(),
        "endDate": leave.end_date.isoformat(),
        "daysRequested": leave.days_requested,
    }


# ── Listing ────────────────────────────────────────────────────────────────

@router.get("/")
def get_leaves(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    employee_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Leave)

    if current_user.role == "employee":
        query = query.filter(Leave.employee_id == current_user.id)
    elif current_user.role == "team_lead":
        team_member_ids = [
            row[0] for row in db.query(Employee.user_id).filter(Employee.manager_id == current_user.id).all()
        ] + [current_user.id]
        query = query.filter(Leave.employee_id.in_(team_member_ids))

    if status_filter:
        query = query.filter(Leave.status == status_filter)
    if employee_id and current_user.role in ("admin", "hr"):
        query = query.filter(Leave.employee_id == employee_id)

    leaves = query.order_by(Leave.created_at.desc()).offset(skip).limit(limit).all()
    return [_leave_row(db, leave) for leave in leaves]


@router.get("/my-leaves", response_model=List[LeaveResponse])
def get_my_leaves(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    leaves = db.query(Leave).filter(Leave.employee_id == current_user.id).order_by(Leave.created_at.desc()).all()
    return [
        {
            "id": lv.id,
            "employee_id": lv.employee_id,
            "leave_type": lv.leave_type,
            "start_date": lv.start_date,
            "end_date": lv.end_date,
            "days_requested": lv.days_requested,
            "duration": lv.days_requested,
            "reason": lv.reason,
            "status": lv.status,
            "approved_by": lv.approved_by,
            "approved_at": lv.approved_at,
            "rejection_reason": lv.rejection_reason,
            "created_at": lv.created_at,
        }
        for lv in leaves
    ]


@router.get("/balance")
def get_leave_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Current user's leave balances for this year."""
    current_year = datetime.now().year
    balances = db.query(LeaveBalance).filter(
        and_(
            LeaveBalance.employee_id == current_user.id,
            LeaveBalance.year == current_year,
        )
    ).all()
    return [
        {
            "leave_type": b.leave_type,
            "total_allocated": b.total_allocated,
            "taken": b.taken,
            "remaining": b.remaining,
        }
        for b in balances
    ]


# ── Admin/aggregate endpoints (must precede /{leave_id}) ───────────────────

@router.get("/admin/stats")
def get_admin_leave_stats(
    current_user: User = Depends(require_role(["admin", "hr"])),
    db: Session = Depends(get_db),
):
    now = datetime.now()
    approved_this_month = db.query(Leave).filter(
        and_(
            Leave.status == "approved",
            Leave.approved_at.isnot(None),
            func.strftime("%m", Leave.approved_at) == f"{now.month:02d}",
            func.strftime("%Y", Leave.approved_at) == str(now.year),
        )
    ).count()

    return {
        "pendingRequests": db.query(Leave).filter(Leave.status == "pending").count(),
        "approvedThisMonth": approved_this_month,
        "rejectedRequests": db.query(Leave).filter(Leave.status == "rejected").count(),
        "totalRequests": db.query(Leave).count(),
    }


@router.get("/admin/pending")
def get_pending_leave_requests(
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db),
):
    query = db.query(Leave).filter(Leave.status == "pending")

    if current_user.role == "team_lead":
        team_member_ids = [
            row[0] for row in db.query(Employee.user_id).filter(Employee.manager_id == current_user.id).all()
        ]
        query = query.filter(Leave.employee_id.in_(team_member_ids))

    leaves = query.order_by(Leave.created_at.desc()).all()
    rows = []
    for leave in leaves:
        row = _leave_row(db, leave)
        rows.append({
            "id": row["id"],
            "employeeId": row["employeeId"],
            "employeeName": row["employeeName"],
            "department": row["department"],
            "position": row["position"],
            "leaveType": row["leaveType"],
            "startDate": row["startDate"],
            "endDate": row["endDate"],
            "daysRequested": row["daysRequested"],
            "reason": row["reason"],
            "status": row["status"],
            "createdAt": leave.created_at.isoformat() if leave.created_at else None,
        })
    return rows


@router.get("/admin/notifications")
def get_admin_leave_notifications(
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db),
):
    recent_leaves = db.query(Leave).filter(Leave.status == "pending").order_by(Leave.created_at.desc()).limit(10).all()
    notifications = []
    for leave in recent_leaves:
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
                "leaveId": leave.id,
            })
    return notifications


# ── Single leave ───────────────────────────────────────────────────────────

@router.get("/{leave_id}", response_model=LeaveResponse)
def get_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    if current_user.role == "employee" and leave.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own leave requests")
    if current_user.role == "team_lead" and leave.employee_id != current_user.id:
        if not _is_team_member(db, current_user.id, leave.employee_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request belongs to another team")

    return leave


# ── Create ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=LeaveResponse)
def create_leave_request(
    leave_data: LeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if leave_data.end_date < leave_data.start_date:
        raise HTTPException(status_code=422, detail="End date must be on or after the start date")

    duration_type = getattr(leave_data, "duration_type", None) or "full_day"
    days_requested = working_days(db, leave_data.start_date, leave_data.end_date, duration_type)
    if days_requested <= 0:
        raise HTTPException(
            status_code=422,
            detail="The selected dates contain no working days (weekends and holidays are not counted)",
        )

    # Block overlapping requests
    overlap = db.query(Leave).filter(
        Leave.employee_id == current_user.id,
        Leave.status.in_(["pending", "approved"]),
        Leave.start_date <= leave_data.end_date,
        Leave.end_date >= leave_data.start_date,
    ).first()
    if overlap:
        raise HTTPException(
            status_code=409,
            detail=f"You already have a {overlap.status} {overlap.leave_type} leave from {overlap.start_date} to {overlap.end_date} that overlaps these dates",
        )

    # Balance check for paid leave types
    if leave_data.leave_type not in UNPAID_TYPES:
        balance = _balance_for(db, current_user.id, leave_data.leave_type, leave_data.start_date.year)
        if balance is None:
            raise HTTPException(
                status_code=422,
                detail=f"No {leave_data.leave_type} leave allocation found for {leave_data.start_date.year}. Contact HR.",
            )
        # Include days already committed to pending requests of the same type
        pending_days = db.query(func.coalesce(func.sum(Leave.days_requested), 0.0)).filter(
            Leave.employee_id == current_user.id,
            Leave.leave_type == leave_data.leave_type,
            Leave.status == "pending",
        ).scalar() or 0.0
        available = (balance.remaining or 0.0) - pending_days
        if days_requested > available:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Insufficient {leave_data.leave_type} leave balance: "
                    f"{available:.1f} day(s) available (including pending requests), {days_requested:.1f} requested"
                ),
            )

    db_leave = Leave(
        employee_id=current_user.id,
        leave_type=leave_data.leave_type,
        duration_type=duration_type,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        days_requested=days_requested,
        reason=leave_data.reason,
        admin_notified=True,
    )
    db.add(db_leave)
    db.flush()

    # Notify approvers: the employee's team lead if any, plus admin/HR
    employee_rec = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    approver_ids = {u.id for u in db.query(User).filter(User.role.in_(["admin", "hr"])).all()}
    if employee_rec and employee_rec.manager_id:
        approver_ids.add(employee_rec.manager_id)
    for uid in approver_ids:
        _notify(
            db, uid, current_user.id,
            "New leave request",
            f"{current_user.first_name} {current_user.last_name} requested {days_requested:.1f} day(s) of {leave_data.leave_type} leave ({leave_data.start_date} – {leave_data.end_date})",
            db_leave.id,
            action_url=f"/admin/leave-management",
        )

    db.commit()
    db.refresh(db_leave)

    return {
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
        "created_at": db_leave.created_at,
    }


# ── Decisions ──────────────────────────────────────────────────────────────

@router.put("/{leave_id}/approve")
def approve_leave(
    leave_id: int,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db),
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if leave.status != "pending":
        raise HTTPException(status_code=409, detail=f"Only pending requests can be approved (current status: {leave.status})")

    # Team leads may only approve their own team's requests
    if current_user.role == "team_lead" and not _is_team_member(db, current_user.id, leave.employee_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request belongs to another team")
    # No self-approval
    if leave.employee_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot approve your own leave request")

    # Deduct balance for paid leave
    if leave.leave_type not in UNPAID_TYPES:
        balance = _balance_for(db, leave.employee_id, leave.leave_type, leave.start_date.year)
        if balance is None:
            raise HTTPException(status_code=422, detail=f"Employee has no {leave.leave_type} allocation for {leave.start_date.year}")
        if (balance.remaining or 0.0) < leave.days_requested:
            raise HTTPException(
                status_code=422,
                detail=f"Insufficient balance: {balance.remaining:.1f} day(s) remaining, {leave.days_requested:.1f} requested",
            )
        balance.taken = (balance.taken or 0.0) + leave.days_requested
        balance.remaining = (balance.remaining or 0.0) - leave.days_requested

    leave.status = "approved"
    leave.approved_by = current_user.id
    leave.approved_at = datetime.now(timezone.utc)

    _notify(
        db, leave.employee_id, current_user.id,
        "Leave request approved",
        f"Your {leave.leave_type} leave ({leave.start_date} – {leave.end_date}, {leave.days_requested:.1f} day(s)) has been approved",
        leave.id,
        action_url="/employee/leave",
    )

    db.commit()
    db.refresh(leave)
    return {"message": "Leave request approved", "leave_id": leave.id, "status": leave.status}


@router.put("/{leave_id}/reject")
def reject_leave(
    leave_id: int,
    rejection_data: dict,
    current_user: User = Depends(require_role(["admin", "hr", "team_lead"])),
    db: Session = Depends(get_db),
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if leave.status != "pending":
        raise HTTPException(status_code=409, detail="Only pending requests can be rejected")

    if current_user.role == "team_lead" and not _is_team_member(db, current_user.id, leave.employee_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This request belongs to another team")

    reason = (rejection_data.get("rejection_reason") or "").strip()
    if not reason:
        raise HTTPException(status_code=422, detail="A rejection reason is required so the employee understands the decision")

    leave.status = "rejected"
    leave.approved_by = current_user.id
    leave.approved_at = datetime.now(timezone.utc)
    leave.rejection_reason = reason

    _notify(
        db, leave.employee_id, current_user.id,
        "Leave request declined",
        f"Your {leave.leave_type} leave ({leave.start_date} – {leave.end_date}) was declined: {reason}",
        leave.id,
        priority="high",
        action_url="/employee/leave",
    )

    db.commit()
    db.refresh(leave)
    return leave


@router.delete("/{leave_id}")
def cancel_leave(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    if current_user.role not in ("admin", "hr") and leave.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only cancel your own leave requests")

    if leave.status == "pending":
        pass  # always cancellable
    elif leave.status == "approved":
        # Approved leave can be cancelled before it starts; the balance is restored.
        if leave.start_date <= date.today() and current_user.role not in ("admin", "hr"):
            raise HTTPException(status_code=409, detail="Leave that has already started can only be cancelled by HR")
        if leave.leave_type not in UNPAID_TYPES:
            balance = _balance_for(db, leave.employee_id, leave.leave_type, leave.start_date.year)
            if balance:
                balance.taken = max((balance.taken or 0.0) - leave.days_requested, 0.0)
                balance.remaining = (balance.remaining or 0.0) + leave.days_requested
    else:
        raise HTTPException(status_code=409, detail=f"A {leave.status} request cannot be cancelled")

    leave.status = "cancelled"
    db.commit()
    return {"message": "Leave request cancelled", "leave_id": leave.id, "status": leave.status}
