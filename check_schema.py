#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect
from app.database import engine

def check_table_schema():
    inspector = inspect(engine)
    
    # Check attendance table columns
    print("=== ATTENDANCE TABLE COLUMNS ===")
    try:
        columns = inspector.get_columns('attendance')
        for col in columns:
            print(f"{col['name']}: {col['type']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== ALL TABLES ===")
    tables = inspector.get_table_names()
    for table in tables:
        print(f"- {table}")

if __name__ == "__main__":
    check_table_schema()