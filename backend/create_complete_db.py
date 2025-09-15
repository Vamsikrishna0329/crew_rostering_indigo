from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.storage.db import Base, engine
from app.storage.models import BaseAirport, AircraftType, Crew, CrewQualification, Flight, DutyPeriod, DutyFlight, DGCAConstraints, CrewPreference
from datetime import datetime, date, timedelta
import random

# Create all tables
Base.metadata.create_all(bind=engine)

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Check if data already exists
    if db.query(BaseAirport).count() == 0:
        print("Initializing database with complete sample data...")
        
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
        
        # Insert DGCA constraints with all enhanced fields
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
            notes="Complete POC defaults with all DGCA constraints"
        )
        db.add(constraints)
        print("Inserted DGCA constraints")
        
        # Insert crew members with real names
        ranks = ["Captain", "FirstOfficer"]
        bases = ["DEL", "BLR", "HYD", "BOM", "MAA"]
        first_names = ["Aarav", "Vivaan", "Aditya", "Arjun", "Reyansh", "Krishna", "Rudra", "Dhruv", "Kabir", "Ritvik",
                      "Aanya", "Diya", "Ira", "Anika", "Kavya", "Shreya", "Isha", "Meera", "Prisha", "Riya"]
        last_names = ["Sharma", "Verma", "Gupta", "Mehta", "Reddy", "Patel", "Singh", "Kumar", "Das", "Mishra"]
        
        crew_members = []
        
        for i in range(1, 1001):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            crew = Crew(
                crew_id=i,
                emp_code=f"E{i:04d}",
                name=f"{first_name} {last_name}",
                rank=random.choice(ranks),
                base_iata=random.choice(bases),
                status="Active"
            )
            crew_members.append(crew)
        
        db.add_all(crew_members)
        print("Inserted crew members")
        
        # Insert crew qualifications with expiry dates
        qualifications = []
        aircraft_codes = ["A320", "A321"]
        
        for crew in crew_members:
            # Most crew qualified for A320, some also for A321
            qualifications.append(CrewQualification(
                crew_id=crew.crew_id,
                aircraft_code="A320",
                qualified_on=date(2024, 1, 1),
                expires_on=date(2026, 1, 1)  # Valid for 2 years
            ))
            
            # 30% of crew also qualified for A321
            if random.random() < 0.3:
                qualifications.append(CrewQualification(
                    crew_id=crew.crew_id,
                    aircraft_code="A321",
                    qualified_on=date(2024, 1, 1),
                    expires_on=date(2026, 1, 1)  # Valid for 2 years
                ))
        
        db.add_all(qualifications)
        print("Inserted crew qualifications")
        
        # Insert crew preferences
        preferences = []
        
        # Add some sample preferences for first 10 crew members
        for i in range(1, 11):
            # Day off preference
            preferences.append(CrewPreference(
                crew_id=i,
                preference_type="day_off",
                preference_value=random.choice(["Sunday", "Saturday", "Friday"]),
                weight=random.randint(1, 10),
                valid_from=date.today(),
                valid_to=date.today() + timedelta(days=365)
            ))
            
            # Base preference
            preferences.append(CrewPreference(
                crew_id=i,
                preference_type="base",
                preference_value=random.choice(bases),
                weight=random.randint(1, 10),
                valid_from=date.today(),
                valid_to=date.today() + timedelta(days=365)
            ))
        
        db.add_all(preferences)
        print("Inserted crew preferences")
        
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
        
        # Insert sample duty periods and duty flights
        print("Inserting sample duty periods and duty flights...")
        duty_periods = []
        duty_flights = []
        duty_id = 1
        
        # Create some sample duty periods for the first 100 crew members
        for crew_id in range(1, 101):
            # Create 5 duty periods for each crew member
            for duty_num in range(5):
                # Get a random flight for this crew member
                flight = random.choice(flights)
                
                duty_period = DutyPeriod(
                    duty_id=duty_id,
                    crew_id=crew_id,
                    duty_start_utc=flight.sched_dep_utc,
                    duty_end_utc=flight.sched_arr_utc,
                    base_iata=flight.dep_iata
                )
                duty_periods.append(duty_period)
                
                duty_flight = DutyFlight(
                    duty_id=duty_id,
                    flight_id=flight.flight_id,
                    leg_seq=1
                )
                duty_flights.append(duty_flight)
                
                duty_id += 1
        
        db.add_all(duty_periods)
        db.add_all(duty_flights)
        db.commit()
        print(f"Inserted {len(duty_periods)} duty periods and {len(duty_flights)} duty flights")
        
        print("Database initialization complete")
    else:
        print("Database already contains data")
    
    # Verify the database structure
    print("\nDatabase verification:")
    print(f"Airports: {db.query(BaseAirport).count()}")
    print(f"Aircraft types: {db.query(AircraftType).count()}")
    print(f"Crew members: {db.query(Crew).count()}")
    print(f"Crew qualifications: {db.query(CrewQualification).count()}")
    print(f"Crew preferences: {db.query(CrewPreference).count()}")
    print(f"Flights: {db.query(Flight).count()}")
    print(f"DGCA constraints: {db.query(DGCAConstraints).count()}")
    print(f"Duty periods: {db.query(DutyPeriod).count()}")
    print(f"Duty flights: {db.query(DutyFlight).count()}")
    
    # Show sample data
    print("\nSample DGCA constraints:")
    constraints = db.query(DGCAConstraints).first()
    if constraints:
        print(f"  Version: {constraints.version}")
        print(f"  Max duty hours per day: {constraints.max_duty_hours_per_day}")
        print(f"  Max duty hours per week: {constraints.max_duty_hours_per_week}")
        print(f"  Max consecutive duty days: {constraints.max_consecutive_duty_days}")
    
    print("\nSample crew preferences:")
    prefs = db.query(CrewPreference).limit(5).all()
    for pref in prefs:
        print(f"  Crew {pref.crew_id}: {pref.preference_type} = {pref.preference_value} (weight: {pref.weight})")
    
    print("\nSample crew members:")
    crew_samples = db.query(Crew).limit(5).all()
    for crew in crew_samples:
        print(f"  {crew.emp_code}: {crew.name} ({crew.rank}) at {crew.base_iata}")
        
    print("\nSample duty periods:")
    duty_samples = db.query(DutyPeriod).limit(3).all()
    for duty in duty_samples:
        print(f"  Duty {duty.duty_id}: Crew {duty.crew_id} from {duty.duty_start_utc} to {duty.duty_end_utc}")
        
    print("\nSample duty flights:")
    duty_flight_samples = db.query(DutyFlight).limit(3).all()
    for df in duty_flight_samples:
        print(f"  Duty {df.duty_id} -> Flight {df.flight_id} (leg {df.leg_seq})")
        
except Exception as e:
    print(f"Error initializing database: {e}")
    db.rollback()
finally:
    db.close()