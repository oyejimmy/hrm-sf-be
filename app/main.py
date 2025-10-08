from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .models import user, employee, department, position, notification, language, technical_skill, payroll, attendance  # Import models to ensure tables are created
from .routers import (
    auth, reports, employees, positions, leaves, attendance, performance,
    payroll, requests, complaints, training, assets, health_insurance,
    documents, notifications, announcements, holidays, recruitment, languages, technical_skills, leave_types
)

app = FastAPI(title="HRM System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

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

@app.get("/")
def read_root():
    return {"message": "HRM System API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

