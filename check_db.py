import sqlite3
import os

# Connect to the database
db_path = "backend/data/crew_rostering.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(f"  - {table[0]}")
        
        # Check row count for each table
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
        count = cursor.fetchone()[0]
        print(f"    Rows: {count}")
        
        # Show sample data for small tables
        if count > 0 and count <= 10:
            print(f"    Sample data:")
            cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5;")
            rows = cursor.fetchall()
            for row in rows:
                print(f"      {row}")
        elif count > 0:
            print(f"    Sample data (first 3 rows):")
            cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3;")
            rows = cursor.fetchall()
            for row in rows:
                print(f"      {row}")
        print()
    
    conn.close()
else:
    print(f"Database file {db_path} does not exist.")