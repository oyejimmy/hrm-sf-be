"""Payroll API.

Design notes (accounting controls):
- Payslip generation is a POST (state-changing) and is idempotent per employee+period.
- Every payslip writes itemized earning/deduction lines (audit trail for the totals).
- Maker/checker: the user who generated a payslip cannot approve it (SoD).
- Status machine: generated -> approved -> paid. Transitions are enforced.
- Compensation visibility: admin/HR see all; employees see their own only.
  Team leads intentionally have NO access to team pay data.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from ..database import get_db
from ..models import Payslip, PayslipEarning, PayslipDeduction, SalaryStructure, Bonus, User, Employee
from ..models.leave import Leave
from ..schemas.payroll import (
    PayslipResponse, PayslipCreate, SalaryStructureResponse, SalaryStructureCreate,
    BonusResponse, BonusCreate,
)
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/payroll", tags=["payroll"])

# ESI statutory gross-salary eligibility ceiling (monthly). Configurable per deployment.
ESI_GROSS_CEILING = 21000.0
# PF statutory wage ceiling on basic (monthly). Contributions computed on min(basic, ceiling).
PF_WAGE_CEILING = 15000.0


def _period_bounds(year: int, month: Optional[int] = None):
    """Inclusive start, exclusive end for a year or month."""
    if month:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    else:
        start, end = date(year, 1, 1), date(year + 1, 1, 1)
    return start, end


def _apply_period_filters(query, year: Optional[int], month: Optional[int]):
    if year:
        start, end = _period_bounds(year, month if month else None)
        query = query.filter(Payslip.pay_period_start >= start, Payslip.pay_period_start < end)
    return query


def _with_employee_names(db: Session, payslips: List[Payslip]) -> List[dict]:
    ids = {p.employee_id for p in payslips}
    users = {u.id: u for u in db.query(User).filter(User.id.in_(ids)).all()} if ids else {}
    out = []
    for p in payslips:
        d = {c.name: getattr(p, c.name) for c in Payslip.__table__.columns}
        u = users.get(p.employee_id)
        d["employee_name"] = u.full_name if u else f"Employee #{p.employee_id}"
        out.append(d)
    return out


# ── Payslips ────────────────────────────────────────────────────────────────

@router.get("/payslips/", response_model=List[PayslipResponse])
def get_payslips(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Payslip)

    if current_user.role in ("admin", "hr"):
        if employee_id:
            query = query.filter(Payslip.employee_id == employee_id)
    else:
        # Employees and team leads: own payslips only. Pay data is confidential.
        query = query.filter(Payslip.employee_id == current_user.id)

    query = _apply_period_filters(query, year, month)
    payslips = query.order_by(Payslip.pay_period_start.desc()).offset(skip).limit(limit).all()
    return _with_employee_names(db, payslips)


@router.get("/my-payslips/")
def get_my_payslips(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Payslip).filter(Payslip.employee_id == current_user.id)
    query = _apply_period_filters(query, year, None)
    payslips = query.order_by(Payslip.pay_period_start.desc()).all()
    return _with_employee_names(db, payslips)


@router.get("/admin/payslips/")
def get_all_payslips_admin(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    query = db.query(Payslip)
    if employee_id:
        query = query.filter(Payslip.employee_id == employee_id)
    if status:
        query = query.filter(Payslip.status == status)
    query = _apply_period_filters(query, year, month)
    payslips = query.order_by(Payslip.pay_period_start.desc()).offset(skip).limit(limit).all()
    return _with_employee_names(db, payslips)


@router.get("/payslips/{payslip_id}/details")
def get_payslip_details(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if current_user.role not in ("admin", "hr") and payslip.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own payslips")

    earnings = db.query(PayslipEarning).filter(PayslipEarning.payslip_id == payslip_id).all()
    deductions = db.query(PayslipDeduction).filter(PayslipDeduction.payslip_id == payslip_id).all()

    result = _with_employee_names(db, [payslip])[0]
    result["earnings"] = [
        {"type": e.earning_type, "amount": e.amount, "description": e.description} for e in earnings
    ]
    result["deductions"] = [
        {"type": d.deduction_type, "amount": d.amount, "description": d.description} for d in deductions
    ]
    return result


@router.get("/payslips/{payslip_id}", response_model=PayslipResponse)
def get_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if current_user.role not in ("admin", "hr") and payslip.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own payslips")
    return payslip


@router.post("/payslips/", response_model=PayslipResponse)
def create_payslip(
    payslip: PayslipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    existing = db.query(Payslip).filter(
        Payslip.employee_id == payslip.employee_id,
        Payslip.pay_period_start == payslip.pay_period_start,
        Payslip.pay_period_end == payslip.pay_period_end,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="A payslip already exists for this employee and period")

    db_payslip = Payslip(**payslip.dict(), generated_by=current_user.id)
    db.add(db_payslip)
    db.commit()
    db.refresh(db_payslip)
    return db_payslip


@router.put("/payslips/{payslip_id}/approve")
def approve_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if payslip.status != "generated":
        raise HTTPException(status_code=409, detail=f"Only generated payslips can be approved (current status: {payslip.status})")
    if payslip.generated_by == current_user.id:
        # Segregation of duties: maker cannot be checker.
        raise HTTPException(status_code=403, detail="Payslips must be approved by someone other than the person who generated them")

    payslip.status = "approved"
    payslip.approved_by = current_user.id
    payslip.approved_at = datetime.utcnow()
    db.commit()
    return {"message": "Payslip approved", "payslip_id": payslip.id, "status": payslip.status}


@router.put("/payslips/{payslip_id}/mark-paid")
def mark_payslip_paid(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if payslip.status != "approved":
        raise HTTPException(status_code=409, detail="Only approved payslips can be marked as paid")

    payslip.status = "paid"
    db.commit()
    return {"message": "Payslip marked as paid", "payslip_id": payslip.id, "status": payslip.status}


@router.delete("/payslips/{payslip_id}")
def delete_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if payslip.status in ("approved", "paid"):
        raise HTTPException(status_code=409, detail="Approved or paid payslips cannot be deleted")

    db.query(PayslipEarning).filter(PayslipEarning.payslip_id == payslip_id).delete()
    db.query(PayslipDeduction).filter(PayslipDeduction.payslip_id == payslip_id).delete()
    db.delete(payslip)
    db.commit()
    return {"message": "Payslip deleted"}


# ── Payslip generation ─────────────────────────────────────────────────────

@router.post("/generate-payslips")
def generate_monthly_payslips(
    pay_period: str = Body(..., embed=True, description="Format: YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    try:
        year, month = (int(x) for x in pay_period.split("-"))
        period_start, next_month = _period_bounds(year, month)
        period_end = next_month - timedelta(days=1)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid pay_period format. Use YYYY-MM")

    days_in_month = (next_month - period_start).days
    # Active = the linked user account is active (Employee has no status column)
    employees = (
        db.query(Employee)
        .join(User, User.id == Employee.user_id)
        .filter(User.status == "active")
        .all()
    )
    generated, skipped_no_structure, skipped_existing = 0, [], 0

    for employee in employees:
        uid = employee.user_id

        if db.query(Payslip).filter(
            Payslip.employee_id == uid,
            Payslip.pay_period_start == period_start,
        ).first():
            skipped_existing += 1
            continue

        structure = db.query(SalaryStructure).filter(
            SalaryStructure.employee_id == uid,
            SalaryStructure.is_active == True,  # noqa: E712
        ).first()
        if not structure:
            skipped_no_structure.append(uid)
            continue

        # Earnings
        basic = structure.basic_salary or 0.0
        hra = round(basic * (structure.hra_percentage or 0) / 100, 2)
        transport = structure.transport_allowance or 0.0
        medical = structure.medical_allowance or 0.0
        special = structure.special_allowance or 0.0

        # Approved bonuses dated in this period and not yet paid out
        bonuses = db.query(Bonus).filter(
            Bonus.employee_id == uid,
            Bonus.status == "approved",
            Bonus.paid_in_payslip_id.is_(None),
            Bonus.bonus_date >= period_start,
            Bonus.bonus_date < next_month,
        ).all()
        bonus_total = round(sum(b.amount for b in bonuses), 2)

        gross_before_lop = basic + hra + transport + medical + special

        # Loss of pay: approved unpaid leave days overlapping the period,
        # prorated against the fixed monthly components.
        unpaid_days = 0.0
        unpaid_leaves = db.query(Leave).filter(
            Leave.employee_id == uid,
            Leave.status == "approved",
            Leave.leave_type == "unpaid",
            Leave.start_date <= period_end,
            Leave.end_date >= period_start,
        ).all()
        for lv in unpaid_leaves:
            overlap_start = max(lv.start_date, period_start)
            overlap_end = min(lv.end_date, period_end)
            overlap = (overlap_end - overlap_start).days + 1
            if lv.days_requested and (lv.end_date - lv.start_date).days + 1 > 0:
                # Scale requested days by the fraction of the leave inside this period
                total_span = (lv.end_date - lv.start_date).days + 1
                unpaid_days += lv.days_requested * (overlap / total_span)
            else:
                unpaid_days += overlap
        lop_amount = round(gross_before_lop * min(unpaid_days, days_in_month) / days_in_month, 2)

        total_earnings = round(gross_before_lop + bonus_total - lop_amount, 2)

        # Statutory deductions
        pf_base = min(basic, PF_WAGE_CEILING)
        pf = round(pf_base * (structure.pf_percentage or 0) / 100, 2)
        # ESI applies on gross, only if gross is within the eligibility ceiling
        esi = 0.0
        if total_earnings <= ESI_GROSS_CEILING:
            esi = round(total_earnings * (structure.esi_percentage or 0) / 100, 2)
        professional_tax = structure.professional_tax or 0.0
        total_deductions = round(pf + esi + professional_tax, 2)

        net_salary = round(total_earnings - total_deductions, 2)

        payslip = Payslip(
            employee_id=uid,
            pay_period_start=period_start,
            pay_period_end=period_end,
            pay_date=date.today(),
            basic_salary=basic,
            gross_salary=total_earnings,
            net_salary=net_salary,
            total_earnings=total_earnings,
            total_deductions=total_deductions,
            payslip_number=f"PAY-{uid}-{pay_period}",
            generated_by=current_user.id,
            status="generated",
        )
        db.add(payslip)
        db.flush()  # get payslip.id for line items

        # Itemized lines — the audit trail behind the totals
        earn_lines = [
            ("basic", basic, "Basic salary"),
            ("hra", hra, f"House rent allowance ({structure.hra_percentage or 0}% of basic)"),
            ("transport", transport, "Transport allowance"),
            ("medical", medical, "Medical allowance"),
            ("special", special, "Special allowance"),
        ]
        for etype, amount, desc in earn_lines:
            if amount:
                db.add(PayslipEarning(payslip_id=payslip.id, earning_type=etype, amount=amount, description=desc))
        for b in bonuses:
            db.add(PayslipEarning(
                payslip_id=payslip.id, earning_type="bonus", amount=b.amount,
                description=f"{b.bonus_type.title()} bonus",
            ))
            b.status = "paid"
            b.paid_in_payslip_id = payslip.id

        if lop_amount:
            db.add(PayslipDeduction(
                payslip_id=payslip.id, deduction_type="loss_of_pay", amount=lop_amount,
                description=f"Unpaid leave: {round(unpaid_days, 1)} day(s)",
            ))
        ded_lines = [
            ("pf", pf, f"Provident fund ({structure.pf_percentage or 0}% of capped basic)"),
            ("esi", esi, f"ESI ({structure.esi_percentage or 0}% of gross)"),
            ("professional_tax", professional_tax, "Professional tax"),
        ]
        for dtype, amount, desc in ded_lines:
            if amount:
                db.add(PayslipDeduction(payslip_id=payslip.id, deduction_type=dtype, amount=amount, description=desc))

        generated += 1

    db.commit()
    return {
        "message": f"Generated {generated} payslip(s) for {pay_period}",
        "generated": generated,
        "skipped_existing": skipped_existing,
        "skipped_missing_salary_structure": skipped_no_structure,
    }


# ── Salary structures ───────────────────────────────────────────────────────

@router.get("/salary-structures/", response_model=List[SalaryStructureResponse])
def get_salary_structures(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    query = db.query(SalaryStructure)
    if employee_id:
        query = query.filter(SalaryStructure.employee_id == employee_id)
    return query.offset(skip).limit(limit).all()


@router.get("/my-salary-structure/", response_model=SalaryStructureResponse)
def get_my_salary_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    structure = db.query(SalaryStructure).filter(
        SalaryStructure.employee_id == current_user.id,
        SalaryStructure.is_active == True,  # noqa: E712
    ).first()
    if not structure:
        raise HTTPException(status_code=404, detail="No active salary structure found")
    return structure


@router.post("/salary-structures/", response_model=SalaryStructureResponse)
def create_salary_structure(
    salary_structure: SalaryStructureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    existing = db.query(SalaryStructure).filter(
        SalaryStructure.employee_id == salary_structure.employee_id,
        SalaryStructure.is_active == True,  # noqa: E712
    ).first()
    if existing:
        existing.is_active = False
        existing.effective_to = salary_structure.effective_from

    db_structure = SalaryStructure(**salary_structure.dict(), created_by=current_user.id)
    db.add(db_structure)
    db.commit()
    db.refresh(db_structure)
    return db_structure


# ── Bonuses ─────────────────────────────────────────────────────────────────

@router.get("/bonuses/", response_model=List[BonusResponse])
def get_bonuses(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    bonus_type: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Bonus)
    if current_user.role in ("admin", "hr"):
        if employee_id:
            query = query.filter(Bonus.employee_id == employee_id)
    else:
        query = query.filter(Bonus.employee_id == current_user.id)

    if bonus_type:
        query = query.filter(Bonus.bonus_type == bonus_type)
    if year:
        start, end = _period_bounds(year)
        query = query.filter(Bonus.bonus_date >= start, Bonus.bonus_date < end)

    return query.offset(skip).limit(limit).all()


@router.get("/my-bonuses/", response_model=List[BonusResponse])
def get_my_bonuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Bonus).filter(Bonus.employee_id == current_user.id).all()


@router.post("/bonuses/", response_model=BonusResponse)
def create_bonus(
    bonus: BonusCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    db_bonus = Bonus(**bonus.dict(), created_by=current_user.id)
    db.add(db_bonus)
    db.commit()
    db.refresh(db_bonus)
    return db_bonus


@router.put("/bonuses/{bonus_id}/approve")
def approve_bonus(
    bonus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    bonus = db.query(Bonus).filter(Bonus.id == bonus_id).first()
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus not found")
    if bonus.status != "pending":
        raise HTTPException(status_code=409, detail=f"Only pending bonuses can be approved (current status: {bonus.status})")
    if bonus.created_by == current_user.id:
        raise HTTPException(status_code=403, detail="Bonuses must be approved by someone other than the person who created them")

    bonus.status = "approved"
    bonus.approved_by = current_user.id
    bonus.approved_at = datetime.utcnow()
    db.commit()
    return {"message": "Bonus approved", "bonus_id": bonus.id, "status": bonus.status}


# ── Statistics ──────────────────────────────────────────────────────────────

@router.get("/stats/overview")
def get_payroll_stats(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "hr"])),
):
    query = _apply_period_filters(db.query(Payslip), year, month)
    payslips = query.all()
    return {
        "total_payslips": len(payslips),
        "total_gross_pay": round(sum(p.gross_salary or 0 for p in payslips), 2),
        "total_net_pay": round(sum(p.net_salary or 0 for p in payslips), 2),
        "total_deductions": round(sum(p.total_deductions or 0 for p in payslips), 2),
    }


# ── PDF (placeholder, authenticated) ────────────────────────────────────────

@router.get("/payslips/{payslip_id}/pdf")
def download_payslip_pdf(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    if current_user.role not in ("admin", "hr") and payslip.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only download your own payslips")

    return {
        "message": "PDF generation not implemented yet",
        "payslip_id": payslip_id,
        "download_url": f"/api/payroll/payslips/{payslip_id}/details",
    }
