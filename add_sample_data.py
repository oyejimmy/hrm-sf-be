from app.database import SessionLocal
from app.models.leave import Leave, LeaveBalance
from app.models.attendance import Attendance
from datetime import date, datetime
import json

def add_sample_data():
    db = SessionLocal()
    
    try:
        # Add sample leave data for employee (user_id = 3)
        existing_leaves = db.query(Leave).filter(Leave.employee_id == 3).count()
        if existing_leaves == 0:
            print("Adding sample leave data...")
            
            leave1 = Leave(
                employee_id=3,
                leave_type="annual",
                duration_type="full_day",
                start_date=date(2025, 1, 15),
                end_date=date(2025, 1, 17),
                days_requested=3.0,
                reason="Family vacation",
                status="approved"
            )
            
            leave2 = Leave(
                employee_id=3,
                leave_type="sick",
                duration_type="half_day_morning",
                start_date=date(2025, 1, 10),
                end_date=date(2025, 1, 10),
                days_requested=0.5,
                reason="Medical appointment",
                status="approved"
            )
            
            db.add(leave1)
            db.add(leave2)
        
        # Add leave balances
        existing_balances = db.query(LeaveBalance).filter(LeaveBalance.employee_id == 3).count()
        if existing_balances == 0:
            print("Adding leave balances...")
            
            balances = [
                LeaveBalance(employee_id=3, leave_type="annual", year=2025, total_allocated=20.0, taken=3.0, remaining=17.0),
                LeaveBalance(employee_id=3, leave_type="sick", year=2025, total_allocated=10.0, taken=0.5, remaining=9.5),
                LeaveBalance(employee_id=3, leave_type="casual", year=2025, total_allocated=5.0, taken=0.0, remaining=5.0)
            ]
            
            for balance in balances:
                db.add(balance)
        
        # Add attendance data
        existing_attendance = db.query(Attendance).filter(Attendance.employee_id == 3).count()
        if existing_attendance == 0:
            print("Adding attendance data...")
            
            attendance_records = [
                Attendance(
                    employee_id=3,
                    date=date(2025, 1, 13),
                    check_in=datetime(2025, 1, 13, 9, 0),
                    check_out=datetime(2025, 1, 13, 17, 30),
                    status="present",
                    total_hours=8.5,
                    working_hours=8.0
                ),
                Attendance(
                    employee_id=3,
                    date=date(2025, 1, 14),
                    check_in=datetime(2025, 1, 14, 9, 15),
                    check_out=datetime(2025, 1, 14, 17, 45),
                    status="present",
                    total_hours=8.5,
                    working_hours=8.0
                ),
                Attendance(
                    employee_id=3,
                    date=date(2025, 1, 15),
                    status="on_leave",
                    total_hours=0.0,
                    working_hours=0.0
                )
            ]
            
            for record in attendance_records:
                db.add(record)
        
        db.commit()
        print("Sample data added successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()