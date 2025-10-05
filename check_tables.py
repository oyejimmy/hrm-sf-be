import sqlite3

def check_tables():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='languages' OR name='technical_skills');")
    tables = cursor.fetchall()
    print("Tables found:", tables)
    
    # Check languages data
    try:
        cursor.execute("SELECT COUNT(*) FROM languages;")
        lang_count = cursor.fetchone()[0]
        print(f"Languages count: {lang_count}")
        
        cursor.execute("SELECT * FROM languages LIMIT 5;")
        langs = cursor.fetchall()
        print("Sample languages:", langs)
    except Exception as e:
        print(f"Languages table error: {e}")
    
    # Check technical_skills data
    try:
        cursor.execute("SELECT COUNT(*) FROM technical_skills;")
        skill_count = cursor.fetchone()[0]
        print(f"Technical skills count: {skill_count}")
        
        cursor.execute("SELECT * FROM technical_skills LIMIT 5;")
        skills = cursor.fetchall()
        print("Sample skills:", skills)
    except Exception as e:
        print(f"Technical skills table error: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_tables()