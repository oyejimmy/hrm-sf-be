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

def create_sample_data():
    """Create sample data for all tables"""
    
    # Check if departments exist, if not create them
    if db.query(Department).count() == 0:
        departments = [
            Department(name="IT", description="Information Technology"),
            Department(name="HR", description="Human Resources"),
            Department(name="Finance", description="Finance and Accounting"),
            Department(name="Marketing", description="Marketing and Sales"),
        ]
        for dept in departments:
            db.add(dept)
        db.commit()
        print("✓ Departments created")
    
    # Get department IDs
    dept_it = db.query(Department).filter(Department.name == "IT").first()
    dept_hr = db.query(Department).filter(Department.name == "HR").first()
    dept_finance = db.query(Department).filter(Department.name == "Finance").first()
    dept_marketing = db.query(Department).filter(Department.name == "Marketing").first()
    
    # Create users if they don't exist
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    users_to_create = [
        {"email": "admin@hrm.com", "password": "admin123", "role": "admin"},
        {"email": "hr@hrm.com", "password": "hr123", "role": "hr"},
        {"email": "teamlead@hrm.com", "password": "lead123", "role": "team_lead"},
        {"email": "employee@hrm.com", "password": "emp123", "role": "employee"},
        {"email": "employee2@hrm.com", "password": "emp123", "role": "employee"},
    ]
    
    user_ids = []
    for user_data in users_to_create:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            user = User(
                email=user_data["email"],
                hashed_password=pwd_context.hash(user_data["password"]),
                role=user_data["role"],
                status="active"
            )
            db.add(user)
            db.flush()
            user_ids.append(user.id)
            
            # Create corresponding employee
            dept_map = {
                "admin@hrm.com": dept_it.id,
                "hr@hrm.com": dept_hr.id,
                "teamlead@hrm.com": dept_it.id,
                "employee@hrm.com": dept_finance.id,
                "employee2@hrm.com": dept_marketing.id,
            }
            
            name_map = {
                "admin@hrm.com": ("John", "Admin"),
                "hr@hrm.com": ("Sarah", "Wilson"),
                "teamlead@hrm.com": ("David", "Brown"),
                "employee@hrm.com": ("Alice", "Smith"),
                "employee2@hrm.com": ("Bob", "Jones"),
            }
            
            first_name, last_name = name_map[user_data["email"]]
            
            employee = Employee(
                user_id=user.id,
                employee_id=f"EMP{user.id:03d}",
                first_name=first_name,
                last_name=last_name,
                email=user_data["email"],
                phone=f"+1-555-{random.randint(1000, 9999)}",
                address=f"{random.randint(100, 999)} Main St, City, State",
                date_of_birth=date(1985, random.randint(1, 12), random.randint(1, 28)),
                hire_date=date.today() - timedelta(days=random.randint(30, 500)),
                department_id=dept_map[user_data["email"]],
                position=f"{user_data['role'].title()} Position",
                salary=random.randint(40000, 80000),
                status="active"
            )
            db.add(employee)
        else:
            user_ids.append(existing_user.id)
    
    db.commit()
    print("✓ Users and employees created")
    
    # Create sample leaves
    for user_id in user_ids[2:]:  # Skip admin and HR
        for _ in range(random.randint(1, 3)):
            start_date = date.today() - timedelta(days=random.randint(1, 90))
            duration = random.randint(1, 5)
            
            leave = Leave(
                employee_id=user_id,
                leave_type=random.choice(["annual", "sick", "personal"]),
                start_date=start_date,
                end_date=start_date + timedelta(days=duration-1),
                duration=duration,
                reason="Sample leave request",
                status=random.choice(["pending", "approved", "rejected"]),
                applied_date=start_date - timedelta(days=random.randint(1, 15))
            )
            db.add(leave)
    
    # Create sample attendance
    for user_id in user_ids:
        for days_back in range(10):  # Last 10 days
            att_date = date.today() - timedelta(days=days_back)
            if att_date.weekday() < 5:  # Weekdays only
                attendance = Attendance(
                    employee_id=user_id,
                    date=att_date,
                    check_in=datetime.combine(att_date, datetime.min.time().replace(hour=9, minute=random.randint(0, 30))),
                    check_out=datetime.combine(att_date, datetime.min.time().replace(hour=17, minute=random.randint(0, 60))),
                    status=random.choice(["present", "late"]),
                    total_hours=8.0
                )
                db.add(attendance)
    
    # Create sample performance reviews
    for user_id in user_ids[2:]:  # Employees only
        review = Performance(
            employee_id=user_id,
            reviewer_id=user_ids[0],  # Admin as reviewer
            review_period_start=date.today() - timedelta(days=365),
            review_period_end=date.today() - timedelta(days=1),
            goals="Complete assigned projects",
            achievements="Successfully delivered projects",
            areas_for_improvement="Communication skills",
            overall_rating=random.uniform(3.0, 5.0),
            status="completed"
        )
        db.add(review)
    
    # Create sample payslips
    for user_id in user_ids:
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if employee:
            payslip = Payslip(
                employee_id=user_id,
                pay_period=date.today().strftime("%Y-%m"),
                basic_salary=employee.salary,
                allowances=employee.salary * 0.1,
                gross_pay=employee.salary * 1.1,
                tax_deduction=employee.salary * 0.15,
                insurance_deduction=200,
                total_deductions=employee.salary * 0.15 + 200,
                net_pay=employee.salary * 0.95,
                pay_date=date.today()
            )
            db.add(payslip)
    
    # Create sample requests
    for user_id in user_ids[2:]:  # Employees only
        request = EmployeeRequest(
            employee_id=user_id,
            request_type="equipment",
            title="Equipment Request",
            description="Need new laptop",
            status=random.choice(["pending", "approved"]),
            priority="medium",
            requested_date=date.today() - timedelta(days=random.randint(1, 30))
        )
        db.add(request)
    
    # Create sample complaints
    for user_id in user_ids[3:]:  # Some employees
        complaint = Complaint(
            employee_id=user_id,
            category="workplace",
            title="Workplace Issue",
            description="Sample complaint",
            priority="medium",
            status=random.choice(["pending", "resolved"]),
            filed_date=date.today() - timedelta(days=random.randint(1, 60))
        )
        db.add(complaint)
    
    # Create sample training programs
    training = TrainingProgram(
        title="Python Programming",
        description="Learn Python basics",
        trainer="John Doe",
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=60),
        max_participants=20,
        status="scheduled"
    )
    db.add(training)
    db.flush()
    
    # Create training enrollments
    for user_id in user_ids[2:]:
        enrollment = TrainingEnrollment(
            employee_id=user_id,
            training_id=training.id,
            enrollment_date=date.today(),
            status="enrolled"
        )
        db.add(enrollment)
    
    # Create sample assets
    for i in range(5):
        asset = Asset(
            asset_tag=f"AST{i+1:03d}",
            asset_type=random.choice(["laptop", "desktop", "monitor"]),
            brand="Dell",
            model=f"Model-{i+1}",
            serial_number=f"SN{random.randint(100000, 999999)}",
            purchase_date=date.today() - timedelta(days=random.randint(30, 365)),
            purchase_cost=random.uniform(500, 2000),
            status=random.choice(["available", "assigned"]),
            assigned_to=random.choice(user_ids) if random.choice([True, False]) else None
        )
        db.add(asset)
    
    # Create sample insurance claims
    for user_id in user_ids[2:]:
        claim = InsuranceClaim(
            employee_id=user_id,
            claim_type="medical",
            claim_amount=random.uniform(100, 1000),
            claim_date=date.today() - timedelta(days=random.randint(1, 90)),
            description="Medical expense claim",
            status=random.choice(["pending", "approved"])
        )
        db.add(claim)
    
    # Create sample documents
    for user_id in user_ids:
        document = Document(
            employee_id=user_id,
            document_type="contract",
            title="Employment Contract",
            file_path=f"/documents/contract_{user_id}.pdf",
            uploaded_date=date.today() - timedelta(days=random.randint(1, 180)),
            uploaded_by=user_ids[0]  # Admin
        )
        db.add(document)
    
    # Create sample notifications
    for user_id in user_ids:
        for _ in range(3):
            notification = Notification(
                user_id=user_id,
                title="Sample Notification",
                message="This is a sample notification",
                notification_type="general",
                is_read=random.choice([True, False]),
                created_at=datetime.now() - timedelta(days=random.randint(1, 15))
            )
            db.add(notification)
    
    db.commit()
    print("✓ All sample data created successfully!")
    
    print("\\nLogin Credentials:")
    print("Admin: admin@hrm.com / admin123")
    print("HR: hr@hrm.com / hr123")
    print("Team Lead: teamlead@hrm.com / lead123")
    print("Employee: employee@hrm.com / emp123")

if __name__ == "__main__":
    print("Starting database population...")
    create_sample_data()
    db.close()
    print("Database population completed!")