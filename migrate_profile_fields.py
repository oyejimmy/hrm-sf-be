#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def add_profile_columns():
    """Add new profile columns to employees table"""
    
    columns_to_add = [
        "blood_group VARCHAR",
        "qualification VARCHAR",
        "work_schedule VARCHAR DEFAULT 'Standard (9:00 AM - 6:00 PM)'",
        "team_size INTEGER DEFAULT 0",
        "avatar_url VARCHAR",
        "cover_image_url VARCHAR",
        "emergency_contact_relationship VARCHAR",
        "emergency_contact_work_phone VARCHAR",
        "emergency_contact_home_phone VARCHAR",
        "emergency_contact_address TEXT",
        "bonus_target VARCHAR",
        "stock_options VARCHAR",
        "last_salary_increase VARCHAR",
        "next_review_date VARCHAR"
    ]
    
    print("Adding new profile columns to employees table...")
    
    for column in columns_to_add:
        try:
            db.execute(text(f"ALTER TABLE employees ADD COLUMN {column}"))
            print(f"Added column: {column.split()[0]}")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print(f"- Column {column.split()[0]} already exists")
            else:
                print(f"Error adding {column.split()[0]}: {e}")
    
    db.commit()
    print("Profile columns migration completed!")

if __name__ == "__main__":
    add_profile_columns()
    db.close()