import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('hrm.db')
cursor = conn.cursor()

# Check the leaves table structure
print("=== LEAVES TABLE STRUCTURE ===")
cursor.execute("PRAGMA table_info(leaves)")
columns = cursor.fetchall()
for col in columns:
    print(f"{col[1]} - {col[2]}")

print("\n=== ALL LEAVES DATA ===")
cursor.execute("SELECT id, employee_id, leave_type, status, start_date, end_date, approved_at, created_at FROM leaves ORDER BY id")
leaves = cursor.fetchall()

for leave in leaves:
    print(f"ID: {leave[0]}, Employee: {leave[1]}, Type: {leave[2]}, Status: {leave[3]}")
    print(f"  Start: {leave[4]}, End: {leave[5]}")
    print(f"  Approved At: {leave[6]}, Created: {leave[7]}")
    print()

print(f"\n=== STATUS COUNTS ===")
cursor.execute("SELECT status, COUNT(*) FROM leaves GROUP BY status")
status_counts = cursor.fetchall()
for status, count in status_counts:
    print(f"{status}: {count}")

print(f"\n=== APPROVED LEAVES THIS MONTH ===")
current_month = datetime.now().month
current_year = datetime.now().year
cursor.execute("""
    SELECT id, employee_id, status, approved_at 
    FROM leaves 
    WHERE status = 'approved' 
    AND strftime('%m', approved_at) = ? 
    AND strftime('%Y', approved_at) = ?
""", (f"{current_month:02d}", str(current_year)))

approved_this_month = cursor.fetchall()
print(f"Found {len(approved_this_month)} approved leaves this month:")
for leave in approved_this_month:
    print(f"  ID: {leave[0]}, Employee: {leave[1]}, Status: {leave[2]}, Approved: {leave[3]}")

conn.close()