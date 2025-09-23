from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models.health_insurance import (
    HealthInsurancePolicy, InsuranceClaim, InsuranceDependent, PanelHospital
)
from app.routers.auth import get_current_user
from app.models.sql_models import User, UserRole

router = APIRouter(prefix="/health-insurance", tags=["Health Insurance"])

@router.get("/data")
async def get_insurance_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all health insurance data for current user"""
    if not current_user.employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Get policy
    policy_result = await db.execute(
        select(HealthInsurancePolicy).filter(
            HealthInsurancePolicy.employee_id == current_user.employee.id
        )
    )
    policy = policy_result.scalar_one_or_none()
    
    if not policy:
        return {"policy": None, "claims": [], "dependents": [], "stats": {}}
    
    # Get claims
    claims_result = await db.execute(
        select(InsuranceClaim).filter(InsuranceClaim.policy_id == policy.id)
    )
    claims = claims_result.scalars().all()
    
    # Get dependents
    dependents_result = await db.execute(
        select(InsuranceDependent).filter(
            InsuranceDependent.policy_id == policy.id,
            InsuranceDependent.is_active == True
        )
    )
    dependents = dependents_result.scalars().all()
    
    # Calculate stats
    approved_claims = [c for c in claims if c.status == 'approved']
    used_amount = sum(c.approved_amount or 0 for c in approved_claims)
    
    stats = {
        "totalCoverage": policy.coverage_amount,
        "usedAmount": used_amount,
        "remainingAmount": policy.coverage_amount - used_amount,
        "approvedClaims": len(approved_claims),
        "totalClaims": len(claims)
    }
    
    return {
        "policy": policy,
        "claims": claims,
        "dependents": dependents,
        "stats": stats
    }

@router.get("/hospitals")
async def get_hospitals(
    search: Optional[str] = None,
    city: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get panel hospitals"""
    query = select(PanelHospital).filter(PanelHospital.is_active == True)
    
    if search:
        query = query.filter(PanelHospital.name.ilike(f"%{search}%"))
    if city:
        query = query.filter(PanelHospital.city.ilike(f"%{city}%"))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/claims")
async def create_claim(
    claim_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new insurance claim"""
    if not current_user.employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    policy_result = await db.execute(
        select(HealthInsurancePolicy).filter(
            HealthInsurancePolicy.employee_id == current_user.employee.id
        )
    )
    policy = policy_result.scalar_one_or_none()
    
    if not policy:
        raise HTTPException(status_code=404, detail="No active policy found")
    
    # Generate claim number
    import uuid
    claim_number = f"CLM{str(uuid.uuid4())[:8].upper()}"
    
    claim = InsuranceClaim(
        policy_id=policy.id,
        claim_number=claim_number,
        patient_name=claim_data.get('patient_name'),
        patient_relationship=claim_data.get('patient_relationship', 'self'),
        claim_type=claim_data.get('claim_type'),
        treatment_date=claim_data.get('treatment_date'),
        diagnosis=claim_data.get('diagnosis'),
        total_bill_amount=claim_data.get('total_bill_amount'),
        claimed_amount=claim_data.get('claimed_amount'),
        submitted_date=date.today(),
        status='pending'
    )
    
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    
    return claim

@router.get("/provider/{policy_id}")
async def get_provider_info(policy_id: int):
    """Get provider contact information"""
    return {
        "name": "PakQatar",
        "full_name": "PakQatar Family Takaful Limited",
        "phone": "+92-21-111-725-282",
        "email": "info@pakqatar.com.pk",
        "website": "https://www.pakqatar.com.pk",
        "address": "PakQatar House, Plot No. 5-C, Block-9, Clifton, Karachi",
        "city": "Karachi",
        "country": "Pakistan",
        "business_hours": "Monday - Friday: 9:00 AM - 6:00 PM",
        "emergency_contact": "+92-21-111-725-911"
    }