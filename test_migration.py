#!/usr/bin/env python3
"""
Test script to verify the MongoDB to SQLite migration.
"""

import asyncio
import sys
from datetime import datetime, date
from app.database import create_tables, AsyncSessionLocal
from app.db.sqlite import SQLiteService
from app.core.security import get_password_hash
from app.models.sql_models import UserRole, UserStatus, Department, EmploymentStatus, PositionLevel

async def test_database_operations():
    """Test basic database operations."""
    print("Testing database operations...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Test user creation
            print("1. Testing user creation...")
            user_data = {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "role": UserRole.EMPLOYEE,
                "status": UserStatus.ACTIVE,
                "password_hash": get_password_hash("test123")
            }
            
            user = await SQLiteService.create_user(db, user_data)
            print(f"   ✓ User created with ID: {user.id}")
            
            # Test user retrieval
            print("2. Testing user retrieval...")
            retrieved_user = await SQLiteService.get_user_by_email(db, "test@example.com")
            if retrieved_user:
                print(f"   ✓ User retrieved: {retrieved_user.first_name} {retrieved_user.last_name}")
            else:
                print("   ✗ User retrieval failed")
                return False
            
            # Test employee creation
            print("3. Testing employee creation...")
            employee_data = {
                "user_id": user.id,
                "employee_id": "EMP001",
                "department": Department.INFORMATION_TECHNOLOGY,
                "position": "Software Developer",
                "position_level": PositionLevel.MID_LEVEL,
                "employment_status": EmploymentStatus.FULL_TIME,
                "hire_date": date.today(),
                "salary": 75000.0
            }
            
            employee = await SQLiteService.create_employee(db, employee_data)
            print(f"   ✓ Employee created with ID: {employee.id}")
            
            # Test attendance creation
            print("4. Testing attendance creation...")
            attendance_data = {
                "user_id": user.id,
                "date": date.today(),
                "check_in": datetime.now().time(),
                "status": "present",
                "work_hours": 8.0
            }
            
            attendance = await SQLiteService.create_attendance(db, attendance_data)
            print(f"   ✓ Attendance created with ID: {attendance.id}")
            
            # Test leave request creation
            print("5. Testing leave request creation...")
            leave_data = {
                "user_id": user.id,
                "leave_type": "annual_leave",
                "start_date": date.today(),
                "end_date": date.today(),
                "reason": "Personal reasons"
            }
            
            leave_request = await SQLiteService.create_leave_request(db, leave_data)
            print(f"   ✓ Leave request created with ID: {leave_request.id}")
            
            print("\n✓ All database operations completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n✗ Database operation failed: {e}")
            return False

async def main():
    """Main test function."""
    print("HRM System Migration Test")
    print("=" * 30)
    
    try:
        # Initialize database
        print("Initializing database...")
        await create_tables()
        print("✓ Database tables created")
        
        # Test operations
        success = await test_database_operations()
        
        if success:
            print("\n🎉 Migration test completed successfully!")
            print("The SQLite database is working correctly.")
        else:
            print("\n❌ Migration test failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())