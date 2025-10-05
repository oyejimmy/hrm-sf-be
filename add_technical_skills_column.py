import sqlite3

def add_technical_skills_column():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    try:
        # Add technical_skills column to employees table
        cursor.execute('ALTER TABLE employees ADD COLUMN technical_skills TEXT')
        conn.commit()
        print("Successfully added technical_skills column to employees table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("technical_skills column already exists")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_technical_skills_column()