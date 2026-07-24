"""Finance API — powers the accountant portal.

Scope: expenses (payables), invoices (receivables), a filterable financial audit
trail, and the aggregated summary that drives the dashboard.

Access: the whole router is restricted to admin + accountant. HR deliberately
has no visibility into company financials (they keep payroll access via
/api/payroll, which has its own gate).

Controls mirrored from the payroll module:
- Status machines are enforced server-side (pending -> approved -> paid).
- Maker/checker: whoever raised an expense cannot approve it.
- Every mutation writes a FinancialAuditLog row; the log is never updated.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func as sa_func
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta

from ..database import get_db
from ..models import User
from ..models.finance import Expense, Invoice, FinancialAuditLog
from ..models.payroll import Payslip
from ..schemas.finance import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseDecision,
    InvoiceCreate, InvoiceUpdate, InvoicePayment, InvoiceResponse,
    AuditLogResponse, FinancialSummary, CategoryBreakdown, CashFlowPoint,
)
from ..auth import require_role

router = APIRouter(prefix="/api/finance", tags=["finance"])

# Only these two roles touch company money.
finance_user = require_role(["admin", "accountant"])

EXPENSE_CATEGORIES = [
    "cloud_infrastructure", "software_licenses", "office_rent", "utilities",
    "hardware", "client_entertainment", "travel", "marketing",
    "professional_services", "internet_telecom", "training", "miscellaneous",
]

TIMEFRAMES = ("daily", "monthly", "quarterly", "annual")

# Expenses in these states are money already committed but not yet out the door.
PAYABLE_STATUSES = ("pending", "approved")
# Invoices in these states still owe us money.
RECEIVABLE_STATUSES = ("sent", "partially_paid", "draft")


# ── helpers ─────────────────────────────────────────────────────────────────

def _resolve_period(
    timeframe: str,
    start_date: Optional[date],
    end_date: Optional[date],
    today: Optional[date] = None,
):
    """Inclusive [start, end] for a named timeframe, unless explicit dates win."""
    if start_date and end_date:
        if start_date > end_date:
            raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
        return start_date, end_date

    today = today or date.today()
    if timeframe == "daily":
        return today, today
    if timeframe == "quarterly":
        quarter_start_month = 3 * ((today.month - 1) // 3) + 1
        start = date(today.year, quarter_start_month, 1)
        end = _month_end(date(today.year, quarter_start_month + 2, 1))
        return start, end
    if timeframe == "annual":
        return date(today.year, 1, 1), date(today.year, 12, 31)
    # monthly (default)
    return date(today.year, today.month, 1), _month_end(today)


def _month_end(any_day: date) -> date:
    if any_day.month == 12:
        return date(any_day.year, 12, 31)
    return date(any_day.year, any_day.month + 1, 1) - timedelta(days=1)


def _shift_months(any_day: date, months: int) -> date:
    """First day of the month `months` away from `any_day`'s month."""
    total = (any_day.year * 12 + any_day.month - 1) + months
    return date(total // 12, total % 12 + 1, 1)


def _next_sequence(db: Session, model, column, prefix: str, year: int) -> str:
    """`PREFIX-YYYY-0001`, counting only rows issued in the same year."""
    like = f"{prefix}-{year}-%"
    count = db.query(model).filter(column.like(like)).count()
    # Guard against gaps from deletes producing a duplicate.
    while True:
        count += 1
        candidate = f"{prefix}-{year}-{count:04d}"
        if not db.query(model).filter(column == candidate).first():
            return candidate


def _user_names(db: Session, ids) -> Dict[int, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {u.id: u.full_name for u in db.query(User).filter(User.id.in_(ids)).all()}


def _expense_payload(expense: Expense, names: Dict[int, str]) -> dict:
    data = {c.name: getattr(expense, c.name) for c in Expense.__table__.columns}
    data["created_by_name"] = names.get(expense.created_by)
    data["approved_by_name"] = names.get(expense.approved_by)
    return data


def _invoice_payload(invoice: Invoice, today: Optional[date] = None) -> dict:
    today = today or date.today()
    data = {c.name: getattr(invoice, c.name) for c in Invoice.__table__.columns}
    outstanding = round((invoice.amount or 0) + (invoice.tax_amount or 0) - (invoice.amount_received or 0), 2)
    data["outstanding"] = max(outstanding, 0.0)
    data["is_overdue"] = bool(
        invoice.status in RECEIVABLE_STATUSES
        and invoice.due_date
        and invoice.due_date < today
        and outstanding > 0
    )
    return data


def _log(
    db: Session,
    *,
    entity_type: str,
    action: str,
    user: User,
    entity_id: Optional[int] = None,
    entity_ref: Optional[str] = None,
    direction: str = "neutral",
    amount: Optional[float] = None,
    description: Optional[str] = None,
) -> None:
    """Append one audit row. Caller owns the commit so the log shares its txn."""
    db.add(FinancialAuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_ref=entity_ref,
        action=action,
        direction=direction,
        amount=amount,
        description=description,
        performed_by=user.id,
    ))


def _expense_total(expense: Expense) -> float:
    return round((expense.amount or 0) + (expense.tax_amount or 0), 2)


# ── Expenses ────────────────────────────────────────────────────────────────

@router.get("/expenses", response_model=List[ExpenseResponse])
def list_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, le=1000),
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    query = db.query(Expense)
    if status:
        query = query.filter(Expense.status == status)
    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            Expense.title.ilike(term),
            Expense.vendor.ilike(term),
            Expense.expense_number.ilike(term),
            Expense.description.ilike(term),
            Expense.reference_number.ilike(term),
        ))

    expenses = query.order_by(Expense.expense_date.desc(), Expense.id.desc()).offset(skip).limit(limit).all()
    names = _user_names(db, [e.created_by for e in expenses] + [e.approved_by for e in expenses])
    return [_expense_payload(e, names) for e in expenses]


