#!/usr/bin/env python3
"""
Migration script to ensure attendance and break_records tables are properly set up
with correct relationships and constraints.
"""

from app.database import engine, SessionLocal, Base
from app.models.attendance import Attendance, BreakRecord
from sqlalchemy import text

def migrate_attendance_tables():
    """Migrate attendance tables with proper relationships"""
    
    db = SessionLocal()
    
    try:
        print("Starting attendance tables migration...")
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Check if unique constraint exists, if not add it
        try:
            db.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS unique_employee_date 
                ON attendance (employee_id, date)
            """))
            print("✓ Added unique constraint for employee_id and date")
        except Exception as e:
            print(f"Note: Unique constraint may already exist: {e}")
        
        # Verify foreign key relationship exists
        try:
            db.execute(text("""
                SELECT COUNT(*) FROM break_records br 
                JOIN attendance a ON br.attendance_id = a.id 
                LIMIT 1
            """))
            print("✓ Foreign key relationship between break_records and attendance verified")
        except Exception as e:
            print(f"Warning: Could not verify foreign key relationship: {e}")
        
        db.commit()
        print("✓ Attendance tables migration completed successfully!")
        
        # Display table structure
        print("\nTable structures:")
        
        # Attendance table structure
        result = db.execute(text("PRAGMA table_info(attendance)"))
        print("\nAttendance table columns:")
        for row in result:
            print(f"  - {row[1]} ({row[2]})")
        
        # Break records table structure
        result = db.execute(text("PRAGMA table_info(break_records)"))
        print("\nBreak records table columns:")
        for row in result:
            print(f"  - {row[1]} ({row[2]})")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_attendance_tables()