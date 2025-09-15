import sys
import os
# Add backend to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Set working directory to backend for proper imports
os.chdir(backend_path)

from sqlalchemy.orm import sessionmaker
from backend.app.storage.db import engine
from backend.app.storage.models import DutyPeriod, DutyFlight, Flight, Crew
from datetime import date

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Check if there are duty periods
    duty_count = db.query(DutyPeriod).count()
    print(f"Duty periods count: {duty_count}")
    
    # Check if there are duty flights
    duty_flight_count = db.query(DutyFlight).count()
    print(f"Duty flights count: {duty_flight_count}")
    
    # Check if there are flights
    flight_count = db.query(Flight).count()
    print(f"Flights count: {flight_count}")
    
    # Check if there are crew
    crew_count = db.query(Crew).count()
    print(f"Crew count: {crew_count}")
    
    if duty_count > 0:
        # Get a few duty periods
        duties = db.query(DutyPeriod).limit(5).all()
        print("\nSample duty periods:")
        for duty in duties:
            print(f"  Duty ID: {duty.duty_id}, Crew ID: {duty.crew_id}, Start: {duty.duty_start_utc}, End: {duty.duty_end_utc}")
    
    if duty_flight_count > 0:
        # Get a few duty flights
        duty_flights = db.query(DutyFlight).limit(5).all()
        print("\nSample duty flights:")
        for df in duty_flights:
            print(f"  Duty ID: {df.duty_id}, Flight ID: {df.flight_id}, Leg Seq: {df.leg_seq}")
            
finally:
    db.close()