@router.get("/expenses/categories")
def list_expense_categories(current_user: User = Depends(finance_user)):
    """Canonical category list so the UI never hardcodes its own copy."""
    return [{"value": c, "label": c.replace("_", " ").title()} for c in EXPENSE_CATEGORIES]


@router.post("/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    if payload.category not in EXPENSE_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Unknown category '{payload.category}'")

    expense = Expense(
        **payload.dict(),
        expense_number=_next_sequence(db, Expense, Expense.expense_number, "EXP", payload.expense_date.year),
        status="pending",
        created_by=current_user.id,
    )
    db.add(expense)
    db.flush()

    _log(
        db, entity_type="expense", action="created", user=current_user,
        entity_id=expense.id, entity_ref=expense.expense_number,
        direction="outflow", amount=_expense_total(expense),
        description=f"Expense raised: {expense.title}",
    )
    db.commit()
    db.refresh(expense)
    return _expense_payload(expense, _user_names(db, [expense.created_by]))


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.status != "pending":
        raise HTTPException(status_code=409, detail=f"Only pending expenses can be edited (current status: {expense.status})")

    updates = payload.dict(exclude_unset=True)
    if "category" in updates and updates["category"] not in EXPENSE_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Unknown category '{updates['category']}'")
    for field, value in updates.items():
        setattr(expense, field, value)

    _log(
        db, entity_type="expense", action="updated", user=current_user,
        entity_id=expense.id, entity_ref=expense.expense_number,
        direction="outflow", amount=_expense_total(expense),
        description=f"Expense updated: {expense.title}",
    )
    db.commit()
    db.refresh(expense)
    names = _user_names(db, [expense.created_by, expense.approved_by])
    return _expense_payload(expense, names)


@router.put("/expenses/{expense_id}/approve", response_model=ExpenseResponse)
def approve_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.status != "pending":
        raise HTTPException(status_code=409, detail=f"Only pending expenses can be approved (current status: {expense.status})")
    if expense.created_by == current_user.id and current_user.role != "admin":
        # Segregation of duties: maker cannot be checker.
        raise HTTPException(status_code=403, detail="Expenses must be approved by someone other than the person who raised them")

    expense.status = "approved"
    expense.approved_by = current_user.id
    expense.approved_at = datetime.utcnow()

    _log(
        db, entity_type="expense", action="approved", user=current_user,
        entity_id=expense.id, entity_ref=expense.expense_number,
        direction="outflow", amount=_expense_total(expense),
        description=f"Expense approved: {expense.title}",
    )
    db.commit()
    db.refresh(expense)
    return _expense_payload(expense, _user_names(db, [expense.created_by, expense.approved_by]))


