#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models import *
from datetime import datetime, date, timedelta
import random

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def clear_all_tables():
    """Clear all tables"""
    try:
        # Delete in reverse dependency order
        db.query(InsuranceClaim).delete()
        db.query(Asset).delete()
        db.query(TrainingEnrollment).delete()
        db.query(Training).delete()
        db.query(Complaint).delete()
        db.query(EmployeeRequest).delete()
        db.query(Payslip).delete()
        db.query(Performance).delete()
        db.query(Attendance).delete()
        db.query(Leave).delete()
        db.query(Document).delete()
        db.query(Notification).delete()
        db.query(Employee).delete()
        db.query(Department).delete()
        db.query(User).delete()
        db.commit()
        print("✓ All tables cleared")
    except Exception as e:
        db.rollback()
        print(f"Error clearing tables: {e}")

def create_departments():
    """Create departments"""
    departments = [
        Department(name="IT", description="Information Technology"),
        Department(name="HR", description="Human Resources"),
        Department(name="Finance", description="Finance and Accounting"),
        Department(name="Marketing", description="Marketing and Sales"),
        Department(name="Operations", description="Operations Management")
    ]
    
    for dept in departments:
        db.add(dept)
    db.commit()
    print("✓ Departments created")
    return {dept.name: dept.id for dept in departments}

def create_users_and_employees(dept_ids):
    """Create users and employees"""
    users_data = [
        # Admin
        {"email": "admin@hrm.com", "password": "admin123", "role": "admin", "is_active": True,
         "first_name": "John", "last_name": "Admin", "department": "IT", "position": "System Administrator", "salary": 80000},
        
        # HR
        {"email": "hr@hrm.com", "password": "hr123", "role": "hr", "is_active": True,
         "first_name": "Sarah", "last_name": "Wilson", "department": "HR", "position": "HR Manager", "salary": 70000},
        {"email": "hr2@hrm.com", "password": "hr123", "role": "hr", "is_active": True,
         "first_name": "Mike", "last_name": "Johnson", "department": "HR", "position": "HR Specialist", "salary": 55000},
        
        # Team Leads
        {"email": "teamlead1@hrm.com", "password": "lead123", "role": "team_lead", "is_active": True,
         "first_name": "David", "last_name": "Brown", "department": "IT", "position": "IT Team Lead", "salary": 75000},
        {"email": "teamlead2@hrm.com", "password": "lead123", "role": "team_lead", "is_active": True,
         "first_name": "Lisa", "last_name": "Davis", "department": "Marketing", "position": "Marketing Lead", "salary": 72000},
        
        # Employees
        {"email": "employee1@hrm.com", "password": "emp123", "role": "employee", "is_active": True,
         "first_name": "Alice", "last_name": "Smith", "department": "IT", "position": "Software Developer", "salary": 65000},
        {"email": "employee2@hrm.com", "password": "emp123", "role": "employee", "is_active": True,
         "first_name": "Bob", "last_name": "Jones", "department": "Finance", "position": "Accountant", "salary": 50000},
        {"email": "employee3@hrm.com", "password": "emp123", "role": "employee", "is_active": True,
         "first_name": "Carol", "last_name": "White", "department": "Marketing", "position": "Marketing Specialist", "salary": 48000},
        {"email": "employee4@hrm.com", "password": "emp123", "role": "employee", "is_active": True,
         "first_name": "Daniel", "last_name": "Green", "department": "Operations", "position": "Operations Analyst", "salary": 52000},
        {"email": "employee5@hrm.com", "password": "emp123", "role": "employee", "is_active": True,
         "first_name": "Emma", "last_name": "Taylor", "department": "IT", "position": "QA Engineer", "salary": 58000},
    ]
    
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user_ids = []
    for user_data in users_data:
        # Create user
        user = User(
            email=user_data["email"],
            hashed_password=pwd_context.hash(user_data["password"]),
            role=user_data["role"],
            is_active=user_data["is_active"]
        )
        db.add(user)
        db.flush()
        
        # Create employee
        employee = Employee(
            user_id=user.id,
            employee_id=f"EMP{user.id:03d}",
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            phone=f"+1-555-{random.randint(1000, 9999)}",
            address=f"{random.randint(100, 999)} Main St, City, State",
            date_of_birth=date(1980 + random.randint(0, 20), random.randint(1, 12), random.randint(1, 28)),
            hire_date=date.today() - timedelta(days=random.randint(30, 1000)),
            department_id=dept_ids[user_data["department"]],
            position=user_data["position"],
            salary=user_data["salary"],
            status="active",
            manager_id=1 if user.id > 1 else None  # Admin is manager for others
        )
        db.add(employee)
        user_ids.append(user.id)
    
    db.commit()
    print("✓ Users and employees created")
    return user_ids

