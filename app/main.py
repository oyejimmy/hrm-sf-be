from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal
from .models import user, employee, department, position, notification, language, technical_skill, payroll, attendance  # Import models to ensure tables are created
from .models.user import User
from .auth import get_password_hash
from .routers import (
    auth, reports, employees, positions, leaves, attendance, performance,
    payroll, requests, complaints, training, assets, health_insurance,
    documents, notifications, announcements, holidays, recruitment, languages, technical_skills, leave_types, admin
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

# Create tables
Base.metadata.create_all(bind=engine)


def seed_demo_users() -> None:
    demo_users = [
        {"email": "admin@hrm.com", "password": "admin123", "role": "admin", "first_name": "Admin", "last_name": "User"},
        {"email": "hr@hrm.com", "password": "hr123", "role": "hr", "first_name": "HR", "last_name": "Manager"},
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
# app.include_router(payroll.router)
from .routers import payroll_simple
app.include_router(payroll_simple.router)
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

@app.get("/")
def read_root():
    return {"message": "HRM System API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

