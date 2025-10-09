import sqlite3

def show_all_attendance():
    try:
        conn = sqlite3.connect('hrm.db')
        cursor = conn.cursor()
        
        # Get all attendance records with user details
        cursor.execute("""
            SELECT 
                a.id,
                a.employee_id,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                a.date,
                a.check_in,
                a.check_out,
                a.status,
                a.hours_worked,
                a.notes,
                a.created_at,
                a.updated_at
            FROM attendance a
            LEFT JOIN users u ON a.employee_id = u.id
            ORDER BY a.date DESC, a.created_at DESC;
        """)
        
        records = cursor.fetchall()
        
        print("=" * 100)
        print("ALL ATTENDANCE RECORDS IN DATABASE")
        print("=" * 100)
        print(f"Total Records: {len(records)}")
        print("=" * 100)
        
        if not records:
            print("No attendance records found in database.")
            return
        
        for i, record in enumerate(records, 1):
            (att_id, emp_id, email, first_name, last_name, role, 
             date, check_in, check_out, status, hours_worked, notes, 
             created_at, updated_at) = record
            
            name = f"{first_name or ''} {last_name or ''}".strip() or "N/A"
            
            print(f"\n{i}. ATTENDANCE RECORD ID: {att_id}")
            print(f"   Employee ID: {emp_id}")
            print(f"   Employee: {name} ({email}) - {role}")
            print(f"   Date: {date}")
            print(f"   Check-in: {check_in}")
            print(f"   Check-out: {check_out}")
            print(f"   Status: {status}")
            print(f"   Hours Worked: {hours_worked}")
            print(f"   Notes: {notes or 'None'}")
            print(f"   Created: {created_at}")
            print(f"   Updated: {updated_at or 'Never'}")
            print("-" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_all_attendance()