def create_leaves(user_ids):
    """Create leave records"""
    leave_types = ["annual", "sick", "personal", "maternity", "emergency"]
    statuses = ["pending", "approved", "rejected"]
    
    for user_id in user_ids[2:]:  # Skip admin and first HR
        for _ in range(random.randint(2, 5)):
            start_date = date.today() - timedelta(days=random.randint(1, 180))
            duration = random.randint(1, 10)
            
            leave = Leave(
                employee_id=user_id,
                leave_type=random.choice(leave_types),
                start_date=start_date,
                end_date=start_date + timedelta(days=duration-1),
                duration=duration,
                reason=f"Sample {random.choice(leave_types)} leave request",
                status=random.choice(statuses),
                applied_date=start_date - timedelta(days=random.randint(1, 30)),
                approved_by=1 if random.choice([True, False]) else None
            )
            db.add(leave)
    
    db.commit()
    print("✓ Leave records created")

def create_attendance(user_ids):
    """Create attendance records"""
    statuses = ["present", "absent", "late", "half_day"]
    
    for user_id in user_ids:
        for days_back in range(30):  # Last 30 days
            att_date = date.today() - timedelta(days=days_back)
            if att_date.weekday() < 5:  # Weekdays only
                status = random.choice(statuses)
                check_in = datetime.combine(att_date, datetime.min.time().replace(hour=9, minute=random.randint(0, 30)))
                check_out = check_in + timedelta(hours=8, minutes=random.randint(0, 60)) if status != "absent" else None
                
                attendance = Attendance(
                    employee_id=user_id,
                    date=att_date,
                    check_in=check_in if status != "absent" else None,
                    check_out=check_out,
                    status=status,
                    total_hours=8.0 if status == "present" else (4.0 if status == "half_day" else 0.0),
                    notes=f"Sample attendance for {att_date}"
                )
                db.add(attendance)
    
    db.commit()
    print("✓ Attendance records created")

def create_performance_reviews(user_ids):
    """Create performance reviews"""
    for user_id in user_ids[3:]:  # Skip admin and HR
        review = Performance(
            employee_id=user_id,
            reviewer_id=random.choice(user_ids[:3]),  # Admin or HR as reviewer
            review_period_start=date.today() - timedelta(days=365),
            review_period_end=date.today() - timedelta(days=1),
            goals="Complete assigned projects on time",
            achievements="Successfully delivered 3 major projects",
            areas_for_improvement="Communication skills, Time management",
            overall_rating=random.uniform(3.0, 5.0),
            status="completed",
            comments="Good performance overall"
        )
        db.add(review)
    
    db.commit()
    print("✓ Performance reviews created")

def create_payroll(user_ids):
    """Create payroll records"""
    for user_id in user_ids:
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if employee:
            for month_back in range(3):  # Last 3 months
                pay_date = date.today().replace(day=1) - timedelta(days=month_back*30)
                
                payslip = Payslip(
                    employee_id=user_id,
                    pay_period=pay_date.strftime("%Y-%m"),
                    basic_salary=employee.salary,
                    allowances=employee.salary * 0.1,
                    overtime_pay=random.uniform(0, 500),
                    gross_pay=employee.salary * 1.1 + random.uniform(0, 500),
                    tax_deduction=employee.salary * 0.15,
                    insurance_deduction=200,
                    other_deductions=50,
                    total_deductions=employee.salary * 0.15 + 250,
                    net_pay=employee.salary * 0.95,
                    pay_date=pay_date
                )
                db.add(payslip)
    
    db.commit()
    print("✓ Payroll records created")

def create_requests(user_ids):
    """Create employee requests"""
    request_types = ["equipment", "leave_extension", "training", "transfer", "salary_review"]
    statuses = ["pending", "approved", "rejected"]
    
    for user_id in user_ids[3:]:  # Employees only
        for _ in range(random.randint(1, 3)):
            request = EmployeeRequest(
                employee_id=user_id,
                request_type=random.choice(request_types),
                title=f"Request for {random.choice(request_types).replace('_', ' ')}",
                description="Sample request description",
                status=random.choice(statuses),
                priority="medium",
                requested_date=date.today() - timedelta(days=random.randint(1, 60)),
                approved_by=random.choice(user_ids[:2]) if random.choice([True, False]) else None
            )
            db.add(request)
    
    db.commit()
    print("✓ Employee requests created")

def create_complaints(user_ids):
    """Create complaints"""
    categories = ["workplace", "harassment", "discrimination", "safety", "policy"]
    priorities = ["low", "medium", "high", "critical"]
    statuses = ["pending", "in_progress", "resolved"]
    
    for user_id in user_ids[4:]:  # Some employees
        complaint = Complaint(
            employee_id=user_id,
            category=random.choice(categories),
            title=f"Complaint about {random.choice(categories)}",
            description="Sample complaint description",
            priority=random.choice(priorities),
            status=random.choice(statuses),
            filed_date=date.today() - timedelta(days=random.randint(1, 90)),
            assigned_to=random.choice(user_ids[:2])  # Admin or HR
        )
        db.add(complaint)
    
    db.commit()
    print("✓ Complaints created")