@router.put("/expenses/{expense_id}/reject", response_model=ExpenseResponse)
def reject_expense(
    expense_id: int,
    decision: ExpenseDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.status != "pending":
        raise HTTPException(status_code=409, detail=f"Only pending expenses can be rejected (current status: {expense.status})")

    expense.status = "rejected"
    expense.approved_by = current_user.id
    expense.approved_at = datetime.utcnow()
    expense.rejection_reason = decision.reason

    _log(
        db, entity_type="expense", action="rejected", user=current_user,
        entity_id=expense.id, entity_ref=expense.expense_number,
        direction="neutral", amount=_expense_total(expense),
        description=f"Expense rejected: {expense.title}" + (f" — {decision.reason}" if decision.reason else ""),
    )
    db.commit()
    db.refresh(expense)
    return _expense_payload(expense, _user_names(db, [expense.created_by, expense.approved_by]))


@router.put("/expenses/{expense_id}/mark-paid", response_model=ExpenseResponse)
def mark_expense_paid(
    expense_id: int,
    decision: ExpenseDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.status != "approved":
        raise HTTPException(status_code=409, detail="Only approved expenses can be marked as paid")

    expense.status = "paid"
    expense.paid_at = datetime.utcnow()
    if decision.payment_method:
        expense.payment_method = decision.payment_method
    if decision.reference_number:
        expense.reference_number = decision.reference_number

    _log(
        db, entity_type="expense", action="paid", user=current_user,
        entity_id=expense.id, entity_ref=expense.expense_number,
        direction="outflow", amount=_expense_total(expense),
        description=f"Expense disbursed: {expense.title}",
    )
    db.commit()
    db.refresh(expense)
    return _expense_payload(expense, _user_names(db, [expense.created_by, expense.approved_by]))


@router.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.status in ("approved", "paid"):
        raise HTTPException(status_code=409, detail="Approved or paid expenses cannot be deleted")

    _log(
        db, entity_type="expense", action="deleted", user=current_user,
        entity_id=expense.id, entity_ref=expense.expense_number,
        direction="neutral", amount=_expense_total(expense),
        description=f"Expense deleted: {expense.title}",
    )
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted", "expense_id": expense_id}


# ── Invoices / receivables ──────────────────────────────────────────────────

@router.get("/invoices", response_model=List[InvoiceResponse])
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, le=1000),
    status: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    if start_date:
        query = query.filter(Invoice.issue_date >= start_date)
    if end_date:
        query = query.filter(Invoice.issue_date <= end_date)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            Invoice.client_name.ilike(term),
            Invoice.invoice_number.ilike(term),
            Invoice.project_name.ilike(term),
        ))

    invoices = query.order_by(Invoice.issue_date.desc(), Invoice.id.desc()).offset(skip).limit(limit).all()
    today = date.today()
    return [_invoice_payload(i, today) for i in invoices]


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    data = payload.dict()
    status_value = data.pop("status", None) or "sent"
    invoice = Invoice(
        **data,
        status=status_value,
        invoice_number=_next_sequence(db, Invoice, Invoice.invoice_number, "INV", payload.issue_date.year),
        created_by=current_user.id,
    )
    db.add(invoice)
    db.flush()

    _log(
        db, entity_type="invoice", action="created", user=current_user,
        entity_id=invoice.id, entity_ref=invoice.invoice_number,
        direction="inflow", amount=round((invoice.amount or 0) + (invoice.tax_amount or 0), 2),
        description=f"Invoice raised for {invoice.client_name}",
    )
    db.commit()
    db.refresh(invoice)
    return _invoice_payload(invoice)


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "paid":
        raise HTTPException(status_code=409, detail="Settled invoices cannot be edited")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(invoice, field, value)

    _log(
        db, entity_type="invoice", action="updated", user=current_user,
        entity_id=invoice.id, entity_ref=invoice.invoice_number,
        direction="inflow", amount=round((invoice.amount or 0) + (invoice.tax_amount or 0), 2),
        description=f"Invoice updated for {invoice.client_name}",
    )
    db.commit()
    db.refresh(invoice)
    return _invoice_payload(invoice)


