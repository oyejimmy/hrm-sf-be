#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def fix_profile_columns():
    """Add any missing profile columns"""
    
    print("Adding missing profile columns...")
    
    # Check and add missing columns to employees table
    missing_columns = [
        "personal_email VARCHAR",
        "nationality VARCHAR", 
        "religion VARCHAR",
        "languages_known VARCHAR",
        "hobbies VARCHAR",
        "skills_summary TEXT",
        "certifications VARCHAR",
        "education_level VARCHAR",
        "university VARCHAR",
        "graduation_year INTEGER"
    ]
    
    for column in missing_columns:
        try:
            db.execute(text(f"ALTER TABLE employees ADD COLUMN {column}"))
            print(f"Added: {column.split()[0]}")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print(f"Exists: {column.split()[0]}")
            else:
                print(f"Error: {column.split()[0]} - {e}")
    
    db.commit()
    print("Profile columns check completed!")

if __name__ == "__main__":
    fix_profile_columns()
    db.close()