from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class HealthInsurancePolicyBase(BaseModel):
    policy_number: str
    plan_type: str
    coverage_amount: float
    room_rent_limit: Optional[float] = None
    start_date: date
    end_date: date
    premium_amount: float
    employer_contribution: Optional[float] = None
    employee_contribution: Optional[float] = None
    insurance_provider: str

class HealthInsurancePolicyCreate(HealthInsurancePolicyBase):
    employee_id: int
    policy_document_url: Optional[str] = None

class HealthInsurancePolicyUpdate(BaseModel):
    status: Optional[str] = None
    end_date: Optional[date] = None

class HealthInsurancePolicy(HealthInsurancePolicyBase):
    id: int
    employee_id: int
    status: str
    policy_document_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InsuranceDependentBase(BaseModel):
    name: str
    relationship: str
    date_of_birth: date
    gender: str
    id_number: Optional[str] = None

class InsuranceDependentCreate(InsuranceDependentBase):
    policy_id: int

class InsuranceDependent(InsuranceDependentBase):
    id: int
    policy_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class InsuranceClaimBase(BaseModel):
    patient_name: str
    patient_relationship: str
    claim_type: str
    treatment_date: date
    hospital_name: str
    diagnosis: str
    total_bill_amount: float
    claimed_amount: float
    submission_date: date

class InsuranceClaimCreate(InsuranceClaimBase):
    policy_id: int
    documents: Optional[List[str]] = None

class InsuranceClaimUpdate(BaseModel):
    status: Optional[str] = None
    approved_amount: Optional[float] = None
    deductible_amount: Optional[float] = None
    rejection_reason: Optional[str] = None
    processing_date: Optional[date] = None
    payment_date: Optional[date] = None

class InsuranceClaim(InsuranceClaimBase):
    id: int
    policy_id: int
    claim_number: str
    approved_amount: Optional[float] = None
    deductible_amount: Optional[float] = None
    status: str
    processing_date: Optional[date] = None
    payment_date: Optional[date] = None
    rejection_reason: Optional[str] = None
    documents: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PanelHospitalBase(BaseModel):
    name: str
    address: str
    city: str
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    specialties: Optional[List[str]] = None
    room_categories: Optional[List[dict]] = None
    minimum_room_entitlement: Optional[float] = None
    cashless_facility: bool = True

class PanelHospitalCreate(PanelHospitalBase):
    pass

class PanelHospital(PanelHospitalBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CoverageDetailBase(BaseModel):
    coverage_type: str
    annual_limit: float
    per_incident_limit: Optional[float] = None
    deductible: Optional[float] = None
    co_payment_percentage: Optional[float] = None

class CoverageDetailCreate(CoverageDetailBase):
    policy_id: int

class CoverageDetailUpdate(BaseModel):
    used_amount: Optional[float] = None
    remaining_amount: Optional[float] = None

class CoverageDetail(CoverageDetailBase):
    id: int
    policy_id: int
    used_amount: float
    remaining_amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class HealthInsurancePolicyResponse(HealthInsurancePolicy):
    pass

class InsuranceDependentResponse(InsuranceDependent):
    pass

class InsuranceClaimResponse(InsuranceClaim):
    pass

class PanelHospitalResponse(PanelHospital):
    pass

class CoverageDetailResponse(CoverageDetail):
    pass
class HealthInsurancePolicyResponse(BaseModel):
    id: int
    employee_id: int
    policy_number: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class InsuranceDependentResponse(BaseModel):
    id: int
    policy_id: int
    name: str
    relation_type: str
    is_active: bool
    class Config:
        from_attributes = True

class InsuranceClaimResponse(BaseModel):
    id: int
    policy_id: int
    claim_number: str
    status: str
    claimed_amount: float
    class Config:
        from_attributes = True

class PanelHospitalResponse(BaseModel):
    id: int
    name: str
    city: str
    is_active: bool
    class Config:
        from_attributes = True

class CoverageDetailResponse(BaseModel):
    id: int
    policy_id: int
    coverage_type: str
    annual_limit: float
    used_amount: float
    class Config:
        from_attributes = True
