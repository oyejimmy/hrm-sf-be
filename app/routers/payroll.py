from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import datetime as dt
from ..database import get_db
from ..models import Payslip, PayslipEarning, PayslipDeduction, SalaryStructure, Bonus, User, Employee
from ..schemas.payroll import (
    PayslipResponse, PayslipCreate, SalaryStructureResponse, SalaryStructureCreate,
    BonusResponse, BonusCreate
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/payroll", tags=["payroll"])

# Payslips
@router.get("/payslips/", response_model=List[PayslipResponse])
def get_payslips(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payslip)
    
    if current_user.role == "employee":
        query = query.filter(Payslip.employee_id == current_user.id)
    elif current_user.role == "team_lead":
        # Team leads can see payslips for their team members
        team_members = db.query(Employee).filter(Employee.supervisor_id == current_user.id).all()
        team_member_ids = [member.user_id for member in team_members]
        query = query.filter(Payslip.employee_id.in_(team_member_ids))
    elif employee_id:
        query = query.filter(Payslip.employee_id == employee_id)
    
    if year:
        query = query.filter(Payslip.pay_period_start >= date(year, 1, 1))
        query = query.filter(Payslip.pay_period_start <= date(year, 12, 31))
    if month and year:
        query = query.filter(Payslip.pay_period_start >= date(year, month, 1))
        if month == 12:
            query = query.filter(Payslip.pay_period_start <= date(year + 1, 1, 1))
        else:
            query = query.filter(Payslip.pay_period_start <= date(year, month + 1, 1))
    
    return query.order_by(Payslip.pay_period_start.desc()).offset(skip).limit(limit).all()

@router.get("/payslips/{payslip_id}", response_model=PayslipResponse)
def get_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if current_user.role == "employee" and payslip.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return payslip

@router.get("/my-payslips/", response_model=List[PayslipResponse])
def get_my_payslips(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payslip).filter(Payslip.employee_id == current_user.id)
    if year:
        query = query.filter(Payslip.pay_period_start >= date(year, 1, 1))
        query = query.filter(Payslip.pay_period_start <= date(year, 12, 31))
    return query.order_by(Payslip.pay_period_start.desc()).all()

@router.post("/payslips/", response_model=PayslipResponse)
def create_payslip(
    payslip: PayslipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if payslip already exists for this employee and period
    existing_payslip = db.query(Payslip).filter(
        Payslip.employee_id == payslip.employee_id,
        Payslip.pay_period_start == payslip.pay_period_start,
        Payslip.pay_period_end == payslip.pay_period_end
    ).first()
    
    if existing_payslip:
        raise HTTPException(status_code=400, detail="Payslip already exists for this period")
    
    db_payslip = Payslip(**payslip.dict(), generated_by=current_user.id)
    db.add(db_payslip)
    db.commit()
    db.refresh(db_payslip)
    return db_payslip

@router.put("/payslips/{payslip_id}/approve")
def approve_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    payslip.status = "approved"
    payslip.approved_by = current_user.id
    payslip.approved_at = datetime.utcnow()
    db.commit()
    return {"message": "Payslip approved successfully"}

@router.delete("/payslips/{payslip_id}")
def delete_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if payslip.status in ["approved", "paid"]:
        raise HTTPException(status_code=400, detail="Cannot delete approved or paid payslip")
    
    db.delete(payslip)
    db.commit()
    return {"message": "Payslip deleted successfully"}

# Salary Structures
@router.get("/salary-structures/", response_model=List[SalaryStructureResponse])
def get_salary_structures(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(SalaryStructure)
    if employee_id:
        query = query.filter(SalaryStructure.employee_id == employee_id)
    return query.offset(skip).limit(limit).all()

@router.get("/my-salary-structure/", response_model=SalaryStructureResponse)
def get_my_salary_structure(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    salary_structure = db.query(SalaryStructure).filter(
        SalaryStructure.employee_id == current_user.id,
        SalaryStructure.is_active == True
    ).first()
    if not salary_structure:
        raise HTTPException(status_code=404, detail="No active salary structure found")
    return salary_structure

@router.post("/salary-structures/", response_model=SalaryStructureResponse)
def create_salary_structure(
    salary_structure: SalaryStructureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Deactivate existing salary structure
    existing_structure = db.query(SalaryStructure).filter(
        SalaryStructure.employee_id == salary_structure.employee_id,
        SalaryStructure.is_active == True
    ).first()
    
    if existing_structure:
        existing_structure.is_active = False
    
    db_structure = SalaryStructure(**salary_structure.dict(), created_by=current_user.id)
    db.add(db_structure)
    db.commit()
    db.refresh(db_structure)
    return db_structure

# Bonuses
@router.get("/bonuses/", response_model=List[BonusResponse])
def get_bonuses(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    bonus_type: Optional[str] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Bonus)
    
    if current_user.role == "employee":
        query = query.filter(Bonus.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(Bonus.employee_id == employee_id)
    
    if bonus_type:
        query = query.filter(Bonus.bonus_type == bonus_type)
    if year:
        query = query.filter(Bonus.bonus_date >= date(year, 1, 1))
        query = query.filter(Bonus.bonus_date <= date(year, 12, 31))
    
    return query.offset(skip).limit(limit).all()

@router.get("/my-bonuses/", response_model=List[BonusResponse])
def get_my_bonuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Bonus).filter(Bonus.employee_id == current_user.id).all()

@router.post("/bonuses/", response_model=BonusResponse)
def create_bonus(
    bonus: BonusCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_bonus = Bonus(**bonus.dict(), created_by=current_user.id)
    db.add(db_bonus)
    db.commit()
    db.refresh(db_bonus)
    return db_bonus

@router.put("/bonuses/{bonus_id}/approve")
def approve_bonus(
    bonus_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    bonus = db.query(Bonus).filter(Bonus.id == bonus_id).first()
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus not found")
    
    bonus.status = "approved"
    bonus.approved_by = current_user.id
    bonus.approved_at = datetime.utcnow()
    db.commit()
    return {"message": "Bonus approved successfully"}

# Payroll Statistics
@router.get("/stats/overview")
def get_payroll_stats(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Payslip)
    if year:
        query = query.filter(Payslip.pay_period.like(f"{year}%"))
    if month and year:
        query = query.filter(Payslip.pay_period.like(f"{year}-{month:02d}%"))
    
    payslips = query.all()
    total_payslips = len(payslips)
    total_gross_pay = sum([p.gross_salary for p in payslips])
    total_net_pay = sum([p.net_salary for p in payslips])
    total_deductions = sum([p.total_deductions for p in payslips])
    
    return {
        "total_payslips": total_payslips,
        "total_gross_pay": total_gross_pay,
        "total_net_pay": total_net_pay,
        "total_deductions": total_deductions
    }

@router.get("/generate-payslips/{pay_period}")
def generate_monthly_payslips(
    pay_period: str,  # Format: YYYY-MM
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all active employees
    employees = db.query(Employee).filter(Employee.status == "active").all()
    generated_count = 0
    
    for employee in employees:
        # Check if payslip already exists
        try:
            year, month = pay_period.split('-')
            period_start = date(int(year), int(month), 1)
            if int(month) == 12:
                period_end = date(int(year) + 1, 1, 1) - dt.timedelta(days=1)
            else:
                period_end = date(int(year), int(month) + 1, 1) - dt.timedelta(days=1)
                
            existing_payslip = db.query(Payslip).filter(
                Payslip.employee_id == employee.user_id,
                Payslip.pay_period_start == period_start
            ).first()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid pay_period format. Use YYYY-MM")
        
        if not existing_payslip:
            # Get salary structure
            salary_structure = db.query(SalaryStructure).filter(
                SalaryStructure.employee_id == employee.user_id,
                SalaryStructure.is_active == True
            ).first()
            
            if salary_structure:
                # Calculate earnings
                basic_salary = salary_structure.basic_salary
                hra = basic_salary * (salary_structure.hra_percentage or 0) / 100
                transport = salary_structure.transport_allowance or 0
                medical = salary_structure.medical_allowance or 0
                special = salary_structure.special_allowance or 0
                total_earnings = basic_salary + hra + transport + medical + special
                
                # Calculate deductions
                pf = basic_salary * (salary_structure.pf_percentage or 0) / 100
                esi = basic_salary * (salary_structure.esi_percentage or 0) / 100
                professional_tax = salary_structure.professional_tax or 0
                total_deductions = pf + esi + professional_tax
                
                net_salary = total_earnings - total_deductions
                
                payslip = Payslip(
                    employee_id=employee.user_id,
                    pay_period_start=period_start,
                    pay_period_end=period_end,
                    pay_date=date.today(),
                    basic_salary=basic_salary,
                    gross_salary=total_earnings,
                    net_salary=net_salary,
                    total_earnings=total_earnings,
                    total_deductions=total_deductions,
                    payslip_number=f"PAY-{employee.user_id}-{pay_period}",
                    generated_by=current_user.id,
                    status="generated"
                )
                db.add(payslip)
                generated_count += 1
    
    db.commit()
    return {"message": f"Generated {generated_count} payslips for {pay_period}"}

# PDF Generation (simplified)
@router.get("/payslips/{payslip_id}/pdf")
def download_payslip_pdf(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if current_user.role == "employee" and payslip.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Return JSON for now (PDF generation can be added later)
    return {
        "message": "PDF generation not implemented yet",
        "payslip_id": payslip_id,
        "download_url": f"/api/payroll/payslips/{payslip_id}/details"
    }

@router.get("/payslips/{payslip_id}/details", response_model=PayslipResponse)
def get_payslip_details(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    if current_user.role == "employee" and payslip.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Load earnings and deductions
    earnings = db.query(PayslipEarning).filter(PayslipEarning.payslip_id == payslip_id).all()
    deductions = db.query(PayslipDeduction).filter(PayslipDeduction.payslip_id == payslip_id).all()
    
    payslip_dict = payslip.__dict__.copy()
    payslip_dict['earnings'] = [{"type": e.earning_type, "amount": e.amount, "description": e.description} for e in earnings]
    payslip_dict['deductions'] = [{"type": d.deduction_type, "amount": d.amount, "description": d.description} for d in deductions]
    
    return payslip_dict

@router.get("/admin/payslips/", response_model=List[PayslipResponse])
def get_all_payslips_admin(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Payslip)
    
    if employee_id:
        query = query.filter(Payslip.employee_id == employee_id)
    if status:
        query = query.filter(Payslip.status == status)
    if year:
        query = query.filter(Payslip.pay_period_start >= date(year, 1, 1))
        query = query.filter(Payslip.pay_period_start <= date(year, 12, 31))
    if month and year:
        query = query.filter(Payslip.pay_period_start >= date(year, month, 1))
        if month == 12:
            query = query.filter(Payslip.pay_period_start <= date(year + 1, 1, 1))
        else:
            query = query.filter(Payslip.pay_period_start <= date(year, month + 1, 1))
    
    return query.order_by(Payslip.pay_period_start.desc()).offset(skip).limit(limit).all()