import sqlite3
from datetime import date, datetime, timedelta
from app.auth import get_password_hash

def populate_existing_database():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    try:
        # Add team lead user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'teamlead@hrm.com'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO users (email, hashed_password, first_name, last_name, phone, role, is_profile_complete, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('teamlead@hrm.com', get_password_hash('lead123'), 'Jane', 'Smith', '+1234567893', 'team_lead', True, 'active'))
            
            user_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO employees (user_id, employee_id, department_id, position, employment_status, hire_date, work_location, salary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 'EMP0004', 2, 'Team Lead', 'full_time', '2024-01-15', 'office', 75000))
        
        # Add another employee if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'emp2@hrm.com'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO users (email, hashed_password, first_name, last_name, phone, role, is_profile_complete, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('emp2@hrm.com', get_password_hash('emp123'), 'Alice', 'Johnson', '+1234567894', 'employee', True, 'active'))
            
            user_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO employees (user_id, employee_id, department_id, position, employment_status, hire_date, work_location, salary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 'EMP0005', 2, 'Junior Developer', 'full_time', '2024-03-01', 'office', 45000))
        
        # Clear and repopulate leave balances
        cursor.execute("DELETE FROM leave_balances")
        leave_balances = []
        for emp_id in [1, 2, 3, 4, 5]:
            leave_balances.extend([
                (emp_id, 'annual', 2025, 20.0, 0.0, 20.0, 0.0),
                (emp_id, 'sick', 2025, 10.0, 0.0, 10.0, 0.0),
                (emp_id, 'casual', 2025, 5.0, 0.0, 5.0, 0.0)
            ])
        cursor.executemany('INSERT INTO leave_balances (employee_id, leave_type, year, total_allocated, taken, remaining, carried_forward) VALUES (?, ?, ?, ?, ?, ?, ?)', leave_balances)
        
        # Add more leave records
        today = date.today()
        cursor.execute("DELETE FROM leaves WHERE employee_id IN (4, 5)")
        new_leaves = [
            (4, 'annual', 'full_day', today + timedelta(days=15), today + timedelta(days=19), 5.0, 'Vacation', 'approved', 1),
            (5, 'casual', 'full_day', today + timedelta(days=5), today + timedelta(days=5), 1.0, 'Personal work', 'pending', None)
        ]
        cursor.executemany('INSERT INTO leaves (employee_id, leave_type, duration_type, start_date, end_date, days_requested, reason, status, approved_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', new_leaves)
        
        # Update leave balances
        cursor.execute('UPDATE leave_balances SET taken = 3.0, remaining = 17.0 WHERE employee_id = 3 AND leave_type = "annual"')
        cursor.execute('UPDATE leave_balances SET taken = 0.5, remaining = 9.5 WHERE employee_id = 3 AND leave_type = "sick"')
        cursor.execute('UPDATE leave_balances SET taken = 5.0, remaining = 15.0 WHERE employee_id = 4 AND leave_type = "annual"')
        
        # Add attendance for all users for last 7 days
        cursor.execute("DELETE FROM attendance")
        attendance_records = []
        for i in range(7):
            att_date = today - timedelta(days=i)
            if att_date.weekday() < 5:  # Weekdays only
                for emp_id in [1, 2, 3, 4, 5]:
                    check_in = datetime.combine(att_date, datetime.min.time().replace(hour=9, minute=0))
                    check_out = datetime.combine(att_date, datetime.min.time().replace(hour=17, minute=30))
                    attendance_records.append((emp_id, att_date, check_in, check_out, 'present', 8.5))
        
        cursor.executemany('INSERT INTO attendance (employee_id, date, check_in, check_out, status, hours_worked) VALUES (?, ?, ?, ?, ?, ?)', attendance_records)
        
        conn.commit()
        print("Database populated successfully!")
        print("\nAll credentials:")
        print("Admin: admin@hrm.com / admin123")
        print("HR: hr@hrm.com / hr123")
        print("Employee: employee@hrm.com / emp123")
        print("Team Lead: teamlead@hrm.com / lead123")
        print("Employee 2: emp2@hrm.com / emp123")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    populate_existing_database()