#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Direct database connection
DATABASE_URL = "sqlite:///./hrm.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_leave_balances():
    db = SessionLocal()
    try:
        # Get current year
        current_year = datetime.now().year
        
        # Get all users using raw SQL to avoid model relationship issues
        users_result = db.execute(text("SELECT id, email FROM users"))
        users = users_result.fetchall()
        
        # Standard leave allocations
        leave_types = {
            'Annual': 20,
            'Sick': 10,
            'Casual': 12,
            'Maternity': 180,
            'Paternity': 10
        }
        
        for user in users:
            user_id, email = user
            print(f"Creating leave balances for user: {email}")
            
            for leave_type, allocation in leave_types.items():
                # Check if balance already exists
                existing = db.execute(text(
                    "SELECT id FROM leave_balances WHERE employee_id = :user_id AND leave_type = :leave_type AND year = :year"
                ), {"user_id": user_id, "leave_type": leave_type, "year": current_year}).fetchone()
                
                if not existing:
                    # Insert new leave balance
                    db.execute(text(
                        "INSERT INTO leave_balances (employee_id, leave_type, year, total_allocated, taken, remaining, carried_forward, created_at) VALUES (:employee_id, :leave_type, :year, :total_allocated, :taken, :remaining, :carried_forward, :created_at)"
                    ), {
                        "employee_id": user_id,
                        "leave_type": leave_type,
                        "year": current_year,
                        "total_allocated": allocation,
                        "taken": 0.0,
                        "remaining": allocation,
                        "carried_forward": 0.0,
                        "created_at": datetime.now()
                    })
                    print(f"  - Added {leave_type}: {allocation} days")
                else:
                    print(f"  - {leave_type} balance already exists")
        
        db.commit()
        print("Leave balances initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing leave balances: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_leave_balances()