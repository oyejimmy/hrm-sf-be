#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def add_missing_fields():
    """Add any missing fields needed for profile editing"""
    
    print("Checking for missing fields...")
    
    # Check if we need to add any additional fields
    # Most fields are already added, but let's ensure we have everything
    
    # Add any missing user fields
    user_columns = [
        "profile_picture VARCHAR"  # For avatar storage
    ]
    
    for column in user_columns:
        try:
            db.execute(text(f"ALTER TABLE users ADD COLUMN {column}"))
            print(f"Added to users: {column.split()[0]}")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print(f"Users field exists: {column.split()[0]}")
            else:
                print(f"Error adding to users {column.split()[0]}: {e}")
    
    db.commit()
    print("Missing fields check completed!")

if __name__ == "__main__":
    add_missing_fields()
    db.close()