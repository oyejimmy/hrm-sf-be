#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine
from datetime import datetime, date, timedelta
import random
import json

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def populate_all_tables():
    """Populate all tables with sample data using correct schema"""
    
    # Get existing user IDs
    result = db.execute(text("SELECT id FROM users"))
    user_ids = [row[0] for row in result.fetchall()]
    print(f"Found {len(user_ids)} users: {user_ids}")
    
    # Get department IDs
    dept_result = db.execute(text("SELECT id FROM departments"))
    dept_ids = [row[0] for row in dept_result.fetchall()]
    
    # 1. Add attendance records
    print("Adding attendance records...")
    for user_id in user_ids:
        for days_back in range(20):
            att_date = date.today() - timedelta(days=days_back)
            if att_date.weekday() < 5:  # Weekdays only
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
                overall_rating, goals_achievement, strengths, areas_for_improvement, goals_next_period, 
                comments, status, created_at, updated_at)
                VALUES (:emp_id, :reviewer, :start_date, :end_date, :rating, :goals_ach, :strengths, 
                :improvements, :next_goals, :comments, :status, :created, :updated)
            """), {
                "emp_id": user_id,
                "reviewer": user_ids[0],
                "start_date": date.today() - timedelta(days=365),
                "end_date": date.today() - timedelta(days=1),
                "rating": str(round(random.uniform(3.5, 4.8), 1)),
                "goals_ach": round(random.uniform(0.7, 0.95), 2),
                "strengths": "Strong technical skills, good team collaboration, meets deadlines consistently",
                "improvements": "Communication skills, time management, leadership development",
                "next_goals": "Lead a project, improve presentation skills, mentor junior team members",
                "comments": "Good overall performance with room for growth in leadership areas",
                "status": "completed",
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 3. Add payslips
    print("Adding payslips...")
    for user_id in user_ids:
        salary_result = db.execute(text(
            "SELECT salary FROM employees WHERE user_id = :user_id"
        ), {"user_id": user_id}).fetchone()
        
        salary = salary_result[0] if salary_result and salary_result[0] else 50000
        
        existing = db.execute(text(
            "SELECT COUNT(*) FROM payslips WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing == 0:
            basic_salary = salary
            gross_salary = basic_salary * 1.15
            total_deductions = gross_salary * 0.25
            net_salary = gross_salary - total_deductions
            
            db.execute(text("""
                INSERT INTO payslips (employee_id, pay_period_start, pay_period_end, pay_date, 
                basic_salary, gross_salary, net_salary, total_earnings, total_deductions, 
                status, payslip_number, generated_by, created_at, updated_at)
                VALUES (:emp_id, :start_date, :end_date, :pay_date, :basic, :gross, :net, 
                :earnings, :deductions, :status, :payslip_num, :generated_by, :created, :updated)
            """), {
                "emp_id": user_id,
                "start_date": date.today().replace(day=1),
                "end_date": date.today(),
                "pay_date": date.today(),
                "basic": basic_salary,
                "gross": gross_salary,
                "net": net_salary,
                "earnings": gross_salary,
                "deductions": total_deductions,
                "status": "paid",
                "payslip_num": f"PAY{user_id:03d}{date.today().strftime('%Y%m')}",
                "generated_by": user_ids[0],
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 4. Add employee requests
    print("Adding employee requests...")
    request_types = ["equipment", "leave_extension", "training", "transfer", "reimbursement"]
    for user_id in user_ids[2:]:  # Employees only
        existing = db.execute(text(
            "SELECT COUNT(*) FROM employee_requests WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing == 0:
            req_type = random.choice(request_types)
            db.execute(text("""
                INSERT INTO employee_requests (employee_id, request_type, subject, details, status, 
                priority, amount, start_date, end_date, approver_id, created_at, updated_at)
                VALUES (:emp_id, :type, :subject, :details, :status, :priority, :amount, 
                :start_date, :end_date, :approver, :created, :updated)
            """), {
                "emp_id": user_id,
                "type": req_type,
                "subject": f"Request for {req_type.replace('_', ' ')}",
                "details": f"Sample {req_type} request with detailed description of requirements",
                "status": random.choice(["pending", "approved", "rejected"]),
                "priority": random.choice(["low", "medium", "high"]),
                "amount": round(random.uniform(100, 5000), 2) if req_type == "reimbursement" else None,
                "start_date": date.today() + timedelta(days=random.randint(1, 30)),
                "end_date": date.today() + timedelta(days=random.randint(31, 90)),
                "approver": user_ids[1],  # HR
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 5. Add complaints
    print("Adding complaints...")
    categories = ["workplace_environment", "harassment", "policy_violation", "safety", "discrimination"]
    for user_id in user_ids[3:]:  # Some employees
        existing = db.execute(text(
            "SELECT COUNT(*) FROM complaints WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing == 0:
            category = random.choice(categories)
            tracking_id = f"COMP{user_id:03d}{random.randint(1000, 9999)}"
            
            db.execute(text("""
                INSERT INTO complaints (employee_id, tracking_id, title, description, category, 
                priority, status, assigned_to, created_at, updated_at)
                VALUES (:emp_id, :tracking, :title, :desc, :category, :priority, :status, 
                :assigned, :created, :updated)
            """), {
                "emp_id": user_id,
                "tracking": tracking_id,
                "title": f"Complaint regarding {category.replace('_', ' ')}",
                "desc": f"Detailed description of the {category.replace('_', ' ')} issue that needs attention and resolution",
                "category": category,
                "priority": random.choice(["low", "medium", "high", "critical"]),
                "status": random.choice(["open", "in_progress", "resolved", "closed"]),
                "assigned": user_ids[1],  # HR
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 6. Add training programs
    print("Adding training programs...")
    existing_programs = db.execute(text("SELECT COUNT(*) FROM training_programs")).fetchone()[0]
    if existing_programs == 0:
        programs = [
            ("Python Programming Fundamentals", "programming", "beginner", 40, "John Smith", 25, True),
            ("Leadership Development", "management", "intermediate", 32, "Sarah Johnson", 15, False),
            ("Data Analysis with Excel", "analytics", "beginner", 24, "Mike Davis", 20, False),
            ("Communication Skills", "soft_skills", "beginner", 16, "Lisa Brown", 30, True),
            ("Project Management", "management", "intermediate", 48, "David Wilson", 12, False)
        ]
        
        program_ids = []
        for title, category, level, duration, instructor, max_participants, is_mandatory in programs:
            learning_objectives = json.dumps([
                f"Understand {title.lower()} concepts",
                f"Apply {category} techniques",
                f"Complete practical exercises"
            ])
            
            materials = json.dumps([
                "Course handbook",
                "Online resources",
                "Practice exercises"
            ])
            
            result = db.execute(text("""
                INSERT INTO training_programs (title, description, category, level, duration_hours, 
                instructor, max_participants, learning_objectives, materials, is_mandatory, 
                is_active, created_by, created_at, updated_at)
                VALUES (:title, :desc, :category, :level, :duration, :instructor, :max_part, 
                :objectives, :materials, :mandatory, :active, :created_by, :created, :updated)
                RETURNING id
            """), {
                "title": title,
                "desc": f"Comprehensive {title.lower()} training program for professional development",
                "category": category,
                "level": level,
                "duration": duration,
                "instructor": instructor,
                "max_part": max_participants,
                "objectives": learning_objectives,
                "materials": materials,
                "mandatory": is_mandatory,
                "active": True,
                "created_by": user_ids[0],
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
        
        for i in range(20):
            asset_type = random.choice(asset_types)
            assigned_to = random.choice(user_ids) if random.choice([True, False]) else None
            
            db.execute(text("""
                INSERT INTO assets (name, asset_type, serial_number, specifications, purchase_date, 
                purchase_cost, warranty_expiry, status, condition, location, department_id, 
                assigned_to, assigned_date, created_at, updated_at)
                VALUES (:name, :type, :serial, :specs, :purchase_date, :cost, :warranty, 
                :status, :condition, :location, :dept_id, :assigned, :assigned_date, :created, :updated)
            """), {
                "name": f"{asset_type.title()} {i+1:03d}",
                "type": asset_type,
                "serial": f"SN{random.randint(100000, 999999)}",
                "specs": f"Standard {asset_type} with basic configuration",
                "purchase_date": date.today() - timedelta(days=random.randint(30, 1000)),
                "cost": round(random.uniform(500, 3000), 2),
                "warranty": date.today() + timedelta(days=random.randint(365, 1095)),
                "status": "assigned" if assigned_to else random.choice(["available", "maintenance"]),
                "condition": random.choice(["excellent", "good", "fair"]),
                "location": f"Floor {random.randint(1, 5)}, Office Building A",
                "dept_id": random.choice(dept_ids) if dept_ids else None,
                "assigned": assigned_to,
                "assigned_date": date.today() if assigned_to else None,
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 8. Add insurance claims (simplified)
    print("Adding insurance claims...")
    claim_types = ["medical", "dental", "vision", "prescription"]
    for user_id in user_ids[2:]:  # Employees
        existing = db.execute(text(
            "SELECT COUNT(*) FROM insurance_claims WHERE policy_id = :user_id"
        ), {"user_id": user_id}).fetchone()[0]
        
        if existing == 0:
            claim_type = random.choice(claim_types)
            claim_number = f"CLM{user_id:03d}{random.randint(1000, 9999)}"
            total_amount = round(random.uniform(500, 5000), 2)
            claimed_amount = total_amount
            approved_amount = round(total_amount * random.uniform(0.8, 1.0), 2)
            
            db.execute(text("""
                INSERT INTO insurance_claims (policy_id, claim_number, patient_name, patient_relationship, 
                claim_type, treatment_date, hospital_name, diagnosis, total_bill_amount, claimed_amount, 
                approved_amount, status, submission_date, created_at, updated_at)
                VALUES (:policy_id, :claim_num, :patient, :relationship, :type, :treatment_date, 
                :hospital, :diagnosis, :total, :claimed, :approved, :status, :submission, :created, :updated)
            """), {
                "policy_id": user_id,
                "claim_num": claim_number,
                "patient": "Employee Self",
                "relationship": "self",
                "type": claim_type,
                "treatment_date": date.today() - timedelta(days=random.randint(1, 90)),
                "hospital": f"Sample {claim_type.title()} Hospital",
                "diagnosis": f"Sample {claim_type} treatment and diagnosis",
                "total": total_amount,
                "claimed": claimed_amount,
                "approved": approved_amount,
                "status": random.choice(["submitted", "under_review", "approved", "paid"]),
                "submission": date.today() - timedelta(days=random.randint(1, 30)),
                "created": datetime.now(),
                "updated": datetime.now()
            })
    
    # 9. Add documents
    print("Adding documents...")
    doc_types = ["contract", "policy", "handbook", "certificate", "form"]
    categories = ["employment", "training", "compliance", "personal", "administrative"]
    
    for user_id in user_ids:
        existing = db.execute(text(
            "SELECT COUNT(*) FROM documents WHERE employee_id = :emp_id"
        ), {"emp_id": user_id}).fetchone()[0]
        
        if existing < 2:  # Add up to 2 documents per employee
            for _ in range(2 - existing):
                doc_type = random.choice(doc_types)
                category = random.choice(categories)
                file_name = f"{doc_type}_{user_id}_{random.randint(1000, 9999)}.pdf"
                
                db.execute(text("""
                    INSERT INTO documents (employee_id, document_type, category, file_name, file_path, 
                    file_size, mime_type, status, description, is_required, uploaded_by, created_at, updated_at)
                    VALUES (:emp_id, :type, :category, :filename, :path, :size, :mime, :status, 
                    :desc, :required, :uploaded_by, :created, :updated)
                """), {
                    "emp_id": user_id,
                    "type": doc_type,
                    "category": category,
                    "filename": file_name,
                    "path": f"/documents/{category}/{file_name}",
                    "size": random.randint(50000, 500000),
                    "mime": "application/pdf",
                    "status": random.choice(["active", "pending", "approved"]),
                    "desc": f"Employee {doc_type} document for {category} purposes",
                    "required": random.choice([True, False]),
                    "uploaded_by": user_ids[0],  # Admin
                    "created": datetime.now(),
                    "updated": datetime.now()
                })
    
    # 10. Add notifications
    print("Adding notifications...")
    notification_types = ["leave_approved", "meeting_reminder", "policy_update", "training_enrollment", "payroll_processed"]
    priorities = ["low", "medium", "high", "urgent"]
    
    for user_id in user_ids:
        existing = db.execute(text(
            "SELECT COUNT(*) FROM notifications WHERE recipient_id = :user_id"
        ), {"user_id": user_id}).fetchone()[0]
        
        if existing < 5:  # Add up to 5 notifications per user
            for _ in range(5 - existing):
                notif_type = random.choice(notification_types)
                priority = random.choice(priorities)
                
                db.execute(text("""
                    INSERT INTO notifications (recipient_id, sender_id, title, message, notification_type, 
                    priority, is_read, is_system_generated, created_at)
                    VALUES (:recipient, :sender, :title, :message, :type, :priority, :is_read, 
                    :system_gen, :created)
                """), {
                    "recipient": user_id,
                    "sender": user_ids[0],  # Admin
                    "title": f"Sample {notif_type.replace('_', ' ')} notification",
                    "message": f"This is a sample notification about {notif_type.replace('_', ' ')} for testing purposes. Please review and take appropriate action if needed.",
                    "type": notif_type,
                    "priority": priority,
                    "is_read": random.choice([True, False]),
                    "system_gen": True,
                    "created": datetime.now() - timedelta(days=random.randint(1, 30))
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