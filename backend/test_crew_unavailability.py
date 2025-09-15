import requests
import json
from datetime import date, timedelta

# Test the crew unavailability functionality
BASE_URL = "http://127.0.0.1:8000/v1"

def test_crew_unavailability():
    """Test handling crew unavailability"""
    print("Testing crew unavailability...")
    
    # Test with proper parameters
    payload = {
        "flight_no": "6E1003",
        "type": "CrewUnavailability",
        "crew_id": 1,
        "unavailable_from": date.today().isoformat(),
        "unavailable_to": (date.today() + timedelta(days=2)).isoformat()
    }
    
    print(f"Sending payload: {payload}")
    
    try:
        response = requests.post(f"{BASE_URL}/reroster", json=payload)
        print(f"Crew unavailability response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Rerostering status: {data.get('status')}")
            print(f"Patch: {data.get('patch')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error handling crew unavailability: {e}")

if __name__ == "__main__":
    test_crew_unavailability()