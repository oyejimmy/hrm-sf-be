#!/usr/bin/env python3

import sqlite3
import os

def fix_notifications():
    db_path = "hrm.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update all notifications with invalid extra_data to NULL
        cursor.execute("UPDATE notifications SET extra_data = NULL WHERE extra_data IS NOT NULL AND extra_data != 'null'")
        
        conn.commit()
        print("Fixed notifications extra_data field")
        return True
        
    except Exception as e:
        print(f"Fix failed: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_notifications()