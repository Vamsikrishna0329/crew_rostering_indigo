import requests
import json
from datetime import date, timedelta

# Test the enhanced rostering functionality
BASE_URL = "http://127.0.0.1:8000/v1"

def test_generate_roster():
    """Test generating a roster with the enhanced optimizer"""
    print("Testing roster generation...")
    
    # Get today's date and next week's date
    today = date.today()
    next_week = today + timedelta(days=7)
    
    payload = {
        "period_start": today.isoformat(),
        "period_end": next_week.isoformat(),
        "rules_version": "v1"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/rosters/generate", json=payload)
        print(f"Roster generation response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Generated roster with {len(data.get('assignments', []))} assignments")
            print(f"Assignment rate: {data.get('kpis', {}).get('assignment_rate', 0):.2%}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error generating roster: {e}")

def test_delay_rerostering():
    """Test handling a flight delay"""
    print("\nTesting delay rerostering...")
    
    payload = {
        "flight_no": "6E1001",
        "type": "Delay",
        "delay_minutes": 60
    }
    
    try:
        response = requests.post(f"{BASE_URL}/reroster", json=payload)
        print(f"Delay rerostering response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Rerostering status: {data.get('status')}")
            print(f"Patch: {data.get('patch')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error handling delay: {e}")

def test_cancellation_rerostering():
    """Test handling a flight cancellation"""
    print("\nTesting cancellation rerostering...")
    
    payload = {
        "flight_no": "6E1002",
        "type": "Cancellation"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/reroster", json=payload)
        print(f"Cancellation rerostering response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Rerostering status: {data.get('status')}")
            print(f"Patch: {data.get('patch')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error handling cancellation: {e}")

def test_crew_unavailability_rerostering():
    """Test handling crew unavailability"""
    print("\nTesting crew unavailability rerostering...")
    
    payload = {
        "flight_no": "6E1003",
        "type": "CrewUnavailability",
        "crew_id": 1,
        "unavailable_from": date.today().isoformat(),
        "unavailable_to": (date.today() + timedelta(days=2)).isoformat()
    }
    
    try:
        response = requests.post(f"{BASE_URL}/reroster", json=payload)
        print(f"Crew unavailability rerostering response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Rerostering status: {data.get('status')}")
            print(f"Patch: {data.get('patch')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error handling crew unavailability: {e}")

def test_ai_suggestions():
    """Test AI suggestions for a flight"""
    print("\nTesting AI suggestions...")
    
    try:
        response = requests.post(f"{BASE_URL}/ai/reroster_suggest", json={"flight_no": "6E1001"})
        print(f"AI suggestions response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"AI suggestion: {data}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error getting AI suggestions: {e}")

def test_ai_disruption_handling():
    """Test AI handling of disruptions"""
    print("\nTesting AI disruption handling...")
    
    payload = {
        "flight_no": "6E1001",
        "disruption_type": "Delay"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ai/handle_disruption", json=payload)
        print(f"AI disruption handling response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"AI disruption handling: {data}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error handling disruption with AI: {e}")

if __name__ == "__main__":
    print("Testing enhanced crew rostering functionality...")
    test_generate_roster()
    test_delay_rerostering()
    test_cancellation_rerostering()
    test_crew_unavailability_rerostering()
    test_ai_suggestions()
    test_ai_disruption_handling()
    print("\nTesting completed.")