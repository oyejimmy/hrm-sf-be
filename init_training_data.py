#!/usr/bin/env python3
"""
Initialize Training & Development data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.training import TrainingProgram, TrainingEnrollment, TrainingRoadmap
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from datetime import datetime, date, timedelta
import json

def init_training_data():
    db = SessionLocal()
    try:
        # Check if training data already exists
        existing_programs = db.query(TrainingProgram).count()
        if existing_programs > 0:
            print("Training data already exists. Skipping initialization.")
            return

        # Get some users and departments for assignments
        users = db.query(User).limit(5).all()
        departments = db.query(Department).all()
        
        if not users:
            print("No users found. Please create users first.")
            return
        
        if not departments:
            print("No departments found. Please create departments first.")
            return

        # Create Training Programs
        training_programs = [
            {
                "title": "Advanced React Development",
                "description": "Learn advanced React patterns, state management, and performance optimization techniques.",
                "category": "Software Development",
                "level": "advanced",
                "duration_hours": 8.0,
                "instructor": "Jane Smith",
                "max_participants": 25,
                "prerequisites": "Basic React knowledge, JavaScript ES6+",
                "learning_objectives": [
                    "Master advanced React patterns",
                    "Implement state management solutions",
                    "Optimize React performance",
                    "Build scalable React applications"
                ],
                "materials": [
                    "https://react.dev/learn",
                    "https://redux.js.org/",
                    "https://nextjs.org/docs"
                ],
                "is_mandatory": False,
                "is_active": True,
                "created_by": users[0].id
            },
            {
                "title": "Leadership Fundamentals",
                "description": "Develop essential leadership skills to effectively manage teams and drive organizational success.",
                "category": "Leadership",
                "level": "intermediate",
                "duration_hours": 6.0,
                "instructor": "Michael Johnson",
                "max_participants": 20,
                "prerequisites": "Management experience or team lead role",
                "learning_objectives": [
                    "Understand leadership principles",
                    "Develop team management skills",
                    "Learn conflict resolution",
                    "Build communication strategies"
                ],
                "materials": [
                    "Leadership handbook",
                    "Team management guide",
                    "Communication templates"
                ],
                "is_mandatory": False,
                "is_active": True,
                "created_by": users[0].id
            },
            {
                "title": "Data Visualization with D3.js",
                "description": "Master the art of creating interactive and engaging data visualizations using D3.js library.",
                "category": "Data Science",
                "level": "intermediate",
                "duration_hours": 10.0,
                "instructor": "Sarah Williams",
                "max_participants": 15,
                "prerequisites": "JavaScript, HTML, CSS basics",
                "learning_objectives": [
                    "Learn D3.js fundamentals",
                    "Create interactive visualizations",
                    "Implement data binding",
                    "Design responsive charts"
                ],
                "materials": [
                    "https://d3js.org/",
                    "D3.js documentation",
                    "Sample datasets"
                ],
                "is_mandatory": False,
                "is_active": True,
                "created_by": users[0].id
            },
            {
                "title": "Effective Communication Skills",
                "description": "Improve your communication skills for better workplace collaboration and professional relationships.",
                "category": "Soft Skills",
                "level": "beginner",
                "duration_hours": 4.0,
                "instructor": "David Brown",
                "max_participants": 30,
                "prerequisites": "None",
                "learning_objectives": [
                    "Improve verbal communication",
                    "Enhance written communication",
                    "Develop active listening skills",
                    "Master presentation techniques"
                ],
                "materials": [
                    "Communication workbook",
                    "Presentation templates",
                    "Practice exercises"
                ],
                "is_mandatory": True,
                "is_active": True,
                "created_by": users[0].id
            },
            {
                "title": "Cloud Infrastructure with AWS",
                "description": "Learn to design, deploy, and manage scalable and reliable applications on AWS cloud platform.",
                "category": "Cloud Computing",
                "level": "advanced",
                "duration_hours": 12.0,
                "instructor": "Emily Chen",
                "max_participants": 20,
                "prerequisites": "Basic cloud computing knowledge",
                "learning_objectives": [
                    "Understand AWS services",
                    "Design cloud architectures",
                    "Implement security best practices",
                    "Optimize cloud costs"
                ],
                "materials": [
                    "AWS documentation",
                    "Hands-on labs",
                    "Architecture diagrams"
                ],
                "is_mandatory": False,
                "is_active": True,
                "created_by": users[0].id
            },
            {
                "title": "Agile Project Management",
                "description": "Master Agile methodologies to deliver projects efficiently and adapt to changing requirements.",
                "category": "Project Management",
                "level": "intermediate",
                "duration_hours": 7.0,
                "instructor": "Robert Taylor",
                "max_participants": 25,
                "prerequisites": "Basic project management knowledge",
                "learning_objectives": [
                    "Understand Agile principles",
                    "Implement Scrum methodology",
                    "Manage project backlogs",
                    "Facilitate team ceremonies"
                ],
                "materials": [
                    "Agile manifesto",
                    "Scrum guide",
                    "Project templates"
                ],
                "is_mandatory": False,
                "is_active": True,
                "created_by": users[0].id
            }
        ]

        # Insert training programs
        for program_data in training_programs:
            program = TrainingProgram(**program_data)
            db.add(program)
        
        db.commit()
        print(f"Created {len(training_programs)} training programs")

        # Get the created programs
        programs = db.query(TrainingProgram).all()

        # Create Training Enrollments
        enrollments_data = []
        for i, user in enumerate(users):
            # Assign each user to 2-3 random programs
            import random
            user_programs = random.sample(programs, min(3, len(programs)))
            
            for j, program in enumerate(user_programs):
                statuses = ["enrolled", "in_progress", "completed"]
                status = statuses[j % len(statuses)]
                
                progress = 0
                completion_date = None
                if status == "in_progress":
                    progress = random.randint(20, 80)
                elif status == "completed":
                    progress = 100
                    completion_date = date.today() - timedelta(days=random.randint(1, 30))

                enrollment = TrainingEnrollment(
                    employee_id=user.id,
                    program_id=program.id,
                    enrollment_date=date.today() - timedelta(days=random.randint(1, 60)),
                    status=status,
                    progress_percentage=progress,
                    completion_date=completion_date,
                    certificate_issued=status == "completed",
                    feedback_rating=random.randint(3, 5) if status == "completed" else None,
                    assigned_by=users[0].id
                )
                enrollments_data.append(enrollment)

        # Insert enrollments
        for enrollment in enrollments_data:
            db.add(enrollment)
        
        db.commit()
        print(f"Created {len(enrollments_data)} training enrollments")

        # Create Training Roadmaps
        roadmaps_data = [
            {
                "title": "Frontend Developer Path",
                "description": "Become a proficient frontend developer with this comprehensive learning path",
                "department_id": departments[0].id if departments else None,
                "position": "Frontend Developer",
                "milestones": [
                    {
                        "id": "1",
                        "topic": "HTML & CSS Fundamentals",
                        "description": "Master the basics of HTML and CSS",
                        "resources": ["https://developer.mozilla.org/", "CSS Grid Guide"],
                        "estimatedTime": "2 weeks",
                        "completed": False
                    },
                    {
                        "id": "2",
                        "topic": "JavaScript ES6+",
                        "description": "Learn modern JavaScript features",
                        "resources": ["https://javascript.info/", "ES6 Tutorial"],
                        "estimatedTime": "3 weeks",
                        "completed": False
                    },
                    {
                        "id": "3",
                        "topic": "React Development",
                        "description": "Build applications with React",
                        "resources": ["https://react.dev", "React Tutorial"],
                        "estimatedTime": "4 weeks",
                        "completed": False
                    },
                    {
                        "id": "4",
                        "topic": "State Management",
                        "description": "Learn Redux and Context API",
                        "resources": ["https://redux.js.org/", "Context API Guide"],
                        "estimatedTime": "2 weeks",
                        "completed": False
                    }
                ],
                "estimated_duration_months": 3,
                "is_active": True,
                "created_by": users[0].id
            },
            {
                "title": "Cloud Architect Path",
                "description": "Master cloud architecture concepts and implementation strategies",
                "department_id": departments[1].id if len(departments) > 1 else departments[0].id,
                "position": "Cloud Architect",
                "milestones": [
                    {
                        "id": "1",
                        "topic": "Cloud Fundamentals",
                        "description": "Understand cloud computing basics",
                        "resources": ["AWS Fundamentals", "Cloud Concepts"],
                        "estimatedTime": "2 weeks",
                        "completed": False
                    },
                    {
                        "id": "2",
                        "topic": "AWS Services",
                        "description": "Learn core AWS services",
                        "resources": ["AWS Documentation", "Service Overview"],
                        "estimatedTime": "4 weeks",
                        "completed": False
                    },
                    {
                        "id": "3",
                        "topic": "Architecture Design",
                        "description": "Design scalable cloud architectures",
                        "resources": ["Architecture Patterns", "Best Practices"],
                        "estimatedTime": "3 weeks",
                        "completed": False
                    }
                ],
                "estimated_duration_months": 2,
                "is_active": True,
                "created_by": users[0].id
            },
            {
                "title": "Leadership Development Path",
                "description": "Develop essential leadership skills for management roles",
                "department_id": departments[0].id,
                "position": "Team Lead",
                "milestones": [
                    {
                        "id": "1",
                        "topic": "Leadership Principles",
                        "description": "Learn fundamental leadership concepts",
                        "resources": ["Leadership Books", "Case Studies"],
                        "estimatedTime": "2 weeks",
                        "completed": False
                    },
                    {
                        "id": "2",
                        "topic": "Team Management",
                        "description": "Manage and motivate teams effectively",
                        "resources": ["Management Guide", "Team Building"],
                        "estimatedTime": "3 weeks",
                        "completed": False
                    },
                    {
                        "id": "3",
                        "topic": "Communication Skills",
                        "description": "Master professional communication",
                        "resources": ["Communication Workshop", "Presentation Skills"],
                        "estimatedTime": "2 weeks",
                        "completed": False
                    }
                ],
                "estimated_duration_months": 2,
                "is_active": True,
                "created_by": users[0].id
            }
        ]

        # Insert roadmaps
        for roadmap_data in roadmaps_data:
            roadmap = TrainingRoadmap(**roadmap_data)
            db.add(roadmap)
        
        db.commit()
        print(f"Created {len(roadmaps_data)} training roadmaps")

        print("Training data initialization completed successfully!")

    except Exception as e:
        print(f"Error initializing training data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_training_data()
