from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class HealthInsurancePolicy(Base):
    __tablename__ = "health_insurance_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    policy_number = Column(String, unique=True, nullable=False)
    plan_type = Column(String, nullable=False)  # basic, premium, family
    coverage_amount = Column(Float, nullable=False)
    room_rent_limit = Column(Float, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    premium_amount = Column(Float, nullable=False)
    employer_contribution = Column(Float, nullable=True)
    employee_contribution = Column(Float, nullable=True)
    status = Column(String, default="active")  # active, expired, cancelled
    insurance_provider = Column(String, nullable=False)
    policy_document_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User")
    dependents = relationship("InsuranceDependent", back_populates="insurance_policy")
    claims = relationship("InsuranceClaim", back_populates="insurance_policy")
    coverage_details = relationship("CoverageDetail", back_populates="insurance_policy")

class InsuranceDependent(Base):
    __tablename__ = "insurance_dependents"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("health_insurance_policies.id"), nullable=False)
    name = Column(String, nullable=False)
    relation_type = Column(String, nullable=False)  # spouse, child, parent
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    id_number = Column(String, nullable=True)  # National ID or passport
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    insurance_policy = relationship("HealthInsurancePolicy", back_populates="dependents")

class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("health_insurance_policies.id"), nullable=False)
    claim_number = Column(String, unique=True, nullable=False)
    patient_name = Column(String, nullable=False)
    patient_relationship = Column(String, nullable=False)  # self, spouse, child, etc.
    claim_type = Column(String, nullable=False)  # hospitalization, outpatient, dental, etc.
    treatment_date = Column(Date, nullable=False)
    hospital_name = Column(String, nullable=False)
    diagnosis = Column(Text, nullable=False)
    total_bill_amount = Column(Float, nullable=False)
    claimed_amount = Column(Float, nullable=False)
    approved_amount = Column(Float, nullable=True)
    deductible_amount = Column(Float, nullable=True)
    status = Column(String, default="submitted")  # submitted, under_review, approved, rejected, paid
    submission_date = Column(Date, nullable=False)
    processing_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    documents = Column(JSON, nullable=True)  # Array of document URLs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    insurance_policy = relationship("HealthInsurancePolicy", back_populates="claims")

class PanelHospital(Base):
    __tablename__ = "panel_hospitals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    specialties = Column(JSON, nullable=True)  # Array of medical specialties
    room_categories = Column(JSON, nullable=True)  # Available room types
    minimum_room_entitlement = Column(Float, nullable=True)
    cashless_facility = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CoverageDetail(Base):
    __tablename__ = "coverage_details"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("health_insurance_policies.id"), nullable=False)
    coverage_type = Column(String, nullable=False)  # hospitalization, outpatient, dental, etc.
    annual_limit = Column(Float, nullable=False)
    used_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float, nullable=False)
    per_incident_limit = Column(Float, nullable=True)
    deductible = Column(Float, nullable=True)
    co_payment_percentage = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    insurance_policy = relationship("HealthInsurancePolicy", back_populates="coverage_details")