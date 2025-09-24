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

def add_missing_data():
    """Add sample data to empty tables"""
    
    # Get existing users
    users = db.query(User).all()
    user_ids = [user.id for user in users]
    
    print(f"Found {len(users)} existing users")
    
    # Add attendance records (simple version without break columns)
    print("Adding attendance records...")
    for user_id in user_ids:
        for days_back in range(15):  # Last 15 days
            att_date = date.today() - timedelta(days=days_back)
            if att_date.weekday() < 5:  # Weekdays only
                existing = db.query(Attendance).filter(
                    Attendance.employee_id == user_id,
                    Attendance.date == att_date
                ).first()
                
                if not existing:
                    check_in_time = datetime.combine(att_date, datetime.min.time().replace(hour=9, minute=random.randint(0, 30)))
                    check_out_time = check_in_time + timedelta(hours=8, minutes=random.randint(0, 60))
                    
                    attendance = Attendance(
                        employee_id=user_id,
                        date=att_date,
                        check_in=check_in_time,
                        check_out=check_out_time,
                        status=random.choice(["present", "late"]),
                        total_hours=8.0,
                        notes=f"Sample attendance for {att_date}"
                    )
                    db.add(attendance)
    
    # Add performance reviews
    print("Adding performance reviews...")
    for user_id in user_ids[2:]:  # Skip admin and HR
        existing = db.query(Performance).filter(Performance.employee_id == user_id).first()
        if not existing:
            review = Performance(
                employee_id=user_id,
                reviewer_id=user_ids[0],  # Admin as reviewer
                review_period_start=date.today() - timedelta(days=365),
                review_period_end=date.today() - timedelta(days=1),
                goals="Complete assigned projects on time",
                achievements="Successfully delivered multiple projects",
                areas_for_improvement="Communication and time management",
                overall_rating=random.uniform(3.5, 4.8),
                status="completed",
                comments="Good performance overall"
            )
            db.add(review)
    
    # Add payslips
    print("Adding payslips...")
    for user_id in user_ids:
        employee = db.query(Employee).filter(Employee.user_id == user_id).first()
        if employee:
            existing = db.query(Payslip).filter(Payslip.employee_id == user_id).first()
            if not existing:
                basic_salary = employee.salary or 50000
                payslip = Payslip(
                    employee_id=user_id,
                    pay_period=date.today().strftime("%Y-%m"),
                    basic_salary=basic_salary,
                    allowances=basic_salary * 0.1,
                    overtime_pay=random.uniform(0, 1000),
                    gross_pay=basic_salary * 1.15,
                    tax_deduction=basic_salary * 0.18,
                    insurance_deduction=300,
                    other_deductions=100,
                    total_deductions=basic_salary * 0.18 + 400,
                    net_pay=basic_salary * 0.97,
                    pay_date=date.today()
                )
                db.add(payslip)
    
    # Add employee requests
    print("Adding employee requests...")
    request_types = ["equipment", "leave_extension", "training", "transfer"]
    for user_id in user_ids[2:]:  # Employees only
        existing = db.query(EmployeeRequest).filter(EmployeeRequest.employee_id == user_id).first()
        if not existing:
            request = EmployeeRequest(
                employee_id=user_id,
                request_type=random.choice(request_types),
                title=f"Request for {random.choice(request_types).replace('_', ' ')}",
                description="Sample employee request description",
                status=random.choice(["pending", "approved", "rejected"]),
                priority="medium",
                requested_date=date.today() - timedelta(days=random.randint(1, 30))
            )
            db.add(request)
    
    # Add complaints
    print("Adding complaints...")
    categories = ["workplace", "harassment", "policy", "safety"]
    for user_id in user_ids[3:]:  # Some employees
        existing = db.query(Complaint).filter(Complaint.employee_id == user_id).first()
        if not existing:
            complaint = Complaint(
                employee_id=user_id,
                category=random.choice(categories),
                title=f"Complaint about {random.choice(categories)}",
                description="Sample complaint description",
                priority=random.choice(["low", "medium", "high"]),
                status=random.choice(["pending", "in_progress", "resolved"]),
                filed_date=date.today() - timedelta(days=random.randint(1, 60)),
                assigned_to=user_ids[1]  # HR
            )
            db.add(complaint)
    
    # Add training programs
    print("Adding training programs...")
    if db.query(TrainingProgram).count() == 0:
        trainings = [
            TrainingProgram(
                title="Python Programming Basics",
                description="Learn Python programming fundamentals",
                trainer="John Smith",
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=60),
                max_participants=25,
                status="scheduled"
            ),
            TrainingProgram(
                title="Leadership Development",
                description="Develop leadership and management skills",
                trainer="Sarah Johnson",
                start_date=date.today() + timedelta(days=15),
                end_date=date.today() + timedelta(days=45),
                max_participants=15,
                status="scheduled"
            )
        ]
        
        for training in trainings:
            db.add(training)
        db.flush()
        
        # Add training enrollments
        training_programs = db.query(TrainingProgram).all()
        for user_id in user_ids[2:]:  # Employees
            for training in training_programs:
                if random.choice([True, False]):  # 50% chance
                    enrollment = TrainingEnrollment(
                        employee_id=user_id,
                        training_id=training.id,
                        enrollment_date=date.today(),
                        status=random.choice(["enrolled", "in_progress", "completed"])
                    )
                    db.add(enrollment)
    
    # Add assets
    print("Adding assets...")
    if db.query(Asset).count() == 0:
        asset_types = ["laptop", "desktop", "monitor", "phone", "tablet"]
        brands = ["Dell", "HP", "Lenovo", "Apple", "Samsung"]
        
        for i in range(15):
            asset = Asset(
                asset_tag=f"AST{i+1:04d}",
                asset_type=random.choice(asset_types),
                brand=random.choice(brands),
                model=f"Model-{random.randint(1000, 9999)}",
                serial_number=f"SN{random.randint(100000, 999999)}",
                purchase_date=date.today() - timedelta(days=random.randint(30, 1000)),
                purchase_cost=random.uniform(500, 3000),
                status=random.choice(["available", "assigned", "maintenance"]),
                assigned_to=random.choice(user_ids) if random.choice([True, False]) else None,
                location="Office Building A"
            )
            db.add(asset)
    
    # Add insurance claims
    print("Adding insurance claims...")
    claim_types = ["medical", "dental", "vision", "prescription"]
    for user_id in user_ids[2:]:  # Employees
        existing = db.query(InsuranceClaim).filter(InsuranceClaim.employee_id == user_id).first()
        if not existing:
            claim = InsuranceClaim(
                employee_id=user_id,
                claim_type=random.choice(claim_types),
                claim_amount=random.uniform(100, 2000),
                claim_date=date.today() - timedelta(days=random.randint(1, 180)),
                description=f"Sample {random.choice(claim_types)} claim",
                status=random.choice(["pending", "approved", "rejected"])
            )
            db.add(claim)
    
    # Add documents
    print("Adding documents...")
    doc_types = ["contract", "policy", "handbook", "certificate"]
    for user_id in user_ids:
        existing = db.query(Document).filter(Document.employee_id == user_id).first()
        if not existing:
            document = Document(
                employee_id=user_id,
                document_type=random.choice(doc_types),
                title=f"Employee {random.choice(doc_types)}",
                file_path=f"/documents/{random.choice(doc_types)}_{user_id}.pdf",
                uploaded_date=date.today() - timedelta(days=random.randint(1, 365)),
                uploaded_by=user_ids[0]  # Admin
            )
            db.add(document)
    
    # Add notifications
    print("Adding notifications...")
    notification_types = ["leave_approved", "meeting_reminder", "policy_update", "training_enrollment"]
    for user_id in user_ids:
        existing_count = db.query(Notification).filter(Notification.user_id == user_id).count()
        if existing_count < 3:
            for _ in range(3 - existing_count):
                notification = Notification(
                    user_id=user_id,
                    title=f"Sample {random.choice(notification_types).replace('_', ' ')} notification",
                    message="This is a sample notification message for testing purposes",
                    notification_type=random.choice(notification_types),
                    is_read=random.choice([True, False]),
                    created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                db.add(notification)
    
    # Commit all changes
    db.commit()
    print("✓ All missing data added successfully!")
    
    # Print summary
    print("\\nData Summary:")
    print(f"Users: {db.query(User).count()}")
    print(f"Employees: {db.query(Employee).count()}")
    print(f"Departments: {db.query(Department).count()}")
    print(f"Leaves: {db.query(Leave).count()}")
    print(f"Attendance: {db.query(Attendance).count()}")
    print(f"Performance Reviews: {db.query(Performance).count()}")
    print(f"Payslips: {db.query(Payslip).count()}")
    print(f"Requests: {db.query(EmployeeRequest).count()}")
    print(f"Complaints: {db.query(Complaint).count()}")
    print(f"Training Programs: {db.query(TrainingProgram).count()}")
    print(f"Training Enrollments: {db.query(TrainingEnrollment).count()}")
    print(f"Assets: {db.query(Asset).count()}")
    print(f"Insurance Claims: {db.query(InsuranceClaim).count()}")
    print(f"Documents: {db.query(Document).count()}")
    print(f"Notifications: {db.query(Notification).count()}")

if __name__ == "__main__":
    print("Adding missing sample data to database...")
    add_missing_data()
    db.close()
    print("Database population completed!")