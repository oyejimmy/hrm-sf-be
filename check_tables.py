import sys
sys.path.append('.')

from sqlalchemy import inspect
from app.database import engine

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Available tables:")
    for table in tables:
        print(f"- {table}")
        
    if 'complaints' in tables:
        print("\nComplaints table columns:")
        columns = inspector.get_columns('complaints')
        for col in columns:
            print(f"- {col['name']}: {col['type']}")
    else:
        print("\nComplaints table does not exist!")
        
except Exception as e:
    print(f"Error: {e}")