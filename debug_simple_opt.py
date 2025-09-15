import sys
import os
from datetime import date, timedelta

# Add the backend directory to the path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from app.storage.db import SessionLocal
from app.rules.engine import RulesEngine
from app.optimizer.simple_opt import generate_roster

def test_simple_opt():
    """Test the simple optimizer directly"""
    try:
        print("Testing simple optimizer...")
        
        # Create a database session
        db = SessionLocal()
        
        # Create a rules engine
        rules = RulesEngine()
        
        # Get today's date and next week's date
        today = date.today()
        next_week = today + timedelta(days=7)
        
        print(f"Generating roster for period: {today} to {next_week}")
        
        # Try to generate a roster
        assignments, kpis = generate_roster(db, today, next_week, rules)
        
        print(f"Generated {len(assignments)} assignments")
        print(f"KPIs: {kpis}")
        
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
    test_simple_opt()