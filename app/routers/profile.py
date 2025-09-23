from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.routers.auth import get_current_active_user
from app.core.logger import logger

router = APIRouter()

# Mock profile data - replace with database later
PROFILE_DATA = {
    "personalInfo": {
        "name": "Simona Clapan",
        "position": "COO",
        "department": "Executive",
        "location": "Kyiv, Ukraine",
        "email": "simona.clapan@company.com",
        "phone": "+380950830332",
        "hireDate": "Mar 05, 2021",
        "employmentType": "Full Time",
        "employeeId": "EMP-0234",
        "manager": "Michael Johnson (CEO)",
        "qualification": "MBA in Business Administration"
    },
    "emergencyContacts": [
        {
            "id": 1,
            "name": "Yulia Kitsmans",
            "relationship": "Sister",
            "mobile": "+380 95 083 03 22",
            "workPhone": "+322 095 083 03 21",
            "homePhone": "71-22-22",
            "address": "Ukraine, Kyiv, Velyka Vasilikvska str. 30, 3d floor, ap. 4"
        }
    ],
    "jobInfo": {
        "title": "Chief Operating Officer",
        "department": "Executive",
        "reportsTo": "CEO",
        "teamSize": 45,
        "startDate": "Mar 05, 2021",
        "employmentType": "Full Time",
        "workSchedule": "Standard (9:00 AM - 6:00 PM)",
        "location": "Kyiv Office"
    },
    "compensation": {
        "salary": "$12,500 monthly",
        "bonus": "15% annual target",
        "stockOptions": "10,000 shares",
        "lastIncrease": "Jun 15, 2023 (5%)",
        "nextReview": "Jun 15, 2024"
    },
    "skills": [
        {"name": "Strategic Planning", "level": 95},
        {"name": "Operations Management", "level": 90},
        {"name": "Team Leadership", "level": 92},
        {"name": "Budget Management", "level": 88},
        {"name": "Process Improvement", "level": 85}
    ],
    "documents": [
        {"name": "Employment Contract", "date": "Mar 01, 2021", "type": "Contract"},
        {"name": "NDA Agreement", "date": "Mar 02, 2021", "type": "Legal"},
        {"name": "Performance Review 2023", "date": "Dec 15, 2023", "type": "Review"},
        {"name": "Compensation Plan", "date": "Jun 15, 2023", "type": "Compensation"}
    ]
}

@router.get("/profile")
async def get_profile(
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile."""
    # For now, return mock data. Later integrate with database
    profile = PROFILE_DATA.copy()
    profile["personalInfo"]["email"] = current_user.email
    profile["personalInfo"]["name"] = f"{current_user.first_name} {current_user.last_name}"
    return profile

@router.put("/profile")
async def update_profile(
    profile_data: Dict[str, Any],
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    # Update mock data - later integrate with database
    if "personalInfo" in profile_data:
        PROFILE_DATA["personalInfo"].update(profile_data["personalInfo"])
    if "jobInfo" in profile_data:
        PROFILE_DATA["jobInfo"].update(profile_data["jobInfo"])
    if "compensation" in profile_data:
        PROFILE_DATA["compensation"].update(profile_data["compensation"])
    
    logger.info(f"Profile updated for user: {current_user.email}")
    return PROFILE_DATA

@router.post("/profile/emergency-contact")
async def add_emergency_contact(
    contact_data: Dict[str, Any],
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add emergency contact."""
    new_id = max([c["id"] for c in PROFILE_DATA["emergencyContacts"]], default=0) + 1
    new_contact = {"id": new_id, **contact_data}
    PROFILE_DATA["emergencyContacts"].append(new_contact)
    
    logger.info(f"Emergency contact added for user: {current_user.email}")
    return new_contact

@router.put("/profile/emergency-contact/{contact_id}")
async def update_emergency_contact(
    contact_id: int,
    contact_data: Dict[str, Any],
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update emergency contact."""
    for i, contact in enumerate(PROFILE_DATA["emergencyContacts"]):
        if contact["id"] == contact_id:
            PROFILE_DATA["emergencyContacts"][i] = {"id": contact_id, **contact_data}
            logger.info(f"Emergency contact updated for user: {current_user.email}")
            return PROFILE_DATA["emergencyContacts"][i]
    
    raise HTTPException(status_code=404, detail="Contact not found")

@router.delete("/profile/emergency-contact/{contact_id}")
async def delete_emergency_contact(
    contact_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete emergency contact."""
    PROFILE_DATA["emergencyContacts"] = [
        c for c in PROFILE_DATA["emergencyContacts"] if c["id"] != contact_id
    ]
    
    logger.info(f"Emergency contact deleted for user: {current_user.email}")
    return {"message": "Contact deleted"}