#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine
from datetime import datetime, date, timedelta
import random

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def populate_all_tables():
    """Populate all tables with sample data using raw SQL"""
    
    # Get existing user IDs
    result = db.execute(text("SELECT id FROM users"))
    user_ids = [row[0] for row in result.fetchall()]
    print(f"Found {len(user_ids)} users: {user_ids}")
    
    # 1. Add attendance records
    print("Adding attendance records...")
    for user_id in user_ids:
        for days_back in range(20):
            att_date = date.today() - timedelta(days=days_back)
            if att_date.weekday() < 5:  # Weekdays only
                # Check if record exists
                existing = db.execute(text(
                    "SELECT COUNT(*) FROM attendance WHERE employee_id = :emp_id AND date = :att_date"
                ), {"emp_id": user_id, "att_date": att_date}).fetchone()[0]
                
                if existing == 0:
                    status = random.choice(["present", "late", "absent"])
                    check_in = f"{9 + random.randint(0, 1)}:{random.randint(0, 59):02d}:00" if status != "absent" else None
                    check_out = f"{17 + random.randint(0, 2)}:{random.randint(0, 59):02d}:00" if status != "absent" else None
                    hours = "8.0" if status == "present" else ("7.5" if status == "late" else "0.0")
                    
                    db.execute(text("""
                        INSERT INTO attendance (employee_id, date, check_in, check_out, status, hours_worked, notes, created_at, updated_at)
                        VALUES (:emp_id, :date, :check_in, :check_out, :status, :hours, :notes, :created, :updated)
                    """), {
                        "emp_id": user_id,
                        "date": att_date,
                        "check_in": check_in,
                        "check_out": check_out,
                        "status": status,
                        "hours": hours,
                        "notes": f"Sample attendance for {att_date}",
                        "created": datetime.now(),
                        "updated": datetime.now()
                    })
    
    # 2. Add performance reviews
    print("Adding performance reviews...")
    for user_id in user_ids[2:]:  # Skip admin and HR
        existing = db.execute(text(
            "SELECT COUNT(*) FROM performance_reviews WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing == 0:
            db.execute(text("""
                INSERT INTO performance_reviews (employee_id, reviewer_id, review_period_start, review_period_end, 
                goals, achievements, areas_for_improvement, overall_rating, status, comments, created_at, updated_at)
                VALUES (:emp_id, :reviewer, :start_date, :end_date, :goals, :achievements, :improvements, 
                :rating, :status, :comments, :created, :updated)
            """), {
                "emp_id": user_id,
                "reviewer": user_ids[0],
                "start_date": date.today() - timedelta(days=365),
                "end_date": date.today() - timedelta(days=1),
                "goals": "Complete assigned projects on time and maintain quality standards",
                "achievements": "Successfully delivered multiple projects and improved team collaboration",
                "improvements": "Focus on communication skills and time management",
                "rating": round(random.uniform(3.5, 4.8), 1),
                "status": "completed",
                "comments": "Good overall performance with room for growth",
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 3. Add payslips
    print("Adding payslips...")
    for user_id in user_ids:
        # Get employee salary
        salary_result = db.execute(text(
            "SELECT salary FROM employees WHERE user_id = :user_id"
        ), {"user_id": user_id}).fetchone()
        
        salary = salary_result[0] if salary_result and salary_result[0] else 50000
        
        existing = db.execute(text(
            "SELECT COUNT(*) FROM payslips WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing == 0:
            basic_salary = salary
            allowances = salary * 0.1
            gross_pay = basic_salary + allowances
            tax_deduction = gross_pay * 0.18
            insurance_deduction = 300
            total_deductions = tax_deduction + insurance_deduction
            net_pay = gross_pay - total_deductions
            
            db.execute(text("""
                INSERT INTO payslips (employee_id, pay_period, basic_salary, gross_pay, net_pay, 
                tax_deduction, insurance_deduction, total_deductions, pay_date, created_at, updated_at)
                VALUES (:emp_id, :period, :basic, :gross, :net, :tax, :insurance, :total_ded, 
                :pay_date, :created, :updated)
            """), {
                "emp_id": user_id,
                "period": date.today().strftime("%Y-%m"),
                "basic": basic_salary,
                "gross": gross_pay,
                "net": net_pay,
                "tax": tax_deduction,
                "insurance": insurance_deduction,
                "total_ded": total_deductions,
                "pay_date": date.today(),
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 4. Add employee requests
    print("Adding employee requests...")
    request_types = ["equipment", "leave_extension", "training", "transfer", "salary_review"]
    for user_id in user_ids[2:]:  # Employees only
        existing = db.execute(text(
            "SELECT COUNT(*) FROM employee_requests WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing == 0:
            req_type = random.choice(request_types)
            db.execute(text("""
                INSERT INTO employee_requests (employee_id, request_type, title, description, status, 
                priority, requested_date, created_at, updated_at)
                VALUES (:emp_id, :type, :title, :desc, :status, :priority, :req_date, :created, :updated)
            """), {
                "emp_id": user_id,
                "type": req_type,
                "title": f"Request for {req_type.replace('_', ' ')}",
                "desc": f"Sample {req_type} request description",
                "status": random.choice(["pending", "approved", "rejected"]),
                "priority": random.choice(["low", "medium", "high"]),
                "req_date": date.today() - timedelta(days=random.randint(1, 30)),
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 5. Add complaints
    print("Adding complaints...")
    categories = ["workplace", "harassment", "policy", "safety", "discrimination"]
    for user_id in user_ids[3:]:  # Some employees
        existing = db.execute(text(
            "SELECT COUNT(*) FROM complaints WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing == 0:
            category = random.choice(categories)
            db.execute(text("""
                INSERT INTO complaints (employee_id, category, title, description, priority, status, 
                filed_date, assigned_to, created_at, updated_at)
                VALUES (:emp_id, :category, :title, :desc, :priority, :status, :filed, :assigned, :created, :updated)
            """), {
                "emp_id": user_id,
                "category": category,
                "title": f"Complaint regarding {category}",
                "desc": f"Sample complaint about {category} issues in the workplace",
                "priority": random.choice(["low", "medium", "high"]),
                "status": random.choice(["pending", "in_progress", "resolved"]),
                "filed": date.today() - timedelta(days=random.randint(1, 60)),
                "assigned": user_ids[1],  # HR
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 6. Add training programs
    print("Adding training programs...")
    existing_programs = db.execute(text("SELECT COUNT(*) FROM training_programs")).fetchone()[0]
    if existing_programs == 0:
        programs = [
            ("Python Programming Fundamentals", "Learn Python programming from basics to advanced", "John Smith", 25),
            ("Leadership Development", "Develop leadership and management skills", "Sarah Johnson", 15),
            ("Data Analysis with Excel", "Master data analysis using Microsoft Excel", "Mike Davis", 20),
            ("Communication Skills", "Improve workplace communication and presentation skills", "Lisa Brown", 30)
        ]
        
        program_ids = []
        for title, desc, trainer, max_participants in programs:
            result = db.execute(text("""
                INSERT INTO training_programs (title, description, trainer, start_date, end_date, 
                max_participants, status, created_at, updated_at)
                VALUES (:title, :desc, :trainer, :start_date, :end_date, :max_part, :status, :created, :updated)
                RETURNING id
            """), {
                "title": title,
                "desc": desc,
                "trainer": trainer,
                "start_date": date.today() + timedelta(days=random.randint(15, 60)),
                "end_date": date.today() + timedelta(days=random.randint(75, 120)),
                "max_part": max_participants,
                "status": "scheduled",
                "created": datetime.now(),
                "updated": datetime.now()
            })
            program_ids.append(result.fetchone()[0])
        
        # Add training enrollments
        for user_id in user_ids[2:]:  # Employees
            for program_id in program_ids:
                if random.choice([True, False]):  # 50% chance
                    db.execute(text("""
                        INSERT INTO training_enrollments (employee_id, training_id, enrollment_date, 
                        status, created_at, updated_at)
                        VALUES (:emp_id, :training_id, :enroll_date, :status, :created, :updated)
                    """), {
                        "emp_id": user_id,
                        "training_id": program_id,
                        "enroll_date": date.today(),
                        "status": random.choice(["enrolled", "in_progress", "completed", "dropped"]),
                        "created": datetime.now(),
                        "updated": datetime.now()
                    })
    
    # 7. Add assets
    print("Adding assets...")
    existing_assets = db.execute(text("SELECT COUNT(*) FROM assets")).fetchone()[0]
    if existing_assets == 0:
        asset_types = ["laptop", "desktop", "monitor", "phone", "tablet", "printer"]
        brands = ["Dell", "HP", "Lenovo", "Apple", "Samsung", "Canon"]
        
        for i in range(20):
            asset_type = random.choice(asset_types)
            brand = random.choice(brands)
            assigned_to = random.choice(user_ids) if random.choice([True, False]) else None
            
            db.execute(text("""
                INSERT INTO assets (asset_tag, asset_type, brand, model, serial_number, purchase_date, 
                purchase_cost, status, assigned_to, location, created_at, updated_at)
                VALUES (:tag, :type, :brand, :model, :serial, :purchase_date, :cost, :status, 
                :assigned, :location, :created, :updated)
            """), {
                "tag": f"AST{i+1:04d}",
                "type": asset_type,
                "brand": brand,
                "model": f"{brand}-{asset_type.upper()}-{random.randint(1000, 9999)}",
                "serial": f"SN{random.randint(100000, 999999)}",
                "purchase_date": date.today() - timedelta(days=random.randint(30, 1000)),
                "cost": round(random.uniform(500, 3000), 2),
                "status": "assigned" if assigned_to else random.choice(["available", "maintenance"]),
                "assigned": assigned_to,
                "location": f"Floor {random.randint(1, 5)}, Office Building A",
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 8. Add insurance claims
    print("Adding insurance claims...")
    claim_types = ["medical", "dental", "vision", "prescription", "emergency"]
    for user_id in user_ids[2:]:  # Employees
        existing = db.execute(text(
            "SELECT COUNT(*) FROM insurance_claims WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing < 2:  # Add up to 2 claims per employee
            for _ in range(2 - existing):
                claim_type = random.choice(claim_types)
                claim_amount = round(random.uniform(100, 2000), 2)
                
                db.execute(text("""
                    INSERT INTO insurance_claims (employee_id, claim_type, claim_amount, claim_date, 
                    description, status, approved_amount, created_at, updated_at)
                    VALUES (:emp_id, :type, :amount, :claim_date, :desc, :status, :approved, :created, :updated)
                """), {
                    "emp_id": user_id,
                    "type": claim_type,
                    "amount": claim_amount,
                    "claim_date": date.today() - timedelta(days=random.randint(1, 180)),
                    "desc": f"Sample {claim_type} insurance claim for medical expenses",
                    "status": random.choice(["pending", "approved", "rejected", "processing"]),
                    "approved": claim_amount * random.uniform(0.7, 1.0) if random.choice([True, False]) else None,
                    "created": datetime.now(),
                    "updated": datetime.now()
                })
    
    # 9. Add documents
    print("Adding documents...")
    doc_types = ["contract", "policy", "handbook", "certificate", "form", "report"]
    for user_id in user_ids:
        existing = db.execute(text(
            "SELECT COUNT(*) FROM documents WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing < 2:  # Add up to 2 documents per employee
            for _ in range(2 - existing):
                doc_type = random.choice(doc_types)
                db.execute(text("""
                    INSERT INTO documents (employee_id, document_type, title, file_path, uploaded_date, 
                    uploaded_by, created_at, updated_at)
                    VALUES (:emp_id, :type, :title, :path, :upload_date, :uploaded_by, :created, :updated)
                """), {
                    "emp_id": user_id,
                    "type": doc_type,
                    "title": f"Employee {doc_type} - {user_id}",
                    "path": f"/documents/{doc_type}_{user_id}_{random.randint(1000, 9999)}.pdf",
                    "upload_date": date.today() - timedelta(days=random.randint(1, 365)),
                    "uploaded_by": user_ids[0],  # Admin
                    "created": datetime.now(),
                    "updated": datetime.now()
                })
    
    # 10. Add notifications
    print("Adding notifications...")
    notification_types = ["leave_approved", "meeting_reminder", "policy_update", "training_enrollment", "payroll_processed"]
    for user_id in user_ids:
        existing = db.execute(text(
            "SELECT COUNT(*) FROM notifications WHERE user_id = :user_id"
        ), {"user_id": user_id}).fetchone()[0]
        
        if existing < 5:  # Add up to 5 notifications per user
            for _ in range(5 - existing):
                notif_type = random.choice(notification_types)
                db.execute(text("""
                    INSERT INTO notifications (user_id, title, message, notification_type, is_read, created_at, updated_at)
                    VALUES (:user_id, :title, :message, :type, :is_read, :created, :updated)
                """), {
                    "user_id": user_id,
                    "title": f"Sample {notif_type.replace('_', ' ')} notification",
                    "message": f"This is a sample notification about {notif_type.replace('_', ' ')} for testing purposes.",
                    "type": notif_type,
                    "is_read": random.choice([True, False]),
                    "created": datetime.now() - timedelta(days=random.randint(1, 30)),
                    "updated": datetime.now()
                })
    
    # Commit all changes
    db.commit()
    print("✓ All tables populated successfully!")
    
    # Print summary
    print("\n=== DATA SUMMARY ===")
    tables_to_check = [
        "users", "employees", "departments", "leaves", "attendance", 
        "performance_reviews", "payslips", "employee_requests", "complaints",
        "training_programs", "training_enrollments", "assets", "insurance_claims",
        "documents", "notifications"
    ]
    
    for table in tables_to_check:
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            print(f"{table}: {count} records")
        except Exception as e:
            print(f"{table}: Error - {e}")

if __name__ == "__main__":
    print("Populating all database tables with sample data...")
    populate_all_tables()
    db.close()
    print("\nDatabase population completed successfully!")
    print("\nLogin Credentials:")
    print("Admin: admin@hrm.com / admin123")
    print("HR: hr@hrm.com / hr123")
    print("Team Lead: teamlead@hrm.com / lead123")
    print("Employee: employee@hrm.com / emp123")