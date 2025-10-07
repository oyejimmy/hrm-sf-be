from app.database import engine
from sqlalchemy import text

conn = engine.connect()

# Check total leave records
result = conn.execute(text('SELECT COUNT(*) FROM leaves'))
count = result.fetchone()[0]
print(f'Total leave records: {count}')

# Check sample records
result = conn.execute(text('SELECT * FROM leaves LIMIT 5'))
rows = result.fetchall()
print('Sample records:')
for row in rows:
    print(row)

conn.close()