@router.put("/invoices/{invoice_id}/record-payment", response_model=InvoiceResponse)
def record_invoice_payment(
    invoice_id: int,
    payment: InvoicePayment,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status in ("paid", "cancelled"):
        raise HTTPException(status_code=409, detail=f"Cannot record a payment against a {invoice.status} invoice")

    billed = round((invoice.amount or 0) + (invoice.tax_amount or 0), 2)
    received = round((invoice.amount_received or 0) + payment.amount_received, 2)
    if received > billed + 0.01:
        raise HTTPException(status_code=422, detail=f"Payment exceeds the outstanding balance of {billed - (invoice.amount_received or 0):.2f}")

    invoice.amount_received = received
    if received >= billed - 0.01:
        invoice.status = "paid"
        invoice.paid_date = payment.paid_date or date.today()
    else:
        invoice.status = "partially_paid"

    _log(
        db, entity_type="invoice", action="paid", user=current_user,
        entity_id=invoice.id, entity_ref=invoice.invoice_number,
        direction="inflow", amount=payment.amount_received,
        description=f"Payment received from {invoice.client_name}",
    )
    db.commit()
    db.refresh(invoice)
    return _invoice_payload(invoice)


@router.delete("/invoices/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if (invoice.amount_received or 0) > 0:
        raise HTTPException(status_code=409, detail="Invoices with recorded payments cannot be deleted")

    _log(
        db, entity_type="invoice", action="deleted", user=current_user,
        entity_id=invoice.id, entity_ref=invoice.invoice_number,
        direction="neutral", amount=invoice.amount,
        description=f"Invoice deleted for {invoice.client_name}",
    )
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted", "invoice_id": invoice_id}


# ── Audit trail ─────────────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    timeframe: str = Query("monthly"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    direction: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(300, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=422, detail=f"timeframe must be one of {', '.join(TIMEFRAMES)}")

    period_start, period_end = _resolve_period(timeframe, start_date, end_date)
    query = db.query(FinancialAuditLog).filter(
        FinancialAuditLog.performed_at >= datetime.combine(period_start, datetime.min.time()),
        FinancialAuditLog.performed_at < datetime.combine(period_end + timedelta(days=1), datetime.min.time()),
    )
    if entity_type:
        query = query.filter(FinancialAuditLog.entity_type == entity_type)
    if action:
        query = query.filter(FinancialAuditLog.action == action)
    if direction:
        query = query.filter(FinancialAuditLog.direction == direction)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            FinancialAuditLog.description.ilike(term),
            FinancialAuditLog.entity_ref.ilike(term),
        ))

    logs = query.order_by(FinancialAuditLog.performed_at.desc(), FinancialAuditLog.id.desc()).offset(skip).limit(limit).all()
    names = _user_names(db, [l.performed_by for l in logs])
    out = []
    for log in logs:
        data = {c.name: getattr(log, c.name) for c in FinancialAuditLog.__table__.columns}
        data["performed_by_name"] = names.get(log.performed_by)
        out.append(data)
    return out


# ── Payroll disbursement bridge ─────────────────────────────────────────────

