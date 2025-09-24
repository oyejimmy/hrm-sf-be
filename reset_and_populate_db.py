import os
import sqlite3
from datetime import date, datetime, timedelta
from app.auth import get_password_hash

def reset_and_populate_database():
    # Remove existing database
    if os.path.exists('hrm.db'):
        os.remove('hrm.db')
    
    # Create new database
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    try:
        # Create tables with correct schema
        cursor.execute('''
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                hashed_password VARCHAR NOT NULL,
                first_name VARCHAR NOT NULL,
                last_name VARCHAR NOT NULL,
                phone VARCHAR,
                role VARCHAR NOT NULL,
                is_profile_complete BOOLEAN DEFAULT FALSE,
                status VARCHAR DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                employee_id VARCHAR UNIQUE NOT NULL,
                department_id INTEGER,
                position VARCHAR,
                employment_status VARCHAR,
                hire_date DATE,
                work_location VARCHAR,
                manager_id INTEGER,
                salary DECIMAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (department_id) REFERENCES departments (id),
                FOREIGN KEY (manager_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE leaves (
                id INTEGER PRIMARY KEY,
                employee_id INTEGER NOT NULL,
                leave_type VARCHAR NOT NULL,
                duration_type VARCHAR DEFAULT 'full_day',
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                days_requested REAL NOT NULL,
                reason TEXT,
                status VARCHAR DEFAULT 'pending',
                approved_by INTEGER,
                approved_at DATETIME,
                rejection_reason TEXT,
                admin_comments TEXT,
                attachment_url VARCHAR,
                recipient_details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (employee_id) REFERENCES users (id),
                FOREIGN KEY (approved_by) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE leave_balances (
                id INTEGER PRIMARY KEY,
                employee_id INTEGER NOT NULL,
                leave_type VARCHAR NOT NULL,
                year INTEGER NOT NULL,
                total_allocated REAL NOT NULL,
                taken REAL DEFAULT 0.0,
                remaining REAL NOT NULL,
                carried_forward REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (employee_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE attendance (
                id INTEGER PRIMARY KEY,
                employee_id INTEGER NOT NULL,
                date DATE NOT NULL,
                check_in DATETIME,
                check_out DATETIME,
                status VARCHAR NOT NULL,
                hours_worked REAL DEFAULT 0.0,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY (employee_id) REFERENCES users (id)
            )
        ''')
        
        # Insert departments
        departments = [
            (1, 'Human Resources', 'HR Department'),
            (2, 'Information Technology', 'IT Department'),
            (3, 'Finance', 'Finance Department'),
            (4, 'Marketing', 'Marketing Department'),
            (5, 'Sales', 'Sales Department')
        ]
        cursor.executemany('INSERT INTO departments (id, name, description) VALUES (?, ?, ?)', departments)
        
        # Insert users
        users = [
            (1, 'admin@hrm.com', get_password_hash('admin123'), 'Admin', 'User', '+1234567890', 'admin', True, 'active'),
            (2, 'hr@hrm.com', get_password_hash('hr123'), 'HR', 'Manager', '+1234567891', 'hr', True, 'active'),
            (3, 'employee@hrm.com', get_password_hash('emp123'), 'John', 'Doe', '+1234567892', 'employee', True, 'active'),
            (4, 'teamlead@hrm.com', get_password_hash('lead123'), 'Jane', 'Smith', '+1234567893', 'team_lead', True, 'active'),
            (5, 'emp2@hrm.com', get_password_hash('emp123'), 'Alice', 'Johnson', '+1234567894', 'employee', True, 'active')
        ]
        cursor.executemany('INSERT INTO users (id, email, hashed_password, first_name, last_name, phone, role, is_profile_complete, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', users)
        
        # Insert employees
        employees = [
            (1, 1, 'EMP0001', 1, 'System Administrator', 'full_time', '2024-01-01', 'office', None, 80000),
            (2, 2, 'EMP0002', 1, 'HR Manager', 'full_time', '2024-01-01', 'office', 1, 70000),
            (3, 3, 'EMP0003', 2, 'Software Developer', 'full_time', '2024-02-01', 'office', 4, 60000),
            (4, 4, 'EMP0004', 2, 'Team Lead', 'full_time', '2024-01-15', 'office', 1, 75000),
            (5, 5, 'EMP0005', 2, 'Junior Developer', 'full_time', '2024-03-01', 'office', 4, 45000)
        ]
        cursor.executemany('INSERT INTO employees (id, user_id, employee_id, department_id, position, employment_status, hire_date, work_location, manager_id, salary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', employees)
        
        # Insert leave balances for all employees
        leave_balances = []
        for emp_id in [1, 2, 3, 4, 5]:
            leave_balances.extend([
                (emp_id, 'annual', 2025, 20.0, 0.0, 20.0, 0.0),
                (emp_id, 'sick', 2025, 10.0, 0.0, 10.0, 0.0),
                (emp_id, 'casual', 2025, 5.0, 0.0, 5.0, 0.0)
            ])
        cursor.executemany('INSERT INTO leave_balances (employee_id, leave_type, year, total_allocated, taken, remaining, carried_forward) VALUES (?, ?, ?, ?, ?, ?, ?)', leave_balances)
        
        # Insert sample leaves
        today = date.today()
        leaves = [
            (3, 'annual', 'full_day', today + timedelta(days=10), today + timedelta(days=12), 3.0, 'Family vacation', 'approved', 2, datetime.now()),
            (3, 'sick', 'half_day_morning', today - timedelta(days=5), today - timedelta(days=5), 0.5, 'Medical appointment', 'approved', 2, datetime.now()),
            (5, 'casual', 'full_day', today + timedelta(days=5), today + timedelta(days=5), 1.0, 'Personal work', 'pending', None, None),
            (4, 'annual', 'full_day', today + timedelta(days=15), today + timedelta(days=19), 5.0, 'Vacation', 'approved', 1, datetime.now())
        ]
        cursor.executemany('INSERT INTO leaves (employee_id, leave_type, duration_type, start_date, end_date, days_requested, reason, status, approved_by, approved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', leaves)
        
        # Update leave balances based on approved leaves
        cursor.execute('UPDATE leave_balances SET taken = 3.0, remaining = 17.0 WHERE employee_id = 3 AND leave_type = "annual"')
        cursor.execute('UPDATE leave_balances SET taken = 0.5, remaining = 9.5 WHERE employee_id = 3 AND leave_type = "sick"')
        cursor.execute('UPDATE leave_balances SET taken = 5.0, remaining = 15.0 WHERE employee_id = 4 AND leave_type = "annual"')
        
        # Insert attendance records for the last 10 days
        attendance_records = []
        for i in range(10):
            att_date = today - timedelta(days=i)
            if att_date.weekday() < 5:  # Weekdays only
                for emp_id in [1, 2, 3, 4, 5]:
                    check_in = datetime.combine(att_date, datetime.min.time().replace(hour=9, minute=0))
                    check_out = datetime.combine(att_date, datetime.min.time().replace(hour=17, minute=30))
                    attendance_records.append((emp_id, att_date, check_in, check_out, 'present', 8.5))
        
        cursor.executemany('INSERT INTO attendance (employee_id, date, check_in, check_out, status, hours_worked) VALUES (?, ?, ?, ?, ?, ?)', attendance_records)
        
        conn.commit()
        print("Database reset and populated successfully!")
        print("\nCredentials:")
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
    reset_and_populate_database()