#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    try:
        from app.routers import auth
        print("auth router imported")
    except Exception as e:
        print(f"auth router failed: {e}")
    
    try:
        from app.routers import reports
        print("reports router imported")
    except Exception as e:
        print(f"reports router failed: {e}")
    
    try:
        from app.routers import employees
        print("employees router imported")
    except Exception as e:
        print(f"employees router failed: {e}")
    
    try:
        from app.routers import leaves
        print("leaves router imported")
    except Exception as e:
        print(f"leaves router failed: {e}")
    
    try:
        from app.routers import attendance
        print("attendance router imported")
    except Exception as e:
        print(f"attendance router failed: {e}")

if __name__ == "__main__":
    test_imports()