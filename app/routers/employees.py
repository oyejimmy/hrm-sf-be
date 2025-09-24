from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..models.employee import Employee
from ..models.department import Department
from ..schemas.employee import EmployeeCreate, EmployeeResponse, EmployeeUpdate, ProfileData
from ..auth import get_current_user, require_role

router = APIRouter(prefix="/api/employees", tags=["Employees"])

@router.get("/", response_model=List[EmployeeResponse])
def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    current_user: User = Depends(require_role(["admin", "hr"])),
    db: Session = Depends(get_db)
):
    query = db.query(Employee)
    
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    
    employees = query.offset(skip).limit(limit).all()
    return employees

@router.get("/me", response_model=EmployeeResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )
    return employee

@router.get("/me/profile", response_model=ProfileData)
def get_my_formatted_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get formatted profile data for frontend"""
    from ..models.skill import EmployeeSkill
    
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found"
        )
    
    # Get department name
    dept_name = employee.department.name if employee.department else "N/A"
    
    # Get manager name
    manager_name = "N/A"
    if employee.manager:
        manager_user = db.query(User).filter(User.id == employee.manager.user_id).first()
        if manager_user:
            manager_name = f"{manager_user.first_name} {manager_user.last_name}"
    
    # Get skills
    skills = db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).all()
    skills_data = [{"name": skill.skill_name, "level": skill.proficiency_level} for skill in skills]
    
    # Format profile data
    profile_data = {
        "personalInfo": {
            "name": f"{current_user.first_name} {current_user.last_name}",
            "position": employee.position or "N/A",
            "department": dept_name,
            "location": employee.work_location or "N/A",
            "email": current_user.email,
            "phone": current_user.phone or "N/A",
            "hireDate": employee.hire_date.strftime("%b %d, %Y") if employee.hire_date else "N/A",
            "employmentType": employee.employment_status.replace("_", " ").title(),
            "employeeId": employee.employee_id,
            "manager": manager_name,
            "qualification": employee.qualification or "N/A",
            "bloodGroup": employee.blood_group or "N/A",
            "gender": employee.gender or "N/A",
            "dateOfBirth": employee.date_of_birth.strftime("%Y-%m-%d") if employee.date_of_birth else "N/A",
            "maritalStatus": employee.marital_status or "N/A",
            "address": employee.address or "N/A",
            "nationality": employee.nationality or "N/A",
            "religion": employee.religion or "N/A",
            "languagesKnown": employee.languages_known or "N/A",
            "hobbies": employee.hobbies or "N/A",
            "personalEmail": employee.personal_email or "N/A",
            "educationLevel": employee.education_level or "N/A",
            "university": employee.university or "N/A",
            "graduationYear": employee.graduation_year or "N/A",
            "certifications": employee.certifications or "N/A",
            "skillsSummary": employee.skills_summary or "N/A",
            "avatar": employee.avatar_url,
            "avatar_url": employee.avatar_url,
            "coverImage": employee.cover_image_url,
            "cover_image_url": employee.cover_image_url,
            # Emergency contact fields in personalInfo for easy access
            "emergency_contact_name": employee.emergency_contact_name,
            "emergency_contact_phone": employee.emergency_contact_phone,
            "emergency_contact_relationship": employee.emergency_contact_relationship,
            "emergency_contact_work_phone": employee.emergency_contact_work_phone,
            "emergency_contact_home_phone": employee.emergency_contact_home_phone,
            "emergency_contact_address": employee.emergency_contact_address
        },
        "emergencyContacts": [{
            "id": 1,
            "name": employee.emergency_contact_name or "N/A",
            "relationship": employee.emergency_contact_relationship or "N/A",
            "mobile": employee.emergency_contact_phone or "N/A",
            "workPhone": employee.emergency_contact_work_phone or "N/A",
            "homePhone": employee.emergency_contact_home_phone or "N/A",
            "address": employee.emergency_contact_address or "N/A"
        }] if employee.emergency_contact_name else [],
        "jobInfo": {
            "title": employee.position or "N/A",
            "department": dept_name,
            "reportsTo": manager_name,
            "teamSize": employee.team_size or 0,
            "startDate": employee.hire_date.strftime("%b %d, %Y") if employee.hire_date else "N/A",
            "employmentStatus": employee.employment_status or "N/A",
            "workLocation": employee.work_location or "N/A",
            "workSchedule": employee.work_schedule or "Standard (9:00 AM - 6:00 PM)"
        },
        "compensation": {
            "salary": f"${employee.salary:,.0f} monthly" if employee.salary else "N/A",
            "bonus": employee.bonus_target or "N/A",
            "stockOptions": employee.stock_options or "N/A",
            "lastIncrease": employee.last_salary_increase or "N/A",
            "nextReview": employee.next_review_date or "N/A"
        },
        "skills": skills_data,
        "documents": [
            {"name": "Employment Contract", "date": "Mar 01, 2021", "type": "Contract"},
            {"name": "NDA Agreement", "date": "Mar 02, 2021", "type": "Legal"},
            {"name": "Performance Review 2023", "date": "Dec 15, 2023", "type": "Review"}
        ]
    }
    
    return profile_data

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check permissions
    if current_user.role not in ["admin", "hr"]:
        # Team leads can only view their team members
        if current_user.role == "team_lead":
            employee = db.query(Employee).filter(Employee.id == employee_id).first()
            if not employee or employee.manager_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        # Employees can only view their own profile
        elif current_user.role == "employee":
            employee = db.query(Employee).filter(
                Employee.id == employee_id,
                Employee.user_id == current_user.id
            ).first()
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    return employee

@router.post("/", response_model=EmployeeResponse)
def create_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(require_role(["admin", "hr"])),
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(User).filter(User.id == employee_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if employee already exists
    if db.query(Employee).filter(Employee.user_id == employee_data.user_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee profile already exists"
        )
    
    db_employee = Employee(**employee_data.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    
    return db_employee

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(require_role(["admin", "hr"])),
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    for field, value in employee_data.dict(exclude_unset=True).items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    return employee

@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    db.delete(employee)
    db.commit()
    
    return {"message": "Employee deleted successfully"}

@router.get("/team/{manager_id}", response_model=List[EmployeeResponse])
def get_team_members(
    manager_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check permissions
    if current_user.role not in ["admin", "hr"] and current_user.id != manager_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    team_members = db.query(Employee).filter(Employee.manager_id == manager_id).all()
    return team_members