#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def setup_enhanced_profile():
    """Complete setup for enhanced profile system"""
    
    print("Setting up enhanced profile system...")
    
    # 1. Add profile columns to employees table
    print("\n1. Adding profile columns...")
    columns_to_add = [
        "blood_group VARCHAR",
        "qualification VARCHAR", 
        "work_schedule VARCHAR DEFAULT 'Standard (9:00 AM - 6:00 PM)'",
        "team_size INTEGER DEFAULT 0",
        "avatar_url VARCHAR",
        "cover_image_url VARCHAR",
        "emergency_contact_relationship VARCHAR",
        "emergency_contact_work_phone VARCHAR",
        "emergency_contact_home_phone VARCHAR", 
        "emergency_contact_address TEXT",
        "bonus_target VARCHAR",
        "stock_options VARCHAR",
        "last_salary_increase VARCHAR",
        "next_review_date VARCHAR"
    ]
    
    for column in columns_to_add:
        try:
            db.execute(text(f"ALTER TABLE employees ADD COLUMN {column}"))
            print(f"  Added: {column.split()[0]}")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  Exists: {column.split()[0]}")
            else:
                print(f"  Error: {column.split()[0]} - {e}")
    
    # 2. Create skills table
    print("\n2. Creating skills table...")
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS employee_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                skill_name VARCHAR NOT NULL,
                proficiency_level FLOAT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        """))
        print("  Skills table created")
    except Exception as e:
        print(f"  Skills table error: {e}")
    
    db.commit()
    
    # 3. Populate profile data
    print("\n3. Populating profile data...")
    import random
    
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    qualifications = [
        "Bachelor's in Computer Science",
        "Master's in Business Administration",
        "Bachelor's in Engineering", 
        "Master's in Computer Science",
        "Bachelor's in Business Administration"
    ]
    
    result = db.execute(text("SELECT id, user_id, position, salary FROM employees"))
    employees = result.fetchall()
    
    for emp_id, user_id, position, salary in employees:
        team_size = 0
        if position and any(title in position.lower() for title in ["coo", "ceo", "director"]):
            team_size = random.randint(20, 50)
        elif position and any(title in position.lower() for title in ["manager", "lead"]):
            team_size = random.randint(5, 15)
        elif position and "senior" in position.lower():
            team_size = random.randint(2, 8)
        
        bonus_percentage = random.randint(10, 20)
        stock_amount = random.randint(1000, 15000)
        
        db.execute(text("""
            UPDATE employees SET 
                blood_group = :blood_group,
                qualification = :qualification,
                work_schedule = 'Standard (9:00 AM - 6:00 PM)',
                team_size = :team_size,
                avatar_url = 'https://images.unsplash.com/photo-1580489944761-15a19d65463f?q=80&w=1961&auto=format&fit=crop',
                emergency_contact_relationship = 'Sister',
                emergency_contact_work_phone = '+1-555-123-4567',
                emergency_contact_home_phone = '22-33-44',
                emergency_contact_address = '123 Main Street, City, State 12345',
                bonus_target = :bonus_target,
                stock_options = :stock_options,
                last_salary_increase = 'Jun 15, 2023 (5%)',
                next_review_date = 'Jun 15, 2024'
            WHERE id = :emp_id
        """), {
            "emp_id": emp_id,
            "blood_group": random.choice(blood_groups),
            "qualification": random.choice(qualifications),
            "team_size": team_size,
            "bonus_target": f"{bonus_percentage}% annual target",
            "stock_options": f"{stock_amount:,} shares"
        })
    
    print(f"  Updated {len(employees)} employee profiles")
    
    # 4. Populate skills
    print("\n4. Populating skills...")
    skills_by_role = {
        "technical": ["Python Programming", "JavaScript", "React", "SQL", "AWS"],
        "management": ["Strategic Planning", "Team Leadership", "Project Management", "Budget Management"],
        "hr": ["Recruitment", "Employee Relations", "Performance Management", "Training & Development"],
        "general": ["Communication", "Problem Solving", "Time Management", "Analytical Thinking"]
    }
    
    for emp_id, user_id, position, salary in employees:
        selected_skills = []
        
        if position:
            pos_lower = position.lower()
            if any(tech in pos_lower for tech in ["developer", "engineer", "programmer"]):
                selected_skills.extend(random.sample(skills_by_role["technical"], 3))
                selected_skills.extend(random.sample(skills_by_role["general"], 2))
            elif any(mgmt in pos_lower for mgmt in ["manager", "director", "ceo", "coo"]):
                selected_skills.extend(random.sample(skills_by_role["management"], 3))
                selected_skills.extend(random.sample(skills_by_role["general"], 2))
            elif "hr" in pos_lower:
                selected_skills.extend(random.sample(skills_by_role["hr"], 3))
                selected_skills.extend(random.sample(skills_by_role["general"], 2))
            else:
                selected_skills.extend(random.sample(skills_by_role["general"], 4))
        else:
            selected_skills.extend(random.sample(skills_by_role["general"], 4))
        
        for skill_name in selected_skills:
            existing = db.execute(text(
                "SELECT COUNT(*) FROM employee_skills WHERE employee_id = :emp_id AND skill_name = :skill"
            ), {"emp_id": emp_id, "skill": skill_name}).fetchone()[0]
            
            if existing == 0:
                proficiency = round(random.uniform(70, 95), 1)
                db.execute(text(
                    "INSERT INTO employee_skills (employee_id, skill_name, proficiency_level) VALUES (:emp_id, :skill, :level)"
                ), {"emp_id": emp_id, "skill": skill_name, "level": proficiency})
    
    db.commit()
    
    # Verify setup
    print("\n5. Verification...")
    profile_count = db.execute(text("SELECT COUNT(*) FROM employees WHERE blood_group IS NOT NULL")).fetchone()[0]
    skills_count = db.execute(text("SELECT COUNT(*) FROM employee_skills")).fetchone()[0]
    
    print(f"  Employees with complete profiles: {profile_count}")
    print(f"  Total skills records: {skills_count}")
    print("\nEnhanced profile system setup completed successfully!")

if __name__ == "__main__":
    setup_enhanced_profile()
    db.close()