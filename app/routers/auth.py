from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from ..models.department import Department
from ..schemas.user import UserCreate, UserLogin, Token, UserResponse, UserProfileUpdate
from ..auth import verify_password, get_password_hash, create_access_token, create_refresh_token, get_current_user, verify_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Set redirect URL based on profile completion
    user_response = UserResponse.from_orm(user)
    if not user.is_profile_complete:
        user_response.redirect_url = "/onboarding"
    else:
        role_redirects = {
            "admin": "/admin/dashboard",
            "hr": "/admin/dashboard", 
            "team_lead": "/team-lead/dashboard",
            "employee": "/employee/dashboard"
        }
        user_response.redirect_url = role_redirects.get(user.role, "/employee/dashboard")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_response
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    user_response = UserResponse.from_orm(current_user)
    if not current_user.is_profile_complete:
        user_response.redirect_url = "/onboarding"
    else:
        role_redirects = {
            "admin": "/admin/dashboard",
            "hr": "/admin/dashboard",
            "team_lead": "/team-lead/dashboard", 
            "employee": "/employee/dashboard"
        }
        user_response.redirect_url = role_redirects.get(current_user.role, "/employee/dashboard")
    
    return user_response

@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    user_id = verify_token(refresh_token, "refresh")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}

@router.get("/profile/me")
def get_profile_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    return {
        "user": current_user,
        "employee": employee,
        "is_profile_complete": current_user.is_profile_complete
    }

@router.put("/profile/me", response_model=UserResponse)
def complete_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Update user info
    current_user.first_name = profile_data.first_name
    current_user.last_name = profile_data.last_name
    current_user.phone = profile_data.phone
    current_user.role = profile_data.role
    current_user.is_profile_complete = True
    
    # Get or create department
    department = db.query(Department).filter(Department.name == profile_data.department).first()
    if not department:
        department = Department(name=profile_data.department)
        db.add(department)
        db.commit()
        db.refresh(department)
    
    # Create or update employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        # Generate employee ID
        employee_count = db.query(Employee).count()
        employee_id = f"EMP{str(employee_count + 1).zfill(4)}"
        
        employee = Employee(
            user_id=current_user.id,
            employee_id=employee_id,
            department_id=department.id,
            position=profile_data.position,
            hire_date=datetime.utcnow().date()
        )
        db.add(employee)
    else:
        employee.department_id = department.id
        employee.position = profile_data.position
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

from pydantic import BaseModel
from typing import Optional

class ProfileUpdateRequest(BaseModel):
    # User fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    
    # Employee fields
    position: Optional[str] = None
    work_location: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    marital_status: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
    qualification: Optional[str] = None
    work_schedule: Optional[str] = None
    team_size: Optional[int] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    
    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_work_phone: Optional[str] = None
    emergency_contact_home_phone: Optional[str] = None
    emergency_contact_address: Optional[str] = None
    
    # Compensation
    salary: Optional[float] = None
    bonus_target: Optional[str] = None
    stock_options: Optional[str] = None
    last_salary_increase: Optional[str] = None
    next_review_date: Optional[str] = None
    
    # Additional profile fields
    personal_email: Optional[str] = None
    nationality: Optional[str] = None
    religion: Optional[str] = None
    languages_known: Optional[str] = None
    hobbies: Optional[str] = None
    skills_summary: Optional[str] = None
    certifications: Optional[str] = None
    education_level: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None

@router.put("/profile/update")
def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user and employee profile data"""
    
    # Update user fields
    user_fields = ['first_name', 'last_name', 'phone', 'email']
    for field in user_fields:
        value = getattr(profile_data, field, None)
        if value is not None:
            setattr(current_user, field, value)
    
    # Get or create employee record
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        employee_count = db.query(Employee).count()
        employee_id = f"EMP{str(employee_count + 1).zfill(4)}"
        employee = Employee(
            user_id=current_user.id,
            employee_id=employee_id,
            hire_date=datetime.utcnow().date()
        )
        db.add(employee)
        db.flush()
    
    # Update employee fields
    employee_fields = [
        'position', 'work_location', 'gender', 'date_of_birth', 'marital_status',
        'address', 'blood_group', 'qualification', 'work_schedule', 'team_size',
        'avatar_url', 'cover_image_url', 'emergency_contact_name', 'emergency_contact_phone',
        'emergency_contact_relationship', 'emergency_contact_work_phone', 'emergency_contact_home_phone',
        'emergency_contact_address', 'salary', 'bonus_target', 'stock_options',
        'last_salary_increase', 'next_review_date', 'personal_email', 'nationality',
        'religion', 'languages_known', 'hobbies', 'skills_summary', 'certifications',
        'education_level', 'university', 'graduation_year'
    ]
    
    for field in employee_fields:
        value = getattr(profile_data, field, None)
        if value is not None:
            setattr(employee, field, value)
    
    # Force update timestamp
    from datetime import datetime
    employee.updated_at = datetime.utcnow()
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(employee)
    db.refresh(current_user)
    
    return {"message": "Profile updated successfully", "updated_at": employee.updated_at}

class SkillUpdateRequest(BaseModel):
    skills: list[dict]  # [{"name": "Python", "level": 85}]

@router.put("/profile/skills")
def update_skills(
    skills_data: SkillUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update employee skills"""
    from ..models.skill import EmployeeSkill
    
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    
    # Delete existing skills
    db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).delete()
    
    # Add new skills
    for skill_data in skills_data.skills:
        skill = EmployeeSkill(
            employee_id=employee.id,
            skill_name=skill_data["name"],
            proficiency_level=skill_data["level"]
        )
        db.add(skill)
    
    db.commit()
    return {"message": "Skills updated successfully"}