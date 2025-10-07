from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class PayslipBase(BaseModel):
    pay_period_start: date
    pay_period_end: date
    pay_date: date
    basic_salary: float
    gross_salary: float
    net_salary: float
    total_earnings: float
    total_deductions: float

class PayslipCreate(PayslipBase):
    employee_id: int
    payslip_number: str

class PayslipUpdate(BaseModel):
    status: Optional[str] = None

class Payslip(PayslipBase):
    id: int
    employee_id: int
    payslip_number: str
    status: str
    generated_by: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PayslipEarningBase(BaseModel):
    earning_type: str
    amount: float
    description: Optional[str] = None
    is_taxable: bool = True

class PayslipEarningCreate(PayslipEarningBase):
    payslip_id: int

class PayslipEarning(PayslipEarningBase):
    id: int
    payslip_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PayslipDeductionBase(BaseModel):
    deduction_type: str
    amount: float
    description: Optional[str] = None

class PayslipDeductionCreate(PayslipDeductionBase):
    payslip_id: int

class PayslipDeduction(PayslipDeductionBase):
    id: int
    payslip_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SalaryStructureBase(BaseModel):
    effective_from: date
    basic_salary: float
    hra_percentage: Optional[float] = None
    transport_allowance: Optional[float] = None
    medical_allowance: Optional[float] = None
    special_allowance: Optional[float] = None
    pf_percentage: Optional[float] = None
    esi_percentage: Optional[float] = None
    professional_tax: Optional[float] = None

class SalaryStructureCreate(SalaryStructureBase):
    employee_id: int
    effective_to: Optional[date] = None

class SalaryStructureUpdate(BaseModel):
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None

class SalaryStructure(SalaryStructureBase):
    id: int
    employee_id: int
    effective_to: Optional[date] = None
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class BonusBase(BaseModel):
    bonus_type: str
    amount: float
    bonus_date: date
    reason: Optional[str] = None

class BonusCreate(BonusBase):
    employee_id: int

class BonusUpdate(BaseModel):
    status: Optional[str] = None

class Bonus(BonusBase):
    id: int
    employee_id: int
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    paid_in_payslip_id: Optional[int] = None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class PayslipResponse(Payslip):
    earnings: Optional[List[dict]] = None
    deductions: Optional[List[dict]] = None
    employee_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class SalaryStructureResponse(SalaryStructure):
    employee_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class BonusResponse(Bonus):
    employee_name: Optional[str] = None
    
    class Config:
        from_attributes = True
