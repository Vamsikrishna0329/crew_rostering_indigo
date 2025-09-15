import requests
from datetime import date, timedelta
import sqlite3
import os

# Generate a roster
try:
    # Get today's date and next week
    today = date.today()
    next_week = today + timedelta(days=7)
    
    payload = {
        "period_start": today.isoformat(),
        "period_end": next_week.isoformat(),
        "rules_version": "v1"
    }
    
    print("Generating roster...")
    response = requests.post("http://127.0.0.1:8000/v1/rosters/generate", json=payload, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        assignments = data.get('assignments', [])
        print(f"Generated roster with {len(assignments)} assignments")
        
        # Connect to the database
        db_path = "backend/data/crew_rostering.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if there are existing duty periods
            cursor.execute("SELECT COUNT(*) FROM duty_period;")
            existing_duty_count = cursor.fetchone()[0]
            
            if existing_duty_count > 0:
                print("Duty periods already exist in database. Skipping save.")
            else:
                # Save assignments to database
                duty_id = 1
                duty_flight_id = 1
                
                for assignment in assignments:
                    crew_id = assignment.get('crew_id')
                    flight_id = assignment.get('flight_id')
                    
                    # Only save assigned flights (not unassigned ones)
                    if crew_id is not None:
                        # Get flight details to get base and times
                        cursor.execute("SELECT dep_iata, sched_dep_utc, sched_arr_utc FROM flight WHERE flight_id = ?", (flight_id,))
                        flight_row = cursor.fetchone()
                        
                        if flight_row:
                            dep_iata, sched_dep_utc, sched_arr_utc = flight_row
                            
                            # Insert duty period
                            cursor.execute("""
                                INSERT INTO duty_period (duty_id, crew_id, duty_start_utc, duty_end_utc, base_iata)
                                VALUES (?, ?, ?, ?, ?)
                            """, (duty_id, crew_id, sched_dep_utc, sched_arr_utc, dep_iata))
                            
                            # Insert duty flight
                            cursor.execute("""
                                INSERT INTO duty_flight (duty_id, flight_id, leg_seq)
                                VALUES (?, ?, ?)
                            """, (duty_id, flight_id, 1))
                            
                            duty_id += 1
                
                conn.commit()
                print(f"Saved {duty_id-1} duty periods to database")
            
            conn.close()
        else:
            print(f"Database file {db_path} does not exist.")
    else:
        print("Error generating roster:", response.text)
        
except requests.exceptions.RequestException as e:
    print("Error:", e)
except Exception as e:
    print("Unexpected error:", e)