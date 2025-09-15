import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'data', 'crew_rostering.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Modify the disruption_record table to allow NULL flight_no
    cursor.execute("PRAGMA foreign_keys = OFF")
    cursor.execute("ALTER TABLE disruption_record RENAME TO disruption_record_old")
    
    # Create the new table with the correct schema
    cursor.execute("""
        CREATE TABLE disruption_record (
            disruption_id INTEGER PRIMARY KEY,
            flight_no TEXT,
            disruption_type TEXT NOT NULL,
            disruption_date DATE NOT NULL,
            impact_duration INTEGER,
            crew_id INTEGER,
            reason TEXT,
            resolution TEXT,
            recorded_at TEXT NOT NULL,
            resolved_at TEXT,
            FOREIGN KEY (crew_id) REFERENCES crew (crew_id)
        )
    """)
    
    # Copy data from the old table to the new table
    cursor.execute("""
        INSERT INTO disruption_record 
        SELECT disruption_id, flight_no, disruption_type, disruption_date, impact_duration, 
               crew_id, reason, resolution, recorded_at, resolved_at
        FROM disruption_record_old
    """)
    
    # Drop the old table
    cursor.execute("DROP TABLE disruption_record_old")
    
    # Commit the changes
    conn.commit()
    print("Successfully updated disruption_record table schema")
    
except Exception as e:
    print(f"Error updating database schema: {e}")
    conn.rollback()
finally:
    conn.close()