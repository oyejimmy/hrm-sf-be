from app.database import SessionLocal, engine
from app.models import *
import sqlite3

def migrate_currency():
    # Add currency_id column to employees table
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    try:
        # Check if currency_id column exists
        cursor.execute("PRAGMA table_info(employees)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'currency_id' not in columns:
            # Add currency_id column
            cursor.execute("ALTER TABLE employees ADD COLUMN currency_id INTEGER DEFAULT 1")
            print("Added currency_id column to employees table")
        else:
            print("currency_id column already exists")
            
        # Create currencies table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS currencies (
                id INTEGER PRIMARY KEY,
                country_name VARCHAR NOT NULL,
                currency_code VARCHAR(3) NOT NULL UNIQUE,
                currency_symbol VARCHAR(5) NOT NULL,
                currency_name VARCHAR NOT NULL
            )
        """)
        
        # Insert default currencies
        cursor.execute("SELECT COUNT(*) FROM currencies")
        if cursor.fetchone()[0] == 0:
            currencies = [
                (1, "Pakistan", "PKR", "₨", "Pakistani Rupee"),
                (2, "United States", "USD", "$", "US Dollar"),
                (3, "United Kingdom", "GBP", "£", "British Pound"),
                (4, "European Union", "EUR", "€", "Euro")
            ]
            cursor.executemany(
                "INSERT INTO currencies (id, country_name, currency_code, currency_symbol, currency_name) VALUES (?, ?, ?, ?, ?)",
                currencies
            )
            print("Inserted default currencies")
        
        conn.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_currency()