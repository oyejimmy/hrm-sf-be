"""Finance domain models for the in-house accounting module.

Three tables back the accountant portal:
- Expense              → operational outflows (payables)
- Invoice              → client billing (receivables)
- FinancialAuditLog    → append-only trail of every money-moving event

Money columns are Float to stay consistent with the existing payroll tables
(Payslip.net_salary etc.) so cross-module aggregations don't mix numeric types.
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Expense(Base):
    """A single operational cost — hosting, licenses, rent, hardware, etc.

    Status machine: pending -> approved -> paid, with pending -> rejected as a
    terminal branch. Only `pending` rows are editable/deletable.
    """
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    expense_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    vendor = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    expense_date = Column(Date, nullable=False, index=True)

    payment_method = Column(String, nullable=True)   # bank_transfer, credit_card, cash, cheque, online
    reference_number = Column(String, nullable=True)  # bank/vendor invoice reference
    receipt_url = Column(String, nullable=True)

    status = Column(String, default="pending", index=True)  # pending, approved, rejected, paid
    is_recurring = Column(Boolean, default=False)
    recurrence = Column(String, nullable=True)        # monthly, quarterly, annual
    department = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])


class Invoice(Base):
    """Client-side receivable. Drives the income half of the P&L."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    client_name = Column(String, nullable=False)
    project_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    amount_received = Column(Float, default=0.0)

    issue_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)

    # draft, sent, partially_paid, paid, cancelled  (overdue is derived from due_date)
    status = Column(String, default="draft", index=True)
    notes = Column(Text, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("User", foreign_keys=[created_by])


class FinancialAuditLog(Base):
    """Append-only ledger of finance events.

    Written by the finance router on every mutation, and by the payroll bridge
    when payslips are disbursed, so the accountant has one filterable timeline
    across expenses, invoices and payroll.
    """
    __tablename__ = "financial_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False, index=True)  # expense, invoice, payslip, bonus, payroll_run
    entity_id = Column(Integer, nullable=True)
    entity_ref = Column(String, nullable=True)                # human-readable: EXP-2026-0001
    action = Column(String, nullable=False, index=True)        # created, updated, approved, rejected, paid, deleted
    direction = Column(String, default="neutral")              # inflow, outflow, neutral
    amount = Column(Float, nullable=True)
    description = Column(Text, nullable=True)

    performed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    performed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    performer = relationship("User", foreign_keys=[performed_by])
