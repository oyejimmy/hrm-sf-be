from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from ..models.skill import EmployeeSkill
from ..models.department import Department
from ..models.access_request import AccessRequest
from ..schemas.user import UserCreate, UserLogin, Token, UserResponse, UserProfileUpdate
from ..schemas.access_request import AccessRequestCreate, AccessRequestResponse
from ..auth import verify_password, get_password_hash, create_access_token, create_refresh_token, get_current_user, verify_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/access-request", response_model=AccessRequestResponse)
def create_access_request(request_data: AccessRequestCreate, db: Session = Depends(get_db)):
    # Check if request already exists
    existing_request = db.query(AccessRequest).filter(AccessRequest.personal_email == request_data.personal_email).first()
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An access request with this email already exists. Please contact HR for status updates."
        )
    
    try:
        # Create access request
        db_request = AccessRequest(
            full_name=request_data.full_name,
            personal_email=request_data.personal_email,
            phone=request_data.phone,
            department=request_data.department,
            message=request_data.message
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        
        return db_request
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create access request: {str(e)}"
        )

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
    
    # Set redirect URL based on user status
    user_response = UserResponse.from_orm(user)
    
    # Priority 1: If user has temp password, redirect to change password
    if user.temp_password:
        user_response.redirect_url = "/change-password"
    # Priority 2: Check if required profile fields are missing (except admin/HR)
    elif user.role in ["admin", "hr"]:
        role_redirects = {
            "admin": "/admin/dashboard",
            "hr": "/admin/dashboard"
        }
        user_response.redirect_url = role_redirects.get(user.role, "/admin/dashboard")
    else:
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        required_fields_missing = (
            not employee or
            not employee.avatar_url or
            not employee.emergency_contact_relationship or
            not employee.personal_email or
            not employee.gender
        )
        
        if required_fields_missing:
            user_response.redirect_url = "/onboarding"
        else:
            role_redirects = {
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
def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_response = UserResponse.from_orm(current_user)
    
    # Priority 1: If user has temp password, redirect to change password
    if current_user.temp_password:
        user_response.redirect_url = "/change-password"
    # Priority 2: Check if required profile fields are missing (except admin/HR)
    elif current_user.role in ["admin", "hr"]:
        role_redirects = {
            "admin": "/admin/dashboard",
            "hr": "/admin/dashboard"
        }
        user_response.redirect_url = role_redirects.get(current_user.role, "/admin/dashboard")
    else:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        required_fields_missing = (
            not employee or
            not employee.avatar_url or
            not employee.emergency_contact_relationship or
            not employee.personal_email or
            not employee.gender
        )
        
        if required_fields_missing:
            user_response.redirect_url = "/onboarding"
        else:
            role_redirects = {
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
from typing import Optional, List

class OnboardingRequest(BaseModel):
    # Personal Information
    title: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    phone: Optional[str] = None
    profile_picture: Optional[str] = None
    
    # Job Information
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[str] = None
    employment_type: Optional[str] = None
    employee_id: Optional[str] = None
    manager: Optional[str] = None
    employment_status: Optional[str] = None
    work_schedule: Optional[str] = None
    work_location: Optional[str] = None
    qualification: Optional[str] = None
    languagesKnown: Optional[List[str]] = None
    
    # Personal Details
    gender: Optional[str] = None
    religion: Optional[str] = None
    date_of_birth: Optional[str] = None
    marital_status: Optional[str] = None
    blood_group: Optional[str] = None
    nationality: Optional[str] = None
    personal_email: Optional[str] = None
    address: Optional[str] = None
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_work_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    emergency_contact_home_phone: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_address: Optional[str] = None
    
    # Education & Skills
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    certifications: Optional[str] = None
    skills_summary: Optional[str] = None
    technical_skills: Optional[List[str]] = None

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
    office_address: Optional[str] = None
    blood_group: Optional[str] = None
    qualification: Optional[str] = None
    work_schedule: Optional[str] = None
    team_size: Optional[int] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    employment_status: Optional[str] = None
    employment_type: Optional[str] = None
    hire_date: Optional[str] = None
    employee_id: Optional[str] = None
    manager: Optional[str] = None
    
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
    technical_skills: Optional[List[str]] = None

@router.put("/profile/update")
def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user and employee profile data"""
    try:
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
        
        # Handle date fields specially
        if profile_data.date_of_birth:
            try:
                from datetime import datetime as dt
                if isinstance(profile_data.date_of_birth, str):
                    employee.date_of_birth = dt.strptime(profile_data.date_of_birth, '%Y-%m-%d').date()
                else:
                    employee.date_of_birth = profile_data.date_of_birth
            except ValueError:
                pass  # Skip invalid date
        
        if profile_data.hire_date:
            try:
                from datetime import datetime as dt
                if isinstance(profile_data.hire_date, str):
                    employee.hire_date = dt.strptime(profile_data.hire_date, '%Y-%m-%d').date()
                else:
                    employee.hire_date = profile_data.hire_date
            except ValueError:
                pass  # Skip invalid date
        
        # Update other employee fields
        employee_fields = [
            'position', 'work_location', 'gender', 'marital_status', 'employment_status',
            'address', 'office_address', 'blood_group', 'qualification', 'work_schedule', 'team_size',
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
        
        # Handle technical skills
        if profile_data.technical_skills is not None:
            # Delete existing skills
            db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).delete()
            
            # Add new skills with default proficiency level
            for skill_name in profile_data.technical_skills:
                skill = EmployeeSkill(
                    employee_id=employee.id,
                    skill_name=skill_name.strip(),
                    proficiency_level=50.0  # Default proficiency level
                )
                db.add(skill)
        
        # Force update timestamp
        from datetime import datetime
        employee.updated_at = datetime.utcnow()
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(employee)
        db.refresh(current_user)
        
        return {"message": "Profile updated successfully", "updated_at": employee.updated_at}
    
    except Exception as e:
        db.rollback()
        print(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")

class SkillUpdateRequest(BaseModel):
    skills: list[dict]  # [{"name": "Python", "level": 85}]

@router.post("/onboarding")
def complete_onboarding(
    onboarding_data: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete user onboarding with comprehensive profile data"""
    try:
        # Update user fields
        if onboarding_data.first_name:
            current_user.first_name = onboarding_data.first_name
        if onboarding_data.last_name:
            current_user.last_name = onboarding_data.last_name
        if onboarding_data.phone:
            current_user.phone = onboarding_data.phone
        if onboarding_data.profile_picture:
            current_user.profile_picture = onboarding_data.profile_picture
        current_user.role = "employee"  # Default role
        current_user.is_profile_complete = True
        
        # Get or create department (only if department is provided)
        department = None
        if onboarding_data.department:
            department = db.query(Department).filter(Department.name == onboarding_data.department).first()
            if not department:
                department = Department(name=onboarding_data.department)
                db.add(department)
                db.commit()
                db.refresh(department)
        
        # Check if employee record exists, create or update
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            # Generate employee ID if not provided
            if not onboarding_data.employee_id:
                employee_count = db.query(Employee).count()
                employee_id = f"EMP{str(employee_count + 1).zfill(4)}"
            else:
                employee_id = onboarding_data.employee_id
            
            employee = Employee(
                user_id=current_user.id,
                employee_id=employee_id,
                department_id=department.id if department else None
            )
            db.add(employee)
        else:
            # Update existing employee's department
            if department:
                employee.department_id = department.id
        
        # Update employee fields safely (only existing database columns)
        from datetime import datetime as dt
        if onboarding_data.position:
            employee.position = onboarding_data.position
        if onboarding_data.hire_date:
            employee.hire_date = dt.strptime(onboarding_data.hire_date, '%Y-%m-%d').date()
        if onboarding_data.employment_status:
            employee.employment_status = onboarding_data.employment_status
        if onboarding_data.work_schedule:
            employee.work_schedule = onboarding_data.work_schedule
        if onboarding_data.work_location:
            employee.work_location = onboarding_data.work_location
        if onboarding_data.qualification:
            employee.qualification = onboarding_data.qualification
        if onboarding_data.gender:
            employee.gender = onboarding_data.gender
        if onboarding_data.religion:
            employee.religion = onboarding_data.religion
        if onboarding_data.date_of_birth:
            employee.date_of_birth = dt.strptime(onboarding_data.date_of_birth, '%Y-%m-%d').date()
        if onboarding_data.marital_status:
            employee.marital_status = onboarding_data.marital_status
        if onboarding_data.blood_group:
            employee.blood_group = onboarding_data.blood_group
        if onboarding_data.nationality:
            employee.nationality = onboarding_data.nationality
        if onboarding_data.personal_email:
            employee.personal_email = onboarding_data.personal_email
        if onboarding_data.address:
            employee.address = onboarding_data.address
        if onboarding_data.emergency_contact_name:
            employee.emergency_contact_name = onboarding_data.emergency_contact_name
        if onboarding_data.emergency_contact_work_phone:
            employee.emergency_contact_work_phone = onboarding_data.emergency_contact_work_phone
        if onboarding_data.emergency_contact_relationship:
            employee.emergency_contact_relationship = onboarding_data.emergency_contact_relationship
        if onboarding_data.emergency_contact_home_phone:
            employee.emergency_contact_home_phone = onboarding_data.emergency_contact_home_phone
        if onboarding_data.emergency_contact_phone:
            employee.emergency_contact_phone = onboarding_data.emergency_contact_phone
        if onboarding_data.emergency_contact_address:
            employee.emergency_contact_address = onboarding_data.emergency_contact_address
        if onboarding_data.university:
            employee.university = onboarding_data.university
        if onboarding_data.graduation_year:
            employee.graduation_year = onboarding_data.graduation_year
        if onboarding_data.certifications:
            employee.certifications = onboarding_data.certifications
        if onboarding_data.skills_summary:
            employee.skills_summary = onboarding_data.skills_summary
        
        # Handle languages known
        if hasattr(onboarding_data, 'languagesKnown') and onboarding_data.languagesKnown:
            import json
            employee.languages_known = json.dumps(onboarding_data.languagesKnown)
        
        # Set profile picture to avatar_url for employee
        if onboarding_data.profile_picture:
            employee.avatar_url = onboarding_data.profile_picture
        
        # Handle technical skills
        if onboarding_data.technical_skills:
            # Delete existing skills for this employee
            db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).delete()
            
            # Add new skills with default proficiency level
            for skill_name in onboarding_data.technical_skills:
                skill = EmployeeSkill(
                    employee_id=employee.id,
                    skill_name=skill_name.strip(),
                    proficiency_level=50.0  # Default proficiency level
                )
                db.add(skill)
        
        db.commit()
        db.refresh(current_user)
        
        return {"message": "Onboarding completed successfully", "user": current_user}
    
    except Exception as e:
        db.rollback()
        print(f"Onboarding error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")

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

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class ChangePasswordWithEmailRequest(BaseModel):
    email: str
    current_password: str
    new_password: str
    confirm_password: str

class ResetPasswordRequest(BaseModel):
    email: str
    temp_password: str
    new_password: str
    confirm_password: str

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change password for authenticated user"""
    # For users with temp password, verify against temp password OR hashed password
    password_valid = False
    if current_user.temp_password and request.current_password == current_user.temp_password:
        password_valid = True
    elif verify_password(request.current_password, current_user.hashed_password):
        password_valid = True
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Check if user had temp password (new user)
    had_temp_password = bool(current_user.temp_password)
    
    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    current_user.temp_password = None  # Clear temp password
    db.commit()
    
    # Determine next redirect - new employees go to onboarding
    next_redirect = None
    if had_temp_password:
        # Check if employee record exists and has complete data
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee or not employee.first_name:
            next_redirect = "/onboarding"
        else:
            role_redirects = {
                "admin": "/admin/dashboard",
                "hr": "/admin/dashboard",
                "team_lead": "/team-lead/dashboard",
                "employee": "/employee/dashboard"
            }
            next_redirect = role_redirects.get(current_user.role, "/employee/dashboard")
    
    return {
        "message": "Password changed successfully",
        "redirect_url": next_redirect
    }

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using temporary password"""
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify temporary password
    if not user.temp_password or user.temp_password != request.temp_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid temporary password"
        )
    
    # Validate new password
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Update password and clear temp password
    user.hashed_password = get_password_hash(request.new_password)
    user.temp_password = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/check-temp-password/{email}")
def check_temp_password(email: str, db: Session = Depends(get_db)):
    """Check if user has a temporary password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "has_temp_password": bool(user.temp_password),
        "user_name": f"{user.first_name} {user.last_name}"
    }