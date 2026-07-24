from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .schema_sync import sync_columns
from .models import user, employee, department, position, notification, language, technical_skill, payroll, attendance, setting  # Import models to ensure tables are created
from .models import award as award_model  # noqa: F401  — registers Award / AwardNomination tables
from .models import gallery as gallery_model  # noqa: F401  — registers Gallery / Celebration tables
from .models import finance as finance_model  # noqa: F401  — registers Expense / Invoice / FinancialAuditLog tables
from .models.user import User
from .auth import get_password_hash
from .routers import (
    auth, reports, employees, positions, leaves, attendance, performance,
    payroll, requests, complaints, training, assets, health_insurance,
    documents, notifications, announcements, holidays, recruitment, languages, technical_skills, leave_types, admin,
    settings as settings_router,
    awards as awards_router,
    gallery as gallery_router,
    finance as finance_router,
    it_assets as it_assets_router,
)

app = FastAPI(title="HRM System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables, then add any columns that were introduced on existing models
# (this project has no Alembic; see app/schema_sync.py).
Base.metadata.create_all(bind=engine)
_synced = sync_columns(engine)
if _synced:
    print(f"[schema-sync] added columns: {', '.join(_synced)}")


def seed_demo_users() -> None:
    from .models.employee import Employee

    demo_users = [
        {"email": "admin@hrm.com", "password": "admin123", "role": "admin", "first_name": "Admin", "last_name": "User"},
        {"email": "hr@hrm.com", "password": "hr123", "role": "hr", "first_name": "HR", "last_name": "Manager"},
        {"email": "teamlead@hrm.com", "password": "lead123", "role": "team_lead", "first_name": "Taylor", "last_name": "Lead"},
        {"email": "accountant@hrm.com", "password": "acc123", "role": "accountant", "first_name": "Alex", "last_name": "Ledger"},
        # 6+ chars: the login form enforces a minimum password length.
        {"email": "it@hrm.com", "password": "it123456", "role": "it", "first_name": "Ivy", "last_name": "Techton"},
        {"email": "employee@hrm.com", "password": "emp123", "role": "employee", "first_name": "Employee", "last_name": "User"},
    ]

    db = SessionLocal()
    try:
        for demo_user in demo_users:
            existing_user = db.query(User).filter(User.email == demo_user["email"]).first()
            if existing_user:
                continue

            db.add(
                User(
                    email=demo_user["email"],
                    hashed_password=get_password_hash(demo_user["password"]),
                    first_name=demo_user["first_name"],
                    last_name=demo_user["last_name"],
                    role=demo_user["role"],
                    status="active",
                    is_profile_complete=True,
                )
            )
        db.commit()

        # Ensure the team lead has an employee record so team features work
        lead_user = db.query(User).filter(User.email == "teamlead@hrm.com").first()
        if lead_user:
            lead_emp = db.query(Employee).filter(Employee.user_id == lead_user.id).first()
            if not lead_emp:
                emp_count = db.query(Employee).count()
                lead_emp = Employee(
                    user_id=lead_user.id,
                    employee_id=f"EMP{emp_count + 1:04d}",
                    position="Team Lead",
                    employment_status="full_time",
                )
                db.add(lead_emp)
                db.commit()

            # Assign the demo employee to report to the team lead
            emp_user = db.query(User).filter(User.email == "employee@hrm.com").first()
            if emp_user:
                emp_record = db.query(Employee).filter(Employee.user_id == emp_user.id).first()
                if emp_record and emp_record.manager_id is None:
                    emp_record.manager_id = lead_user.id
                    db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


seed_demo_users()

# Include routers
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(employees.router, prefix="/api/employees", tags=["employees"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(leaves.router)
app.include_router(attendance.router)
app.include_router(performance.router)
app.include_router(payroll.router)
app.include_router(requests.router)
app.include_router(complaints.router)
app.include_router(training.router)
app.include_router(assets.router)
app.include_router(health_insurance.router)
app.include_router(documents.router)
app.include_router(notifications.router)
app.include_router(announcements.router)
app.include_router(holidays.router, prefix="/api/holidays", tags=["holidays"])
app.include_router(recruitment.router)
app.include_router(languages.router)
app.include_router(technical_skills.router)
app.include_router(leave_types.router)
app.include_router(admin.router)
app.include_router(settings_router.router)
app.include_router(awards_router.router)
app.include_router(gallery_router.router)
app.include_router(finance_router.router)
app.include_router(it_assets_router.router)

@app.get("/")
def read_root():
    return {"message": "HRM System API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

