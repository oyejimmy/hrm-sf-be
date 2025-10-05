#!/usr/bin/env python3
"""
Create a test user for attendance system testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.auth import get_password_hash

def create_test_user():
    """Create a test user for attendance testing"""
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "test@hrm.com").first()
        if existing_user:
            print("Test user already exists!")
            print(f"Email: {existing_user.email}")
            print(f"Role: {existing_user.role}")
            return existing_user.email
        
        # Create new test user
        test_user = User(
            email="test@hrm.com",
            hashed_password=get_password_hash("test123"),
            first_name="Test",
            last_name="Employee",
            role="employee",
            status="active",
            is_profile_complete=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("Test user created successfully!")
        print(f"Email: {test_user.email}")
        print(f"Password: test123")
        print(f"Role: {test_user.role}")
        
        return test_user.email
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()