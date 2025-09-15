import requests
import json
from datetime import date, timedelta

# Debug the rerostering functionality
BASE_URL = "http://127.0.0.1:8000/v1"

def debug_cancellation_rerostering():
    """Debug handling a flight cancellation"""
    print("Debugging cancellation rerostering...")
    
    payload = {
        "flight_no": "6E1002",
        "type": "Cancellation"
    }
    
    print(f"Sending payload: {payload}")
    
    try:
        response = requests.post(f"{BASE_URL}/reroster", json=payload)
        print(f"Cancellation rerostering response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"Rerostering status: {data.get('status')}")
            print(f"Patch: {data.get('patch')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error handling cancellation: {e}")

def debug_crew_unavailability_rerostering():
    """Debug handling crew unavailability"""
    print("\nDebugging crew unavailability rerostering...")
    
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
        print(f"Crew unavailability rerostering response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"Rerostering status: {data.get('status')}")
            print(f"Patch: {data.get('patch')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error handling crew unavailability: {e}")

if __name__ == "__main__":
    debug_cancellation_rerostering()
    debug_crew_unavailability_rerostering()