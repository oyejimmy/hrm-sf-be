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

def populate_profile_data():
    """Populate enhanced profile data for all employees"""
    
    # Sample data
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    qualifications = [
        "Bachelor's in Computer Science",
        "Master's in Business Administration", 
        "Bachelor's in Engineering",
        "Master's in Computer Science",
        "Bachelor's in Business Administration",
        "Master's in Engineering",
        "PhD in Computer Science"
    ]
    
    work_schedules = [
        "Standard (9:00 AM - 6:00 PM)",
        "Flexible (8:00 AM - 5:00 PM)",
        "Remote (10:00 AM - 7:00 PM)",
        "Hybrid (9:00 AM - 6:00 PM)"
    ]
    
    avatar_urls = [
        "https://images.unsplash.com/photo-1580489944761-15a19d65463f?q=80&w=1961&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=1887&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1494790108755-2616b612b786?q=80&w=1887&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=1770&auto=format&fit=crop"
    ]
    
    cover_images = [
        "https://images.unsplash.com/photo-1497366216548-37526070297c?q=80&w=2069&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1497366754035-f200968a6e72?q=80&w=2069&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
    ]
    
    relationships = ["Sister", "Brother", "Spouse", "Parent", "Friend"]
    
    # Get all employees
    result = db.execute(text("SELECT id, user_id, position, salary FROM employees"))
    employees = result.fetchall()
    
    print(f"Updating profile data for {len(employees)} employees...")
    
    for emp in employees:
        emp_id, user_id, position, salary = emp
        
        # Determine team size based on position
        team_size = 0
        if position and any(title in position.lower() for title in ["coo", "ceo", "director"]):
            team_size = random.randint(20, 50)
        elif position and any(title in position.lower() for title in ["manager", "lead"]):
            team_size = random.randint(5, 15)
        elif position and "senior" in position.lower():
            team_size = random.randint(2, 8)
        
        # Calculate compensation details
        bonus_percentage = random.randint(10, 20)
        stock_amount = random.randint(1000, 15000)
        increase_percentage = random.randint(3, 8)
        
        # Emergency contact details
        emergency_name = random.choice(["John Smith", "Sarah Johnson", "Mike Davis", "Lisa Wilson", "David Brown"])
        relationship = random.choice(relationships)
        
        update_data = {
            "emp_id": emp_id,
            "blood_group": random.choice(blood_groups),
            "qualification": random.choice(qualifications),
            "work_schedule": random.choice(work_schedules),
            "team_size": team_size,
            "avatar_url": random.choice(avatar_urls),
            "cover_image_url": random.choice(cover_images),
            "emergency_contact_relationship": relationship,
            "emergency_contact_work_phone": f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
            "emergency_contact_home_phone": f"{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(10,99)}",
            "emergency_contact_address": f"{random.randint(100,999)} Main Street, City, State {random.randint(10000,99999)}",
            "bonus_target": f"{bonus_percentage}% annual target",
            "stock_options": f"{stock_amount:,} shares",
            "last_salary_increase": f"Jun 15, 2023 ({increase_percentage}%)",
            "next_review_date": "Jun 15, 2024"
        }
        
        # Update emergency contact name if not set
        db.execute(text("""
            UPDATE employees SET 
                emergency_contact_name = COALESCE(emergency_contact_name, :emergency_name),
                blood_group = :blood_group,
                qualification = :qualification,
                work_schedule = :work_schedule,
                team_size = :team_size,
                avatar_url = :avatar_url,
                cover_image_url = :cover_image_url,
                emergency_contact_relationship = :emergency_contact_relationship,
                emergency_contact_work_phone = :emergency_contact_work_phone,
                emergency_contact_home_phone = :emergency_contact_home_phone,
                emergency_contact_address = :emergency_contact_address,
                bonus_target = :bonus_target,
                stock_options = :stock_options,
                last_salary_increase = :last_salary_increase,
                next_review_date = :next_review_date
            WHERE id = :emp_id
        """), {**update_data, "emergency_name": emergency_name})
    
    db.commit()
    print("Profile data populated successfully!")
    
    # Verify data
    result = db.execute(text("SELECT COUNT(*) FROM employees WHERE blood_group IS NOT NULL"))
    count = result.fetchone()[0]
    print(f"{count} employees now have complete profile data")

if __name__ == "__main__":
    populate_profile_data()
    db.close()