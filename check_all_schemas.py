#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect
from app.database import engine

def check_all_schemas():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    important_tables = ['attendance', 'performance_reviews', 'payslips', 'employee_requests', 
                       'complaints', 'training_programs', 'assets', 'insurance_claims', 
                       'documents', 'notifications']
    
    for table in important_tables:
        if table in tables:
            print(f"\n=== {table.upper()} TABLE ===")
            try:
                columns = inspector.get_columns(table)
                for col in columns:
                    print(f"{col['name']}: {col['type']}")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"\n=== {table.upper()} TABLE === NOT FOUND")

if __name__ == "__main__":
    check_all_schemas()