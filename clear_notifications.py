#!/usr/bin/env python3

import sqlite3
import os

def clear_notifications():
    db_path = "hrm.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Delete all notifications
        cursor.execute("DELETE FROM notifications")
        
        conn.commit()
        print("Cleared all notifications")
        return True
        
    except Exception as e:
        print(f"Clear failed: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    clear_notifications()