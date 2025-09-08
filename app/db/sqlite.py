from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.database import get_db
from app.models.sql_models import *
from app.core.logger import logger

class SQLiteService:
    """Service class for SQLite database operations."""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user_last_login(db: AsyncSession, user_id: int) -> None:
        """Update user's last login timestamp."""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await db.commit()
    
    @staticmethod
    async def create_employee(db: AsyncSession, employee_data: dict) -> Employee:
        """Create a new employee."""
        employee = Employee(**employee_data)
        db.add(employee)
        await db.commit()
        await db.refresh(employee)
        return employee
    
    @staticmethod
    async def get_employee_by_user_id(db: AsyncSession, user_id: int) -> Optional[Employee]:
        """Get employee by user ID."""
        result = await db.execute(
            select(Employee)
            .options(selectinload(Employee.user))
            .where(Employee.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_employee_by_id(db: AsyncSession, employee_id: int) -> Optional[Employee]:
        """Get employee by ID."""
        result = await db.execute(
            select(Employee)
            .options(selectinload(Employee.user))
            .where(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_employee_by_employee_id(db: AsyncSession, employee_id: str) -> Optional[Employee]:
        """Get employee by employee ID string."""
        result = await db.execute(
            select(Employee).where(Employee.employee_id == employee_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_employees(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 20, 
        department: Optional[str] = None,
        manager_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> List[Employee]:
        """Get employees with filtering and pagination."""
        query = select(Employee).options(selectinload(Employee.user))
        
        if department:
            query = query.where(Employee.department == department)
        if manager_id:
            query = query.where(Employee.manager_id == manager_id)
        if user_id:
            query = query.where(Employee.user_id == user_id)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_employee(db: AsyncSession, employee_id: int, update_data: dict) -> Optional[Employee]:
        """Update employee information."""
        update_data['updated_at'] = datetime.utcnow()
        await db.execute(
            update(Employee)
            .where(Employee.id == employee_id)
            .values(**update_data)
        )
        await db.commit()
        return await SQLiteService.get_employee_by_id(db, employee_id)
    
    @staticmethod
    async def delete_employee(db: AsyncSession, employee_id: int) -> bool:
        """Delete employee."""
        result = await db.execute(
            delete(Employee).where(Employee.id == employee_id)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def create_attendance(db: AsyncSession, attendance_data: dict) -> Attendance:
        """Create attendance record."""
        attendance = Attendance(**attendance_data)
        db.add(attendance)
        await db.commit()
        await db.refresh(attendance)
        return attendance
    
    @staticmethod
    async def get_attendance_by_user_date(db: AsyncSession, user_id: int, date: date) -> Optional[Attendance]:
        """Get attendance by user and date."""
        result = await db.execute(
            select(Attendance).where(
                and_(Attendance.user_id == user_id, Attendance.date == date)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_attendance(
        db: AsyncSession, 
        user_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Attendance]:
        """Get user attendance records."""
        query = select(Attendance).where(Attendance.user_id == user_id)
        
        if start_date:
            query = query.where(Attendance.date >= start_date)
        if end_date:
            query = query.where(Attendance.date <= end_date)
        
        query = query.order_by(Attendance.date.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_attendance(db: AsyncSession, attendance_id: int, update_data: dict) -> Optional[Attendance]:
        """Update attendance record."""
        update_data['updated_at'] = datetime.utcnow()
        await db.execute(
            update(Attendance)
            .where(Attendance.id == attendance_id)
            .values(**update_data)
        )
        await db.commit()
        
        result = await db.execute(select(Attendance).where(Attendance.id == attendance_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_leave_request(db: AsyncSession, leave_data: dict) -> LeaveRequest:
        """Create leave request."""
        leave_request = LeaveRequest(**leave_data)
        db.add(leave_request)
        await db.commit()
        await db.refresh(leave_request)
        return leave_request
    
    @staticmethod
    async def get_leave_request_by_id(db: AsyncSession, request_id: int) -> Optional[LeaveRequest]:
        """Get leave request by ID."""
        result = await db.execute(
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.user))
            .where(LeaveRequest.id == request_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_leave_requests(
        db: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[LeaveRequest]:
        """Get user's leave requests."""
        result = await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.user_id == user_id)
            .order_by(LeaveRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_pending_leave_requests(db: AsyncSession, skip: int = 0, limit: int = 20) -> List[LeaveRequest]:
        """Get pending leave requests."""
        result = await db.execute(
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.user))
            .where(LeaveRequest.status == LeaveStatus.PENDING)
            .order_by(LeaveRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_leave_request(db: AsyncSession, request_id: int, update_data: dict) -> Optional[LeaveRequest]:
        """Update leave request."""
        update_data['updated_at'] = datetime.utcnow()
        await db.execute(
            update(LeaveRequest)
            .where(LeaveRequest.id == request_id)
            .values(**update_data)
        )
        await db.commit()
        return await SQLiteService.get_leave_request_by_id(db, request_id)
    
    @staticmethod
    async def get_today_attendance(
        db: AsyncSession, 
        today: date, 
        user_ids: Optional[List[int]] = None
    ) -> List[Attendance]:
        """Get today's attendance records."""
        query = select(Attendance).where(Attendance.date == today)
        
        if user_ids:
            query = query.where(Attendance.user_id.in_(user_ids))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_team_members_by_manager(db: AsyncSession, manager_id: int) -> List[Employee]:
        """Get team members by manager ID."""
        result = await db.execute(
            select(Employee).where(Employee.manager_id == manager_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_attendance_summary(
        db: AsyncSession, 
        user_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[Attendance]:
        """Get attendance records for summary calculation."""
        result = await db.execute(
            select(Attendance)
            .where(
                and_(
                    Attendance.user_id == user_id,
                    Attendance.date >= start_date,
                    Attendance.date < end_date
                )
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_approved_leave_requests_for_year(
        db: AsyncSession, 
        user_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[LeaveRequest]:
        """Get approved leave requests for a specific year."""
        result = await db.execute(
            select(LeaveRequest)
            .where(
                and_(
                    LeaveRequest.user_id == user_id,
                    LeaveRequest.status == LeaveStatus.APPROVED,
                    LeaveRequest.start_date >= start_date,
                    LeaveRequest.end_date <= end_date
                )
            )
        )
        return result.scalars().all()