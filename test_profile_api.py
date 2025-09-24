#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def test_profile_api():
    """Test profile API endpoints and database schema"""
    
    print("Testing profile API and database schema...")
    
    # Test database schema
    print("\n1. Testing database schema...")
    
    # Check users table
    try:
        result = db.execute(text("SELECT first_name, last_name, email, phone FROM users LIMIT 1"))
        user = result.fetchone()
        print(f"Users table OK: {user}")
    except Exception as e:
        print(f"Users table error: {e}")
    
    # Check employees table with new fields
    try:
        result = db.execute(text("""
            SELECT employee_id, position, blood_group, qualification, 
                   emergency_contact_name, bonus_target, personal_email, nationality
            FROM employees LIMIT 1
        """))
        employee = result.fetchone()
        print(f"Employees table OK: {employee}")
    except Exception as e:
        print(f"Employees table error: {e}")
    
    # Check skills table
    try:
        result = db.execute(text("SELECT skill_name, proficiency_level FROM employee_skills LIMIT 1"))
        skill = result.fetchone()
        print(f"Skills table OK: {skill}")
    except Exception as e:
        print(f"Skills table error: {e}")
    
    # Test data counts
    print("\n2. Testing data counts...")
    tables = ["users", "employees", "employee_skills", "departments"]
    for table in tables:
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            print(f"{table}: {count} records")
        except Exception as e:
            print(f"{table}: Error - {e}")
    
    print("\nProfile API test completed!")

if __name__ == "__main__":
    test_profile_api()
    db.close()