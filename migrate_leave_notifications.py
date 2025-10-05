#!/usr/bin/env python3

import sqlite3
import sys
import os

def migrate_database():
    """Add notification tracking columns to leaves table"""
    
    # Database path
    db_path = "hrm.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(leaves)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add notification_sent column if it doesn't exist
        if 'notification_sent' not in columns:
            cursor.execute("ALTER TABLE leaves ADD COLUMN notification_sent BOOLEAN DEFAULT 0")
            print("Added notification_sent column to leaves table")
        else:
            print("notification_sent column already exists")
        
        # Add admin_notified column if it doesn't exist
        if 'admin_notified' not in columns:
            cursor.execute("ALTER TABLE leaves ADD COLUMN admin_notified BOOLEAN DEFAULT 0")
            print("Added admin_notified column to leaves table")
        else:
            print("admin_notified column already exists")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)