from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.storage.db import Base, engine
from app.storage.models import BaseAirport, AircraftType, Crew, CrewQualification, Flight, DutyPeriod, DutyFlight, DGCAConstraints
from datetime import datetime, date, timedelta
import random

# Create all tables
Base.metadata.create_all(bind=engine)

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Check if data already exists
if db.query(BaseAirport).count() == 0:
    print("Initializing database with sample data...")
    
    # Insert base airports
    airports = [
        BaseAirport(iata="DEL", city="Delhi", tz="Asia/Kolkata"),
        BaseAirport(iata="BLR", city="Bengaluru", tz="Asia/Kolkata"),
        BaseAirport(iata="HYD", city="Hyderabad", tz="Asia/Kolkata"),
        BaseAirport(iata="BOM", city="Mumbai", tz="Asia/Kolkata"),
        BaseAirport(iata="MAA", city="Chennai", tz="Asia/Kolkata"),
    ]
    db.add_all(airports)
    print("Inserted airports")
    
    # Insert aircraft types
    aircraft_types = [
        AircraftType(code="A320", description="Airbus A320"),
        AircraftType(code="A321", description="Airbus A321"),
    ]
    db.add_all(aircraft_types)
    print("Inserted aircraft types")
    
    # Insert DGCA constraints
    constraints = DGCAConstraints(
        version="v1",
        max_duty_hours_per_day=10.0,
        min_rest_hours_after_duty=12.0,
        max_fdp_hours=13.0,
        max_duty_hours_per_week=60.0,
        max_duty_hours_per_month=200.0,
        max_consecutive_duty_days=5,
        min_rest_hours_between_duties=10.0,
        max_night_duties_per_week=3,
        min_rest_hours_after_night_duty=14.0,
        max_extended_fdp_hours=15.0,
        max_flight_time_per_day=9.0,
        max_flight_time_per_week=50.0,
        max_flight_time_per_month=180.0,
        notes="POC defaults with extended DGCA constraints"
    )
    db.add(constraints)
    print("Inserted DGCA constraints")
    
    # Insert crew members
    ranks = ["Captain", "FirstOfficer"]
    bases = ["DEL", "BLR", "HYD", "BOM", "MAA"]
    crew_members = []
    
    for i in range(1, 1001):
        crew = Crew(
            crew_id=i,
            emp_code=f"E{i:04d}",
            name=f"Crew {i}",
            rank=random.choice(ranks),
            base_iata=random.choice(bases),
            status="Active"
        )
        crew_members.append(crew)
    
    db.add_all(crew_members)
    print("Inserted crew members")
    
    # Insert crew qualifications
    qualifications = []
    aircraft_codes = ["A320", "A321"]
    
    for crew in crew_members:
        # Most crew qualified for A320, some also for A321
        qualifications.append(CrewQualification(
            crew_id=crew.crew_id,
            aircraft_code="A320",
            qualified_on=date(2024, 1, 1)
        ))
        
        # 30% of crew also qualified for A321
        if random.random() < 0.3:
            qualifications.append(CrewQualification(
                crew_id=crew.crew_id,
                aircraft_code="A321",
                qualified_on=date(2024, 1, 1)
            ))
    
    db.add_all(qualifications)
    print("Inserted crew qualifications")
    
    # Insert flights for the next 30 days
    flights = []
    flight_routes = [
        ("HYD", "BOM"), ("BLR", "DEL"), ("HYD", "BOM"), ("DEL", "MAA"),
        ("BOM", "BLR"), ("MAA", "HYD"), ("DEL", "BOM"), ("BLR", "MAA"),
        ("HYD", "DEL"), ("BOM", "MAA"), ("DEL", "BLR"), ("MAA", "BOM")
    ]
    
    flight_id = 1
    base_date = date.today()
    
    for day in range(30):
        current_date = base_date + timedelta(days=day)
        # 450 flights per day
        for route_idx in range(450):
            dep_iata, arr_iata = flight_routes[route_idx % len(flight_routes)]
            aircraft_code = random.choice(aircraft_codes)
            
            # Generate flight times
            hour = random.randint(0, 23)
            minute = random.choice([0, 15, 30, 45])
            dep_time = datetime(current_date.year, current_date.month, current_date.day, hour, minute)
            # Flight duration between 1 and 3 hours
            duration = timedelta(hours=random.randint(1, 3), minutes=random.choice([0, 15, 30, 45]))
            arr_time = dep_time + duration
            
            flight = Flight(
                flight_id=flight_id,
                flight_no=f"6E{1000 + flight_id}",
                flight_date=current_date,
                dep_iata=dep_iata,
                arr_iata=arr_iata,
                sched_dep_utc=dep_time,
                sched_arr_utc=arr_time,
                aircraft_code=aircraft_code
            )
            flights.append(flight)
            flight_id += 1
    
    # Insert in batches to avoid memory issues
    batch_size = 1000
    for i in range(0, len(flights), batch_size):
        batch = flights[i:i + batch_size]
        db.add_all(batch)
        db.commit()
        print(f"Inserted flights batch {i//batch_size + 1}/{(len(flights)-1)//batch_size + 1}")
    
    print("Database initialization complete")
else:
    print("Database already contains data")

db.close()