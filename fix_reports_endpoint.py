#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import engine
from datetime import datetime, date

# Test the specific endpoint logic
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def test_employee_dashboard():
    """Test the employee dashboard endpoint logic"""
    try:
        # Simulate current_user.id = 3 (employee)
        current_user_id = 3
        
        print("Testing leave balance query...")
        leave_balance = db.execute(text("""
            SELECT days_requested FROM leaves 
            WHERE employee_id = :emp_id AND status = 'approved' 
            AND strftime('%Y', start_date) = :year
        """), {"emp_id": current_user_id, "year": str(datetime.now().year)}).fetchall()
        
        total_leave_days = sum([row[0] for row in leave_balance])
        print(f"Total leave days: {total_leave_days}")
        
        print("Testing attendance query...")
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        my_attendance = db.execute(text("""
            SELECT status FROM attendance 
            WHERE employee_id = :emp_id 
            AND strftime('%m', date) = :month 
            AND strftime('%Y', date) = :year
        """), {
            "emp_id": current_user_id, 
            "month": f"{current_month:02d}", 
            "year": str(current_year)
        }).fetchall()
        
        present_days = len([att for att in my_attendance if att[0] == "present"])
        total_working_days = len(my_attendance)
        print(f"Present days: {present_days}, Total working days: {total_working_days}")
        
        print("Testing requests query...")
        my_pending_requests = db.execute(text("""
            SELECT COUNT(*) FROM employee_requests 
            WHERE employee_id = :emp_id AND status = 'pending'
        """), {"emp_id": current_user_id}).fetchone()[0]
        print(f"Pending requests: {my_pending_requests}")
        
        print("Testing training query...")
        my_trainings = db.execute(text("""
            SELECT status FROM training_enrollments 
            WHERE employee_id = :emp_id
        """), {"emp_id": current_user_id}).fetchall()
        
        completed_trainings = len([t for t in my_trainings if t[0] == "completed"])
        total_trainings = len(my_trainings)
        print(f"Completed trainings: {completed_trainings}, Total trainings: {total_trainings}")
        
        # Build response
        response = {
            "leave_balance": {
                "used_days": total_leave_days,
                "remaining_days": max(0, 25 - total_leave_days)
            },
            "attendance": {
                "present_days": present_days,
                "total_working_days": total_working_days,
                "attendance_rate": round((present_days / total_working_days * 100) if total_working_days > 0 else 0, 2)
            },
            "requests": {
                "pending": my_pending_requests
            },
            "training": {
                "completed": completed_trainings,
                "total": total_trainings,
                "completion_rate": round((completed_trainings / total_trainings * 100) if total_trainings > 0 else 0, 2)
            }
        }
        
        print("Response:", response)
        print("✓ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_employee_dashboard()