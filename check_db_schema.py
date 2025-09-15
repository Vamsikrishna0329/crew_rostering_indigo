import sqlite3
import os

# Connect to the database
db_path = "backend/data/crew_rostering.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check schema for all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Database schema:")
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] == 1 else ''} {'NOT NULL' if col[3] == 1 else ''}")
    
    conn.close()
else:
    print(f"Database file {db_path} does not exist.")