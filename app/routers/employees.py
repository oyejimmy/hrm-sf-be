from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeProfile
from app.models.user import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.logger import logger

router = APIRouter()

@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """Create a new employee."""
    db = get_database()
    
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(employee_data.user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if employee already exists for this user
    existing_employee = await db.employees.find_one({"user_id": employee_data.user_id})
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee record already exists for this user"
        )
    
    # Check if employee ID is unique
    existing_emp_id = await db.employees.find_one({"employee_id": employee_data.employee_id})
    if existing_emp_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already exists"
        )
    
    # Create employee document
    employee_doc = {
        **employee_data.dict(),
        "employment_status": employee_data.employment_status.value,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.employees.insert_one(employee_doc)
    employee_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Employee created: {employee_data.employee_id}")
    
    return EmployeeResponse(**employee_doc)

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get list of employees with pagination and filtering."""
    db = get_database()
    
    # Build filter
    filter_dict = {}
    if department:
        filter_dict["department"] = department
    
    # Apply role-based filtering
    if current_user["role"] == UserRole.TEAM_LEAD:
        filter_dict["manager_id"] = str(current_user["_id"])
    elif current_user["role"] == UserRole.EMPLOYEE:
        # Employees can only see their own record
        filter_dict["user_id"] = str(current_user["_id"])
    
    cursor = db.employees.find(filter_dict).skip(skip).limit(limit)
    employees = await cursor.to_list(length=limit)
    
    return [EmployeeResponse(**emp) for emp in employees]

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get employee by ID."""
    db = get_database()
    
    employee = await db.employees.find_one({"_id": ObjectId(employee_id)})
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check permissions
    if (current_user["role"] == UserRole.EMPLOYEE and 
        employee["user_id"] != str(current_user["_id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return EmployeeResponse(**employee)

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """Update employee information."""
    db = get_database()
    
    employee = await db.employees.find_one({"_id": ObjectId(employee_id)})
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Prepare update data
    update_data = {k: v for k, v in employee_data.dict().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        await db.employees.update_one(
            {"_id": ObjectId(employee_id)},
            {"$set": update_data}
        )
        
        # Get updated employee
        updated_employee = await db.employees.find_one({"_id": ObjectId(employee_id)})
        
        logger.info(f"Employee updated: {employee_id}")
        
        return EmployeeResponse(**updated_employee)
    
    return EmployeeResponse(**employee)

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """Delete employee record."""
    db = get_database()
    
    result = await db.employees.delete_one({"_id": ObjectId(employee_id)})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    logger.info(f"Employee deleted: {employee_id}")
    
    return {"message": "Employee deleted successfully"}

@router.get("/profile/{user_id}", response_model=EmployeeProfile)
async def get_employee_profile(
    user_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get complete employee profile."""
    db = get_database()
    
    # Check permissions
    if (current_user["role"] == UserRole.EMPLOYEE and 
        user_id != str(current_user["_id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    employee = await db.employees.find_one({"user_id": user_id})
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get user information
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Combine employee and user data
    profile_data = {
        **employee,
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
        "phone": user.get("phone"),
        "profile_picture": user.get("profile_picture")
    }
    
    return EmployeeProfile(**profile_data)
