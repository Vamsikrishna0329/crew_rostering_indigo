from sqlalchemy.orm import sessionmaker
from app.storage.db import engine
from app.storage.models import CrewPreference
from datetime import date, timedelta

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Insert sample crew preferences
preferences = [
    # Crew 1 prefers days off on Sundays
    CrewPreference(
        crew_id=1,
        preference_type="day_off",
        preference_value="Sunday",
        weight=5,
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365)
    ),
    # Crew 1 prefers base DEL
    CrewPreference(
        crew_id=1,
        preference_type="base",
        preference_value="DEL",
        weight=3,
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365)
    ),
    # Crew 2 prefers days off on Saturdays
    CrewPreference(
        crew_id=2,
        preference_type="day_off",
        preference_value="Saturday",
        weight=5,
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365)
    ),
    # Crew 2 prefers base BLR
    CrewPreference(
        crew_id=2,
        preference_type="base",
        preference_value="BLR",
        weight=3,
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365)
    ),
    # Crew 3 prefers days off on Fridays
    CrewPreference(
        crew_id=3,
        preference_type="day_off",
        preference_value="Friday",
        weight=5,
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365)
    ),
    # Crew 3 prefers base HYD
    CrewPreference(
        crew_id=3,
        preference_type="base",
        preference_value="HYD",
        weight=3,
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365)
    )
]

try:
    db.add_all(preferences)
    db.commit()
    print("Sample crew preferences inserted successfully")
except Exception as e:
    db.rollback()
    print(f"Error inserting sample crew preferences: {e}")
finally:
    db.close()