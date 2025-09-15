import os
import sys
from datetime import date, datetime, timedelta

# Add backend to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Set the working directory to backend for proper imports
os.chdir(backend_path)

from app.storage.db import SessionLocal
from app.storage.models import DutyPeriod, DutyFlight, Flight, Crew
from app.services.orchestrator import run_generate_roster

def test_duty_creation():
    # Create database session
    db = SessionLocal()
    
    try:
        # Generate a roster for a week
        period_start = date.today()
        period_end = period_start + timedelta(days=7)
        
        print(f"Generating roster for {period_start} to {period_end}")
        
        # Run roster generation
        assignments, kpis = run_generate_roster(db, period_start, period_end, "v1", "simple")
        
        print(f"Generated {len(assignments)} assignments")
        print(f"Assignment rate: {kpis.get('assignment_rate', 0):.2%}")
        
        # Check duty tables
        duty_count = db.query(DutyPeriod).count()
        duty_flight_count = db.query(DutyFlight).count()
        
        print(f"Duty periods created: {duty_count}")
        print(f"Duty flights created: {duty_flight_count}")
        
        # Show some sample duty data
        if duty_count > 0:
            sample_duties = db.query(DutyPeriod).limit(5).all()
            print("\nSample duty periods:")
            for duty in sample_duties:
                crew = db.query(Crew).filter(Crew.crew_id == duty.crew_id).first()
                print(f"  Duty {duty.duty_id}: {crew.name if crew else 'Unknown'} - {duty.duty_start_utc} to {duty.duty_end_utc}")
        
        if duty_flight_count > 0:
            sample_duty_flights = db.query(DutyFlight).join(DutyPeriod).limit(5).all()
            print("\nSample duty flights:")
            for df in sample_duty_flights:
                duty = db.query(DutyPeriod).filter(DutyPeriod.duty_id == df.duty_id).first()
                flight = db.query(Flight).filter(Flight.flight_id == df.flight_id).first()
                crew = db.query(Crew).filter(Crew.crew_id == duty.crew_id).first() if duty else None
                print(f"  Duty {df.duty_id} -> Flight {flight.flight_no if flight else 'Unknown'} for {crew.name if crew else 'Unknown'}")
        
        return duty_count > 0 and duty_flight_count > 0
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_duty_creation()
    if success:
        print("\n[SUCCESS] Duty creation test passed!")
    else:
        print("\n[FAILED] Duty creation test failed!")