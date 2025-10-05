from sqlalchemy import text
from app.database import engine

def add_profile_crop_column():
    """Add profile_crop column to employees table if it doesn't exist"""
    try:
        with engine.connect() as connection:
            # Check if column exists
            result = connection.execute(text("PRAGMA table_info(employees)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'profile_crop' not in columns:
                print("Adding profile_crop column...")
                connection.execute(text("ALTER TABLE employees ADD COLUMN profile_crop TEXT"))
                connection.commit()
                print("profile_crop column added successfully!")
            else:
                print("profile_crop column already exists.")
                
    except Exception as e:
        print(f"Error adding profile_crop column: {e}")

if __name__ == "__main__":
    add_profile_crop_column()