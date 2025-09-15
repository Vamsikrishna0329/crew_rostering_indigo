import sys
import os
sys.path.append("backend")

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join("backend", ".env")
load_dotenv(env_path)

# Set the correct database path
os.environ["SQLITE_PATH"] = "./backend/data/crew_rostering.db"

from sqlalchemy.orm import sessionmaker
from backend.app.storage.db import engine
from backend.app.services.ai_service import build_context_for_flight

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Check context for a specific flight
context = build_context_for_flight(db, "6E1000")
print(f"Context size: {len(str(context))} characters")
print(f"Number of crew in pool: {len(context.get('crew_pool', []))}")

# Show first few crew members
crew_pool = context.get('crew_pool', [])
print(f"First 5 crew members: {crew_pool[:5]}")

# Check total context
print(f"Context preview: {str(context)[:500]}...")

db.close()