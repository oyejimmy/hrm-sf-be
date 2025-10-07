from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from ..database import get_db
from ..models.payroll import Payslip, SalaryStructure
from ..models.user import User
from ..auth import get_current_user

router = APIRouter(prefix="/api/payroll", tags=["payroll"])

@router.get("/my-payslips/")
def get_my_payslips(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        query = db.query(Payslip).filter(Payslip.employee_id == current_user.id)
        if year:
            query = query.filter(Payslip.pay_period_start >= date(year, 1, 1))
            query = query.filter(Payslip.pay_period_start <= date(year, 12, 31))
        
        payslips = query.order_by(Payslip.pay_period_start.desc()).all()
        
        # Convert to dict format
        result = []
        for p in payslips:
            result.append({
                "id": p.id,
                "employee_id": p.employee_id,
                "pay_period_start": p.pay_period_start.isoformat(),
                "pay_period_end": p.pay_period_end.isoformat(),
                "pay_date": p.pay_date.isoformat(),
                "basic_salary": p.basic_salary,
                "gross_salary": p.gross_salary,
                "net_salary": p.net_salary,
                "total_earnings": p.total_earnings,
                "total_deductions": p.total_deductions,
                "status": p.status,
                "payslip_number": p.payslip_number,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payslips: {str(e)}")

@router.get("/payslips/{payslip_id}/details")
def get_payslip_details(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        
        if current_user.role == "employee" and payslip.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        return {
            "id": payslip.id,
            "employee_id": payslip.employee_id,
            "pay_period_start": payslip.pay_period_start.isoformat(),
            "pay_period_end": payslip.pay_period_end.isoformat(),
            "pay_date": payslip.pay_date.isoformat(),
            "basic_salary": payslip.basic_salary,
            "gross_salary": payslip.gross_salary,
            "net_salary": payslip.net_salary,
            "total_earnings": payslip.total_earnings,
            "total_deductions": payslip.total_deductions,
            "status": payslip.status,
            "payslip_number": payslip.payslip_number,
            "earnings": [],  # Will be populated later
            "deductions": []  # Will be populated later
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payslip: {str(e)}")

@router.get("/admin/payslips/")
def get_admin_payslips(
    skip: int = 0,
    limit: int = 100,
    year: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        query = db.query(Payslip)
        
        if year:
            query = query.filter(Payslip.pay_period_start >= date(year, 1, 1))
            query = query.filter(Payslip.pay_period_start <= date(year, 12, 31))
        if status:
            query = query.filter(Payslip.status == status)
        
        payslips = query.order_by(Payslip.pay_period_start.desc()).offset(skip).limit(limit).all()
        
        result = []
        for p in payslips:
            result.append({
                "id": p.id,
                "employee_id": p.employee_id,
                "pay_period_start": p.pay_period_start.isoformat(),
                "pay_period_end": p.pay_period_end.isoformat(),
                "pay_date": p.pay_date.isoformat(),
                "basic_salary": p.basic_salary,
                "gross_salary": p.gross_salary,
                "net_salary": p.net_salary,
                "total_earnings": p.total_earnings,
                "total_deductions": p.total_deductions,
                "status": p.status,
                "payslip_number": p.payslip_number,
                "employee_name": f"Employee {p.employee_id}"  # Will be improved later
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payslips: {str(e)}")

@router.put("/payslips/{payslip_id}/approve")
def approve_payslip(
    payslip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
        if not payslip:
            raise HTTPException(status_code=404, detail="Payslip not found")
        
        payslip.status = "approved"
        payslip.approved_by = current_user.id
        payslip.approved_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Payslip approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error approving payslip: {str(e)}")

@router.get("/payslips/{payslip_id}/pdf")
def download_payslip_pdf(payslip_id: int):
    # Simplified PDF endpoint
    return {
        "message": "PDF download will be implemented",
        "payslip_id": payslip_id
    }