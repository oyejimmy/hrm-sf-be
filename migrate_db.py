import sqlite3
from app.database import engine
from sqlalchemy import text

def migrate_database():
    """Add missing columns to existing database"""
    
    # Connect to the database
    connection = engine.connect()
    
    try:
        # Check if duration_type column exists
        result = connection.execute(text("PRAGMA table_info(leaves)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'duration_type' not in columns:
            print("Adding duration_type column to leaves table...")
            connection.execute(text("ALTER TABLE leaves ADD COLUMN duration_type VARCHAR DEFAULT 'full_day'"))
            connection.commit()
            print("Added duration_type column")
        else:
            print("duration_type column already exists")
            
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    migrate_database()