from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeProfile
from app.models.sql_models import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.database import get_db
from app.db.sqlite import SQLiteService
from app.core.logger import logger
from app.core.security import sanitize_log_input

router = APIRouter()

@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Create a new employee."""
    # Check if user exists
    user = await SQLiteService.get_user_by_id(db, employee_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if employee already exists for this user
    existing_employee = await SQLiteService.get_employee_by_user_id(db, employee_data.user_id)
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee record already exists for this user"
        )
    
    # Check if employee ID is unique
    existing_emp_id = await SQLiteService.get_employee_by_employee_id(db, employee_data.employee_id)
    if existing_emp_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already exists"
        )
    
    # Create employee
    employee_dict = employee_data.dict()
    employee = await SQLiteService.create_employee(db, employee_dict)
    
    logger.info(f"Employee created: {sanitize_log_input(employee_data.employee_id)}")
    
    return EmployeeResponse(
        id=str(employee.id),
        user_id=employee.user_id,
        employee_id=employee.employee_id,
        department=employee.department,
        position=employee.position,
        position_level=employee.position_level,
        employment_status=employee.employment_status,
        hire_date=employee.hire_date,
        salary=employee.salary,
        manager_id=employee.manager_id,
        work_location=employee.work_location,
        work_schedule=employee.work_schedule,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    department: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of employees with pagination and filtering."""
    # Apply role-based filtering
    manager_id = None
    user_id = None
    
    if current_user.role == UserRole.TEAM_LEAD:
        manager_id = current_user.id
    elif current_user.role == UserRole.EMPLOYEE:
        # Employees can only see their own record
        user_id = current_user.id
    
    employees = await SQLiteService.get_employees(
        db, skip=skip, limit=limit, department=department, 
        manager_id=manager_id, user_id=user_id
    )
    
    return [EmployeeResponse(
        id=str(emp.id),
        user_id=emp.user_id,
        employee_id=emp.employee_id,
        department=emp.department,
        position=emp.position,
        position_level=emp.position_level,
        employment_status=emp.employment_status,
        hire_date=emp.hire_date,
        salary=emp.salary,
        manager_id=emp.manager_id,
        work_location=emp.work_location,
        work_schedule=emp.work_schedule,
        created_at=emp.created_at,
        updated_at=emp.updated_at
    ) for emp in employees]

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get employee by ID."""
    employee = await SQLiteService.get_employee_by_id(db, int(employee_id))
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE and 
        employee.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return EmployeeResponse(
        id=str(employee.id),
        user_id=employee.user_id,
        employee_id=employee.employee_id,
        department=employee.department,
        position=employee.position,
        position_level=employee.position_level,
        employment_status=employee.employment_status,
        hire_date=employee.hire_date,
        salary=employee.salary,
        manager_id=employee.manager_id,
        work_location=employee.work_location,
        work_schedule=employee.work_schedule,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    current_user = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Update employee information."""
    employee = await SQLiteService.get_employee_by_id(db, int(employee_id))
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Prepare update data
    update_data = {k: v for k, v in employee_data.dict().items() if v is not None}
    if update_data:
        updated_employee = await SQLiteService.update_employee(db, int(employee_id), update_data)
        
        logger.info(f"Employee updated: {sanitize_log_input(employee_id)}")
        
        return EmployeeResponse(
            id=str(updated_employee.id),
            user_id=updated_employee.user_id,
            employee_id=updated_employee.employee_id,
            department=updated_employee.department,
            position=updated_employee.position,
            position_level=updated_employee.position_level,
            employment_status=updated_employee.employment_status,
            hire_date=updated_employee.hire_date,
            salary=updated_employee.salary,
            manager_id=updated_employee.manager_id,
            work_location=updated_employee.work_location,
            work_schedule=updated_employee.work_schedule,
            created_at=updated_employee.created_at,
            updated_at=updated_employee.updated_at
        )
    
    return EmployeeResponse(
        id=str(employee.id),
        user_id=employee.user_id,
        employee_id=employee.employee_id,
        department=employee.department,
        position=employee.position,
        position_level=employee.position_level,
        employment_status=employee.employment_status,
        hire_date=employee.hire_date,
        salary=employee.salary,
        manager_id=employee.manager_id,
        work_location=employee.work_location,
        work_schedule=employee.work_schedule,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    current_user = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """Delete employee record."""
    success = await SQLiteService.delete_employee(db, int(employee_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    logger.info(f"Employee deleted: {sanitize_log_input(employee_id)}")
    
    return {"message": "Employee deleted successfully"}

@router.get("/profile/{user_id}", response_model=EmployeeProfile)
async def get_employee_profile(
    user_id: str,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get complete employee profile."""
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE and 
        int(user_id) != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    employee = await SQLiteService.get_employee_by_user_id(db, int(user_id))
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get user information
    user = await SQLiteService.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create profile response
    return EmployeeProfile(
        id=str(employee.id),
        user_id=employee.user_id,
        employee_id=employee.employee_id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        profile_picture=user.profile_picture,
        department=employee.department,
        position=employee.position,
        position_level=employee.position_level,
        employment_status=employee.employment_status,
        hire_date=employee.hire_date,
        salary=employee.salary,
        manager_id=employee.manager_id,
        work_location=employee.work_location,
        work_schedule=employee.work_schedule,
        date_of_birth=employee.date_of_birth,
        gender=employee.gender,
        marital_status=employee.marital_status,
        nationality=employee.nationality,
        address=employee.address,
        emergency_contact_name=employee.emergency_contact_name,
        emergency_contact_phone=employee.emergency_contact_phone,
        emergency_contact_relationship=employee.emergency_contact_relationship,
        skills=employee.skills,
        certifications=employee.certifications,
        education=employee.education,
        work_experience=employee.work_experience,
        created_at=employee.created_at,
        updated_at=employee.updated_at
    )
