import sqlite3
from datetime import datetime

def add_sample_holidays():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    try:
        # Check if holidays table exists and has data
        cursor.execute('SELECT COUNT(*) FROM holidays')
        count = cursor.fetchone()[0]
        print(f'Holidays table has {count} records')
        
        if count == 0:
            print('Adding sample holidays...')
            holidays = [
                ('New Year Day', '2024-01-01', 'national', 'New Year celebration'),
                ('Independence Day', '2024-08-14', 'national', 'Pakistan Independence Day'),
                ('Eid ul Fitr', '2024-04-10', 'religious', 'Festival of Breaking the Fast'),
                ('Eid ul Adha', '2024-06-17', 'religious', 'Festival of Sacrifice'),
                ('Christmas Day', '2024-12-25', 'religious', 'Christmas celebration'),
                ('Labour Day', '2024-05-01', 'national', 'International Workers Day'),
                ('Quaid-e-Azam Birthday', '2024-12-25', 'national', 'Founder of Pakistan Birthday'),
                ('Allama Iqbal Day', '2024-11-09', 'national', 'Poet and Philosopher Day'),
                ('Republic Day', '2025-03-23', 'national', 'Pakistan Day'),
                ('Shab-e-Barat', '2025-02-14', 'religious', 'Night of Forgiveness'),
                ('Shab-e-Qadr', '2025-03-28', 'religious', 'Night of Power'),
                ('Ashura', '2025-07-16', 'religious', 'Day of Ashura')
            ]
            
            for name, date, holiday_type, description in holidays:
                cursor.execute('''
                    INSERT INTO holidays (name, date, holiday_type, description, is_optional, created_by, created_at)
                    VALUES (?, ?, ?, ?, 0, 1, datetime('now'))
                ''', (name, date, holiday_type, description))
            
            conn.commit()
            print('Sample holidays added successfully!')
        
        # Show current holidays
        cursor.execute('SELECT name, date, holiday_type FROM holidays ORDER BY date')
        holidays = cursor.fetchall()
        print('\nCurrent holidays:')
        for holiday in holidays:
            print(f'- {holiday[0]}: {holiday[1]} ({holiday[2]})')
            
    except Exception as e:
        print(f'Error: {e}')
    finally:
        conn.close()

if __name__ == "__main__":
    add_sample_holidays()