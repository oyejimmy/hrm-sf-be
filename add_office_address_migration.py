#!/usr/bin/env python3

import sqlite3
import os

def add_office_address_column():
    """Add office_address column to employees table"""
    
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), 'hrm.db')
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'office_address' not in columns:
            # Add office_address column
            cursor.execute("""
                ALTER TABLE employees 
                ADD COLUMN office_address TEXT
            """)
            
            print("Successfully added office_address column to employees table")
        else:
            print("office_address column already exists in employees table")
        
        # Commit changes
        conn.commit()
        
    except Exception as e:
        print(f"Error adding office_address column: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_office_address_column()