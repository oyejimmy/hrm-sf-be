#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def check_attendance_data():
    """Check attendance data in the database"""
    try:
        # Connect to database
        conn = sqlite3.connect('hrm.db')
        cursor = conn.cursor()
        
        print("=== ATTENDANCE TABLE ANALYSIS ===\n")
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ Attendance table does not exist!")
            return
        
        print("✅ Attendance table exists")
        
        # Get table schema
        cursor.execute("PRAGMA table_info(attendance);")
        columns = cursor.fetchall()
        print(f"\n📋 Table Schema ({len(columns)} columns):")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM attendance;")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 Total Records: {total_count}")
        
        if total_count == 0:
            print("❌ No attendance records found in database!")
            return
        
        # Get sample records
        cursor.execute("SELECT * FROM attendance LIMIT 10;")
        records = cursor.fetchall()
        
        print(f"\n📝 Sample Records (showing first 10):")
        print("-" * 100)
        for i, record in enumerate(records, 1):
            print(f"{i:2d}. ID: {record[0]}, Employee: {record[1]}, Date: {record[2]}, "
                  f"Check-in: {record[3]}, Check-out: {record[4]}, Status: {record[5]}")
        
        # Check recent records
        cursor.execute("SELECT * FROM attendance ORDER BY date DESC LIMIT 5;")
        recent_records = cursor.fetchall()
        
        print(f"\n🕒 Most Recent Records:")
        print("-" * 100)
        for i, record in enumerate(recent_records, 1):
            print(f"{i:2d}. ID: {record[0]}, Employee: {record[1]}, Date: {record[2]}, "
                  f"Check-in: {record[3]}, Check-out: {record[4]}, Status: {record[5]}")
        
        # Check status distribution
        cursor.execute("SELECT status, COUNT(*) FROM attendance GROUP BY status;")
        status_counts = cursor.fetchall()
        
        print(f"\n📈 Status Distribution:")
        for status, count in status_counts:
            print(f"  - {status}: {count} records")
        
        # Check employee distribution
        cursor.execute("""
            SELECT a.employee_id, u.email, COUNT(*) as record_count
            FROM attendance a
            LEFT JOIN users u ON a.employee_id = u.id
            GROUP BY a.employee_id
            ORDER BY record_count DESC
            LIMIT 10;
        """)
        employee_counts = cursor.fetchall()
        
        print(f"\n👥 Records by Employee (top 10):")
        for emp_id, email, count in employee_counts:
            print(f"  - Employee {emp_id} ({email or 'No email'}): {count} records")
        
        conn.close()
        print(f"\n✅ Database analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error checking attendance data: {e}")

if __name__ == "__main__":
    check_attendance_data()