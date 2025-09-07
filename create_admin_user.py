#!/usr/bin/env python3
"""
Script to create an admin user for the HRM system.
Run this script to initialize the database and create a default admin user.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import create_tables, AsyncSessionLocal
from app.models.sql_models import User, UserRole, UserStatus
from app.core.security import get_password_hash
from app.core.logger import logger

async def create_admin_user():
    """Create an admin user in the database."""
    try:
        # Create tables first
        await create_tables()
        logger.info("Database tables created successfully")
        
        # Create admin user
        async with AsyncSessionLocal() as session:
            # Check if admin user already exists
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.email == "admin@hrm.com"))
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                logger.info("Admin user already exists")
                print("Admin user already exists!")
                return
            
            # Create new admin user
            admin_user = User(
                email="admin@hrm.com",
                password_hash=get_password_hash("admin123"),
                first_name="System",
                last_name="Administrator",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            logger.info(f"Admin user created successfully with ID: {admin_user.id}")
            print("=" * 50)
            print("ADMIN USER CREATED SUCCESSFULLY!")
            print("=" * 50)
            print(f"Email: admin@hrm.com")
            print(f"Password: admin123")
            print(f"Role: Administrator")
            print("=" * 50)
            print("You can now login to the HRM system with these credentials.")
            print("=" * 50)
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        print(f"Error creating admin user: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_admin_user())
