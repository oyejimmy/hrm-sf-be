from app.database import SessionLocal
from app.models.user import User
from app.models.employee import Employee
from app.models.leave import Leave, LeaveBalance
from app.models.attendance import Attendance
from app.models.department import Department

def show_database_data():
    db = SessionLocal()
    
    try:
        print("=== USERS ===")
        users = db.query(User).all()
        for user in users:
            print(f"ID: {user.id}, Email: {user.email}, Role: {user.role}, Name: {user.first_name} {user.last_name}")
        
        print("\n=== EMPLOYEES ===")
        employees = db.query(Employee).all()
        for emp in employees:
            print(f"ID: {emp.id}, User ID: {emp.user_id}, Employee ID: {emp.employee_id}, Position: {emp.position}")
        
        print("\n=== DEPARTMENTS ===")
        departments = db.query(Department).all()
        for dept in departments:
            print(f"ID: {dept.id}, Name: {dept.name}")
        
        print("\n=== LEAVES ===")
        leaves = db.query(Leave).all()
        for leave in leaves:
            print(f"ID: {leave.id}, Employee ID: {leave.employee_id}, Type: {leave.leave_type}, Status: {leave.status}")
        
        print("\n=== LEAVE BALANCES ===")
        balances = db.query(LeaveBalance).all()
        for balance in balances:
            print(f"Employee ID: {balance.employee_id}, Type: {balance.leave_type}, Remaining: {balance.remaining}")
        
        print("\n=== ATTENDANCE ===")
        attendance = db.query(Attendance).limit(5).all()
        for att in attendance:
            print(f"Employee ID: {att.employee_id}, Date: {att.date}, Status: {att.status}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    show_database_data()