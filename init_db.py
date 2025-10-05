from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.position import Position
from app.models.attendance import Attendance, BreakRecord
from app.models.notification import Announcement, Notification, AnnouncementRead, Holiday, Task
from app.auth import get_password_hash
from datetime import date

def init_database():
    """Initialize database with clean default data"""
    # Drop all tables and recreate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create comprehensive software house departments
        departments = [
            {"name": "Software Development", "description": "Handles coding, application development, and system architecture."},
            {"name": "AI & Data Science", "description": "Focuses on machine learning, AI research, and data engineering."},
            {"name": "Quality Assurance", "description": "Ensures product quality through testing and automation."},
            {"name": "Design", "description": "Responsible for UI/UX design, graphics, and creative direction."},
            {"name": "Project & Product Management", "description": "Oversees project delivery and product lifecycle."},
            {"name": "IT & Infrastructure", "description": "Manages IT systems, networks, databases, and DevOps."},
            {"name": "Sales & Marketing", "description": "Handles sales, business development, and marketing strategy."},
            {"name": "HR & Operations", "description": "Responsible for HR, recruitment, and company operations."},
            {"name": "Leadership", "description": "Executive management and company leadership."},
        ]
        
        for dept_data in departments:
            dept = Department(**dept_data)
            db.add(dept)
        
        db.commit()
        
        # Get department references
        software_dev = db.query(Department).filter(Department.name == "Software Development").first()
        ai_data = db.query(Department).filter(Department.name == "AI & Data Science").first()
        qa = db.query(Department).filter(Department.name == "Quality Assurance").first()
        design = db.query(Department).filter(Department.name == "Design").first()
        project_mgmt = db.query(Department).filter(Department.name == "Project & Product Management").first()
        it_infra = db.query(Department).filter(Department.name == "IT & Infrastructure").first()
        sales_marketing = db.query(Department).filter(Department.name == "Sales & Marketing").first()
        hr_ops = db.query(Department).filter(Department.name == "HR & Operations").first()
        leadership = db.query(Department).filter(Department.name == "Leadership").first()
        
        positions = [
            # Software Development
            {"title": "Junior Software Engineer", "description": "Entry-level developer role.", "level": "Junior", "department_id": software_dev.id},
            {"title": "Software Engineer", "description": "Mid-level developer role.", "level": "Mid", "department_id": software_dev.id},
            {"title": "Senior Software Engineer", "description": "Experienced developer with leadership responsibility.", "level": "Senior", "department_id": software_dev.id},
            {"title": "Lead Software Engineer", "description": "Leads a team of developers.", "level": "Lead", "department_id": software_dev.id},
            {"title": "Software Architect", "description": "Designs system architecture and oversees technical standards.", "level": "Senior", "department_id": software_dev.id},
            {"title": "Frontend Developer", "description": "Specializes in user interface development.", "level": "Mid", "department_id": software_dev.id},
            {"title": "Backend Developer", "description": "Specializes in server-side development.", "level": "Mid", "department_id": software_dev.id},
            {"title": "Full Stack Developer", "description": "Works on both frontend and backend.", "level": "Mid", "department_id": software_dev.id},
            {"title": "Mobile App Developer", "description": "Develops mobile applications.", "level": "Mid", "department_id": software_dev.id},
            {"title": "Game Developer", "description": "Develops games and interactive applications.", "level": "Mid", "department_id": software_dev.id},
            
            # AI & Data Science
            {"title": "Data Scientist", "description": "Builds models and analyzes data for insights.", "level": "Mid", "department_id": ai_data.id},
            {"title": "Machine Learning Engineer", "description": "Develops and deploys ML models.", "level": "Mid", "department_id": ai_data.id},
            {"title": "Data Engineer", "description": "Builds and maintains data pipelines.", "level": "Mid", "department_id": ai_data.id},
            {"title": "AI Researcher", "description": "Explores new AI technologies.", "level": "Senior", "department_id": ai_data.id},
            
            # Quality Assurance
            {"title": "QA Tester (Manual)", "description": "Tests applications manually for bugs.", "level": "Junior", "department_id": qa.id},
            {"title": "Automation QA Engineer", "description": "Creates automated test scripts.", "level": "Mid", "department_id": qa.id},
            {"title": "Performance Tester", "description": "Tests application performance and load.", "level": "Mid", "department_id": qa.id},
            {"title": "Security Tester", "description": "Tests application security vulnerabilities.", "level": "Senior", "department_id": qa.id},
            {"title": "QA Lead", "description": "Leads QA team and testing strategies.", "level": "Lead", "department_id": qa.id},
            
            # Design
            {"title": "UI Designer", "description": "Designs user interfaces.", "level": "Mid", "department_id": design.id},
            {"title": "UX Designer", "description": "Designs user experiences and workflows.", "level": "Mid", "department_id": design.id},
            {"title": "UI/UX Designer", "description": "Designs user interfaces and experiences.", "level": "Mid", "department_id": design.id},
            {"title": "Graphic Designer", "description": "Creates visuals, graphics, and branding.", "level": "Mid", "department_id": design.id},
            {"title": "Motion Graphics Designer", "description": "Creates animated graphics and videos.", "level": "Mid", "department_id": design.id},
            {"title": "Brand Designer", "description": "Develops brand identity and guidelines.", "level": "Senior", "department_id": design.id},
            {"title": "Creative Lead", "description": "Oversees design and creative direction.", "level": "Lead", "department_id": design.id},
            
            # Project & Product Management
            {"title": "Project Coordinator", "description": "Assists in managing project tasks.", "level": "Junior", "department_id": project_mgmt.id},
            {"title": "Project Manager", "description": "Manages project delivery and timelines.", "level": "Mid", "department_id": project_mgmt.id},
            {"title": "Scrum Master", "description": "Facilitates Agile practices.", "level": "Mid", "department_id": project_mgmt.id},
            {"title": "Product Owner", "description": "Defines product requirements.", "level": "Mid", "department_id": project_mgmt.id},
            
            # IT & Infrastructure
            {"title": "System Administrator", "description": "Maintains systems and servers.", "level": "Mid", "department_id": it_infra.id},
            {"title": "DevOps Engineer", "description": "Handles CI/CD pipelines and deployments.", "level": "Mid", "department_id": it_infra.id},
            {"title": "Network Administrator", "description": "Manages company networks.", "level": "Mid", "department_id": it_infra.id},
            {"title": "Database Administrator (DBA)", "description": "Manages databases and performance.", "level": "Senior", "department_id": it_infra.id},
            {"title": "Cloud Engineer", "description": "Manages cloud infrastructure and services.", "level": "Mid", "department_id": it_infra.id},
            {"title": "Security Engineer", "description": "Handles cybersecurity and system protection.", "level": "Senior", "department_id": it_infra.id},
            {"title": "IT Support Specialist", "description": "Provides technical support to employees.", "level": "Junior", "department_id": it_infra.id},
            
            # Sales & Marketing
            {"title": "Business Development Executive (BDE)", "description": "Finds new clients and business opportunities.", "level": "Junior", "department_id": sales_marketing.id},
            {"title": "Business Development Manager (BDM)", "description": "Leads business development strategy.", "level": "Mid", "department_id": sales_marketing.id},
            {"title": "Sales Executive", "description": "Handles client sales.", "level": "Mid", "department_id": sales_marketing.id},
            {"title": "Account Manager", "description": "Manages client relationships and accounts.", "level": "Mid", "department_id": sales_marketing.id},
            {"title": "Digital Marketing Specialist", "description": "Handles online marketing.", "level": "Mid", "department_id": sales_marketing.id},
            {"title": "SEO Specialist", "description": "Optimizes search engine visibility.", "level": "Mid", "department_id": sales_marketing.id},
            {"title": "Content Writer", "description": "Creates marketing content and copy.", "level": "Junior", "department_id": sales_marketing.id},
            {"title": "Social Media Manager", "description": "Manages social media presence.", "level": "Mid", "department_id": sales_marketing.id},
            {"title": "Marketing Manager", "description": "Leads marketing campaigns and strategy.", "level": "Senior", "department_id": sales_marketing.id},
            
            # HR & Operations
            {"title": "HR Executive", "description": "Handles HR tasks and employee relations.", "level": "Junior", "department_id": hr_ops.id},
            {"title": "HR Manager", "description": "Leads HR operations and strategy.", "level": "Mid", "department_id": hr_ops.id},
            {"title": "Recruiter", "description": "Manages hiring and recruitment.", "level": "Mid", "department_id": hr_ops.id},
            {"title": "Talent Acquisition Specialist", "description": "Specializes in finding and attracting talent.", "level": "Mid", "department_id": hr_ops.id},
            {"title": "HR Business Partner", "description": "Partners with business units on HR strategy.", "level": "Senior", "department_id": hr_ops.id},
            {"title": "Accountant / Finance Officer", "description": "Handles company finances.", "level": "Mid", "department_id": hr_ops.id},
            {"title": "Payroll Specialist", "description": "Manages employee payroll and benefits.", "level": "Mid", "department_id": hr_ops.id},
            {"title": "Office Manager", "description": "Manages office operations and facilities.", "level": "Mid", "department_id": hr_ops.id},
            {"title": "Administrative Assistant", "description": "Provides administrative support.", "level": "Junior", "department_id": hr_ops.id},
            
            # Leadership
            {"title": "Team Lead", "description": "Leads a small team of employees.", "level": "Lead", "department_id": leadership.id},
            {"title": "Engineering Manager", "description": "Oversees engineering teams.", "level": "Lead", "department_id": leadership.id},
            {"title": "CTO", "description": "Chief Technology Officer.", "level": "Executive", "department_id": leadership.id},
            {"title": "CEO", "description": "Chief Executive Officer.", "level": "Executive", "department_id": leadership.id},
        ]
        
        for pos_data in positions:
            position = Position(**pos_data)
            db.add(position)
        
        db.commit()
        
        # Create admin user
        admin_user = User(
            email="admin@hrm.com",
            hashed_password=get_password_hash("admin123"),
            first_name="Admin",
            last_name="User",
            phone="+923001234567",
            role="admin",
            is_profile_complete=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Create admin employee record
        it_infra_dept = db.query(Department).filter(Department.name == "IT & Infrastructure").first()
        hr_ops_dept = db.query(Department).filter(Department.name == "HR & Operations").first()
        sys_admin_position = db.query(Position).filter(Position.title == "System Administrator").first()
        admin_employee = Employee(
            user_id=admin_user.id,
            employee_id="EMP001",
            department_id=it_infra_dept.id,
            position="System Administrator",
            position_id=sys_admin_position.id,
            employment_status="full_time",
            hire_date=date.today(),
            work_location="office"
        )
        db.add(admin_employee)
        
        # Create HR user
        hr_user = User(
            email="hr@hrm.com",
            hashed_password=get_password_hash("hr123"),
            first_name="HR",
            last_name="Manager",
            phone="+923001234568",
            role="hr",
            is_profile_complete=True
        )
        db.add(hr_user)
        db.commit()
        db.refresh(hr_user)
        
        # Create HR employee record
        hr_manager_position = db.query(Position).filter(Position.title == "HR Manager").first()
        hr_employee = Employee(
            user_id=hr_user.id,
            employee_id="EMP002",
            department_id=hr_ops_dept.id,
            position="HR Manager",
            position_id=hr_manager_position.id,
            employment_status="full_time",
            hire_date=date.today(),
            work_location="office"
        )
        db.add(hr_employee)
        
        db.commit()
        print("Database cleaned and initialized successfully!")
        print("\nDefault Login Credentials:")
        print("Admin: admin@hrm.com / admin123")
        print("HR: hr@hrm.com / hr123")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()