import requests
from datetime import date, timedelta

# Test roster generation
try:
    # Get today's date and next week
    today = date.today()
    next_week = today + timedelta(days=7)
    
    payload = {
        "period_start": today.isoformat(),
        "period_end": next_week.isoformat(),
        "rules_version": "v1"
    }
    
    print("Testing roster generation...")
    print(f"Payload: {payload}")
    
    response = requests.post("http://127.0.0.1:8000/v1/rosters/generate", json=payload, timeout=30)
    print("Roster generation response:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Success! Generated roster with:")
        print(f"  Status: {data.get('status')}")
        print(f"  Period: {data.get('period_start')} to {data.get('period_end')}")
        print(f"  Assignments: {len(data.get('assignments', []))}")
        print(f"  KPIs: {data.get('kpis')}")
        
        # Show first few assignments
        assignments = data.get('assignments', [])
        if assignments:
            print("\nFirst 3 assignments:")
            for i, assignment in enumerate(assignments[:3]):
                print(f"  {i+1}. Crew: {assignment.get('crew_id')}, Flight: {assignment.get('flight_id')}")
    else:
        print("Error:", response.text)
except requests.exceptions.RequestException as e:
    print("Roster generation failed:", e)
except Exception as e:
    print("Unexpected error:", e)