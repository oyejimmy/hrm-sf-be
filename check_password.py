import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

try:
    user = db.query(User).filter(User.email == "jamil@smartforum.org").first()
    if user:
        print(f"User found: {user.email}")
        print(f"Hashed password: {user.hashed_password}")
        
        # Test common passwords
        test_passwords = ["password123", "123456", "password", "admin123", "jamil123"]
        for pwd in test_passwords:
            if pwd_context.verify(pwd, user.hashed_password):
                print(f"Correct password is: {pwd}")
                break
        else:
            print("None of the test passwords work")
    else:
        print("User not found")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()