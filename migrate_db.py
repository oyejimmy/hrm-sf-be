import sqlite3
import os

def migrate_database():
    """Add missing columns to existing database"""
    db_path = "hrm.db"
    
    if not os.path.exists(db_path):
        print("Database file not found. Please run init_db.py first.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if work_type column exists
        cursor.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns if they don't exist
        if 'work_type' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN work_type TEXT DEFAULT 'office'")
            print("Added work_type column")
        
        if 'work_schedule' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN work_schedule TEXT DEFAULT 'Standard (9:00 AM - 6:00 PM)'")
            print("Added work_schedule column")
        
        if 'employment_status' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN employment_status TEXT DEFAULT 'full_time'")
            print("Added employment_status column")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()