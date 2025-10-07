#!/usr/bin/env python3

import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('hrm.db')
        cursor = conn.cursor()
        
        # Check if leave_balances table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leave_balances';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("leave_balances table exists")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM leave_balances;")
            count = cursor.fetchone()[0]
            print(f"Total leave balance records: {count}")
            
            # Show sample data
            cursor.execute("SELECT employee_id, leave_type, total_allocated, remaining FROM leave_balances LIMIT 5;")
            results = cursor.fetchall()
            
            print("\nSample leave balance data:")
            for row in results:
                print(f"Employee ID: {row[0]}, Type: {row[1]}, Allocated: {row[2]}, Remaining: {row[3]}")
        else:
            print("leave_balances table does not exist")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()