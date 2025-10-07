from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
import sys
sys.path.append('.')
from app.models.user import User
from app.models.request import Request, RequestType, RequestStatus, RequestPriority
from datetime import datetime, date

def init_requests():
    # Create tables
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if requests already exist
        existing_requests = db.query(Request).first()
        if existing_requests:
            print("Requests already exist, skipping initialization")
            return
        
        # Get users for sample data
        users = db.query(User).all()
        if not users:
            print("No users found, please run init_db.py first")
            return
        
        # Sample requests data
        sample_requests = [
            {
                "user_id": users[0].id,
                "title": "Home Loan Request",
                "description": "Need a loan for home purchase. Planning to buy a new apartment in the city center.",
                "request_type": RequestType.LOAN,
                "priority": RequestPriority.HIGH,
                "status": RequestStatus.PENDING,
                "amount": 50000.0,
                "created_at": datetime(2023, 1, 1)
            },
            {
                "user_id": users[0].id,
                "title": "Salary Slip Request",
                "description": "Request for last 3 months salary slips for bank loan application.",
                "request_type": RequestType.DOCUMENT,
                "priority": RequestPriority.MEDIUM,
                "status": RequestStatus.APPROVED,
                "document_type": "Salary Certificate",
                "approved_by": users[1].id if len(users) > 1 else users[0].id,
                "approved_at": datetime(2023, 1, 6),
                "created_at": datetime(2023, 1, 5)
            },
            {
                "user_id": users[0].id,
                "title": "Annual Leave Request",
                "description": "Need to take 2 weeks off for family vacation.",
                "request_type": RequestType.LEAVE,
                "priority": RequestPriority.MEDIUM,
                "status": RequestStatus.REJECTED,
                "start_date": date(2023, 2, 1),
                "end_date": date(2023, 2, 14),
                "approver_comments": "Project deadline during this period. Please reschedule.",
                "approved_by": users[1].id if len(users) > 1 else users[0].id,
                "approved_at": datetime(2023, 1, 12),
                "created_at": datetime(2023, 1, 10)
            },
            {
                "user_id": users[0].id,
                "title": "New Laptop Request",
                "description": "Current laptop is outdated and affecting productivity. Need a replacement.",
                "request_type": RequestType.EQUIPMENT,
                "priority": RequestPriority.LOW,
                "status": RequestStatus.APPROVED,
                "equipment_type": 'MacBook Pro 16"',
                "approved_by": users[1].id if len(users) > 1 else users[0].id,
                "approved_at": datetime(2023, 1, 17),
                "created_at": datetime(2023, 1, 15)
            },
            {
                "user_id": users[0].id,
                "title": "Business Trip to Conference",
                "description": "Request for travel approval to attend Tech Conference in San Francisco.",
                "request_type": RequestType.TRAVEL,
                "priority": RequestPriority.HIGH,
                "status": RequestStatus.PENDING,
                "destination": "San Francisco, USA",
                "start_date": date(2023, 3, 15),
                "end_date": date(2023, 3, 20),
                "created_at": datetime(2023, 1, 20)
            },
            {
                "user_id": users[0].id,
                "title": "Employee of the Month Nomination",
                "description": "Nomination for outstanding performance and contribution to the project.",
                "request_type": RequestType.RECOGNITION,
                "priority": RequestPriority.MEDIUM,
                "status": RequestStatus.IN_PROGRESS,
                "recognition_type": "Employee of the Month",
                "created_at": datetime(2023, 1, 25)
            }
        ]
        
        # Create requests
        for request_data in sample_requests:
            request = Request(**request_data)
            db.add(request)
        
        db.commit()
        print("Sample requests created successfully!")
        
        # Print summary
        total_requests = db.query(Request).count()
        print(f"Total requests in database: {total_requests}")
        
    except Exception as e:
        print(f"Error initializing requests: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_requests()