def create_training(user_ids):
    """Create training programs and enrollments"""
    # Create training programs
    trainings = [
        Training(
            title="Python Programming",
            description="Learn Python programming basics",
            trainer="John Doe",
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=60),
            max_participants=20,
            status="scheduled"
        ),
        Training(
            title="Leadership Skills",
            description="Develop leadership and management skills",
            trainer="Jane Smith",
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=45),
            max_participants=15,
            status="scheduled"
        ),
        Training(
            title="Data Analysis",
            description="Learn data analysis techniques",
            trainer="Mike Johnson",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=1),
            max_participants=25,
            status="completed"
        )
    ]
    
    for training in trainings:
        db.add(training)
    db.flush()
    
    # Create enrollments
    for user_id in user_ids[2:]:  # All except admin
        for training in trainings:
            if random.choice([True, False]):  # 50% chance of enrollment
                enrollment = TrainingEnrollment(
                    employee_id=user_id,
                    training_id=training.id,
                    enrollment_date=training.start_date - timedelta(days=random.randint(1, 15)),
                    status=random.choice(["enrolled", "in_progress", "completed", "dropped"]),
                    completion_date=training.end_date if random.choice([True, False]) else None,
                    certificate_issued=random.choice([True, False])
                )
                db.add(enrollment)
    
    db.commit()
    print("✓ Training programs and enrollments created")

def create_assets(user_ids):
    """Create assets"""
    asset_types = ["laptop", "desktop", "monitor", "phone", "tablet"]
    statuses = ["available", "assigned", "maintenance", "retired"]
    
    for i in range(20):
        asset = Asset(
            asset_tag=f"AST{i+1:03d}",
            asset_type=random.choice(asset_types),
            brand=random.choice(["Dell", "HP", "Lenovo", "Apple", "Samsung"]),
            model=f"Model-{random.randint(1000, 9999)}",
            serial_number=f"SN{random.randint(100000, 999999)}",
            purchase_date=date.today() - timedelta(days=random.randint(30, 1000)),
            purchase_cost=random.uniform(500, 3000),
            status=random.choice(statuses),
            assigned_to=random.choice(user_ids) if random.choice([True, False]) else None,
            location="Office Floor 1"
        )
        db.add(asset)
    
    db.commit()
    print("✓ Assets created")

def create_health_insurance(user_ids):
    """Create health insurance claims"""
    claim_types = ["medical", "dental", "vision", "prescription"]
    statuses = ["pending", "approved", "rejected", "processing"]
    
    for user_id in user_ids[2:]:  # All except admin
        for _ in range(random.randint(0, 3)):
            claim = InsuranceClaim(
                employee_id=user_id,
                claim_type=random.choice(claim_types),
                claim_amount=random.uniform(100, 2000),
                claim_date=date.today() - timedelta(days=random.randint(1, 180)),
                description=f"Sample {random.choice(claim_types)} claim",
                status=random.choice(statuses),
                approved_amount=random.uniform(50, 1500) if random.choice([True, False]) else None,
                processed_date=date.today() - timedelta(days=random.randint(1, 30)) if random.choice([True, False]) else None
            )
            db.add(claim)
    
    db.commit()
    print("✓ Health insurance claims created")

def create_documents(user_ids):
    """Create documents"""
    doc_types = ["contract", "policy", "handbook", "form", "certificate"]
    
    for user_id in user_ids:
        for _ in range(random.randint(1, 3)):
            document = Document(
                employee_id=user_id,
                document_type=random.choice(doc_types),
                title=f"Sample {random.choice(doc_types)} document",
                file_path=f"/documents/sample_{random.randint(1000, 9999)}.pdf",
                uploaded_date=date.today() - timedelta(days=random.randint(1, 365)),
                uploaded_by=random.choice(user_ids[:2])  # Admin or HR
            )
            db.add(document)
    
    db.commit()
    print("✓ Documents created")

def create_notifications(user_ids):
    """Create notifications"""
    notification_types = ["leave_approved", "meeting_reminder", "policy_update", "training_enrollment", "payroll_processed"]
    
    for user_id in user_ids:
        for _ in range(random.randint(3, 8)):
            notification = Notification(
                user_id=user_id,
                title=f"Sample {random.choice(notification_types).replace('_', ' ')} notification",
                message="This is a sample notification message",
                notification_type=random.choice(notification_types),
                is_read=random.choice([True, False]),
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            db.add(notification)
    
    db.commit()
    print("✓ Notifications created")

def main():
    print("Starting database population...")
    
    # Clear existing data
    clear_all_tables()
    
    # Create data
    dept_ids = create_departments()
    user_ids = create_users_and_employees(dept_ids)
    create_leaves(user_ids)
    create_attendance(user_ids)
    create_performance_reviews(user_ids)
    create_payroll(user_ids)
    create_requests(user_ids)
    create_complaints(user_ids)
    create_training(user_ids)
    create_assets(user_ids)
    create_health_insurance(user_ids)
    create_documents(user_ids)
    create_notifications(user_ids)
    
    db.close()
    print("Database population completed successfully!")
    print("\nLogin Credentials:")
    print("Admin: admin@hrm.com / admin123")
    print("HR: hr@hrm.com / hr123")
    print("Team Lead: teamlead1@hrm.com / lead123")
    print("Employee: employee1@hrm.com / emp123")

if __name__ == "__main__":
    main()