import sqlite3

def check_user_ids():
    try:
        conn = sqlite3.connect('hrm.db')
        cursor = conn.cursor()
        
        print("=== USER AND ATTENDANCE ANALYSIS ===")
        
        # Get all users
        cursor.execute("SELECT id, email, role FROM users;")
        users = cursor.fetchall()
        
        print(f"\nUsers in database:")
        for user_id, email, role in users:
            print(f"  - ID: {user_id}, Email: {email}, Role: {role}")
        
        # Get attendance records with user info
        cursor.execute("""
            SELECT a.id, a.employee_id, u.email, u.role, a.date, a.status
            FROM attendance a
            LEFT JOIN users u ON a.employee_id = u.id
            ORDER BY a.date DESC;
        """)
        attendance_records = cursor.fetchall()
        
        print(f"\nAttendance records:")
        for att_id, emp_id, email, role, date, status in attendance_records:
            print(f"  - Attendance ID: {att_id}, Employee ID: {emp_id}, Email: {email}, Role: {role}, Date: {date}, Status: {status}")
        
        conn.close()
        print(f"\n[OK] Analysis completed")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    check_user_ids()