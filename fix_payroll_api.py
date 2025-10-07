#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.database import Base
from app.models.payroll import Payslip, PayslipEarning, PayslipDeduction, SalaryStructure, Bonus
from app.models.user import User
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_payroll_tables():
    """Fix payroll tables"""
    try:
        engine = create_engine(settings.database_url)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Payroll tables created/updated")
        
        # Test basic query
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Test queries
            users_count = db.query(User).count()
            payslips_count = db.query(Payslip).count()
            
            logger.info(f"📊 Users: {users_count}, Payslips: {payslips_count}")
            
            # Create a simple test payslip if none exist
            if payslips_count == 0 and users_count > 0:
                user = db.query(User).first()
                if user:
                    from datetime import date
                    
                    payslip = Payslip(
                        employee_id=user.id,
                        pay_period_start=date(2024, 1, 1),
                        pay_period_end=date(2024, 1, 31),
                        pay_date=date(2024, 2, 5),
                        basic_salary=5000.0,
                        gross_salary=6000.0,
                        net_salary=5200.0,
                        total_earnings=6000.0,
                        total_deductions=800.0,
                        payslip_number=f"PAY-{user.id}-2024-01",
                        generated_by=user.id,
                        status="approved"
                    )
                    db.add(payslip)
                    db.commit()
                    logger.info("✅ Test payslip created")
            
        except Exception as e:
            logger.error(f"❌ Database test failed: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_payroll_tables()
    print("Payroll API fix completed!")