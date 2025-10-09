import sqlite3

def check_attendance_data():
    try:
        conn = sqlite3.connect('hrm.db')
        cursor = conn.cursor()
        
        print("=== ATTENDANCE TABLE ANALYSIS ===")
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("[ERROR] Attendance table does not exist!")
            return
        
        print("[OK] Attendance table exists")
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM attendance;")
        total_count = cursor.fetchone()[0]
        print(f"Total Records: {total_count}")
        
        if total_count == 0:
            print("[ERROR] No attendance records found in database!")
            return
        
        # Get sample records
        cursor.execute("SELECT * FROM attendance LIMIT 5;")
        records = cursor.fetchall()
        
        print(f"\nSample Records (first 5):")
        print("-" * 80)
        for i, record in enumerate(records, 1):
            print(f"{i}. ID: {record[0]}, Employee: {record[1]}, Date: {record[2]}")
            print(f"   Check-in: {record[3]}, Check-out: {record[4]}, Status: {record[5]}")
        
        conn.close()
        print("\n[OK] Database analysis completed")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    check_attendance_data()