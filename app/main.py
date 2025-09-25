from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import (
    auth, reports, employees, leaves, attendance, performance,
    payroll, requests, complaints, training, assets, health_insurance,
    documents, notifications, announcements, holidays, recruitment
)

app = FastAPI(title="HRM System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(employees.router)
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
app.include_router(holidays.router)
app.include_router(recruitment.router)

@app.get("/")
def read_root():
    return {"message": "HRM System API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}