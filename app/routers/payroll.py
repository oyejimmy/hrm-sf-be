from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
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
    pay_period: Optional[str] = None,
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
    
    if pay_period:
        query = query.filter(Payslip.pay_period == pay_period)
    if year:
        query = query.filter(Payslip.pay_period.like(f"{year}%"))
    if month and year:
        query = query.filter(Payslip.pay_period.like(f"{year}-{month:02d}%"))
    
    return query.offset(skip).limit(limit).all()

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
        query = query.filter(Payslip.pay_period.like(f"{year}%"))
    return query.order_by(Payslip.pay_period.desc()).all()

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
        Payslip.pay_period == payslip.pay_period
    ).first()
    
    if existing_payslip:
        raise HTTPException(status_code=400, detail="Payslip already exists for this period")
    
    db_payslip = Payslip(**payslip.dict(), generated_by=current_user.id)
    db.add(db_payslip)
    db.commit()
    db.refresh(db_payslip)
    return db_payslip

@router.put("/payslips/{payslip_id}/finalize")
def finalize_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    payslip.status = "finalized"
    db.commit()
    return {"message": "Payslip finalized successfully"}

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
    
    if payslip.status == "finalized":
        raise HTTPException(status_code=400, detail="Cannot delete finalized payslip")
    
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
        query = query.filter(Bonus.award_date.like(f"{year}%"))
    
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
    
    db_bonus = Bonus(**bonus.dict(), awarded_by=current_user.id)
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
    total_gross_pay = sum([p.gross_pay for p in payslips])
    total_net_pay = sum([p.net_pay for p in payslips])
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
        existing_payslip = db.query(Payslip).filter(
            Payslip.employee_id == employee.user_id,
            Payslip.pay_period == pay_period
        ).first()
        
        if not existing_payslip:
            # Get salary structure
            salary_structure = db.query(SalaryStructure).filter(
                SalaryStructure.employee_id == employee.user_id,
                SalaryStructure.is_active == True
            ).first()
            
            if salary_structure:
                # Create payslip with basic calculation
                gross_pay = salary_structure.basic_salary + salary_structure.allowances
                total_deductions = salary_structure.deductions
                net_pay = gross_pay - total_deductions
                
                payslip = Payslip(
                    employee_id=employee.user_id,
                    pay_period=pay_period,
                    gross_pay=gross_pay,
                    total_deductions=total_deductions,
                    net_pay=net_pay,
                    generated_by=current_user.id,
                    status="draft"
                )
                db.add(payslip)
                generated_count += 1
    
    db.commit()
    return {"message": f"Generated {generated_count} payslips for {pay_period}"}