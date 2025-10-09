import sqlite3
from datetime import date

def add_test_attendance():
    try:
        conn = sqlite3.connect('hrm.db')
        cursor = conn.cursor()
        
        print("=== ADDING TEST ATTENDANCE FOR ADMIN ===")
        
        # Add attendance record for admin user (ID=1)
        admin_attendance = [
            (1, str(date.today()), "09:00:00", "17:30:00", "present", "8:30", "Test attendance for admin"),
            (1, "2025-10-06", "09:15:00", "17:45:00", "late", "8:30", "Late arrival"),
        ]
        
        for emp_id, att_date, check_in, check_out, status, hours, notes in admin_attendance:
            # Check if record already exists
            cursor.execute("""
                SELECT id FROM attendance 
                WHERE employee_id = ? AND date = ?
            """, (emp_id, att_date))
            
            existing = cursor.fetchone()
            if not existing:
                cursor.execute("""
                    INSERT INTO attendance (employee_id, date, check_in, check_out, status, hours_worked, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (emp_id, att_date, check_in, check_out, status, hours, notes))
                print(f"Added attendance record for employee {emp_id} on {att_date}")
            else:
                print(f"Attendance record already exists for employee {emp_id} on {att_date}")
        
        conn.commit()
        
        # Verify the records were added
        cursor.execute("""
            SELECT a.id, a.employee_id, u.email, a.date, a.status
            FROM attendance a
            LEFT JOIN users u ON a.employee_id = u.id
            ORDER BY a.date DESC;
        """)
        all_records = cursor.fetchall()
        
        print(f"\nAll attendance records after addition:")
        for att_id, emp_id, email, att_date, status in all_records:
            print(f"  - ID: {att_id}, Employee: {emp_id} ({email}), Date: {att_date}, Status: {status}")
        
        conn.close()
        print(f"\n[OK] Test attendance records added successfully")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    add_test_attendance()