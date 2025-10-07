#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.database import Base, get_db
from app.models.payroll import Payslip, PayslipEarning, PayslipDeduction, SalaryStructure, Bonus
from app.models.user import User
from app.models.employee import Employee
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_payroll_tables():
    """Create payroll tables and add sample data"""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Payroll tables created successfully")
        
        # Add sample data
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Check if we have users
            users = db.query(User).limit(5).all()
            if not users:
                logger.warning("⚠️ No users found. Please run init_db.py first")
                return
            
            # Create sample salary structures
            for user in users:
                existing_structure = db.query(SalaryStructure).filter(
                    SalaryStructure.employee_id == user.id,
                    SalaryStructure.is_active == True
                ).first()
                
                if not existing_structure:
                    salary_structure = SalaryStructure(
                        employee_id=user.id,
                        effective_from="2024-01-01",
                        basic_salary=5000.0,
                        hra_percentage=20.0,
                        transport_allowance=500.0,
                        medical_allowance=300.0,
                        special_allowance=200.0,
                        pf_percentage=12.0,
                        esi_percentage=1.75,
                        professional_tax=200.0,
                        is_active=True,
                        created_by=1
                    )
                    db.add(salary_structure)
            
            # Create sample payslips for the last 3 months
            import datetime
            from dateutil.relativedelta import relativedelta
            
            today = datetime.date.today()
            
            for i in range(3):  # Last 3 months
                month_start = today.replace(day=1) - relativedelta(months=i)
                month_end = month_start + relativedelta(months=1) - datetime.timedelta(days=1)
                pay_date = month_end + datetime.timedelta(days=5)
                
                for user in users:
                    # Check if payslip already exists
                    existing_payslip = db.query(Payslip).filter(
                        Payslip.employee_id == user.id,
                        Payslip.pay_period_start == month_start
                    ).first()
                    
                    if not existing_payslip:
                        # Get salary structure
                        salary_structure = db.query(SalaryStructure).filter(
                            SalaryStructure.employee_id == user.id,
                            SalaryStructure.is_active == True
                        ).first()
                        
                        if salary_structure:
                            # Calculate earnings
                            basic_salary = salary_structure.basic_salary
                            hra = basic_salary * (salary_structure.hra_percentage or 0) / 100
                            transport = salary_structure.transport_allowance or 0
                            medical = salary_structure.medical_allowance or 0
                            special = salary_structure.special_allowance or 0
                            total_earnings = basic_salary + hra + transport + medical + special
                            
                            # Calculate deductions
                            pf = basic_salary * (salary_structure.pf_percentage or 0) / 100
                            esi = basic_salary * (salary_structure.esi_percentage or 0) / 100
                            professional_tax = salary_structure.professional_tax or 0
                            total_deductions = pf + esi + professional_tax
                            
                            net_salary = total_earnings - total_deductions
                            
                            # Create payslip
                            payslip = Payslip(
                                employee_id=user.id,
                                pay_period_start=month_start,
                                pay_period_end=month_end,
                                pay_date=pay_date,
                                basic_salary=basic_salary,
                                gross_salary=total_earnings,
                                net_salary=net_salary,
                                total_earnings=total_earnings,
                                total_deductions=total_deductions,
                                payslip_number=f"PAY-{user.id}-{month_start.strftime('%Y%m')}",
                                generated_by=1,
                                status="approved" if i > 0 else "generated"
                            )
                            db.add(payslip)
                            db.flush()  # Get the payslip ID
                            
                            # Add earnings breakdown
                            earnings_data = [
                                ("Basic Salary", basic_salary, True),
                                ("HRA", hra, True),
                                ("Transport Allowance", transport, False),
                                ("Medical Allowance", medical, False),
                                ("Special Allowance", special, True),
                            ]
                            
                            for earning_type, amount, is_taxable in earnings_data:
                                if amount > 0:
                                    earning = PayslipEarning(
                                        payslip_id=payslip.id,
                                        earning_type=earning_type,
                                        amount=amount,
                                        is_taxable=is_taxable
                                    )
                                    db.add(earning)
                            
                            # Add deductions breakdown
                            deductions_data = [
                                ("Provident Fund", pf),
                                ("ESI", esi),
                                ("Professional Tax", professional_tax),
                            ]
                            
                            for deduction_type, amount in deductions_data:
                                if amount > 0:
                                    deduction = PayslipDeduction(
                                        payslip_id=payslip.id,
                                        deduction_type=deduction_type,
                                        amount=amount
                                    )
                                    db.add(deduction)
            
            db.commit()
            logger.info("✅ Sample payroll data created successfully")
            
            # Print summary
            payslip_count = db.query(Payslip).count()
            salary_structure_count = db.query(SalaryStructure).count()
            logger.info(f"📊 Created {payslip_count} payslips and {salary_structure_count} salary structures")
            
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating sample data: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error creating payroll tables: {e}")
        raise

if __name__ == "__main__":
    create_payroll_tables()
    print("🎉 Payroll system setup completed!")