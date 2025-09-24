from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import HealthInsurancePolicy, InsuranceDependent, InsuranceClaim, PanelHospital, CoverageDetail, User
from ..schemas.health_insurance import (
    HealthInsurancePolicyResponse, InsuranceDependentCreate, InsuranceDependentResponse,
    InsuranceClaimCreate, InsuranceClaimResponse, PanelHospitalResponse, CoverageDetailResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/health-insurance", tags=["health-insurance"])

# Health Insurance Policies
@router.get("/policies/", response_model=List[HealthInsurancePolicyResponse])
def get_health_insurance_policies(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(HealthInsurancePolicy)
    if current_user.role == "employee":
        query = query.filter(HealthInsurancePolicy.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(HealthInsurancePolicy.employee_id == employee_id)
    if status:
        query = query.filter(HealthInsurancePolicy.status == status)
    return query.offset(skip).limit(limit).all()

@router.get("/policies/{policy_id}", response_model=HealthInsurancePolicyResponse)
def get_health_insurance_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    policy = db.query(HealthInsurancePolicy).filter(HealthInsurancePolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    if current_user.role == "employee" and policy.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return policy

@router.get("/my-policy/", response_model=HealthInsurancePolicyResponse)
def get_my_health_insurance_policy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    policy = db.query(HealthInsurancePolicy).filter(
        HealthInsurancePolicy.employee_id == current_user.id,
        HealthInsurancePolicy.status == "active"
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="No active policy found")
    return policy

# Insurance Dependents
@router.get("/dependents/", response_model=List[InsuranceDependentResponse])
def get_insurance_dependents(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(InsuranceDependent)
    if current_user.role == "employee":
        query = query.filter(InsuranceDependent.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(InsuranceDependent.employee_id == employee_id)
    return query.offset(skip).limit(limit).all()

@router.get("/my-dependents/", response_model=List[InsuranceDependentResponse])
def get_my_dependents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(InsuranceDependent).filter(
        InsuranceDependent.employee_id == current_user.id,
        InsuranceDependent.is_active == True
    ).all()

@router.post("/dependents/", response_model=InsuranceDependentResponse)
def add_dependent(
    dependent: InsuranceDependentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_dependent = InsuranceDependent(**dependent.dict(), employee_id=current_user.id)
    db.add(db_dependent)
    db.commit()
    db.refresh(db_dependent)
    return db_dependent

@router.put("/dependents/{dependent_id}/deactivate")
def deactivate_dependent(
    dependent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dependent = db.query(InsuranceDependent).filter(InsuranceDependent.id == dependent_id).first()
    if not dependent:
        raise HTTPException(status_code=404, detail="Dependent not found")
    
    if current_user.role == "employee" and dependent.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    dependent.is_active = False
    db.commit()
    return {"message": "Dependent deactivated successfully"}

# Insurance Claims
@router.get("/claims/", response_model=List[InsuranceClaimResponse])
def get_insurance_claims(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    claim_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(InsuranceClaim)
    if current_user.role == "employee":
        query = query.filter(InsuranceClaim.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(InsuranceClaim.employee_id == employee_id)
    if status:
        query = query.filter(InsuranceClaim.status == status)
    if claim_type:
        query = query.filter(InsuranceClaim.claim_type == claim_type)
    return query.offset(skip).limit(limit).all()

@router.get("/my-claims/", response_model=List[InsuranceClaimResponse])
def get_my_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(InsuranceClaim).filter(InsuranceClaim.employee_id == current_user.id).all()

@router.post("/claims/", response_model=InsuranceClaimResponse)
def submit_insurance_claim(
    claim: InsuranceClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_claim = InsuranceClaim(**claim.dict(), employee_id=current_user.id, status="submitted")
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim

@router.get("/claims/{claim_id}", response_model=InsuranceClaimResponse)
def get_insurance_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    if current_user.role == "employee" and claim.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return claim

@router.put("/claims/{claim_id}/approve")
def approve_insurance_claim(
    claim_id: int,
    approved_amount: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim.status = "approved"
    claim.approved_amount = approved_amount
    db.commit()
    return {"message": "Claim approved successfully"}

@router.put("/claims/{claim_id}/reject")
def reject_insurance_claim(
    claim_id: int,
    rejection_reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    claim.status = "rejected"
    claim.rejection_reason = rejection_reason
    db.commit()
    return {"message": "Claim rejected successfully"}

# Panel Hospitals
@router.get("/panel-hospitals/", response_model=List[PanelHospitalResponse])
def get_panel_hospitals(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(PanelHospital).filter(PanelHospital.is_active == True)
    if city:
        query = query.filter(PanelHospital.city == city)
    return query.offset(skip).limit(limit).all()

@router.post("/panel-hospitals/", response_model=PanelHospitalResponse)
def add_panel_hospital(
    hospital_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_hospital = PanelHospital(**hospital_data)
    db.add(db_hospital)
    db.commit()
    db.refresh(db_hospital)
    return db_hospital

# Coverage Details
@router.get("/coverage/", response_model=List[CoverageDetailResponse])
def get_coverage_details(
    employee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CoverageDetail)
    if current_user.role == "employee":
        query = query.filter(CoverageDetail.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(CoverageDetail.employee_id == employee_id)
    return query.all()

@router.get("/my-coverage/", response_model=List[CoverageDetailResponse])
def get_my_coverage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(CoverageDetail).filter(CoverageDetail.employee_id == current_user.id).all()

@router.get("/stats/overview")
def get_insurance_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_policies = db.query(HealthInsurancePolicy).count()
    active_policies = db.query(HealthInsurancePolicy).filter(HealthInsurancePolicy.status == "active").count()
    total_claims = db.query(InsuranceClaim).count()
    pending_claims = db.query(InsuranceClaim).filter(InsuranceClaim.status == "submitted").count()
    approved_claims = db.query(InsuranceClaim).filter(InsuranceClaim.status == "approved").count()
    
    return {
        "total_policies": total_policies,
        "active_policies": active_policies,
        "total_claims": total_claims,
        "pending_claims": pending_claims,
        "approved_claims": approved_claims
    }