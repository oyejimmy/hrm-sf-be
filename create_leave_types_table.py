#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Direct database connection
DATABASE_URL = "sqlite:///./hrm.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_leave_types_table():
    db = SessionLocal()
    try:
        # Create leave_types table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS leave_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR UNIQUE NOT NULL,
                description TEXT,
                default_allocation FLOAT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Insert default leave types
        default_types = [
            ('Annual', 'Annual vacation leave', 20.0, 1),
            ('Sick', 'Medical leave for illness', 10.0, 1),
            ('Casual', 'Casual personal leave', 12.0, 1),
            ('Maternity', 'Maternity leave for mothers', 180.0, 1),
            ('Paternity', 'Paternity leave for fathers', 10.0, 1)
        ]
        
        for name, desc, allocation, created_by in default_types:
            # Check if exists
            existing = db.execute(text(
                "SELECT id FROM leave_types WHERE name = :name"
            ), {"name": name}).fetchone()
            
            if not existing:
                db.execute(text("""
                    INSERT INTO leave_types (name, description, default_allocation, created_by)
                    VALUES (:name, :description, :default_allocation, :created_by)
                """), {
                    "name": name,
                    "description": desc,
                    "default_allocation": allocation,
                    "created_by": created_by
                })
                print(f"Added leave type: {name}")
        
        db.commit()
        print("Leave types table created and populated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_leave_types_table()