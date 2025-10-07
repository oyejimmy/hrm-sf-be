import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.request import Request

db = SessionLocal()

try:
    # Delete all existing requests
    db.query(Request).delete()
    db.commit()
    print("All requests cleared successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()