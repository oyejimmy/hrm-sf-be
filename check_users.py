import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()

try:
    users = db.query(User).all()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"- {user.email} (role: {user.role}, status: {user.status})")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()