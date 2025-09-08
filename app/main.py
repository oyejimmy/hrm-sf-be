from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from app.core.config import settings
from app.core.logger import logger
from app.database import create_tables
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.routers import auth, employees, attendance, leave, reports, recruitment, performance, training, documents, notifications, announcements

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting HRM API server...")
    await create_tables()
    logger.info("SQLite database initialized successfully")
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()
    logger.info("Shutting down HRM API server...")

app = FastAPI(
    title="HRM System API",
    description="Comprehensive Human Resource Management System",
    version="1.0.0",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
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