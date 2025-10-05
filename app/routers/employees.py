from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.employee import Employee
from app.models.skill import EmployeeSkill
from app.models.user import User
from app.models.department import Department
from app.models.currency import Currency
from app.auth import get_current_user
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class UpdateProfileRequest(BaseModel):
    avatar: Optional[str] = None
    coverImage: Optional[str] = None
    profileCrop: Optional[dict] = None

class UserCreate(BaseModel):
    title: Optional[str] = None
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: str = "employee"
    active: Optional[bool] = True

class EmployeeCreateRequest(BaseModel):
    user: UserCreate
    employee: EmployeeCreate
    
class EmployeeCreateData(BaseModel):
    employee_id: str
    position: Optional[str] = None
    position_id: Optional[int] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    employment_type: Optional[str] = None
    employment_status: str = "full_time"
    hire_date: Optional[str] = None
    salary: Optional[float] = None
    salary_in_words: Optional[str] = None
    work_location: str = "office"
    work_schedule: Optional[str] = "Standard (9:00 AM - 6:00 PM)"
    work_type: Optional[str] = "office"

class EmployeeCreateRequestFixed(BaseModel):
    user: UserCreate
    employee: EmployeeCreateData

@router.get("/search")
def search_employees(
    query: str = Query(..., min_length=3, description="Search query (minimum 3 characters)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search employees by name for manager assignment
    """
    try:
        # Search employees by first_name or last_name
        employees = db.query(Employee).join(User).filter(
            (User.first_name.ilike(f"%{query}%")) | 
            (User.last_name.ilike(f"%{query}%"))
        ).limit(10).all()
        
        # Format response with employee names
        results = []
        for employee in employees:
            full_name = f"{employee.user.first_name} {employee.user.last_name}"
            results.append({
                "value": full_name,
                "label": f"{full_name} - {employee.position or 'Employee'}"
            })
        
        return {"employees": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error searching employees")

@router.get("/managers")
def get_managers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all potential managers"""
    managers = db.query(Employee).join(User).filter(
        User.role.in_(["admin", "hr", "team_lead"])
    ).all()
    
    return [{
        "id": mgr.id,
        "name": f"{mgr.user.first_name} {mgr.user.last_name}",
        "position": mgr.position
    } for mgr in managers]

@router.get("/me/profile")
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's employee profile
    """
    try:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        
        # Format data to match frontend expectations
        manager_name = None
        if employee.manager and employee.manager.user:
            manager_name = f"{employee.manager.user.first_name} {employee.manager.user.last_name}"
        
        department_name = employee.department.name if employee.department else None
        
        # Get employee skills
        skills = db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).all()
        technical_skills = [skill.skill_name for skill in skills]
        
        def capitalize_field(value):
            return value.title() if value else None
        
        return {
            "personalInfo": {
                "title": capitalize_field(current_user.title),
                "name": f"{current_user.first_name} {current_user.last_name}".title(),
                "position": capitalize_field(employee.position),
                "department": capitalize_field(department_name),
                "location": capitalize_field(employee.work_location),
                "email": current_user.email,
                "phone": current_user.phone,
                "hireDate": str(employee.hire_date) if employee.hire_date else None,
                "employmentType": capitalize_field(employee.employment_status),
                "employeeId": employee.employee_id,
                "manager": manager_name,
                "qualification": capitalize_field(employee.qualification),
                "bloodGroup": capitalize_field(employee.blood_group),
                "gender": capitalize_field(employee.gender),
                "dateOfBirth": str(employee.date_of_birth) if employee.date_of_birth else None,
                "maritalStatus": capitalize_field(employee.marital_status),
                "nationality": capitalize_field(employee.nationality),
                "religion": capitalize_field(employee.religion),
                "languagesKnown": capitalize_field(employee.languages_known),
                "hobbies": capitalize_field(employee.hobbies),
                "address": capitalize_field(employee.address),
                "office_address": capitalize_field(getattr(employee, 'office_address', None)),
                "personalEmail": employee.personal_email,
                "avatar": employee.avatar_url,
                "coverImage": employee.cover_image_url,
                "profileCrop": getattr(employee, 'profile_crop', None),
                "emergency_contact_name": capitalize_field(employee.emergency_contact_name),
                "emergency_contact_phone": employee.emergency_contact_phone,
                "emergency_contact_relationship": capitalize_field(employee.emergency_contact_relationship),
                "emergency_contact_work_phone": employee.emergency_contact_work_phone,
                "emergency_contact_home_phone": employee.emergency_contact_home_phone,
                "emergency_contact_address": capitalize_field(employee.emergency_contact_address),
                "university": capitalize_field(employee.university),
                "graduationYear": employee.graduation_year,
                "certifications": capitalize_field(employee.certifications),
                "skillsSummary": capitalize_field(employee.skills_summary),
                "educationLevel": capitalize_field(employee.education_level),
                "technical_skills": technical_skills
            },
            "jobInfo": {
                "title": capitalize_field(employee.position),
                "department": capitalize_field(department_name),
                "reportsTo": manager_name,
                "teamSize": employee.team_size or 0,
                "startDate": str(employee.hire_date) if employee.hire_date else None,
                "employmentType": capitalize_field(employee.employment_status),
                "workSchedule": capitalize_field(employee.work_schedule),
                "workLocation": capitalize_field(employee.work_location),
                "employmentStatus": capitalize_field(employee.employment_status)
            },
            "compensation": {
                "salary": f"${employee.salary:,.2f}" if employee.salary else "-",
                "bonus": capitalize_field(employee.bonus_target),
                "stockOptions": capitalize_field(employee.stock_options),
                "lastIncrease": employee.last_salary_increase,
                "nextReview": employee.next_review_date
            },
            "skills": [],
            "documents": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee profile: {str(e)}")

@router.get("/")
def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all employees (Admin/HR only)"""
    try:
        if current_user.role not in ["admin", "hr"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        employees = db.query(Employee).join(User).offset(skip).limit(limit).all()
        
        result = []
        for emp in employees:
            try:
                dept_name = emp.department.name if emp.department else "Unknown"
                manager_name = None
                if emp.manager and emp.manager.user:
                    manager_name = f"{emp.manager.user.first_name} {emp.manager.user.last_name}"
                
                result.append({
                    # Employee table fields
                    "id": emp.id,
                    "user_id": emp.user_id,
                    "employee_id": emp.employee_id,
                    "department_id": emp.department_id,
                    "position": emp.position,
                    "employment_type": getattr(emp, 'employment_type', None),
                    "employment_status": emp.employment_status,
                    "hire_date": str(emp.hire_date) if emp.hire_date else None,
                    "salary": emp.salary,
                    "manager_id": emp.manager_id,
                    "work_location": emp.work_location,
                    "work_type": getattr(emp, 'work_type', None),
                    "gender": getattr(emp, 'gender', None),
                    "date_of_birth": str(emp.date_of_birth) if getattr(emp, 'date_of_birth', None) else None,
                    "marital_status": getattr(emp, 'marital_status', None),
                    "address": getattr(emp, 'address', None),
                    "emergency_contact_name": getattr(emp, 'emergency_contact_name', None),
                    "emergency_contact_phone": getattr(emp, 'emergency_contact_phone', None),
                    "blood_group": getattr(emp, 'blood_group', None),
                    "qualification": getattr(emp, 'qualification', None),
                    "work_schedule": getattr(emp, 'work_schedule', None),
                    "team_size": getattr(emp, 'team_size', None),
                    "avatar_url": getattr(emp, 'avatar_url', None),
                    "cover_image_url": getattr(emp, 'cover_image_url', None),
                    "emergency_contact_relationship": getattr(emp, 'emergency_contact_relationship', None),
                    "emergency_contact_work_phone": getattr(emp, 'emergency_contact_work_phone', None),
                    "emergency_contact_home_phone": getattr(emp, 'emergency_contact_home_phone', None),
                    "emergency_contact_address": getattr(emp, 'emergency_contact_address', None),
                    "bonus_target": getattr(emp, 'bonus_target', None),
                    "stock_options": getattr(emp, 'stock_options', None),
                    "last_salary_increase": getattr(emp, 'last_salary_increase', None),
                    "next_review_date": str(emp.next_review_date) if getattr(emp, 'next_review_date', None) else None,
                    "personal_email": getattr(emp, 'personal_email', None),
                    "nationality": getattr(emp, 'nationality', None),
                    "religion": getattr(emp, 'religion', None),
                    "languages_known": getattr(emp, 'languages_known', None),
                    "hobbies": getattr(emp, 'hobbies', None),
                    "skills_summary": getattr(emp, 'skills_summary', None),
                    "certifications": getattr(emp, 'certifications', None),
                    "education_level": getattr(emp, 'education_level', None),
                    "university": getattr(emp, 'university', None),
                    "graduation_year": getattr(emp, 'graduation_year', None),
                    "currency_id": getattr(emp, 'currency_id', None),
                    "salary_in_words": getattr(emp, 'salary_in_words', None),
                    "created_at": emp.created_at.isoformat() if emp.created_at else None,
                    "updated_at": emp.updated_at.isoformat() if getattr(emp, 'updated_at', None) else None,
                    
                    # User table fields
                    "email": emp.user.email,
                    "title": getattr(emp.user, 'title', None),
                    "first_name": emp.user.first_name,
                    "last_name": emp.user.last_name,
                    "name": f"{emp.user.first_name} {emp.user.last_name}",
                    "phone": emp.user.phone,
                    "role": emp.user.role,
                    "status": getattr(emp.user, 'status', 'active'),
                    "is_profile_complete": getattr(emp.user, 'is_profile_complete', False),
                    "profile_picture": getattr(emp.user, 'profile_picture', None),
                    "temp_password": emp.user.temp_password if current_user.role == "admin" else None,
                    "user_created_at": emp.user.created_at.isoformat() if emp.user.created_at else None,
                    "user_updated_at": emp.user.updated_at.isoformat() if getattr(emp.user, 'updated_at', None) else None,
                    "last_login": str(emp.user.last_login) if getattr(emp.user, 'last_login', None) else None,
                    "active": getattr(emp.user, 'active', True),
                    
                    # Computed fields
                    "department": dept_name,
                    "manager": manager_name
                })
            except Exception as emp_error:
                print(f"Error processing employee {emp.id}: {str(emp_error)}")
                continue
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_employees: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get employees: {str(e)}")

@router.post("/")
def create_employee(
    request: EmployeeCreateRequestFixed,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new employee (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Generate secure temporary password
    from app.utils.temp_password import generate_temp_password
    from app.utils.email_service import email_service
    
    password_data = generate_temp_password(length=12, include_symbols=False)
    temp_password = password_data['temp_password']
    hashed_password = password_data['hashed_password']
    
    # Create user with temporary password
    user = User(
        title=request.user.title,
        first_name=request.user.first_name,
        last_name=request.user.last_name,
        email=request.user.email,
        phone=request.user.phone,
        role=request.user.role,
        status="active",
        hashed_password=hashed_password,
        temp_password=temp_password
    )
    db.add(user)
    db.flush()
    
    # Create employee
    hire_date = None
    if request.employee.hire_date:
        from datetime import datetime
        hire_date = datetime.strptime(request.employee.hire_date, '%Y-%m-%d').date()
    
    # Get position title from position_id if provided
    position_title = request.employee.position
    if request.employee.position_id:
        from app.models.position import Position
        position_obj = db.query(Position).filter(Position.id == request.employee.position_id).first()
        if position_obj:
            position_title = position_obj.title
    
    employee = Employee(
        user_id=user.id,
        employee_id=request.employee.employee_id,
        position=position_title,
        position_id=request.employee.position_id,
        department_id=request.employee.department_id,
        manager_id=request.employee.manager_id,
        employment_type=request.employee.employment_type,
        employment_status=request.employee.employment_status,
        hire_date=hire_date,
        salary=request.employee.salary,
        work_location=request.employee.work_location
    )
    
    # Set optional fields if they exist in the model
    if hasattr(employee, 'work_schedule'):
        employee.work_schedule = request.employee.work_schedule
    if hasattr(employee, 'work_type'):
        employee.work_type = request.employee.work_type
    
    try:
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        # Send temporary password email
        user_name = f"{user.first_name} {user.last_name}"
        email_sent = email_service.send_temp_password_email(
            to_email=user.email,
            temp_password=temp_password,
            user_name=user_name
        )
        
        return {
            "message": "Employee created successfully", 
            "id": employee.id,
            "email_sent": email_sent,
            "temp_password": temp_password if current_user.role == "admin" else None
        }
    except Exception as e:
        db.rollback()
        print(f"Error creating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create employee: {str(e)}")

@router.put("/{employee_id}")
def update_employee(
    employee_id: int,
    request: EmployeeCreateRequestFixed,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update employee (Admin/HR only)"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Update user
    user = employee.user
    user.title = request.user.title
    user.first_name = request.user.first_name
    user.last_name = request.user.last_name
    user.email = request.user.email
    user.phone = request.user.phone
    user.role = request.user.role
    
    # Set active field if provided
    if hasattr(user, 'active'):
        user.active = request.user.active
    
    # Update employee
    hire_date = None
    if request.employee.hire_date:
        from datetime import datetime
        hire_date = datetime.strptime(request.employee.hire_date, '%Y-%m-%d').date()
    
    # Get position title from position_id if provided
    position_title = request.employee.position
    if request.employee.position_id:
        from app.models.position import Position
        position_obj = db.query(Position).filter(Position.id == request.employee.position_id).first()
        if position_obj:
            position_title = position_obj.title
    
    employee.employee_id = request.employee.employee_id
    employee.position = position_title
    employee.position_id = request.employee.position_id
    employee.department_id = request.employee.department_id
    employee.manager_id = request.employee.manager_id
    employee.employment_type = request.employee.employment_type
    employee.employment_status = request.employee.employment_status
    employee.hire_date = hire_date
    employee.salary = request.employee.salary
    employee.work_location = request.employee.work_location
    
    # Set optional fields if they exist in the model
    if hasattr(employee, 'salary_in_words'):
        employee.salary_in_words = request.employee.salary_in_words
    
    # Set optional fields if they exist in the model
    if hasattr(employee, 'work_schedule'):
        employee.work_schedule = request.employee.work_schedule
    if hasattr(employee, 'work_type'):
        employee.work_type = request.employee.work_type
    
    try:
        db.commit()
        return {"message": "Employee updated successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update employee: {str(e)}")

@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete employee (Admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Delete employee and user
    user = employee.user
    db.delete(employee)
    db.delete(user)
    db.commit()
    
    return {"message": "Employee deleted successfully"}

@router.get("/generate-employee-id")
def generate_employee_id(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate next available employee ID"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get the highest employee ID number
    employees = db.query(Employee).all()
    max_num = 0
    
    for emp in employees:
        if emp.employee_id and emp.employee_id.startswith("EMP"):
            try:
                num = int(emp.employee_id[3:])  # Remove "EMP" prefix
                max_num = max(max_num, num)
            except ValueError:
                continue
    
    next_id = f"EMP{max_num + 1:03d}"  # Format as EMP001, EMP002, etc.
    return {"employee_id": next_id}

@router.post("/import")
def import_employees(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk import employees from CSV data"""
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employees_data = request.get('employees', [])
    if not employees_data:
        raise HTTPException(status_code=400, detail="No employee data provided")
    
    success_count = 0
    failed_count = 0
    errors = []
    
    for index, emp_data in enumerate(employees_data):
        try:
            # Generate secure temporary password
            from app.utils.temp_password import generate_temp_password
            password_data = generate_temp_password(length=12, include_symbols=False)
            temp_password = password_data['temp_password']
            hashed_password = password_data['hashed_password']
            
            # Check if email already exists
            existing_user = db.query(User).filter(User.email == emp_data.get('email')).first()
            if existing_user:
                errors.append({
                    "row": index + 1,
                    "field": "email",
                    "message": "Email already exists",
                    "data": emp_data
                })
                failed_count += 1
                continue
            
            # Create user
            user = User(
                title=emp_data.get('title'),
                first_name=emp_data.get('first_name'),
                last_name=emp_data.get('last_name'),
                email=emp_data.get('email'),
                phone=emp_data.get('phone'),
                role=emp_data.get('role', 'employee'),
                status="active",
                hashed_password=hashed_password,
                temp_password=temp_password
            )
            db.add(user)
            db.flush()
            
            # Find department by name
            department = None
            if emp_data.get('department'):
                department = db.query(Department).filter(Department.name == emp_data.get('department')).first()
            
            # Find position by title
            position = None
            if emp_data.get('position'):
                from app.models.position import Position
                position = db.query(Position).filter(Position.title == emp_data.get('position')).first()
            
            # Parse hire date
            hire_date = None
            if emp_data.get('hire_date'):
                from datetime import datetime
                try:
                    hire_date = datetime.strptime(emp_data.get('hire_date'), '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            # Create employee
            employee = Employee(
                user_id=user.id,
                employee_id=emp_data.get('employee_id'),
                position=emp_data.get('position'),
                position_id=position.id if position else None,
                department_id=department.id if department else None,
                employment_type=emp_data.get('employment_type'),
                employment_status=emp_data.get('employment_status', 'full_time'),
                hire_date=hire_date,
                salary=float(emp_data.get('salary', 0)) if emp_data.get('salary') else None,
                work_location=emp_data.get('work_location', 'office')
            )
            
            # Set optional fields
            if hasattr(employee, 'work_schedule'):
                employee.work_schedule = emp_data.get('work_schedule')
            if hasattr(employee, 'work_type'):
                employee.work_type = emp_data.get('work_type')
            
            db.add(employee)
            db.commit()
            success_count += 1
            
        except Exception as e:
            db.rollback()
            errors.append({
                "row": index + 1,
                "field": "general",
                "message": str(e),
                "data": emp_data
            })
            failed_count += 1
    
    return {
        "success": success_count,
        "failed": failed_count,
        "errors": errors
    }

@router.get("/departments")
def get_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all departments"""
    departments = db.query(Department).all()
    return [{"id": dept.id, "name": dept.name} for dept in departments]

@router.put("/me/profile-images")
def update_profile_images(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile images"""
    # Get the employee record for the current user
    employee_record = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    
    if not employee_record:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Update the profile images
    if request.avatar is not None:
        employee_record.avatar_url = request.avatar
    
    if request.coverImage is not None:
        employee_record.cover_image_url = request.coverImage
    
    if request.profileCrop is not None:
        import json
        employee_record.profile_crop = json.dumps(request.profileCrop)
    
    # Commit the changes
    db.commit()
    db.refresh(employee_record)
    
    return {
        "success": True,
        "message": "Profile images updated successfully",
        "data": {
            "avatar": employee_record.avatar_url,
            "coverImage": employee_record.cover_image_url
        }
    }

@router.get("/{employee_id}")
def get_employee_details(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed employee information"""
    try:
        if current_user.role not in ["admin", "hr"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        manager_name = None
        if hasattr(employee, 'manager') and employee.manager and hasattr(employee.manager, 'user') and employee.manager.user:
            manager_name = f"{employee.manager.user.first_name} {employee.manager.user.last_name}"
        
        department_name = "Unknown"
        if hasattr(employee, 'department') and employee.department:
            department_name = employee.department.name
        
        return {
            "id": employee.id,
            "user_id": employee.user_id,
            "employee_id": employee.employee_id,
            "name": f"{employee.user.first_name} {employee.user.last_name}",
            "email": employee.user.email,
            "phone": getattr(employee.user, 'phone', None),
            "position": getattr(employee, 'position', None),
            "department": department_name,
            "manager": manager_name,
            "salary": getattr(employee, 'salary', None),
            "salary_in_words": getattr(employee, 'salary_in_words', None),
            "currency_symbol": "PKR",
            "employment_type": getattr(employee, 'employment_type', None),
            "employment_status": getattr(employee, 'employment_status', None),
            "work_location": getattr(employee, 'work_location', None),
            "work_schedule": getattr(employee, 'work_schedule', None),
            "work_type": getattr(employee, 'work_type', None),
            "hire_date": str(employee.hire_date) if getattr(employee, 'hire_date', None) else None,
            "role": employee.user.role,
            "status": getattr(employee.user, 'status', 'active'),
            "active": getattr(employee.user, 'active', True),
            "avatar_url": getattr(employee, 'avatar_url', None),
            "personal_email": getattr(employee, 'personal_email', None),
            "gender": getattr(employee, 'gender', None),
            "date_of_birth": str(employee.date_of_birth) if getattr(employee, 'date_of_birth', None) else None,
            "marital_status": getattr(employee, 'marital_status', None),
            "blood_group": getattr(employee, 'blood_group', None),
            "nationality": getattr(employee, 'nationality', None),
            "religion": getattr(employee, 'religion', None),
            "address": getattr(employee, 'address', None),
            "office_address": getattr(employee, 'office_address', None),
            "qualification": getattr(employee, 'qualification', None),
            "university": getattr(employee, 'university', None),
            "graduation_year": getattr(employee, 'graduation_year', None),
            "bonus_target": getattr(employee, 'bonus_target', None),
            "stock_options": getattr(employee, 'stock_options', None),
            "last_salary_increase": getattr(employee, 'last_salary_increase', None),
            "emergency_contact_name": getattr(employee, 'emergency_contact_name', None),
            "emergency_contact_relationship": getattr(employee, 'emergency_contact_relationship', None),
            "emergency_contact_phone": getattr(employee, 'emergency_contact_phone', None),
            "emergency_contact_work_phone": getattr(employee, 'emergency_contact_work_phone', None),
            "emergency_contact_home_phone": getattr(employee, 'emergency_contact_home_phone', None),
            "emergency_contact_address": getattr(employee, 'emergency_contact_address', None),
            "skills_summary": getattr(employee, 'skills_summary', None),
            "certifications": getattr(employee, 'certifications', None),
            "languages_known": getattr(employee, 'languages_known', None),
            "hobbies": getattr(employee, 'hobbies', None),
            "team_size": getattr(employee, 'team_size', None)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee details: {str(e)}")