from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.auth import get_password_hash
from datetime import date

def init_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    """Initialize database with sample data"""
    db = SessionLocal()
    
    try:
        # Create departments
        departments = [
            {"name": "Human Resources", "description": "HR Department"},
            {"name": "Information Technology", "description": "IT Department"},
            {"name": "Finance", "description": "Finance Department"},
            {"name": "Marketing", "description": "Marketing Department"},
            {"name": "Sales", "description": "Sales Department"},
        ]
        
        for dept_data in departments:
            existing_dept = db.query(Department).filter(Department.name == dept_data["name"]).first()
            if not existing_dept:
                dept = Department(**dept_data)
                db.add(dept)
        
        db.commit()
        
        # Create admin user
        admin_email = "admin@hrm.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if not existing_admin:
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                first_name="Admin",
                last_name="User",
                phone="+1234567890",
                role="admin",
                is_profile_complete=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            # Create admin employee record
            hr_dept = db.query(Department).filter(Department.name == "Human Resources").first()
            admin_employee = Employee(
                user_id=admin_user.id,
                employee_id="EMP0001",
                department_id=hr_dept.id,
                position="System Administrator",
                employment_status="full_time",
                hire_date=date.today(),
                work_location="office"
            )
            db.add(admin_employee)
        
        # Create HR user
        hr_email = "hr@hrm.com"
        existing_hr = db.query(User).filter(User.email == hr_email).first()
        
        if not existing_hr:
            hr_user = User(
                email=hr_email,
                hashed_password=get_password_hash("hr123"),
                first_name="HR",
                last_name="Manager",
                phone="+1234567891",
                role="hr",
                is_profile_complete=True
            )
            db.add(hr_user)
            db.commit()
            db.refresh(hr_user)
            
            # Create HR employee record
            hr_dept = db.query(Department).filter(Department.name == "Human Resources").first()
            hr_employee = Employee(
                user_id=hr_user.id,
                employee_id="EMP0002",
                department_id=hr_dept.id,
                position="HR Manager",
                employment_status="full_time",
                hire_date=date.today(),
                work_location="office"
            )
            db.add(hr_employee)
        
        # Create sample employee
        emp_email = "employee@hrm.com"
        existing_emp = db.query(User).filter(User.email == emp_email).first()
        
        if not existing_emp:
            emp_user = User(
                email=emp_email,
                hashed_password=get_password_hash("emp123"),
                first_name="John",
                last_name="Doe",
                phone="+1234567892",
                role="employee",
                is_profile_complete=True
            )
            db.add(emp_user)
            db.commit()
            db.refresh(emp_user)
            
            # Create employee record
            it_dept = db.query(Department).filter(Department.name == "Information Technology").first()
            employee = Employee(
                user_id=emp_user.id,
                employee_id="EMP0003",
                department_id=it_dept.id,
                position="Software Developer",
                employment_status="full_time",
                hire_date=date.today(),
                work_location="office"
            )
            db.add(employee)
        
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()