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

async def main():
    """Main function."""
    print("HRM System Database Initialization")
    print("=" * 40)
    
    try:
        # Initialize database
        await init_database()
        
        # Ask if user wants to create admin user
        create_admin = input("\nDo you want to create an admin user? (y/n): ").lower().strip()
        if create_admin in ['y', 'yes']:
            await create_admin_user()
        
        print("\nDatabase initialization completed successfully!")
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())