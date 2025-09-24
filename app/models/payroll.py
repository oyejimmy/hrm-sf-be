from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Payslip(Base):
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=False)
    basic_salary = Column(Float, nullable=False)
    gross_salary = Column(Float, nullable=False)
    net_salary = Column(Float, nullable=False)
    total_earnings = Column(Float, nullable=False)
    total_deductions = Column(Float, nullable=False)
    status = Column(String, default="generated")  # generated, approved, paid
    payslip_number = Column(String, unique=True, nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    generator = relationship("User", foreign_keys=[generated_by])
    approver = relationship("User", foreign_keys=[approved_by])
    earnings = relationship("PayslipEarning", back_populates="payslip")
    deductions = relationship("PayslipDeduction", back_populates="payslip")

class PayslipEarning(Base):
    __tablename__ = "payslip_earnings"
    
    id = Column(Integer, primary_key=True, index=True)
    payslip_id = Column(Integer, ForeignKey("payslips.id"), nullable=False)
    earning_type = Column(String, nullable=False)  # basic, hra, transport, bonus, overtime, etc.
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    is_taxable = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    payslip = relationship("Payslip", back_populates="earnings")

class PayslipDeduction(Base):
    __tablename__ = "payslip_deductions"
    
    id = Column(Integer, primary_key=True, index=True)
    payslip_id = Column(Integer, ForeignKey("payslips.id"), nullable=False)
    deduction_type = Column(String, nullable=False)  # tax, pf, esi, loan, advance, etc.
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    payslip = relationship("Payslip", back_populates="deductions")

class SalaryStructure(Base):
    __tablename__ = "salary_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    basic_salary = Column(Float, nullable=False)
    hra_percentage = Column(Float, nullable=True)
    transport_allowance = Column(Float, nullable=True)
    medical_allowance = Column(Float, nullable=True)
    special_allowance = Column(Float, nullable=True)
    pf_percentage = Column(Float, nullable=True)
    esi_percentage = Column(Float, nullable=True)
    professional_tax = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    creator = relationship("User", foreign_keys=[created_by])

class Bonus(Base):
    __tablename__ = "bonuses"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bonus_type = Column(String, nullable=False)  # performance, festival, annual, etc.
    amount = Column(Float, nullable=False)
    bonus_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, paid
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    paid_in_payslip_id = Column(Integer, ForeignKey("payslips.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])
    payslip = relationship("Payslip")