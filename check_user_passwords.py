import sqlite3

def check_user_passwords():
    try:
        conn = sqlite3.connect('hrm.db')
        cursor = conn.cursor()
        
        print("=== USER PASSWORD ANALYSIS ===")
        
        # Get user info including temp passwords
        cursor.execute("SELECT id, email, role, temp_password FROM users WHERE email = 'jamil@smartforum.org';")
        user = cursor.fetchone()
        
        if user:
            user_id, email, role, temp_password = user
            print(f"User: {email}")
            print(f"ID: {user_id}")
            print(f"Role: {role}")
            print(f"Temp Password: {temp_password}")
        else:
            print("User not found")
        
        # Also check all users with temp passwords
        cursor.execute("SELECT id, email, role, temp_password FROM users WHERE temp_password IS NOT NULL;")
        temp_users = cursor.fetchall()
        
        print(f"\nUsers with temp passwords:")
        for user_id, email, role, temp_password in temp_users:
            print(f"  - ID: {user_id}, Email: {email}, Role: {role}, Temp Password: {temp_password}")
        
        conn.close()
        print(f"\n[OK] Analysis completed")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    check_user_passwords()