import sys
import os
import json
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
# Limit crew pool to 10 as in the updated code
if "crew_pool" in context and len(context["crew_pool"]) > 10:
    context["crew_pool"] = context["crew_pool"][:10]
print(f"Context size: {len(str(context))} characters")

# Check total prompt size with updated format
user_prompt = "Flight: " + json.dumps(context["flight"]) + "\nCrew: " + json.dumps(context["crew_pool"])
print(f"Total prompt size: {len(user_prompt)} characters")

# Show prompt preview
print(f"Prompt preview: {user_prompt[:500]}...")

db.close()