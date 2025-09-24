import sqlite3
from datetime import date

def add_basic_data():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    try:
        # Check current table structure
        cursor.execute("PRAGMA table_info(attendance)")
        attendance_columns = [row[1] for row in cursor.fetchall()]
        print(f"Attendance columns: {attendance_columns}")
        
        cursor.execute("PRAGMA table_info(leaves)")
        leaves_columns = [row[1] for row in cursor.fetchall()]
        print(f"Leaves columns: {leaves_columns}")
        
        # Add basic leave data
        cursor.execute("""
            INSERT OR IGNORE INTO leaves 
            (employee_id, leave_type, start_date, end_date, days_requested, reason, status)
            VALUES 
            (3, 'annual', '2025-01-15', '2025-01-17', 3.0, 'Family vacation', 'approved'),
            (3, 'sick', '2025-01-10', '2025-01-10', 0.5, 'Medical appointment', 'approved')
        """)
        
        # Add basic attendance data (using only existing columns)
        if 'date' in attendance_columns and 'employee_id' in attendance_columns:
            cursor.execute("""
                INSERT OR IGNORE INTO attendance 
                (employee_id, date, status)
                VALUES 
                (3, '2025-01-13', 'present'),
                (3, '2025-01-14', 'present'),
                (3, '2025-01-15', 'on_leave')
            """)
        
        # Check if leave_balances table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leave_balances'")
        if cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO leave_balances 
                (employee_id, leave_type, year, total_allocated, taken, remaining)
                VALUES 
                (3, 'annual', 2025, 20.0, 3.0, 17.0),
                (3, 'sick', 2025, 10.0, 0.5, 9.5),
                (3, 'casual', 2025, 5.0, 0.0, 5.0)
            """)
        
        conn.commit()
        print("Basic data added successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_basic_data()