import sqlite3
from app.database import engine
from sqlalchemy import text

def fix_database_schema():
    """Add all missing columns to existing database tables"""
    
    connection = engine.connect()
    
    try:
        # Check leaves table structure
        result = connection.execute(text("PRAGMA table_info(leaves)"))
        columns = [row[1] for row in result.fetchall()]
        print(f"Current leaves columns: {columns}")
        
        # Add missing columns to leaves table
        missing_columns = [
            ("admin_comments", "TEXT"),
            ("attachment_url", "VARCHAR"),
            ("recipient_details", "TEXT"),  # JSON stored as TEXT in SQLite
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME")
        ]
        
        for col_name, col_type in missing_columns:
            if col_name not in columns:
                print(f"Adding {col_name} column...")
                connection.execute(text(f"ALTER TABLE leaves ADD COLUMN {col_name} {col_type}"))
                connection.commit()
        
        # Create sample leave data for employee
        print("Adding sample leave data...")
        connection.execute(text("""
            INSERT OR IGNORE INTO leaves 
            (employee_id, leave_type, duration_type, start_date, end_date, days_requested, reason, status)
            VALUES 
            (3, 'annual', 'full_day', '2025-01-15', '2025-01-17', 3.0, 'Family vacation', 'approved'),
            (3, 'sick', 'half_day_morning', '2025-01-10', '2025-01-10', 0.5, 'Medical appointment', 'approved')
        """))
        
        # Create leave balances
        print("Adding leave balances...")
        connection.execute(text("""
            INSERT OR IGNORE INTO leave_balances 
            (employee_id, leave_type, year, total_allocated, taken, remaining)
            VALUES 
            (3, 'annual', 2025, 20.0, 3.0, 17.0),
            (3, 'sick', 2025, 10.0, 0.5, 9.5),
            (3, 'casual', 2025, 5.0, 0.0, 5.0)
        """))
        
        # Create sample attendance data
        print("Adding attendance data...")
        connection.execute(text("""
            INSERT OR IGNORE INTO attendance 
            (employee_id, date, check_in_time, check_out_time, status, hours_worked)
            VALUES 
            (3, '2025-01-13', '09:00:00', '17:30:00', 'present', 8.5),
            (3, '2025-01-14', '09:15:00', '17:45:00', 'present', 8.5),
            (3, '2025-01-15', NULL, NULL, 'on_leave', 0.0)
        """))
        
        connection.commit()
        print("Database schema fixed and sample data added successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    fix_database_schema()