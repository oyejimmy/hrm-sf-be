#!/usr/bin/env python3

import sys
import os
from datetime import date, datetime
import uuid

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Complaint, ComplaintComment, User
from sqlalchemy.orm import Session

def init_sample_complaints():
    """Initialize sample complaint data for testing"""
    db = SessionLocal()
    
    try:
        # Check if complaints already exist
        existing_complaints = db.query(Complaint).count()
        if existing_complaints > 0:
            print(f"Complaints already exist ({existing_complaints} found). Skipping initialization.")
            return
        
        # Get sample users
        admin_user = db.query(User).filter(User.role == "admin").first()
        hr_user = db.query(User).filter(User.role == "hr").first()
        employee_user = db.query(User).filter(User.role == "employee").first()
        
        if not admin_user or not hr_user or not employee_user:
            print("Required users not found. Please run init_db.py first.")
            return
        
        # Sample complaints data
        sample_complaints = [
            {
                "employee_id": employee_user.id,
                "tracking_id": f"CMP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                "title": "Workplace Harassment Issue",
                "description": "I am experiencing inappropriate behavior from a colleague that makes me uncomfortable in the workplace. This has been ongoing for several weeks and affects my ability to work effectively.",
                "category": "harassment",
                "priority": "high",
                "status": "pending"
            },
            {
                "employee_id": employee_user.id,
                "tracking_id": f"CMP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                "title": "Policy Violation Concern",
                "description": "There seems to be a violation of company policy regarding work hours and overtime compensation. I would like this to be reviewed and addressed.",
                "category": "policy_violation",
                "priority": "medium",
                "status": "resolved",
                "assigned_to": hr_user.id,
                "resolution": "Issue has been reviewed and resolved. Policy clarification has been provided to all team members.",
                "resolved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "tracking_id": f"CMP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                "title": "Unsafe Working Conditions",
                "description": "The warehouse area has several safety hazards including exposed wiring and blocked emergency exits. This poses a serious risk to employee safety.",
                "category": "workplace_safety",
                "priority": "high",
                "status": "in_progress",
                "assigned_to": admin_user.id
            },
            {
                "employee_id": employee_user.id,
                "tracking_id": f"CMP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                "title": "Discrimination in Promotion Process",
                "description": "I believe there has been discriminatory practices in the recent promotion decisions. I would like this matter to be investigated thoroughly.",
                "category": "discrimination",
                "priority": "high",
                "status": "pending"
            },
            {
                "employee_id": employee_user.id,
                "tracking_id": f"CMP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                "title": "Equipment Malfunction",
                "description": "My computer equipment has been malfunctioning for the past week, significantly impacting my productivity. IT support has been unresponsive.",
                "category": "technical_issue",
                "priority": "medium",
                "status": "resolved",
                "assigned_to": admin_user.id,
                "resolution": "Equipment has been replaced and IT support process has been improved.",
                "resolved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "tracking_id": f"CMP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                "title": "Management Communication Issues",
                "description": "There are ongoing communication issues with my direct supervisor that are affecting team morale and project delivery.",
                "category": "management_issue",
                "priority": "medium",
                "status": "in_progress",
                "assigned_to": hr_user.id
            },
            {
                "employee_id": employee_user.id,
                "tracking_id": f"CMP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                "title": "Workplace Environment Concern",
                "description": "The office temperature is consistently too cold, and several employees have complained about this affecting their comfort and productivity.",
                "category": "other",
                "priority": "low",
                "status": "resolved",
                "resolution": "HVAC system has been adjusted and temperature monitoring implemented.",
                "resolved_at": datetime.now()
            }
        ]
        
        # Create complaint records
        created_complaints = []
        for complaint_data in sample_complaints:
            complaint = Complaint(**complaint_data)
            db.add(complaint)
            created_complaints.append(complaint)
        
        db.commit()
        
        # Refresh to get IDs
        for complaint in created_complaints:
            db.refresh(complaint)
        
        print(f"Successfully created {len(created_complaints)} sample complaints:")
        for complaint in created_complaints:
            print(f"  - {complaint.title} ({complaint.category}) - {complaint.status}")
        
        # Create some sample comments
        sample_comments = [
            {
                "complaint_id": created_complaints[1].id,  # Policy violation complaint
                "user_id": hr_user.id,
                "content": "Thank you for bringing this to our attention. We are reviewing the policy and will provide clarification soon.",
                "is_internal": False
            },
            {
                "complaint_id": created_complaints[2].id,  # Safety complaint
                "user_id": admin_user.id,
                "content": "Safety inspection has been scheduled for next week. We will address all identified hazards immediately.",
                "is_internal": False
            },
            {
                "complaint_id": created_complaints[2].id,  # Safety complaint - internal comment
                "user_id": admin_user.id,
                "content": "Internal note: Contact facilities management to prioritize electrical work.",
                "is_internal": True
            }
        ]
        
        created_comments = []
        for comment_data in sample_comments:
            comment = ComplaintComment(**comment_data)
            db.add(comment)
            created_comments.append(comment)
        
        db.commit()
        
        print(f"\\nSuccessfully created {len(created_comments)} sample comments")
        print("\\nComplaint initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing complaints: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing sample complaint data...")
    init_sample_complaints()