@router.get("/payroll/transfers")
def list_salary_transfers(
    year: Optional[int] = None,
    month: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    """Payslips seen through a treasury lens: who gets paid, how much, and whether
    the transfer has cleared. Reads the payroll tables — no duplicate state."""
    today = date.today()
    year = year or today.year
    query = db.query(Payslip).filter(
        Payslip.pay_period_start >= date(year, 1, 1),
        Payslip.pay_period_start <= date(year, 12, 31),
    )
    if month:
        start = date(year, month, 1)
        query = query.filter(Payslip.pay_period_start >= start, Payslip.pay_period_start <= _month_end(start))
    if status:
        query = query.filter(Payslip.status == status)

    payslips = query.order_by(Payslip.pay_period_start.desc(), Payslip.id.desc()).all()
    names = _user_names(db, [p.employee_id for p in payslips])
    return [
        {
            "id": p.id,
            "payslip_number": p.payslip_number,
            "employee_id": p.employee_id,
            "employee_name": names.get(p.employee_id, f"Employee #{p.employee_id}"),
            "pay_period_start": p.pay_period_start,
            "pay_period_end": p.pay_period_end,
            "pay_date": p.pay_date,
            "basic_salary": p.basic_salary,
            "gross_salary": p.gross_salary,
            "total_earnings": p.total_earnings,
            "total_deductions": p.total_deductions,
            "net_salary": p.net_salary,
            "status": p.status,
            "transfer_status": "transferred" if p.status == "paid" else ("scheduled" if p.status == "approved" else "pending"),
            "approved_at": p.approved_at,
        }
        for p in payslips
    ]


# ── Dashboard summary ───────────────────────────────────────────────────────

@router.get("/summary", response_model=FinancialSummary)
def financial_summary(
    timeframe: str = Query("monthly"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(finance_user),
):
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=422, detail=f"timeframe must be one of {', '.join(TIMEFRAMES)}")

    today = date.today()
    period_start, period_end = _resolve_period(timeframe, start_date, end_date, today)

    # ── Income: cash actually collected in the window
    paid_invoices = db.query(Invoice).filter(
        Invoice.paid_date.isnot(None),
        Invoice.paid_date >= period_start,
        Invoice.paid_date <= period_end,
    ).all()
    total_income = round(sum(i.amount_received or 0 for i in paid_invoices), 2)

    # ── Operating expenses settled in the window
    period_expenses = db.query(Expense).filter(
        Expense.status == "paid",
        Expense.expense_date >= period_start,
        Expense.expense_date <= period_end,
    ).all()
    total_expenses = round(sum(_expense_total(e) for e in period_expenses), 2)

    # ── Payroll cost for the same window
    payroll_cost = round(
        db.query(sa_func.coalesce(sa_func.sum(Payslip.net_salary), 0.0))
        .filter(
            Payslip.status == "paid",
            Payslip.pay_period_start >= period_start,
            Payslip.pay_period_start <= period_end,
        )
        .scalar() or 0.0,
        2,
    )

    total_outflow = round(total_expenses + payroll_cost, 2)
    net_cash_flow = round(total_income - total_outflow, 2)
    profit_margin = round((net_cash_flow / total_income * 100), 2) if total_income else 0.0

    # ── Payables: approved/pending, not yet disbursed (period-independent)
    open_expenses = db.query(Expense).filter(Expense.status.in_(PAYABLE_STATUSES)).all()
    pending_payables = round(sum(_expense_total(e) for e in open_expenses), 2)
    pending_expense_approvals = sum(1 for e in open_expenses if e.status == "pending")

    unpaid_payslips = db.query(Payslip).filter(Payslip.status.in_(("generated", "approved"))).count()

    # ── Receivables: billed but not collected
    open_invoices = db.query(Invoice).filter(Invoice.status.in_(RECEIVABLE_STATUSES)).all()
    outstanding = [
        (i, round((i.amount or 0) + (i.tax_amount or 0) - (i.amount_received or 0), 2))
        for i in open_invoices
    ]
    outstanding = [(i, amt) for i, amt in outstanding if amt > 0]
    pending_receivables = round(sum(amt for _, amt in outstanding), 2)
    overdue = [(i, amt) for i, amt in outstanding if i.due_date and i.due_date < today]
    overdue_receivables = round(sum(amt for _, amt in overdue), 2)

    # ── Burn rate: mean monthly outflow across the trailing 3 full months + current
    burn_window_start = _shift_months(today, -2)
    burn_expenses = db.query(sa_func.coalesce(sa_func.sum(Expense.amount + sa_func.coalesce(Expense.tax_amount, 0.0)), 0.0)).filter(
        Expense.status == "paid",
        Expense.expense_date >= burn_window_start,
        Expense.expense_date <= today,
    ).scalar() or 0.0
    burn_payroll = db.query(sa_func.coalesce(sa_func.sum(Payslip.net_salary), 0.0)).filter(
        Payslip.status == "paid",
        Payslip.pay_period_start >= burn_window_start,
        Payslip.pay_period_start <= today,
    ).scalar() or 0.0
    monthly_burn_rate = round((burn_expenses + burn_payroll) / 3, 2)

    # Runway assumes collected-but-unspent cash is what's left in the bank.
    lifetime_collected = db.query(sa_func.coalesce(sa_func.sum(Invoice.amount_received), 0.0)).scalar() or 0.0
    lifetime_expenses = (
        db.query(sa_func.coalesce(sa_func.sum(Expense.amount + sa_func.coalesce(Expense.tax_amount, 0.0)), 0.0))
        .filter(Expense.status == "paid")
        .scalar() or 0.0
    )
    lifetime_payroll = (
        db.query(sa_func.coalesce(sa_func.sum(Payslip.net_salary), 0.0))
        .filter(Payslip.status == "paid")
        .scalar() or 0.0
    )
    cash_on_hand = round(lifetime_collected - lifetime_expenses - lifetime_payroll, 2)
    runway_months = round(cash_on_hand / monthly_burn_rate, 1) if monthly_burn_rate > 0 and cash_on_hand > 0 else None

    # ── Expense mix for the window
    by_category: Dict[str, Dict[str, float]] = {}
    for expense in period_expenses:
        bucket = by_category.setdefault(expense.category, {"amount": 0.0, "count": 0})
        bucket["amount"] += _expense_total(expense)
        bucket["count"] += 1
    expense_breakdown = [
        CategoryBreakdown(
            category=category,
            amount=round(bucket["amount"], 2),
            count=int(bucket["count"]),
            percentage=round(bucket["amount"] / total_expenses * 100, 2) if total_expenses else 0.0,
        )
        for category, bucket in sorted(by_category.items(), key=lambda kv: kv[1]["amount"], reverse=True)
    ]

    # ── Trailing 6-month trend, always monthly regardless of the selected timeframe
    cash_flow_trend: List[CashFlowPoint] = []
    for offset in range(-5, 1):
        month_start = _shift_months(today, offset)
        month_end = _month_end(month_start)
        income = db.query(sa_func.coalesce(sa_func.sum(Invoice.amount_received), 0.0)).filter(
            Invoice.paid_date.isnot(None), Invoice.paid_date >= month_start, Invoice.paid_date <= month_end,
        ).scalar() or 0.0
        spend = db.query(sa_func.coalesce(sa_func.sum(Expense.amount + sa_func.coalesce(Expense.tax_amount, 0.0)), 0.0)).filter(
            Expense.status == "paid", Expense.expense_date >= month_start, Expense.expense_date <= month_end,
        ).scalar() or 0.0
        pay = db.query(sa_func.coalesce(sa_func.sum(Payslip.net_salary), 0.0)).filter(
            Payslip.status == "paid", Payslip.pay_period_start >= month_start, Payslip.pay_period_start <= month_end,
        ).scalar() or 0.0
        cash_flow_trend.append(CashFlowPoint(
            period=month_start.strftime("%b %Y"),
            income=round(income, 2),
            expenses=round(spend, 2),
            payroll=round(pay, 2),
            net=round(income - spend - pay, 2),
        ))

    return FinancialSummary(
        timeframe=timeframe,
        period_start=period_start,
        period_end=period_end,
        total_income=total_income,
        total_expenses=total_expenses,
        payroll_cost=payroll_cost,
        total_outflow=total_outflow,
        net_cash_flow=net_cash_flow,
        profit_loss=net_cash_flow,
        profit_margin=profit_margin,
        pending_payables=pending_payables,
        pending_payables_count=len(open_expenses),
        pending_receivables=pending_receivables,
        pending_receivables_count=len(outstanding),
        overdue_receivables=overdue_receivables,
        overdue_receivables_count=len(overdue),
        monthly_burn_rate=monthly_burn_rate,
        runway_months=runway_months,
        pending_expense_approvals=pending_expense_approvals,
        unpaid_payslips=unpaid_payslips,
        expense_breakdown=expense_breakdown,
        cash_flow_trend=cash_flow_trend,
    )
