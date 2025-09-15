import sys
import os
from datetime import date, timedelta

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from app.storage.db import SessionLocal
from app.rules.engine import RulesEngine
from app.optimizer.simple_opt import handle_crew_unavailability

def test_crew_unavailability():
    """Test the crew unavailability handler directly"""
    try:
        print("Testing crew unavailability handler...")
        
        # Create a database session
        db = SessionLocal()
        
        # Create a rules engine
        rules = RulesEngine()
        
        # Test crew unavailability
        crew_id = 1
        unavailable_from = date.today()
        unavailable_to = date.today() + timedelta(days=2)
        
        print(f"Handling unavailability for crew {crew_id} from {unavailable_from} to {unavailable_to}")
        
        # Try to handle crew unavailability
        result = handle_crew_unavailability(db, crew_id, unavailable_from, unavailable_to, rules)
        
        print(f"Result: {result}")
        
        # Close the database session
        db.close()
        
        print("Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_crew_unavailability()