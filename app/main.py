from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

from app.core.config import settings
from app.core.logger import logger
from app.database import create_tables
from app.routers import auth, employees, attendance, leave, reports, recruitment, performance, training, documents, notifications, announcements, health_insurance_optimized as health_insurance, profile

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting HRM API server...")
    await create_tables()
    logger.info("SQLite database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down HRM API server...")

app = FastAPI(
    title="HRM System API",
    description="Comprehensive Human Resource Management System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Must be first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(profile.router, tags=["Profile"])
app.include_router(employees.router, prefix="/employees", tags=["Employees"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(leave.router, prefix="/leave", tags=["Leave Management"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])
app.include_router(recruitment.router, prefix="/recruitment", tags=["Recruitment"])
app.include_router(performance.router, prefix="/performance", tags=["Performance"])
app.include_router(training.router, prefix="/training", tags=["Training"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(announcements.router, prefix="/announcements", tags=["Announcements"])
app.include_router(health_insurance.router, tags=["Health Insurance"])

@app.get("/")
async def root():
    return {"message": "HRM System API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )