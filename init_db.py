#!/usr/bin/env python3
"""
Database initialization script for HRM System.
This script creates all tables and can optionally create an admin user.
"""

import asyncio
import sys
from datetime import datetime
from app.database import create_tables
from app.db.sqlite import SQLiteService
from app.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.sql_models import UserRole, UserStatus

async def init_database():
    """Initialize the database with tables."""
    print("Creating database tables...")
    await create_tables()
    print("Database tables created successfully!")

async def create_admin_user():
    """Create an admin user."""
    try:
        async with AsyncSessionLocal() as db:
            # Check if admin user already exists
            admin_user = await SQLiteService.get_user_by_email(db, "admin@hrm.com")
            if admin_user:
                print("Admin user already exists!")
                return
            
            # Create admin user
            admin_data = {
                "email": "admin@hrm.com",
                "first_name": "Admin",
                "last_name": "User",
                "role": UserRole.ADMIN,
                "status": UserStatus.ACTIVE,
                "password_hash": get_password_hash("admin123"),
                "phone": "+1234567890"
            }
            
            admin_user = await SQLiteService.create_user(db, admin_data)
            print(f"Admin user created with ID: {admin_user.id}")
            print("Email: admin@hrm.com")
            print("Password: admin123")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        # Create a simple admin user directly
        print("Creating admin user with basic method...")
        await create_simple_admin()

async def create_simple_admin():
    """Create admin user with simple method."""
    from sqlalchemy import text
    from app.database import engine
    
    async with engine.begin() as conn:
        # Check if user exists
        result = await conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": "admin@hrm.com"}
        )
        if result.fetchone():
            print("Admin user already exists!")
            return
        
        # Insert admin user
        await conn.execute(
            text("""
                INSERT INTO users (email, password_hash, first_name, last_name, role, status, phone)
                VALUES (:email, :password_hash, :first_name, :last_name, :role, :status, :phone)
            """),
            {
                "email": "admin@hrm.com",
                "password_hash": get_password_hash("admin123"),
                "first_name": "Admin",
                "last_name": "User",
                "role": "ADMIN",
                "status": "ACTIVE",
                "phone": "+1234567890"
            }
        )
        print("Admin user created successfully!")
        print("Email: admin@hrm.com")
        print("Password: admin123")

async def main():
    """Main function."""
    print("HRM System Database Initialization")
    print("=" * 40)
    
    try:
        # Initialize database
        await init_database()
        
        # Create admin user automatically
        print("\nCreating admin user...")
        await create_admin_user()
        
        print("\nDatabase initialization completed successfully!")
        print("\nYou can now start the server with:")
        print("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())