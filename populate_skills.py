#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine
import random

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def create_skills_table():
    """Create employee_skills table"""
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
        db.commit()
        print("employee_skills table created")
    except Exception as e:
        print(f"Skills table creation: {e}")

def populate_skills():
    """Populate skills for all employees"""
    
    # Skill categories by role
    skills_by_role = {
        "technical": [
            "Python Programming", "JavaScript", "React", "Node.js", "SQL", 
            "Docker", "AWS", "Git", "API Development", "Database Design"
        ],
        "management": [
            "Strategic Planning", "Team Leadership", "Project Management", 
            "Budget Management", "Process Improvement", "Stakeholder Management"
        ],
        "hr": [
            "Recruitment", "Employee Relations", "Performance Management",
            "Training & Development", "Compensation Planning", "HR Analytics"
        ],
        "general": [
            "Communication", "Problem Solving", "Time Management", 
            "Analytical Thinking", "Collaboration", "Adaptability"
        ]
    }
    
    # Get all employees with their positions
    result = db.execute(text("SELECT id, position FROM employees"))
    employees = result.fetchall()
    
    print(f"Adding skills for {len(employees)} employees...")
    
    for emp_id, position in employees:
        # Determine skill categories based on position
        selected_skills = []
        
        if position:
            pos_lower = position.lower()
            if any(tech in pos_lower for tech in ["developer", "engineer", "programmer", "technical"]):
                selected_skills.extend(random.sample(skills_by_role["technical"], 4))
                selected_skills.extend(random.sample(skills_by_role["general"], 2))
            elif any(mgmt in pos_lower for mgmt in ["manager", "director", "ceo", "coo", "lead"]):
                selected_skills.extend(random.sample(skills_by_role["management"], 4))
                selected_skills.extend(random.sample(skills_by_role["general"], 2))
            elif "hr" in pos_lower:
                selected_skills.extend(random.sample(skills_by_role["hr"], 4))
                selected_skills.extend(random.sample(skills_by_role["general"], 2))
            else:
                selected_skills.extend(random.sample(skills_by_role["general"], 5))
        else:
            selected_skills.extend(random.sample(skills_by_role["general"], 5))
        
        # Add skills to database
        for skill_name in selected_skills:
            # Check if skill already exists
            existing = db.execute(text(
                "SELECT COUNT(*) FROM employee_skills WHERE employee_id = :emp_id AND skill_name = :skill"
            ), {"emp_id": emp_id, "skill": skill_name}).fetchone()[0]
            
            if existing == 0:
                proficiency = round(random.uniform(60, 95), 1)
                db.execute(text(
                    "INSERT INTO employee_skills (employee_id, skill_name, proficiency_level) VALUES (:emp_id, :skill, :level)"
                ), {"emp_id": emp_id, "skill": skill_name, "level": proficiency})
    
    db.commit()
    print("Skills populated successfully!")
    
    # Verify
    result = db.execute(text("SELECT COUNT(*) FROM employee_skills"))
    count = result.fetchone()[0]
    print(f"Total skills records: {count}")

if __name__ == "__main__":
    create_skills_table()
    populate_skills()
    db.close()