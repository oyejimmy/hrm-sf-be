# MongoDB to SQLite Migration Guide

This document outlines the migration from MongoDB to SQLite for the HRM System.

## Changes Made

### 1. Database Layer
- **Removed**: MongoDB connection (`app/db/mongodb.py`)
- **Added**: SQLite connection and models (`app/database.py`, `app/models/sql_models.py`)
- **Added**: SQLite service layer (`app/db/sqlite.py`)

### 2. Dependencies
- **Removed**: `motor`, `pymongo`
- **Added**: `sqlalchemy`, `aiosqlite`

### 3. Data Models
- Migrated from MongoDB documents to SQLAlchemy ORM models
- Added proper relationships and foreign keys
- Maintained data integrity with enum types

### 4. API Endpoints
Updated all routers to use SQLAlchemy instead of MongoDB:
- `auth.py` - Authentication endpoints
- `employees.py` - Employee management
- `attendance.py` - Attendance tracking
- `leave.py` - Leave management

## Database Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python init_db.py
```

This will:
- Create all necessary tables
- Optionally create an admin user (admin@hrm.com / admin123)

### 3. Start the Application
```bash
uvicorn app.main:app --reload
```

## Key Benefits

1. **Simplified Deployment**: No need for separate MongoDB server
2. **Better Performance**: SQLite is faster for small to medium applications
3. **ACID Compliance**: Better data consistency and integrity
4. **Easier Backup**: Single file database
5. **Reduced Dependencies**: Fewer external services required

## Data Migration (if needed)

If you have existing MongoDB data, you'll need to:

1. Export data from MongoDB
2. Transform the data structure to match SQLAlchemy models
3. Import data using the SQLite service methods

## Configuration Changes

- Removed `MONGODB_URL` from settings
- Database file is created as `hrm_system.db` in the project root
- All MongoDB-specific configurations have been removed

## Testing

Run the application and test all endpoints to ensure proper functionality:

1. Authentication (login/signup)
2. Employee management
3. Attendance tracking
4. Leave management

## Rollback Plan

If you need to rollback to MongoDB:

1. Restore the original `requirements.txt`
2. Restore MongoDB connection files
3. Restore original router implementations
4. Update `main.py` to use MongoDB connection

The original MongoDB implementation files are preserved in the git history for reference.