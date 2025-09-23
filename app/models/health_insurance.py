from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship as sql_relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
from datetime import datetime, date

# Health Insurance Enums
class InsurancePlan(str, enum.Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    EXECUTIVE = "executive"

class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    PAID = "paid"

class ClaimType(str, enum.Enum):
    HOSPITALIZATION = "hospitalization"
    OUTPATIENT = "outpatient"
    EMERGENCY = "emergency"
    MATERNITY = "maternity"
    DENTAL = "dental"
    OPTICAL = "optical"
    PHARMACY = "pharmacy"

class HospitalType(str, enum.Enum):
    PANEL = "panel"
    NON_PANEL = "non_panel"
    EXCLUDED = "excluded"

class PolicyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

# Health Insurance Models
class HealthInsurancePolicy(Base):
    __tablename__ = "health_insurance_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("insurance_providers.id"), nullable=True)
    policy_number = Column(String(50), unique=True, index=True, nullable=False)
    plan_type = Column(SQLEnum(InsurancePlan), nullable=False)
    coverage_amount = Column(Float, nullable=False)
    annual_premium = Column(Float, nullable=False)
    room_rent_limit = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SQLEnum(PolicyStatus), default=PolicyStatus.ACTIVE)
    
    # Family Coverage
    spouse_covered = Column(Boolean, default=False)
    children_covered = Column(Integer, default=0)
    parents_covered = Column(Integer, default=0)
    
    # Policy Details
    pre_existing_conditions = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)
    waiting_period_months = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = sql_relationship("Employee")
    provider = sql_relationship("InsuranceProvider")
    claims = sql_relationship("InsuranceClaim", back_populates="policy")
    dependents = sql_relationship("InsuranceDependent", back_populates="policy")

class InsuranceDependent(Base):
    __tablename__ = "insurance_dependents"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("health_insurance_policies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    relationship = Column(String(50), nullable=False)  # spouse, child, parent
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    id_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    policy = sql_relationship("HealthInsurancePolicy", back_populates="dependents")

class PanelHospital(Base):
    __tablename__ = "panel_hospitals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    hospital_type = Column(SQLEnum(HospitalType), default=HospitalType.PANEL)
    minimum_room_entitlement = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    is_non_reimbursable = Column(Boolean, default=False)
    
    # Additional Information
    specialties = Column(Text, nullable=True)  # JSON string
    facilities = Column(Text, nullable=True)   # JSON string
    emergency_services = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    claims = sql_relationship("InsuranceClaim", back_populates="hospital")

class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("health_insurance_policies.id"), nullable=False)
    hospital_id = Column(Integer, ForeignKey("panel_hospitals.id"), nullable=True)
    claim_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Patient Information
    patient_name = Column(String(100), nullable=False)
    patient_relationship = Column(String(50), nullable=False)  # self, spouse, child, parent
    
    # Claim Details
    claim_type = Column(SQLEnum(ClaimType), nullable=False)
    treatment_date = Column(Date, nullable=False)
    discharge_date = Column(Date, nullable=True)
    diagnosis = Column(Text, nullable=False)
    treatment_details = Column(Text, nullable=True)
    
    # Financial Details
    total_bill_amount = Column(Float, nullable=False)
    claimed_amount = Column(Float, nullable=False)
    approved_amount = Column(Float, nullable=True)
    deductible_amount = Column(Float, default=0)
    copay_amount = Column(Float, default=0)
    
    # Status and Processing
    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.PENDING)
    submitted_date = Column(Date, nullable=False)
    processed_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Documents
    documents = Column(Text, nullable=True)  # JSON string of document paths
    
    # Processing Information
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    policy = sql_relationship("HealthInsurancePolicy", back_populates="claims")
    hospital = sql_relationship("PanelHospital", back_populates="claims")
    processor = sql_relationship("User")

class InsuranceCard(Base):
    __tablename__ = "insurance_cards"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("health_insurance_policies.id"), nullable=False)
    card_number = Column(String(50), unique=True, index=True, nullable=False)
    member_name = Column(String(100), nullable=False)
    member_id = Column(String(50), nullable=False)
    
    # Card Details
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Digital Card
    qr_code = Column(Text, nullable=True)
    card_image_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    policy = sql_relationship("HealthInsurancePolicy")

class InsuranceProvider(Base):
    __tablename__ = "insurance_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(500), nullable=False)
    
    # Contact Information
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    website = Column(String(200), nullable=True)
    
    # Address
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    
    # Business Hours
    business_hours = Column(String(200), nullable=True)
    emergency_contact = Column(String(20), nullable=True)
    
    # Additional Info
    logo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PreAuthorization(Base):
    __tablename__ = "pre_authorizations"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("health_insurance_policies.id"), nullable=False)
    hospital_id = Column(Integer, ForeignKey("panel_hospitals.id"), nullable=False)
    authorization_number = Column(String(50), unique=True, index=True, nullable=False)
    
    # Patient Information
    patient_name = Column(String(100), nullable=False)
    patient_relationship = Column(String(50), nullable=False)
    
    # Treatment Information
    proposed_treatment = Column(Text, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    treatment_date = Column(Date, nullable=False)
    doctor_name = Column(String(100), nullable=False)
    
    # Authorization Details
    status = Column(String(20), default="pending")  # pending, approved, rejected
    approved_amount = Column(Float, nullable=True)
    valid_until = Column(Date, nullable=True)
    
    # Processing
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_date = Column(Date, nullable=True)
    remarks = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    policy = sql_relationship("HealthInsurancePolicy")
    hospital = sql_relationship("PanelHospital")
    processor = sql_relationship("User")