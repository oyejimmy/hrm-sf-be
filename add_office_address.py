from sqlalchemy import text
from app.database import engine

def add_office_address_column():
    """Add office_address column to employees table if it doesn't exist"""
    try:
        with engine.connect() as connection:
            # Check if column exists
            result = connection.execute(text("PRAGMA table_info(employees)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'office_address' not in columns:
                print("Adding office_address column...")
                connection.execute(text("ALTER TABLE employees ADD COLUMN office_address TEXT"))
                connection.commit()
                print("office_address column added successfully!")
            else:
                print("office_address column already exists.")
                
    except Exception as e:
        print(f"Error adding office_address column: {e}")

if __name__ == "__main__":
    add_office_address_column()