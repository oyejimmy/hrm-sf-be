#!/usr/bin/env python3
"""
Migration script to add temp_password column to users table
"""

import sqlite3
import os
from pathlib import Path

def add_temp_password_column():
    """Add temp_password column to users table"""
    
    # Get database path
    db_path = Path(__file__).parent / "hrm.db"
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'temp_password' in columns:
            print("temp_password column already exists in users table")
            conn.close()
            return True
        
        # Add temp_password column
        cursor.execute("ALTER TABLE users ADD COLUMN temp_password TEXT")
        
        # Set default temp password for existing users (only for employees)
        cursor.execute("""
            UPDATE users 
            SET temp_password = 'employee123' 
            WHERE role = 'employee' AND temp_password IS NULL
        """)
        
        conn.commit()
        print("Successfully added temp_password column to users table")
        print("Set default temp_password for existing employees")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error adding temp_password column: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    success = add_temp_password_column()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")